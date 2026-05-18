import sys
sys.path.insert(0, '.')
from dotenv import load_dotenv; load_dotenv()
from app import _dre_ler_lancamentos, _ler_lancamentos_jun_jul, _dre_calcular, _BRT
from datetime import datetime
from calendar import monthrange

hoje = datetime.now(_BRT)
mes_ini = hoje.month + 1
ano_ini = hoje.year - 1
if mes_ini > 12:
    mes_ini -= 12
    ano_ini += 1
d_ini = datetime(ano_ini, mes_ini, 1)
d_fim = datetime(hoje.year, hoje.month, monthrange(hoje.year, hoje.month)[1], 23, 59, 59)

print(f'Periodo: {d_ini.strftime("%m/%Y")} a {d_fim.strftime("%m/%Y")}')

todos = _dre_ler_lancamentos() + _ler_lancamentos_jun_jul()
filtrados = [l for l in todos if d_ini <= l["dt"] <= d_fim]
print(f'Lancamentos no periodo: {len(filtrados)}')

dre = _dre_calcular(filtrados)
print(f'Receita Liquida: R$ {dre["receita_liquida"]:,.2f}')
print(f'EBITDA:          R$ {dre["ebitda"]:,.2f}')
print(f'M. EBITDA:       {dre["pct_ebitda"]*100:.2f}%')
print(f'Depreciacao:     R$ 363,911.40')
ebit = dre["ebitda"] - 363911.40
rl = dre["receita_liquida"]
print(f'EBIT ajustado:   R$ {ebit:,.2f}')
print(f'M. EBIT:         {(ebit/rl*100) if rl else 0:.2f}%')
