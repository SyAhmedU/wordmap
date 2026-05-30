"""
fetch_openalex.py — Build the full 84-year + 30-year projection dataset.

Real data:   1970-2024  (OpenAlex Social Sciences, title+abstract search)
Projected:   2025-2054  (logistic extrapolation per term)

Usage:
    python fetch_openalex.py

Outputs: words.json  +  data.js
Cache:   openalex_cache.json  (stores ALL years returned by OpenAlex;
          re-run safe — only re-fetches if a key is missing)
"""

import json, time, math
from pathlib import Path
import urllib.request, urllib.parse

# ── Config ───────────────────────────────────────────────────────────────────
YEAR_REAL_MIN = 1970
YEAR_REAL_MAX = 2024
YEAR_PROJ_MIN = 2025
YEAR_PROJ_MAX = 2054

EMAIL      = "asrarsaa@gmail.com"
SLEEP      = 0.15
CACHE_FILE = Path(__file__).parent / "openalex_cache.json"
OUT_JSON   = Path(__file__).parent / "words.json"
OUT_JS     = Path(__file__).parent / "data.js"

BASE_URL   = "https://api.openalex.org/works"
SS_CONCEPT = "C17744445"

YEARS_REAL = list(range(YEAR_REAL_MIN, YEAR_REAL_MAX + 1))
YEARS_PROJ = list(range(YEAR_PROJ_MIN, YEAR_PROJ_MAX + 1))
YEARS_ALL  = YEARS_REAL + YEARS_PROJ

# ── Groups ───────────────────────────────────────────────────────────────────
GROUPS = [
    {"id": "sociology",         "label": "Sociology",         "color": "#e74c8e"},
    {"id": "political_science", "label": "Political Science", "color": "#5b8def"},
    {"id": "economics",         "label": "Economics",         "color": "#22c55e"},
    {"id": "psychology",        "label": "Psychology",        "color": "#a78bfa"},
    {"id": "anthropology",      "label": "Anthropology",      "color": "#f59e0b"},
    {"id": "communication",     "label": "Communication",     "color": "#06b6d4"},
    {"id": "methods",           "label": "Emerging & Computational",           "color": "#94a3b8"},
]

# ── Terms ─────────────────────────────────────────────────────────────────────
TERMS = [
    # SOCIOLOGY
    ("social capital",        "social capital",           "sociology"),
    ("class",                 "social class",             "sociology"),
    ("inequality",            "inequality",               "sociology"),
    ("intersectionality",     "intersectionality",        "sociology"),
    ("race",                  "race racism",              "sociology"),
    ("gender",                "gender",                   "sociology"),
    ("identity",              "social identity",          "sociology"),
    ("network",               "social network",           "sociology"),
    ("family",                "family",                   "sociology"),
    ("modernity",             "modernity",                "sociology"),
    ("postmodern",            "postmodernism",            "sociology"),
    ("structuralism",         "structuralism",            "sociology"),
    ("habitus",               "habitus",                  "sociology"),
    ("solidarity",            "solidarity",               "sociology"),
    ("migration",             "migration",                "sociology"),
    # POLITICAL SCIENCE
    ("neoliberalism",         "neoliberalism",            "political_science"),
    ("democracy",             "democracy",                "political_science"),
    ("populism",              "populism",                 "political_science"),
    ("authoritarianism",      "authoritarianism",         "political_science"),
    ("globalization",         "globalization",            "political_science"),
    ("polarization",          "political polarization",   "political_science"),
    ("nationalism",           "nationalism",              "political_science"),
    ("cold war",              "cold war",                 "political_science"),
    ("voting",                "voting behavior",          "political_science"),
    ("election",              "election",                 "political_science"),
    ("governance",            "governance",               "political_science"),
    ("institutions",          "institutions",             "political_science"),
    ("populist",              "populist",                 "political_science"),
    ("brexit",                "brexit",                   "political_science"),
    # ECONOMICS
    ("economic growth",       "economic growth",          "economics"),
    ("inflation",             "inflation",                "economics"),
    ("recession",             "recession",                "economics"),
    ("financial crisis",      "financial crisis",         "economics"),
    ("development",           "economic development",     "economics"),
    ("trade",                 "international trade",      "economics"),
    ("labor",                 "labor market",             "economics"),
    ("automation",            "automation",               "economics"),
    ("microfinance",          "microfinance",             "economics"),
    ("behavioral economics",  "behavioral economics",     "economics"),
    ("rational choice",       "rational choice",          "economics"),
    ("game theory",           "game theory",              "economics"),
    ("welfare state",         "welfare state",            "economics"),
    ("austerity",             "austerity",                "economics"),
    # PSYCHOLOGY
    ("cognitive",             "cognitive",                "psychology"),
    ("anxiety",               "anxiety",                  "psychology"),
    ("depression",            "depression",               "psychology"),
    ("trauma",                "trauma",                   "psychology"),
    ("wellbeing",             "wellbeing",                "psychology"),
    ("mental health",         "mental health",            "psychology"),
    ("emotion",               "emotion",                  "psychology"),
    ("personality",           "personality",              "psychology"),
    ("self-esteem",           "self-esteem",              "psychology"),
    ("attachment",            "attachment theory",        "psychology"),
    ("burnout",               "burnout",                  "psychology"),
    ("mindfulness",           "mindfulness",              "psychology"),
    ("therapy",               "therapy",                  "psychology"),
    ("cognitive bias",        "cognitive bias",           "psychology"),
    ("childhood",             "childhood",                "psychology"),
    # ANTHROPOLOGY
    ("kinship",               "kinship",                  "anthropology"),
    ("ritual",                "ritual",                   "anthropology"),
    ("ethnography",           "ethnography",              "anthropology"),
    ("colonial",              "colonial",                 "anthropology"),
    ("postcolonial",          "postcolonial",             "anthropology"),
    ("indigenous",            "indigenous",               "anthropology"),
    ("decolonial",            "decolonial",               "anthropology"),
    ("culture",               "culture",                  "anthropology"),
    ("ethnicity",             "ethnicity",                "anthropology"),
    ("body",                  "body",                     "anthropology"),
    ("religion",              "religion",                 "anthropology"),
    # COMMUNICATION
    ("media",                 "media",                    "communication"),
    ("internet",              "internet",                 "communication"),
    ("social media",          "social media",             "communication"),
    ("misinformation",        "misinformation",           "communication"),
    ("disinformation",        "disinformation",           "communication"),
    ("digital media",         "digital media",            "communication"),
    ("platform",              "digital platform",         "communication"),
    ("algorithm",             "algorithm",                "communication"),
    ("audience",              "audience",                 "communication"),
    ("framing",               "framing",                  "communication"),
    ("propaganda",            "propaganda",               "communication"),
    ("twitter",               "twitter",                  "communication"),
    # METHODS
    ("machine learning",      "machine learning",         "methods"),
    ("big data",              "big data",                 "methods"),
    ("text analysis",         "text analysis",            "methods"),
    ("causal inference",      "causal inference",         "methods"),
    ("covid",                 "covid",                    "methods"),
    ("pandemic",              "pandemic",                 "methods"),
    ("climate change",        "climate change",           "methods"),
    ("artificial intelligence","artificial intelligence", "methods"),
    # ── EXPANSION 2026: substantive social-science constructs/topics ──
    ("social mobility",       "social mobility",          "sociology"),
    ("stigma",                "social stigma",            "sociology"),
    ("social movements",      "social movements",         "sociology"),
    ("precarity",             "precarity",                "sociology"),
    ("gentrification",        "gentrification",           "sociology"),
    ("cultural capital",      "cultural capital",         "sociology"),
    ("surveillance",          "surveillance",             "sociology"),
    ("civil society",         "civil society",            "political_science"),
    ("legitimacy",            "political legitimacy",     "political_science"),
    ("political trust",       "political trust",          "political_science"),
    ("state capacity",        "state capacity",           "political_science"),
    ("financialization",      "financialization",         "economics"),
    ("informal economy",      "informal economy",         "economics"),
    ("universal basic income","universal basic income",   "economics"),
    ("loneliness",            "loneliness",               "psychology"),
    ("resilience",            "psychological resilience", "psychology"),
    ("prejudice",             "prejudice",                "psychology"),
    ("prosocial behavior",    "prosocial behavior",       "psychology"),
    ("moral judgment",        "moral judgment",           "psychology"),
    ("embodiment",            "embodiment",               "anthropology"),
    ("materiality",           "materiality",              "anthropology"),
    ("echo chamber",          "echo chamber",             "communication"),
    ("parasocial",            "parasocial",               "communication"),
    ("media literacy",        "media literacy",           "communication"),
    ("computational social science","computational social science","methods"),
    ("algorithmic bias",      "algorithmic bias",         "methods"),
    ("datafication",          "datafication",             "methods"),
    ("generative ai",         "generative artificial intelligence","methods"),
]

# ── OpenAlex fetch (stores ALL years — no year filter) ────────────────────────
def fetch_all_years(search_query=None):
    filter_parts = [f"concepts.id:{SS_CONCEPT}"]
    if search_query:
        safe = search_query.replace('"', '')
        filter_parts.append(f'title_and_abstract.search:"{safe}"')
    params = {
        "filter":   ",".join(filter_parts),
        "group_by": "publication_year",
        "per-page": "200",
        "mailto":   EMAIL,
    }
    url = BASE_URL + "?" + urllib.parse.urlencode(params)
    for attempt in range(3):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": f"WordMap/2.0 (mailto:{EMAIL})"})
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read())
            result = {}
            for g in data.get("group_by", []):
                try:
                    result[int(g["key"])] = g["count"]
                except (ValueError, KeyError):
                    pass
            return result
        except Exception as exc:
            print(f"  [retry {attempt+1}/3] {exc}")
            time.sleep(2 ** attempt)
    print("  FAILED — returning empty")
    return {}

# ── Cache ─────────────────────────────────────────────────────────────────────
def load_cache():
    if CACHE_FILE.exists():
        raw = json.loads(CACHE_FILE.read_text())
        # Convert string keys to int (JSON serializes int keys as strings)
        return {k: {int(yr): cnt for yr, cnt in v.items()} for k, v in raw.items()}
    return {}

def save_cache(cache):
    # Store with string keys for JSON compatibility
    serialisable = {k: {str(yr): cnt for yr, cnt in v.items()} for k, v in cache.items()}
    CACHE_FILE.write_text(json.dumps(serialisable, separators=(",", ":")))

# ── Projection ────────────────────────────────────────────────────────────────
def project_shares(real_counts, baseline_proj):
    """
    Logistic / decay extrapolation for YEARS_PROJ based on YEARS_REAL trend.

    Returns {year: projected_share} for YEARS_PROJ.

    Method:
      - Use last 7 years of real data to estimate CAGR
      - Growing terms  (CAGR > 2%): logistic growth toward a cap
      - Declining terms(CAGR < -2%): exponential decay toward a floor
      - Stable terms              : gradual mean-reversion
    """
    WINDOW = 7
    recent_real = YEARS_REAL[-WINDOW:]

    # Get shares for recent real years
    real_shares = []
    for y in recent_real:
        base = 1
        cnt  = real_counts.get(y, 0)
        # We need baseline to compute share — use a flat reference since
        # we already have share stored; here we just use raw counts with
        # relative comparison (absolute scale corrected later by caller)
        real_shares.append(cnt)

    # Remove zero prefix
    nonzero = [(y, s) for y, s in zip(recent_real, real_shares) if s > 0]
    if len(nonzero) < 2:
        return {y: 0 for y in YEARS_PROJ}

    s0 = nonzero[0][1]
    s1 = nonzero[-1][1]
    span = nonzero[-1][0] - nonzero[0][0]
    cagr = (s1 / s0) ** (1 / span) - 1 if span > 0 and s0 > 0 else 0.0

    current_count = real_counts.get(YEAR_REAL_MAX, s1)

    projected = {}
    for i, y in enumerate(YEARS_PROJ):
        t = i + 1
        base_proj = baseline_proj.get(y, 1)

        if cagr > 0.02:
            # Logistic: grows toward cap, slowing as it approaches
            K_count = current_count * min((1 + cagr) ** 20, 8)
            proj_count = K_count / (1 + (K_count / max(current_count, 1) - 1) * math.exp(-cagr * 0.6 * t))
        elif cagr < -0.02:
            # Exponential decay toward a floor (5% of current)
            floor = max(current_count * 0.05, 1)
            proj_count = floor + (current_count - floor) * math.exp(cagr * t)
        else:
            # Stable: tiny drift toward 95% of current
            proj_count = current_count * (1 + (0.95 - 1) * t / 30)

        proj_count = max(proj_count, 0)
        projected[y] = proj_count / base_proj if base_proj > 0 else 0.0

    return projected

# ── Baseline projection (total SS papers 2025-2054) ──────────────────────────
def project_baseline(real_baseline):
    """Project total SS papers per year for the forecast window."""
    WINDOW = 7
    recent = [(y, real_baseline.get(y, 0)) for y in YEARS_REAL[-WINDOW:] if real_baseline.get(y, 0) > 0]
    if len(recent) < 2:
        last = real_baseline.get(YEAR_REAL_MAX, 1_000_000)
        return {y: last for y in YEARS_PROJ}

    s0, s1 = recent[0][1], recent[-1][1]
    span   = recent[-1][0] - recent[0][0]
    cagr   = (s1 / s0) ** (1 / span) - 1 if span > 0 and s0 > 0 else 0.03
    # Cap SS growth at 5%/yr — digitisation and scope will slow it
    cagr   = min(cagr, 0.05)

    current = real_baseline.get(YEAR_REAL_MAX, s1)
    result  = {}
    for i, y in enumerate(YEARS_PROJ):
        t = i + 1
        K = current * 4
        result[y] = int(K / (1 + (K / current - 1) * math.exp(-cagr * t)))
    return result

# ── Metric helpers ────────────────────────────────────────────────────────────
def compute_growth(by_year_counts, window=5):
    result = {}
    for y in YEARS_ALL:
        past = y - window
        c = by_year_counts.get(y, 0)
        p = by_year_counts.get(past, 0)
        if p > 0 and c >= 0:
            result[y] = round((max(c, 0) / p) ** (1 / window) - 1, 4)
        else:
            result[y] = 2.0 if c > 0 else 0.0
    return result

def compute_novelty(by_year_counts, last_n=5):
    total  = sum(by_year_counts.get(y, 0) for y in YEARS_REAL) or 1
    recent = sum(by_year_counts.get(y, 0) for y in YEARS_REAL[-last_n:])
    return round(recent / total, 4)

# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    cache = load_cache()
    n = len(TERMS)

    # 1. Baseline
    BASELINE_KEY = "__baseline__"
    if BASELINE_KEY not in cache or max(cache[BASELINE_KEY]) < 1975:
        print("Fetching SS baseline (all years)...")
        cache[BASELINE_KEY] = fetch_all_years(search_query=None)
        save_cache(cache)
        time.sleep(SLEEP)
    else:
        print("Baseline cached.")

    real_baseline = {y: cache[BASELINE_KEY].get(y, 0) for y in YEARS_REAL}
    baseline_proj = project_baseline(real_baseline)
    baseline_all  = {**real_baseline, **{y: baseline_proj[y] for y in YEARS_PROJ}}
    for y in YEARS_ALL:
        baseline_all.setdefault(y, 1)

    print(f"Baseline 1970:{real_baseline.get(1970,'?'):,}  1990:{real_baseline.get(1990,'?'):,}  2024:{real_baseline.get(2024,'?'):,}")

    # 2. Fetch each term
    terms_out = []
    for i, (display, query, group) in enumerate(TERMS):
        cache_key = query
        # Re-fetch if cache only has post-1989 data (old format)
        cached = cache.get(cache_key, {})
        if not cached or max((k for k in cached if isinstance(k, int)), default=1990) < 1975:
            print(f"[{i+1}/{n}] {display!r} -> '{query}'...", end=" ", flush=True)
            cached = fetch_all_years(search_query=query)
            cache[cache_key] = cached
            save_cache(cache)
            time.sleep(SLEEP)
            total = sum(cached.get(y, 0) for y in YEARS_REAL)
            print(f"{total:,} papers (real)")
        else:
            print(f"[{i+1}/{n}] {display!r} -- cached ({max(k for k in cached if isinstance(k,int))} max yr)")

        real_counts = {y: cached.get(y, 0) for y in YEARS_REAL}

        # Project forward
        proj_shares = project_shares(real_counts, baseline_proj)

        growth  = compute_growth({**real_counts, **{y: int(proj_shares[y] * baseline_all.get(y,1)) for y in YEARS_PROJ}})
        novelty = compute_novelty(real_counts)

        by_year = {}

        # Real years
        for y in YEARS_REAL:
            raw   = real_counts.get(y, 0)
            base  = baseline_all.get(y, 1)
            share = raw / base if base > 0 else 0.0
            by_year[str(y)] = {
                "c": raw,
                "s": round(share, 6),
                "g": growth.get(y, 0.0),
                "n": novelty,
            }

        # Projected years
        for y in YEARS_PROJ:
            share = proj_shares.get(y, 0.0)
            base  = baseline_all.get(y, 1)
            raw   = int(share * base)
            by_year[str(y)] = {
                "c": raw,
                "s": round(share, 6),
                "g": growth.get(y, 0.0),
                "n": novelty,
                "p": 1,            # p=1 flags this as a projection
            }

        terms_out.append({"term": display, "group": group, "by_year": by_year})

    # 3. Annual volume
    annual_volume = {}
    for y in YEARS_REAL:
        annual_volume[str(y)] = real_baseline.get(y, 0)
    for y in YEARS_PROJ:
        annual_volume[str(y)] = baseline_proj.get(y, 0)

    # 4. Payload
    payload = {
        "meta": {
            "year_min":       YEAR_REAL_MIN,
            "year_max":       YEAR_PROJ_MAX,
            "real_year_min":  YEAR_REAL_MIN,
            "real_year_max":  YEAR_REAL_MAX,
            "proj_year_min":  YEAR_PROJ_MIN,
            "proj_year_max":  YEAR_PROJ_MAX,
            "groups":         GROUPS,
            "metrics": [
                {"id": "s", "label": "Doc-frequency share", "unit": "%",    "fmt": "pct",
                 "desc": "Fraction of SS papers mentioning the term"},
                {"id": "g", "label": "5-yr growth (CAGR)",  "unit": "%/yr", "fmt": "pct_signed",
                 "desc": "Compound annual growth rate over 5 years"},
                {"id": "n", "label": "Novelty",             "unit": "",     "fmt": "pct",
                 "desc": "Share of all-time mentions in last 5 real years"},
                {"id": "c", "label": "Raw count",           "unit": "",     "fmt": "int",
                 "desc": "Papers mentioning the term in that year"},
            ],
            "n_terms":        len(terms_out),
            "annual_volume":  annual_volume,
            "source_note":    f"Real: OpenAlex Social Sciences {YEAR_REAL_MIN}-{YEAR_REAL_MAX} | Projected: logistic extrapolation {YEAR_PROJ_MIN}-{YEAR_PROJ_MAX}",
        },
        "terms": terms_out,
    }

    compact = json.dumps(payload, separators=(",", ":"))
    OUT_JSON.write_text(compact, encoding="utf-8")
    OUT_JS.write_text("window.__WORDS_DATA__ = " + compact + ";", encoding="utf-8")

    print(f"\nWrote {OUT_JSON}  ({OUT_JSON.stat().st_size:,} bytes)")
    print(f"Wrote {OUT_JS}    ({OUT_JS.stat().st_size:,} bytes)")
    print(f"  {len(terms_out)} terms x {len(YEARS_ALL)} years ({len(YEARS_REAL)} real + {len(YEARS_PROJ)} projected)")

if __name__ == "__main__":
    main()
