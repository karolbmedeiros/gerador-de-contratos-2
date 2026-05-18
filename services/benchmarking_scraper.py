import requests
from bs4 import BeautifulSoup
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

# Chave interna → label exato que aparece no HTML do StatusInvest
LABEL_MAP = {
    "pl":             "P/L",
    "pvp":            "P/VP",
    "roe":            "ROE",
    "margem_bruta":   "M. Bruta",
    "margem_ebitda":  "M. EBITDA",
    "margem_ebit":    "M. EBIT",
    "margem_liquida": "M. Líquida",
    "div_ebitda":     "Dív. líquida/EBITDA",
    "div_ebit":       "Dív. líquida/EBIT",
}

INDICADORES = [
    ("pl",            "P/L"),
    ("pvp",           "P/VP"),
    ("roe",           "ROE"),
    ("margem_bruta",  "M. Bruta"),
    ("margem_ebitda", "M. EBITDA"),
    ("margem_ebit",   "M. EBIT"),
    ("margem_liquida","M. Líquida"),
    ("div_ebitda",    "Dív. Líq./EBITDA"),
    ("div_ebit",      "Dív. Líq./EBIT"),
]

_cache: dict = {}
_CACHE_TTL = timedelta(hours=24)


def _build_map(html: str) -> dict:
    """Extrai todos os indicadores da página, usando apenas o primeiro valor encontrado."""
    soup = BeautifulSoup(html, "html.parser")
    result = {}
    for h3 in soup.find_all("h3", class_=lambda c: c and "title" in c and "uppercase" in c):
        label = h3.get_text(strip=True)
        if label in result:
            continue
        strong = h3.find_next("strong", class_=lambda c: c and "value" in c)
        if strong:
            val = strong.get_text(strip=True)
            if val and val != "-":
                result[label] = val
    return result


def scrape_ticker(ticker: str) -> dict:
    try:
        url = f"https://statusinvest.com.br/acoes/{ticker.lower()}"
        r = requests.get(url, headers=HEADERS, timeout=15)
        r.raise_for_status()
        mapa = _build_map(r.text)
        resultado = {"ticker": ticker, "erro": None}
        for chave, label_html in LABEL_MAP.items():
            resultado[chave] = mapa.get(label_html, "N/D")
        return resultado
    except Exception as e:
        return {"ticker": ticker, "erro": str(e),
                **{chave: "N/D" for chave in LABEL_MAP}}


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
