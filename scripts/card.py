"""GitHub 프로필 카드 SVG 생성. env: GH_TOKEN, GH_USER. 출력: profile-card.svg"""
import base64, datetime as dt, json, os, urllib.request
from html import escape

TOKEN, USER = os.environ["GH_TOKEN"], os.environ.get("GH_USER", "rianhq")
TODAY = dt.datetime.now(dt.timezone(dt.timedelta(hours=9))).date()


def gql(query, **variables):
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        json.dumps({"query": query, "variables": variables}).encode(),
        {"Authorization": f"bearer {TOKEN}", "Content-Type": "application/json"},
    )
    data = json.load(urllib.request.urlopen(req))
    if "errors" in data:
        raise SystemExit(data["errors"])
    return data["data"]["user"]


u = gql("""query($l:String!){user(login:$l){name login createdAt avatarUrl(size:96)
  followers{totalCount}
  repositories(ownerAffiliations:OWNER,first:100,isFork:false){totalCount
    nodes{stargazerCount languages(first:10){edges{size node{name color}}}}}
  contributionsCollection{contributionYears}}}""", l=USER)

# 연도별 달력(1년 단위 제한) 이어붙여 전체 일자 확보
days = {}
for y in u["contributionsCollection"]["contributionYears"]:
    c = gql("""query($l:String!,$f:DateTime!,$t:DateTime!){user(login:$l){
      contributionsCollection(from:$f,to:$t){contributionCalendar{weeks{contributionDays{date contributionCount}}}}}}""",
            l=USER, f=f"{y}-01-01T00:00:00Z", t=f"{y}-12-31T23:59:59Z")
    for w in c["contributionsCollection"]["contributionCalendar"]["weeks"]:
        for d in w["contributionDays"]:
            days[dt.date.fromisoformat(d["date"])] = d["contributionCount"]


def streaks(days, today):
    best = run = 0
    for d in sorted(days):
        if d > today:
            break
        run = run + 1 if days[d] else 0
        best = max(best, run)
    cur, d = 0, today if days.get(today) else today - dt.timedelta(days=1)  # 오늘 아직 0이면 어제부터
    while days.get(d):
        cur, d = cur + 1, d - dt.timedelta(days=1)
    return cur, best


cur, best = streaks(days, TODAY)
total = sum(days.values())
year = sum(v for d, v in days.items() if d.year == TODAY.year)

langs = {}
for r in u["repositories"]["nodes"]:
    for e in r["languages"]["edges"]:
        n = e["node"]["name"]
        langs.setdefault(n, [0, e["node"]["color"] or "#8b949e"])[0] += e["size"]
top = sorted(langs.items(), key=lambda kv: -kv[1][0])[:6]
lsum = sum(v[0] for _, v in top) or 1

avatar = base64.b64encode(urllib.request.urlopen(u["avatarUrl"]).read()).decode()

# ---- SVG ----
W, H = 820, 300
out = [f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" font-family="-apple-system,Segoe UI,Helvetica,Arial,sans-serif">
<style>
:root{{--bg:#ffffff;--bd:#d0d7de;--fg:#1f2328;--mu:#59636e;--c0:#ebedf0;--c1:#9be9a8;--c2:#40c463;--c3:#30a14e;--c4:#216e39}}
@media (prefers-color-scheme:dark){{:root{{--bg:#0d1117;--bd:#30363d;--fg:#e6edf3;--mu:#9198a1;--c0:#161b22;--c1:#0e4429;--c2:#006d32;--c3:#26a641;--c4:#39d353}}}}
.bg{{fill:var(--bg);stroke:var(--bd)}} .fg{{fill:var(--fg)}} .mu{{fill:var(--mu)}}
.c0{{fill:var(--c0)}} .c1{{fill:var(--c1)}} .c2{{fill:var(--c2)}} .c3{{fill:var(--c3)}} .c4{{fill:var(--c4)}}
.flame{{transform-origin:center bottom;transform-box:fill-box;animation:f 1.6s ease-in-out infinite alternate}}
@keyframes f{{from{{transform:scale(1,1)}}to{{transform:scale(.94,1.06)}}}}
@media (prefers-reduced-motion:reduce){{.flame{{animation:none}}}}
</style>
<rect class="bg" x=".5" y=".5" width="{W-1}" height="{H-1}" rx="12"/>
<defs><clipPath id="av"><circle cx="52" cy="52" r="28"/></clipPath>
<linearGradient id="fl" x1="0" y1="1" x2="0" y2="0"><stop offset="0" stop-color="#d1242f"/><stop offset=".55" stop-color="#fb8500"/><stop offset="1" stop-color="#ffb703"/></linearGradient></defs>
<image href="data:image/png;base64,{avatar}" x="24" y="24" width="56" height="56" clip-path="url(#av)"/>
<text x="94" y="48" class="fg" font-size="20" font-weight="700">{escape(u["name"] or u["login"])}</text>
<text x="94" y="70" class="mu" font-size="13">@{u["login"]} · GitHub {TODAY.year - int(u["createdAt"][:4])}년차 · 팔로워 {u["followers"]["totalCount"]}</text>
''']


def stat(x, label, value, sub):
    return (f'<text x="{x}" y="128" class="fg" font-size="26" font-weight="700">{value}</text>'
            f'<text x="{x}" y="148" class="mu" font-size="12">{label}</text>'
            f'<text x="{x}" y="164" class="mu" font-size="11">{sub}</text>')


# 불꽃 + 현재 streak
out.append('<g class="flame"><path fill="url(#fl)" d="M44 96c8 9 14 17 14 27a16 16 0 0 1-32 0c0-6 3-11 7-15 0 5 2 8 5 9-1-8 1-15 6-21z"/>'
           '<path fill="#ffe8a3" d="M42 116c4 4 6 7 6 10a6 6 0 0 1-12 0c0-3 2-6 6-10z"/></g>')
out.append(stat(72, "현재 연속 기여", f"{cur}일", "오늘까지 이어지는 중" if days.get(TODAY) else "오늘 기여하면 +1"))
out.append(stat(230, "최장 연속", f"{best}일", "전체 기간"))
out.append(stat(360, f"{TODAY.year}년 기여", f"{year:,}", f"전체 {total:,}"))
out.append(stat(500, "저장소", u["repositories"]["totalCount"], f"⭐ {sum(r['stargazerCount'] for r in u['repositories']['nodes'])}"))

# 언어 막대 (오른쪽)
if top:
    x0, y0, bw = 620, 104, 176
    out.append(f'<text x="{x0}" y="96" class="mu" font-size="12">자주 쓰는 언어</text>')
    cx = x0
    for _, (size, color) in top:
        w = bw * size / lsum
        out.append(f'<rect x="{cx:.1f}" y="{y0}" width="{w:.1f}" height="8" fill="{color}"/>')
        cx += w
    for i, (name, (size, color)) in enumerate(top):
        lx, ly = x0 + (i % 2) * 90, y0 + 26 + (i // 2) * 18
        out.append(f'<circle cx="{lx+4}" cy="{ly-4}" r="4" fill="{color}"/>'
                   f'<text x="{lx+12}" y="{ly}" class="fg" font-size="11">{escape(name)} <tspan class="mu">{size*100/lsum:.0f}%</tspan></text>')

# 기여 달력: 최근 53주
start = TODAY - dt.timedelta(days=TODAY.isoweekday() % 7 + 52 * 7)
lvl = lambda n: 0 if n == 0 else 1 if n < 3 else 2 if n < 8 else 3 if n < 15 else 4  # ponytail: 고정 구간, GitHub 은 사분위
out.append(f'<text x="24" y="196" class="mu" font-size="12">최근 1년</text>')
for i in range((TODAY - start).days + 1):
    d = start + dt.timedelta(days=i)
    out.append(f'<rect x="{24 + (i // 7) * 14.4:.1f}" y="{204 + (i % 7) * 12}" width="10" height="10" rx="2" class="c{lvl(days.get(d, 0))}"/>')
out.append("</svg>")

open("profile-card.svg", "w").write("\n".join(out))
print(f"cur={cur} best={best} year={year} total={total} langs={len(top)}")
