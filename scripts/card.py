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


u = gql("""query($l:String!){user(login:$l){name login createdAt avatarUrl(size:96) location
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
    best, bs, run, rs = (0, None), None, 0, None
    for d in sorted(days):
        if d > today:
            break
        if days[d]:
            run, rs = run + 1, rs or d
            if run > best[0]:
                best, bs = (run, d), rs
        else:
            run, rs = 0, None
    cur, d = 0, today if days.get(today) else today - dt.timedelta(days=1)  # 오늘 아직 0이면 어제부터
    end = d
    while days.get(d):
        cur, d = cur + 1, d - dt.timedelta(days=1)
    return (cur, d + dt.timedelta(days=1), end), (best[0], bs, best[1])


(cur, cs, ce), (best, bs, be) = streaks(days, TODAY)
total = sum(days.values())
first = min((d for d, v in days.items() if v), default=TODAY)
last365 = [(d, v) for d, v in days.items() if TODAY - dt.timedelta(days=364) <= d <= TODAY]
year = sum(v for _, v in last365)

# 최근 12개월 월별 합계
months = []
for k in range(11, -1, -1):
    y, m = divmod(TODAY.year * 12 + TODAY.month - 1 - k, 12)
    months.append((m + 1, sum(v for d, v in days.items() if (d.year, d.month) == (y, m + 1))))
# 최근 1년 요일별 합계 (일~토)
week = [0] * 7
for d, v in last365:
    week[d.isoweekday() % 7] += v

langs = {}
for r in u["repositories"]["nodes"]:
    for e in r["languages"]["edges"]:
        n = e["node"]["name"]
        langs.setdefault(n, [0, e["node"]["color"] or "#8b949e"])[0] += e["size"]
top = sorted(langs.items(), key=lambda kv: -kv[1][0])[:6]
lsum = sum(v[0] for _, v in top) or 1

avatar = base64.b64encode(urllib.request.urlopen(u["avatarUrl"]).read()).decode()

# ---- SVG ----
W, H = 820, 430
fmt = lambda d: f"{d.year}.{d.month}.{d.day}" if d else "-"
out = [f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" font-family="-apple-system,Segoe UI,Helvetica,Arial,sans-serif">
<style>
:root{{--bg:#ffffff;--bd:#d0d7de;--fg:#1f2328;--mu:#59636e;--ac:#116329;--lt:#2da44e;--gr:#1a7f37;--fire:#bc4c00}}
@media (prefers-color-scheme:dark){{:root{{--bg:#0d1117;--bd:#30363d;--fg:#e6edf3;--mu:#9198a1;--ac:#56d364;--lt:#238636;--gr:#3fb950;--fire:#f0883e}}}}
.bg{{fill:var(--bg);stroke:var(--bd)}} .fg{{fill:var(--fg)}} .mu{{fill:var(--mu)}} .ac{{fill:var(--ac)}} .fire{{fill:var(--fire)}}
.ln{{stroke:var(--bd)}} .lt{{fill:var(--lt)}} .gr{{stroke:var(--gr)}} .gf{{fill:var(--gr)}} .cut{{fill:var(--bg)}}
.flame{{transform-origin:center bottom;transform-box:fill-box;animation:f 1.6s ease-in-out infinite alternate}}
@keyframes f{{from{{transform:scale(1,1)}}to{{transform:scale(.92,1.08)}}}}
.ring{{animation:draw 1.2s ease-out both}} @keyframes draw{{from{{stroke-dashoffset:289}}}}
.bar{{transform-origin:center bottom;transform-box:fill-box;animation:grow .8s ease-out both}} @keyframes grow{{from{{transform:scaleY(0)}}}}
.fade{{animation:fade 1s ease-out both}} @keyframes fade{{from{{opacity:0}}}}
@media (prefers-reduced-motion:reduce){{.flame,.ring,.bar,.fade{{animation:none}}}}
</style>
<defs><clipPath id="av"><circle cx="52" cy="52" r="28"/></clipPath>
<linearGradient id="fl" x1="0" y1="1" x2="0" y2="0"><stop offset="0" stop-color="#d1242f"/><stop offset=".55" stop-color="#fb8500"/><stop offset="1" stop-color="#ffb703"/></linearGradient>
<linearGradient id="rg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#ffb703"/><stop offset="1" stop-color="#d1242f"/></linearGradient>
<linearGradient id="ar" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#40c463" stop-opacity=".55"/><stop offset="1" stop-color="#40c463" stop-opacity="0"/></linearGradient></defs>
<rect class="bg" x=".5" y=".5" width="{W-1}" height="{H-1}" rx="12"/>
<image href="data:image/png;base64,{avatar}" x="24" y="24" width="56" height="56" clip-path="url(#av)"/>
<text x="94" y="48" class="fg" font-size="20" font-weight="700">{escape(u["name"] or u["login"])}</text>
<text x="94" y="70" class="mu" font-size="13">@{u["login"]} · {escape(u["location"] or "")} · GitHub {TODAY.year - int(u["createdAt"][:4])}년차</text>
"""]

# 헤더 오른쪽 수치 칩
chips = [("저장소", u["repositories"]["totalCount"]), ("스타", sum(r["stargazerCount"] for r in u["repositories"]["nodes"])),
         ("팔로워", u["followers"]["totalCount"]), ("언어", len(langs))]
for i, (k, v) in enumerate(chips):
    x = 520 + i * 70
    out.append(f'<text x="{x+30}" y="50" text-anchor="middle" class="fg" font-size="18" font-weight="700">{v}</text>'
               f'<text x="{x+30}" y="68" text-anchor="middle" class="mu" font-size="11">{k}</text>')
out.append('<line x1="24" y1="96" x2="796" y2="96" class="ln"/>')

# streak 밴드: 전체 | 링+불꽃 현재 | 최장
def col(cx, value, label, sub, cls="fg"):
    return (f'<text x="{cx}" y="168" text-anchor="middle" class="{cls}" font-size="30" font-weight="700">{value}</text>'
            f'<text x="{cx}" y="194" text-anchor="middle" class="fg" font-size="13">{label}</text>'
            f'<text x="{cx}" y="214" text-anchor="middle" class="mu" font-size="11">{sub}</text>')
out.append(col(150, f"{total:,}", "전체 기여", f"{fmt(first)} – 현재"))
out.append(col(670, f"{best}일", "최장 연속 기여", f"{fmt(bs)} – {fmt(be)}"))
out.append('<line x1="276" y1="118" x2="276" y2="228" class="ln"/><line x1="544" y1="118" x2="544" y2="228" class="ln"/>')
out.append('<circle cx="410" cy="160" r="46" fill="none" class="ln" stroke-width="5"/>'
           '<circle cx="410" cy="160" r="46" fill="none" stroke="url(#rg)" stroke-width="5" stroke-dasharray="289" class="ring" transform="rotate(-90 410 160)" stroke-linecap="round"/>'
           '<circle cx="410" cy="114" r="13" class="cut"/>'
           '<g class="flame"><path fill="url(#fl)" d="M412 99c5 5 9 10 9 16a11 11 0 0 1-22 0c0-4 2-7 5-10 0 3 1 5 3 6-1-5 1-9 5-12z"/>'
           '<path fill="#ffe8a3" d="M410 111c3 3 4 5 4 7a4 4 0 0 1-8 0c0-2 1-4 4-7z"/></g>')
out.append(f'<text x="410" y="172" text-anchor="middle" class="fire" font-size="32" font-weight="700">{cur}</text>'
           f'<text x="410" y="226" text-anchor="middle" class="fire" font-size="13" font-weight="600">현재 연속 기여 (일)</text>'
           f'<text x="410" y="242" text-anchor="middle" class="mu" font-size="11">{fmt(cs) if cur else "-"} – {fmt(ce) if cur else "-"}</text>')
out.append('<line x1="24" y1="258" x2="796" y2="258" class="ln"/>')

# 월별 추이 (영역 그래프)
x0, y0, cw, ch = 24, 384, 300, 80
mx = max(v for _, v in months) or 1
pts = [(x0 + i * cw / 11, y0 - v / mx * ch) for i, (_, v) in enumerate(months)]
line = " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
out.append(f'<text x="{x0}" y="282" class="fg" font-size="13" font-weight="600">월별 기여</text>'
           f'<text x="{x0+cw}" y="282" text-anchor="end" class="mu" font-size="11">최근 12개월 {year:,}</text>'
           f'<g class="fade"><polygon points="{x0},{y0} {line} {x0+cw},{y0}" fill="url(#ar)"/>'
           f'<polyline points="{line}" fill="none" class="gr" stroke-width="2.5" stroke-linejoin="round"/>')
for (x, y), (m, v) in zip(pts, months):
    out.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3" class="gf"/>')
out.append("</g>")
for i, ((x, _), (m, _)) in enumerate(zip(pts, months)):
    if i % 2 == 1 or i == 11:
        out.append(f'<text x="{x:.1f}" y="{y0+18}" text-anchor="middle" class="mu" font-size="10">{m}월</text>')

# 요일별 막대
bx, bw = 364, 26
wm = max(week) or 1
out.append(f'<text x="{bx}" y="282" class="fg" font-size="13" font-weight="600">요일별 기여</text>')
for i, (name, v) in enumerate(zip("일월화수목금토", week)):
    h = max(2, v / wm * ch)
    x = bx + i * (bw + 4)
    out.append(f'<rect x="{x}" y="{y0-h:.1f}" width="{bw}" height="{h:.1f}" rx="4" class="bar {"ac" if v == wm else "lt"}" '
               f'style="animation-delay:{i*60}ms"/>'
               f'<text x="{x+bw/2}" y="{y0+18}" text-anchor="middle" class="mu" font-size="10">{name}</text>')

# 언어 도넛
dx, dy, r = 618, 340, 38
C = 2 * 3.14159 * r
out.append(f'<text x="{dx-42}" y="282" class="fg" font-size="13" font-weight="600">자주 쓰는 언어</text>')
acc = 0
for name, (size, color) in top:
    seg = C * size / lsum
    out.append(f'<circle cx="{dx}" cy="{dy}" r="{r}" fill="none" stroke="{color}" stroke-width="14" '
               f'stroke-dasharray="{seg:.2f} {C-seg:.2f}" stroke-dashoffset="{-acc:.2f}" transform="rotate(-90 {dx} {dy})" class="fade"/>')
    acc += seg
for i, (name, (size, color)) in enumerate(top):
    ly = 304 + i * 17
    out.append(f'<circle cx="{dx+56}" cy="{ly-4}" r="4" fill="{color}"/>'
               f'<text x="{dx+64}" y="{ly}" class="fg" font-size="11">{escape(name)} <tspan class="mu">{size*100/lsum:.0f}%</tspan></text>')
out.append("</svg>")

open("profile-card.svg", "w").write("\n".join(out))
print(f"cur={cur} best={best} total={total} months={months} week={week}")
