import re
import requests
from datetime import datetime, timedelta

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.8",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Referer": "https://statusinvest.com.br/",
}

TICKERS = [
    {"ticker": "RENT3", "nome": "Localiza"},
    {"ticker": "MOVI3", "nome": "Movida"},
    {"ticker": "LCAM3", "nome": "Unidas"},
]

INDICADORES = [
    ("pl",            "P/L"),
    ("pvp",           "P/VP"),
    ("roe",           "ROE"),
    ("margem_bruta",  "M. Bruta"),
    ("margem_ebit",   "M. EBIT"),
    ("margem_ebitda", "M. EBITDA"),
    ("margem_liquida","M. Líquida"),
    ("div_ebitda",    "Dív. líq./EBITDA"),
    ("div_ebit",      "Dív. líq./EBIT"),
]

_cache: dict = {}
_CACHE_TTL = timedelta(hours=4)


def _get_html(ticker: str) -> str:
    url = f"https://statusinvest.com.br/acoes/{ticker.lower()}"
    r = requests.get(url, headers=HEADERS, timeout=15)
    r.raise_for_status()
    return r.text


def _extrair(html: str, label: str) -> str:
    """
    Localiza o label no HTML e retorna o valor na strong mais próxima.
    Tenta dois padrões diferentes para cobrir variações de estrutura.
    """
    escaped = re.escape(label)

    # Padrão 1: label aparece como texto, valor em <strong> nas próximas 300 chars
    m = re.search(
        escaped + r'[\s\S]{0,300}?<strong[^>]*>\s*([\d\.,\-\–]+\s*%?)\s*</strong>',
        html, re.IGNORECASE
    )
    if m:
        return m.group(1).strip()

    # Padrão 2: valor em span/b/div imediatamente após o label
    m = re.search(
        escaped + r'[^<]{0,80}<(?:span|b|div)[^>]*>\s*([\d\.,\-\–]+\s*%?)\s*</',
        html, re.IGNORECASE
    )
    if m:
        return m.group(1).strip()

    return "N/D"


def scrape_ticker(ticker: str) -> dict:
    try:
        html = _get_html(ticker)
        resultado = {"ticker": ticker, "erro": None}
        for chave, label in INDICADORES:
            resultado[chave] = _extrair(html, label)
        return resultado
    except Exception as e:
        return {"ticker": ticker, "erro": str(e),
                **{chave: "N/D" for chave, _ in INDICADORES}}


def obter_dados(forcar: bool = False) -> list[dict]:
    agora = datetime.now()
    if not forcar and _cache.get("dados") and agora - _cache["ts"] < _CACHE_TTL:
        return _cache["dados"]

    dados = [scrape_ticker(t["ticker"]) for t in TICKERS]

    for i, d in enumerate(dados):
        d["nome"] = TICKERS[i]["nome"]

    _cache["dados"] = dados
    _cache["ts"] = agora
    _cache["atualizado_em"] = agora.strftime("%d/%m/%Y %H:%M")
    return dados


def cache_info() -> str:
    return _cache.get("atualizado_em", "Nunca")
