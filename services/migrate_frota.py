"""
One-time migration: Excel Frota_FIPE2.xlsx → Supabase tables
  frota_veiculos      — dados cadastrais dos veículos
  frota_fipe_historico — valores FIPE mensais (planilha + manual)

Run AFTER creating the tables in Supabase with the SQL in migrate_frota_ddl.sql.
"""
from __future__ import annotations
import os
import sys
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent / ".env")

XLSX_PATH = Path(__file__).resolve().parent / "docx_templates" / "Frota_FIPE2.xlsx"

# (col_index, mes_ref_label)
MESES_COLS = [
    (6,  "JAN/25"), (7,  "FEV/25"), (8,  "MAR/25"), (9,  "ABR/25"),
    (10, "MAI/25"), (11, "JUN/25"), (12, "JUL/25"), (13, "AGO/25"),
    (14, "SET/25"), (15, "OUT/25"), (16, "NOV/25"), (17, "DEZ/25"),
    (20, "JAN/26"), (21, "FEV/26"), (22, "MAR/26"), (23, "ABR/26"),
]


def _s(v):
    if v is None:
        return None
    s = str(v).strip()
    return s if s else None


def _n(v):
    if v is None:
        return None
    if isinstance(v, str) and v.strip() in ("", "← VIA API"):
        return None
    try:
        return float(v)
    except (ValueError, TypeError):
        return None


def _iso_date(v):
    """Converts dd/mm/yyyy string to ISO yyyy-mm-dd. Returns None on failure."""
    s = _s(v)
    if not s:
        return None
    for fmt in ("%d/%m/%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(s, fmt).strftime("%Y-%m-%d")
        except ValueError:
            pass
    return None


def read_excel():
    import openpyxl
    wb = openpyxl.load_workbook(str(XLSX_PATH), read_only=True, data_only=True)
    ws = wb["Frota_FIPE"]
    rows = list(ws.iter_rows(values_only=True))
    wb.close()

    veiculos = []
    historico = []  # (placa, mes_ref, valor)

    for row in rows[2:45]:
        modelo = _s(row[0])
        placa  = _s(row[1])
        if not modelo or not placa:
            continue

        dt_iso = _iso_date(row[4])
        vl     = _n(row[5])

        veiculos.append({
            "modelo":       modelo,
            "placa":        placa,
            "ano_modelo":   _s(row[2]),
            "cod_fipe":     _s(row[3]),
            "dt_aquisicao": dt_iso,
            "vl_aquisicao": vl,
            "ativo":        True,
        })

        for col_idx, mes_ref in MESES_COLS:
            valor = _n(row[col_idx])
            if valor is not None:
                historico.append({
                    "placa":        placa,
                    "mes_ref":      mes_ref,
                    "valor":        valor,
                    "fonte":        "planilha",
                    "atualizado_em": dt_iso or "2025-01-01",
                })

    return veiculos, historico


def migrate(dry_run=False):
    from supabase import create_client
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_KEY")
    if not url or not key:
        print("ERROR: SUPABASE_URL / SUPABASE_KEY não definidos em .env")
        sys.exit(1)

    sb = create_client(url, key)

    print("Lendo Excel...")
    veiculos, historico = read_excel()
    print(f"  {len(veiculos)} veículos, {len(historico)} entradas de histórico planilha")

    # Migrate fipe_manual rows
    print("Lendo fipe_manual (Supabase)...")
    res = sb.table("fipe_manual").select("placa, ref, valor, atualizado_em").execute()
    manual_rows = res.data or []
    print(f"  {len(manual_rows)} entradas manuais")

    manual_historico = []
    for row in manual_rows:
        manual_historico.append({
            "placa":        row["placa"],
            "mes_ref":      row["ref"],
            "valor":        float(row["valor"]),
            "fonte":        "manual",
            "atualizado_em": row.get("atualizado_em") or datetime.now().strftime("%Y-%m-%d"),
        })

    if dry_run:
        print("\n--- DRY RUN ---")
        print("frota_veiculos upsert:", len(veiculos), "rows")
        print("frota_fipe_historico planilha:", len(historico), "rows")
        print("frota_fipe_historico manual:", len(manual_historico), "rows")
        return

    # 1. Upsert frota_veiculos (conflict on placa)
    print("\nInserindo frota_veiculos...")
    sb.table("frota_veiculos").upsert(veiculos, on_conflict="placa").execute()
    print("  OK")

    # 2. Upsert frota_fipe_historico — planilha
    print("Inserindo frota_fipe_historico (planilha)...")
    BATCH = 100
    for i in range(0, len(historico), BATCH):
        sb.table("frota_fipe_historico").upsert(
            historico[i:i+BATCH], on_conflict="placa,mes_ref"
        ).execute()
    print(f"  {len(historico)} rows OK")

    # 3. Upsert frota_fipe_historico — manual (only if not already present as planilha)
    if manual_historico:
        print("Inserindo frota_fipe_historico (manual)...")
        # Manual rows win over planilha for same (placa, mes_ref) only if no planilha entry
        # Strategy: insert with ON CONFLICT DO NOTHING for planilha entries,
        # but for manual we want to upsert (they may have been entered after planilha)
        sb.table("frota_fipe_historico").upsert(
            manual_historico, on_conflict="placa,mes_ref"
        ).execute()
        print(f"  {len(manual_historico)} rows OK")

    print("\nMigração concluída.")
    print("Você pode agora testar a página /insights/frota.")
    print("Se tudo OK, pode apagar a tabela fipe_manual do Supabase.")


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--dry-run", action="store_true", help="Mostra o que seria feito sem executar")
    args = p.parse_args()
    migrate(dry_run=args.dry_run)
