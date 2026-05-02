"""
fetch_openalex.py — Pull real bibliometric data from OpenAlex for Project 4 Word Map.

Uses the free OpenAlex API (no key needed).  Queries each term via
title+abstract search scoped to Social-Science papers, then computes
doc-frequency share, 5-yr CAGR growth, and novelty.

Usage:
    python fetch_openalex.py

Outputs: words.json  +  data.js  (same schema as build_data.py)
Cache:   openalex_cache.json (re-run safe — skips already-fetched terms)
"""

import json, time, sys, math
from pathlib import Path
import urllib.request, urllib.parse

# ── Config ───────────────────────────────────────────────────────────────────
YEAR_MIN    = 1990
YEAR_MAX    = 2024
EMAIL       = "asrarsaa@gmail.com"
SLEEP       = 0.15          # seconds between requests (polite pool = 100 req/s, we stay gentle)
CACHE_FILE  = Path(__file__).parent / "openalex_cache.json"
OUT_JSON    = Path(__file__).parent / "words.json"
OUT_JS      = Path(__file__).parent / "data.js"

BASE_URL    = "https://api.openalex.org/works"
SS_CONCEPT  = "C17744445"   # OpenAlex concept ID for "Social sciences"

# ── Groups / subfields ───────────────────────────────────────────────────────
GROUPS = [
    {"id": "sociology",         "label": "Sociology",         "color": "#e74c8e"},
    {"id": "political_science", "label": "Political Science", "color": "#5b8def"},
    {"id": "economics",         "label": "Economics",         "color": "#22c55e"},
    {"id": "psychology",        "label": "Psychology",        "color": "#a78bfa"},
    {"id": "anthropology",      "label": "Anthropology",      "color": "#f59e0b"},
    {"id": "communication",     "label": "Communication",     "color": "#06b6d4"},
    {"id": "methods",           "label": "Methods",           "color": "#94a3b8"},
]

# ── Term list: (display_name, search_query, group_id) ────────────────────────
# search_query is sent to OpenAlex title+abstract search.
# Disambiguated where plain words are too polysemous.
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

    # METHODS / CROSS-CUTTING
    ("qualitative",           "qualitative research",     "methods"),
    ("quantitative",          "quantitative research",    "methods"),
    ("regression",            "regression analysis",      "methods"),
    ("survey",                "survey",                   "methods"),
    ("interview",             "interview",                "methods"),
    ("case study",            "case study",               "methods"),
    ("meta-analysis",         "meta-analysis",            "methods"),
    ("machine learning",      "machine learning",         "methods"),
    ("big data",              "big data",                 "methods"),
    ("text analysis",         "text analysis",            "methods"),
    ("longitudinal",          "longitudinal",             "methods"),
    ("causal inference",      "causal inference",         "methods"),
    ("experimental",          "experimental",             "methods"),
    ("covid",                 "covid",                    "methods"),
    ("pandemic",              "pandemic",                 "methods"),
    ("climate change",        "climate change",           "methods"),
    ("artificial intelligence","artificial intelligence", "methods"),
]

YEARS = list(range(YEAR_MIN, YEAR_MAX + 1))


# ── HTTP helper ───────────────────────────────────────────────────────────────
def openalex_group_by_year(search_query=None):
    """
    Return {year: count} for papers matching search_query (optional),
    scoped to social-science concept, grouped by publication_year.
    """
    filter_parts = [f"concepts.id:{SS_CONCEPT}"]
    if search_query:
        # Escape quotes in the search string
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
            req = urllib.request.Request(url, headers={"User-Agent": f"WordMap/1.0 (mailto:{EMAIL})"})
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read())
            by_year = {}
            for g in data.get("group_by", []):
                try:
                    y = int(g["key"])
                    if YEAR_MIN <= y <= YEAR_MAX:
                        by_year[y] = g["count"]
                except (ValueError, KeyError):
                    pass
            return by_year
        except Exception as exc:
            print(f"  [retry {attempt+1}/3] {exc}")
            time.sleep(2 ** attempt)

    print(f"  FAILED after 3 attempts — returning zeros")
    return {}


# ── Cache ─────────────────────────────────────────────────────────────────────
def load_cache():
    if CACHE_FILE.exists():
        return json.loads(CACHE_FILE.read_text())
    return {}

def save_cache(cache):
    CACHE_FILE.write_text(json.dumps(cache, separators=(",", ":")))


# ── Metric helpers ────────────────────────────────────────────────────────────
def compute_growth(by_year_counts, window=5):
    """5-yr CAGR of doc-frequency share per year."""
    result = {}
    for y in YEARS:
        past = y - window
        if past in by_year_counts and y in by_year_counts:
            p = by_year_counts[past]
            c = by_year_counts[y]
            if p > 0:
                result[y] = round((c / p) ** (1 / window) - 1, 4)
            else:
                result[y] = 2.0 if c > 0 else 0.0
        else:
            result[y] = 0.0
    return result

def compute_novelty(by_year_counts, last_n=5):
    """Fraction of all-time mentions in the last N years."""
    total = sum(by_year_counts.get(y, 0) for y in YEARS) or 1
    recent = sum(by_year_counts.get(y, 0) for y in YEARS[-last_n:])
    return round(recent / total, 4)


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    cache = load_cache()
    n = len(TERMS)

    # 1. Fetch baseline (total SS articles per year)
    BASELINE_KEY = "__baseline__"
    if BASELINE_KEY not in cache:
        print("Fetching SS baseline (total articles per year)…")
        cache[BASELINE_KEY] = openalex_group_by_year(search_query=None)
        save_cache(cache)
        time.sleep(SLEEP)
    else:
        print("Baseline already cached.")

    baseline = {int(k): v for k, v in cache[BASELINE_KEY].items()} if isinstance(
        next(iter(cache[BASELINE_KEY]), 0), str) else cache[BASELINE_KEY]
    # Ensure all years present (fill zeros for missing years)
    for y in YEARS:
        baseline.setdefault(y, 1)

    print(f"Baseline SS papers — sample: {baseline.get(2020, '?')} in 2020, {baseline.get(2024, '?')} in 2024")

    # 2. Fetch each term
    terms_out = []
    for i, (display, query, group) in enumerate(TERMS):
        cache_key = query
        if cache_key not in cache:
            print(f"[{i+1}/{n}] {display!r} -> searching '{query}'...", end=" ", flush=True)
            counts = openalex_group_by_year(search_query=query)
            cache[cache_key] = counts
            save_cache(cache)
            time.sleep(SLEEP)
            total_in_range = sum(counts.get(y, 0) for y in YEARS)
            print(f"{total_in_range:,} papers")
        else:
            counts = cache[cache_key]
            print(f"[{i+1}/{n}] {display!r} — cached")

        # Normalise year keys to int
        counts_int = {}
        for k, v in counts.items():
            try:
                counts_int[int(k)] = v
            except ValueError:
                pass

        growth  = compute_growth(counts_int)
        novelty = compute_novelty(counts_int)

        by_year = {}
        for y in YEARS:
            raw   = counts_int.get(y, 0)
            base  = baseline.get(y, 1)
            share = raw / base if base > 0 else 0.0
            by_year[str(y)] = {
                "c": raw,
                "s": round(share, 6),
                "g": growth[y],
                "n": novelty,
            }

        terms_out.append({
            "term":    display,
            "group":   group,
            "by_year": by_year,
        })

    # 3. Build annual_volume from baseline
    annual_volume = {str(y): baseline.get(y, 0) for y in YEARS}

    # 4. Assemble payload
    payload = {
        "meta": {
            "year_min":      YEAR_MIN,
            "year_max":      YEAR_MAX,
            "groups":        GROUPS,
            "metrics": [
                {"id": "s", "label": "Doc-frequency share", "unit": "%",     "fmt": "pct",
                 "desc": "Fraction of that year's SS papers mentioning the term"},
                {"id": "g", "label": "5-yr growth (CAGR)",  "unit": "%/yr",  "fmt": "pct_signed",
                 "desc": "Compound annual growth rate of mention share over 5 years"},
                {"id": "n", "label": "Novelty",             "unit": "",      "fmt": "pct",
                 "desc": "Share of all-time mentions occurring in the last 5 years"},
                {"id": "c", "label": "Raw count",           "unit": "",      "fmt": "int",
                 "desc": "Number of SS papers in that year mentioning the term"},
            ],
            "n_terms":       len(terms_out),
            "annual_volume": annual_volume,
            "source_note":   f"OpenAlex API · Social Sciences concept (C17744445) · {YEAR_MIN}–{YEAR_MAX} · fetched 2026",
        },
        "terms": terms_out,
    }

    # 5. Write output
    compact = json.dumps(payload, separators=(",", ":"))
    OUT_JSON.write_text(compact, encoding="utf-8")
    OUT_JS.write_text("window.__WORDS_DATA__ = " + compact + ";", encoding="utf-8")

    print()
    print(f"Wrote {OUT_JSON}  ({OUT_JSON.stat().st_size:,} bytes)")
    print(f"Wrote {OUT_JS}    ({OUT_JS.stat().st_size:,} bytes)")
    print(f"  {len(terms_out)} terms × {len(YEARS)} years")


if __name__ == "__main__":
    main()
