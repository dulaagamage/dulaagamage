import json
import math
import os
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

today = datetime.now(timezone.utc).date()
start = today - timedelta(days=29)

query = """
query($login: String!, $from: DateTime!, $to: DateTime!) {
  user(login: $login) {
    contributionsCollection(from: $from, to: $to) {
      contributionCalendar {
        weeks {
          contributionDays {
            date
            contributionCount
          }
        }
      }
    }
  }
}
"""

payload = {
    "query": query,
    "variables": {
        "login": "dulaagamage",
        "from": f"{start}T00:00:00Z",
        "to": datetime.now(timezone.utc).isoformat(),
    },
}

request = urllib.request.Request(
    "https://api.github.com/graphql",
    data=json.dumps(payload).encode(),
    headers={
        "Authorization": f"Bearer {os.environ['GH_TOKEN']}",
        "Content-Type": "application/json",
        "User-Agent": "profile-activity-graph",
    },
)

with urllib.request.urlopen(request, timeout=60) as response:
    result = json.load(response)

if result.get("errors"):
    raise RuntimeError(result["errors"])

weeks = result["data"]["user"]["contributionsCollection"][
    "contributionCalendar"
]["weeks"]

counts = {
    day["date"]: day["contributionCount"]
    for week in weeks
    for day in week["contributionDays"]
}

dates = [start + timedelta(days=i) for i in range(30)]
values = [counts.get(str(day), 0) for day in dates]

left, top, width, height = 65, 75, 870, 205
tick = max(1, math.ceil(max(values, default=0) / 4))
maximum = tick * 4

points = [
    (
        left + i * width / 29,
        top + height - value * height / maximum,
    )
    for i, value in enumerate(values)
]

svg = [
    '<svg xmlns="http://www.w3.org/2000/svg" '
    'viewBox="0 0 1000 350" role="img" '
    'aria-labelledby="title description">',
    '<title id="title">GitHub Contribution Activity</title>',
    '<desc id="description">Daily contributions over the last '
    '30 UTC calendar dates, including today.</desc>',
    '<rect width="1000" height="350" rx="14" fill="#0d1117"/>',
    '<g font-family="Arial,sans-serif">',
    '<text x="65" y="33" fill="#7cf5a3" font-size="22">'
    'Contribution Activity</text>',
    f'<text x="65" y="55" fill="#8b949e" font-size="13">'
    f'Last 30 days · {sum(values)} contributions · UTC</text>',
]

for i in range(5):
    value = i * tick
    y = top + height - value * height / maximum
    svg.append(
        f'<path d="M{left},{y} H{left + width}" '
        'stroke="#21262d"/>'
        f'<text x="52" y="{y + 4}" text-anchor="end" '
        f'fill="#8b949e" font-size="12">{value}</text>'
    )

line = " ".join(f"{x:.1f},{y:.1f}" for x, y in points)
baseline = top + height

svg.append(
    f'<polygon points="{left},{baseline} {line} '
    f'{left + width},{baseline}" fill="#7cf5a3" opacity="0.10"/>'
)
svg.append(
    f'<polyline points="{line}" fill="none" '
    'stroke="#7cf5a3" stroke-width="3" stroke-linejoin="round"/>'
)

for day, value, (x, y) in zip(dates, values, points):
    svg.append(
        f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3" '
        f'fill="#7cf5a3"><title>{day}: '
        f'{value} contributions</title></circle>'
    )

for i in [0, 5, 10, 15, 20, 25, 29]:
    x = points[i][0]
    label = dates[i].strftime("%d %b")
    svg.append(
        f'<text x="{x:.1f}" y="310" text-anchor="middle" '
        f'fill="#8b949e" font-size="12">{label}</text>'
    )

svg.append("</g></svg>")

Path("profile").mkdir(exist_ok=True)
Path("profile/activity.svg").write_text(
    "\n".join(svg), encoding="utf-8"
)
