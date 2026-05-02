"""
Pilot dataset for the Social Science Research Word-Map.

Generates a realistic year-by-term frequency dataset modeled on actual
known disciplinary trends in social-science research, 1970-2025.

This script produces the same SHAPE of output that a real Scopus or
OpenAlex pipeline would. To swap in real data later, replace the
`seeded_terms()` function with one that pulls article abstracts,
tokenizes, counts, and emits the same dict structure.

Output: words.json (consumed by index.html)
Schema:
{
  "meta": {
    "year_min": 1970, "year_max": 2025,
    "groups": [{"id": "sociology", "label": "Sociology", "color": "#..."} ...],
    "metrics": [{"id": "share", "label": "Doc-frequency share", ...}, ...]
  },
  "terms": [
    {
      "term": "neoliberalism",
      "group": "political_science",
      "by_year": {
        "1970": {"count": 3, "share": 0.0001, "growth_5y": 0.0},
        ...
      }
    }
  ]
}
"""

import json
import math
import random
from pathlib import Path

random.seed(42)

YEAR_MIN, YEAR_MAX = 1970, 2025
YEARS = list(range(YEAR_MIN, YEAR_MAX + 1))

# Approximate annual article volume for our 5-journal social-science pilot.
# Real social-science publishing volume has roughly 4-5x'd since 1970.
def annual_volume(year):
    # Sigmoid-ish growth from ~600 articles/yr in 1970 to ~3000 in 2025
    t = (year - YEAR_MIN) / (YEAR_MAX - YEAR_MIN)
    return int(600 + 2400 * (1 / (1 + math.exp(-6 * (t - 0.55)))))


GROUPS = [
    {"id": "sociology",         "label": "Sociology",         "color": "#e74c8e"},
    {"id": "political_science", "label": "Political Science", "color": "#5b8def"},
    {"id": "economics",         "label": "Economics",         "color": "#22c55e"},
    {"id": "psychology",        "label": "Psychology",        "color": "#a78bfa"},
    {"id": "anthropology",      "label": "Anthropology",      "color": "#f59e0b"},
    {"id": "communication",     "label": "Communication",     "color": "#06b6d4"},
    {"id": "methods",           "label": "Methods",           "color": "#94a3b8"},
]


def shape(kind, peak=2000, width=15, base=0.0005, peak_val=0.05):
    """Return a function year -> share given a curve kind.

    Shapes are calibrated to look like real bibliometric trajectories.
    """
    def gauss(year):
        return base + (peak_val - base) * math.exp(-((year - peak) ** 2) / (2 * width ** 2))

    def logistic_rise(year):
        # rises to peak_val around 'peak', stays high
        return base + (peak_val - base) / (1 + math.exp(-(year - peak) / (width / 4)))

    def logistic_fall(year):
        return base + (peak_val - base) * (1 - 1 / (1 + math.exp(-(year - peak) / (width / 4))))

    def flat(year):
        return base + 0.7 * peak_val

    def late_explosion(year):
        # very small until peak-5, then explodes
        if year < peak - 5:
            return base
        return base + (peak_val - base) / (1 + math.exp(-(year - peak) / (width / 5)))

    def emergent(year):
        # zero before peak-3, then sigmoidal up
        if year < peak - 3:
            return 0.0
        return (peak_val) / (1 + math.exp(-(year - peak) / 3))

    return {
        "gauss": gauss,
        "rise": logistic_rise,
        "fall": logistic_fall,
        "flat": flat,
        "late": late_explosion,
        "emergent": emergent,
    }[kind]


# (term, group, shape, peak_year, width, base_share, peak_share)
# Calibrated against real, well-known trajectories in social-science
# discourse. Numbers are realistic orders of magnitude for share-of-articles.
SEEDS = [
    # SOCIOLOGY
    ("social capital",        "sociology", "gauss", 2005, 12, 0.0005, 0.045),
    ("class",                 "sociology", "fall",  1985, 25, 0.012,  0.060),
    ("inequality",            "sociology", "rise",  2012, 18, 0.008,  0.065),
    ("intersectionality",     "sociology", "late",  2018, 8,  0.0001, 0.055),
    ("race",                  "sociology", "rise",  2018, 30, 0.012,  0.072),
    ("gender",                "sociology", "rise",  2010, 25, 0.005,  0.078),
    ("identity",              "sociology", "gauss", 2008, 18, 0.004,  0.055),
    ("network",               "sociology", "rise",  2010, 20, 0.002,  0.052),
    ("family",                "sociology", "flat",  2000, 30, 0.022,  0.030),
    ("modernity",             "sociology", "gauss", 1995, 12, 0.001,  0.030),
    ("postmodern",            "sociology", "gauss", 1998, 10, 0.0005, 0.022),
    ("structuralism",         "sociology", "fall",  1980, 12, 0.0005, 0.025),
    ("habitus",               "sociology", "gauss", 2008, 15, 0.0005, 0.012),
    ("solidarity",            "sociology", "fall",  1985, 25, 0.005,  0.018),
    ("migration",             "sociology", "rise",  2015, 22, 0.004,  0.048),

    # POLITICAL SCIENCE
    ("neoliberalism",         "political_science", "rise",  2010, 15, 0.0005, 0.058),
    ("democracy",             "political_science", "flat",  2000, 30, 0.045,  0.062),
    ("populism",              "political_science", "late",  2018, 7,  0.0008, 0.052),
    ("authoritarianism",      "political_science", "gauss", 2020, 12, 0.005,  0.040),
    ("globalization",         "political_science", "gauss", 2003, 10, 0.002,  0.058),
    ("polarization",          "political_science", "late",  2020, 6,  0.0015, 0.048),
    ("nationalism",           "political_science", "rise",  2018, 22, 0.008,  0.040),
    ("cold war",              "political_science", "fall",  1988, 8,  0.001,  0.038),
    ("soviet",                "political_science", "fall",  1988, 8,  0.0005, 0.045),
    ("voting",                "political_science", "flat",  2000, 30, 0.025,  0.035),
    ("election",              "political_science", "rise",  2018, 25, 0.012,  0.045),
    ("governance",            "political_science", "rise",  2008, 18, 0.003,  0.042),
    ("institutions",          "political_science", "rise",  2005, 22, 0.008,  0.040),
    ("populist",              "political_science", "late",  2019, 7,  0.0005, 0.030),
    ("brexit",                "political_science", "emergent", 2018, 5, 0.0,  0.018),
    ("trump",                 "political_science", "emergent", 2020, 5, 0.0,  0.025),

    # ECONOMICS
    ("growth",                "economics", "flat",  2000, 30, 0.040,  0.055),
    ("inflation",             "economics", "gauss", 1980, 8,  0.005,  0.045),
    ("recession",             "economics", "gauss", 2010, 8,  0.002,  0.040),
    ("financial crisis",      "economics", "gauss", 2012, 7,  0.0001, 0.045),
    ("development",           "economics", "rise",  2005, 25, 0.020,  0.060),
    ("trade",                 "economics", "flat",  2000, 35, 0.025,  0.038),
    ("labor",                 "economics", "flat",  2000, 35, 0.030,  0.045),
    ("automation",            "economics", "late",  2020, 8,  0.0008, 0.032),
    ("inequality (econ)",     "economics", "rise",  2015, 15, 0.003,  0.055),
    ("supply",                "economics", "flat",  1990, 35, 0.020,  0.030),
    ("microfinance",          "economics", "gauss", 2008, 10, 0.0001, 0.018),
    ("behavioral",            "economics", "rise",  2015, 20, 0.001,  0.030),
    ("rational choice",       "economics", "gauss", 1995, 15, 0.0005, 0.025),
    ("game theory",           "economics", "gauss", 1998, 18, 0.001,  0.028),
    ("welfare",               "economics", "fall",  1985, 25, 0.012,  0.030),
    ("austerity",             "economics", "gauss", 2014, 7,  0.0001, 0.022),

    # PSYCHOLOGY
    ("cognitive",             "psychology", "rise", 2005, 25, 0.012,  0.060),
    ("anxiety",               "psychology", "rise", 2018, 18, 0.005,  0.052),
    ("depression",            "psychology", "rise", 2015, 22, 0.008,  0.060),
    ("trauma",                "psychology", "rise", 2018, 18, 0.003,  0.048),
    ("wellbeing",             "psychology", "rise", 2018, 15, 0.0008, 0.050),
    ("mental health",         "psychology", "rise", 2020, 12, 0.005,  0.058),
    ("emotion",               "psychology", "rise", 2008, 22, 0.005,  0.048),
    ("personality",           "psychology", "flat", 2000, 30, 0.020,  0.030),
    ("self-esteem",           "psychology", "gauss",1998, 14, 0.001,  0.028),
    ("attachment",            "psychology", "gauss",2002, 18, 0.001,  0.032),
    ("burnout",               "psychology", "late", 2020, 8,  0.0005, 0.028),
    ("mindfulness",           "psychology", "late", 2018, 9,  0.0001, 0.035),
    ("therapy",               "psychology", "flat", 2000, 30, 0.018,  0.028),
    ("bias",                  "psychology", "rise", 2015, 18, 0.005,  0.038),
    ("identity (psy)",        "psychology", "rise", 2010, 20, 0.005,  0.038),
    ("childhood",             "psychology", "flat", 2000, 30, 0.012,  0.020),

    # ANTHROPOLOGY
    ("kinship",               "anthropology", "fall", 1985, 18, 0.005,  0.040),
    ("ritual",                "anthropology", "fall", 1990, 20, 0.004,  0.030),
    ("ethnography",           "anthropology", "rise", 2008, 25, 0.005,  0.045),
    ("colonial",              "anthropology", "fall", 1985, 18, 0.008,  0.035),
    ("postcolonial",          "anthropology", "gauss",2005, 14, 0.0005, 0.032),
    ("indigenous",            "anthropology", "rise", 2015, 18, 0.003,  0.045),
    ("decolonial",            "anthropology", "late", 2020, 8,  0.0001, 0.028),
    ("culture",               "anthropology", "flat", 2000, 35, 0.030,  0.045),
    ("ethnicity",             "anthropology", "rise", 2008, 20, 0.005,  0.038),
    ("body",                  "anthropology", "rise", 2010, 18, 0.002,  0.030),
    ("globalization (anth)",  "anthropology", "gauss",2005, 12, 0.001,  0.038),
    ("religion",              "anthropology", "flat", 2000, 35, 0.018,  0.030),

    # COMMUNICATION
    ("media",                 "communication", "rise", 2010, 22, 0.012,  0.060),
    ("internet",              "communication", "rise", 2010, 14, 0.0001, 0.055),
    ("social media",          "communication", "late", 2017, 9,  0.0001, 0.060),
    ("misinformation",        "communication", "emergent", 2020, 5, 0.0,  0.030),
    ("disinformation",        "communication", "emergent", 2021, 5, 0.0,  0.022),
    ("digital",               "communication", "rise", 2015, 18, 0.001,  0.060),
    ("platform",              "communication", "late", 2020, 8,  0.0003, 0.045),
    ("algorithm",             "communication", "late", 2020, 8,  0.0001, 0.038),
    ("audience",              "communication", "flat", 2000, 25, 0.012,  0.022),
    ("framing",               "communication", "rise", 2008, 18, 0.003,  0.030),
    ("propaganda",            "communication", "fall", 1985, 18, 0.005,  0.018),
    ("twitter",               "communication", "emergent", 2017, 6, 0.0,  0.028),

    # METHODS / CROSS-CUTTING
    ("qualitative",           "methods", "rise", 2010, 25, 0.005,  0.060),
    ("quantitative",          "methods", "flat", 2000, 30, 0.025,  0.040),
    ("regression",            "methods", "flat", 2000, 30, 0.018,  0.030),
    ("survey",                "methods", "flat", 2000, 35, 0.020,  0.030),
    ("interview",             "methods", "rise", 2010, 22, 0.012,  0.040),
    ("case study",            "methods", "flat", 2000, 30, 0.012,  0.022),
    ("meta-analysis",         "methods", "rise", 2015, 18, 0.0005, 0.038),
    ("machine learning",      "methods", "late", 2020, 7,  0.0001, 0.030),
    ("big data",              "methods", "late", 2018, 8,  0.0001, 0.025),
    ("text analysis",         "methods", "rise", 2018, 15, 0.0005, 0.022),
    ("longitudinal",          "methods", "rise", 2008, 22, 0.005,  0.025),
    ("causal",                "methods", "rise", 2015, 15, 0.003,  0.035),
    ("experimental",          "methods", "rise", 2008, 20, 0.008,  0.028),
    ("ethnographic",          "methods", "rise", 2010, 22, 0.004,  0.025),
    ("covid",                 "methods", "emergent", 2021, 4, 0.0,  0.038),
    ("pandemic",              "methods", "emergent", 2021, 4, 0.0,  0.034),
    ("climate",               "methods", "rise", 2018, 15, 0.0008, 0.045),
    ("ai",                    "methods", "late", 2022, 5,  0.0005, 0.040),
    ("artificial intelligence","methods", "late", 2022, 5, 0.0001, 0.030),
]


def build_corpus():
    """Generate the full term x year matrix."""
    terms_data = []
    for term, group, kind, peak, width, base, peak_val in SEEDS:
        # share = fraction of articles in that year mentioning the term
        fn = shape(kind, peak=peak, width=width, base=base, peak_val=peak_val)
        by_year = {}
        for y in YEARS:
            share = max(0.0, fn(y))
            # add small year-to-year noise (±5% multiplicative)
            share *= 1 + random.uniform(-0.06, 0.06)
            share = max(0.0, share)
            volume = annual_volume(y)
            count = round(share * volume)
            by_year[y] = {
                "count": count,
                "share": share,
            }
        terms_data.append({
            "term": term,
            "group": group,
            "by_year": by_year,
        })
    return terms_data


def add_growth_metric(terms_data, window=5):
    """Add 5-year CAGR of share to each year-bucket."""
    for t in terms_data:
        ys = sorted(t["by_year"].keys())
        for y in ys:
            past = y - window
            if past in t["by_year"]:
                p_share = t["by_year"][past]["share"]
                c_share = t["by_year"][y]["share"]
                if p_share > 1e-6:
                    cagr = (c_share / p_share) ** (1 / window) - 1
                else:
                    # emerging from zero -- cap at +200%/yr
                    cagr = 2.0 if c_share > 0 else 0.0
                t["by_year"][y]["growth_5y"] = round(cagr, 4)
            else:
                t["by_year"][y]["growth_5y"] = 0.0


def add_novelty_metric(terms_data):
    """Novelty = fraction of all-time mentions occurring in the last 5 years."""
    for t in terms_data:
        all_counts = [t["by_year"][y]["count"] for y in YEARS]
        total = sum(all_counts) or 1
        recent_5 = sum(t["by_year"][y]["count"] for y in YEARS[-5:])
        novelty = recent_5 / total
        for y in YEARS:
            t["by_year"][y]["novelty"] = round(novelty, 4)


def to_compact(terms_data):
    """Convert string years and round numbers for smaller JSON."""
    out = []
    for t in terms_data:
        by_year = {}
        for y, vals in t["by_year"].items():
            by_year[str(y)] = {
                "c": vals["count"],
                "s": round(vals["share"], 5),
                "g": vals.get("growth_5y", 0.0),
                "n": vals.get("novelty", 0.0),
            }
        out.append({
            "term": t["term"],
            "group": t["group"],
            "by_year": by_year,
        })
    return out


def main():
    terms = build_corpus()
    add_growth_metric(terms)
    add_novelty_metric(terms)
    compact = to_compact(terms)

    payload = {
        "meta": {
            "year_min": YEAR_MIN,
            "year_max": YEAR_MAX,
            "groups": GROUPS,
            "metrics": [
                {"id": "s", "label": "Doc-frequency share", "unit": "%", "fmt": "pct",
                 "desc": "Percent of that year's articles containing the term"},
                {"id": "g", "label": "5-yr growth (CAGR)",   "unit": "%/yr", "fmt": "pct_signed",
                 "desc": "Compound annual growth rate of share over preceding 5 years"},
                {"id": "n", "label": "Novelty",              "unit": "",   "fmt": "pct",
                 "desc": "Share of total mentions occurring in last 5 years"},
                {"id": "c", "label": "Raw count",            "unit": "",   "fmt": "int",
                 "desc": "Number of articles in that year mentioning the term"},
            ],
            "n_terms": len(compact),
            "annual_volume": {str(y): annual_volume(y) for y in YEARS},
            "source_note": "Pilot dataset with seeded realistic trajectories (2026). Replace with real Scopus/OpenAlex extract.",
        },
        "terms": compact,
    }

    out_path = Path(__file__).parent / "words.json"
    out_path.write_text(json.dumps(payload, separators=(",", ":")))
    print(f"Wrote {out_path} ({out_path.stat().st_size:,} bytes)")

    # Also emit data.js so index.html can be opened directly via file://
    js_path = Path(__file__).parent / "data.js"
    js_path.write_text("window.__WORDS_DATA__ = " + json.dumps(payload, separators=(",", ":")) + ";")
    print(f"Wrote {js_path} ({js_path.stat().st_size:,} bytes)")
    print(f"  {len(compact)} terms x {len(YEARS)} years")
    # Quick sanity check
    sample = compact[0]
    print(f"  sample: '{sample['term']}' ({sample['group']}) — "
          f"share 1970={sample['by_year']['1970']['s']:.4f}, "
          f"share 2025={sample['by_year']['2025']['s']:.4f}")


if __name__ == "__main__":
    main()
years")
    sample = compact[0]
    print(f"  sample: '{sample['term']}' ({sample['group']}) "
          f"share 1970={sample['by_year']['1970']['s']:.4f}, "
          f"share 2025={sample['by_year']['2025']['s']:.4f}")


if __name__ == "__main__":
    main()
__ == "__main__":
    main()
