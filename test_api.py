import urllib.request, urllib.parse, json

# Test 1: social capital term
filter_str = "concepts.id:C17744445,title_and_abstract.search:social capital"
params = {"filter": filter_str, "group_by": "publication_year", "per-page": "200", "mailto": "asrarsaa@gmail.com"}
url = "https://api.openalex.org/works?" + urllib.parse.urlencode(params)
req = urllib.request.Request(url, headers={"User-Agent": "WordMap/1.0 (mailto:asrarsaa@gmail.com)"})
with urllib.request.urlopen(req, timeout=15) as r:
    data = json.loads(r.read())
groups = data.get("group_by", [])
by_year = {int(g["key"]): g["count"] for g in groups if g["key"].isdigit() and 1990 <= int(g["key"]) <= 2024}
print(f"social capital — {len(by_year)} years, sample 2000-2024:")
for y in [2000, 2005, 2010, 2015, 2020, 2024]:
    print(f"  {y}: {by_year.get(y, 0):,}")

# Test 2: baseline (all SS papers)
filter_str2 = "concepts.id:C17744445"
params2 = {"filter": filter_str2, "group_by": "publication_year", "per-page": "200", "mailto": "asrarsaa@gmail.com"}
url2 = "https://api.openalex.org/works?" + urllib.parse.urlencode(params2)
req2 = urllib.request.Request(url2, headers={"User-Agent": "WordMap/1.0 (mailto:asrarsaa@gmail.com)"})
with urllib.request.urlopen(req2, timeout=15) as r2:
    data2 = json.loads(r2.read())
groups2 = data2.get("group_by", [])
base = {int(g["key"]): g["count"] for g in groups2 if g["key"].isdigit() and 1990 <= int(g["key"]) <= 2024}
print(f"\nBaseline (all SS) — {len(base)} years, sample:")
for y in [2000, 2005, 2010, 2015, 2020, 2024]:
    print(f"  {y}: {base.get(y, 0):,}")

# Test 3: compute share
print("\nDerived share (social capital / all SS):")
for y in [2000, 2005, 2010, 2015, 2020, 2024]:
    share = by_year.get(y, 0) / base.get(y, 1)
    print(f"  {y}: {share:.4f} ({share*100:.2f}%)")
