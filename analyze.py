"""Compute internet outages from a copy of Uptime Kuma's database.

Reads data/db/kuma.db (copied off the Pi by scripts/pull-kuma.ps1) and writes:
  data/all-outages.csv    every outage, including ones caused by the home network (kept local)
  docs/internet-outages.csv  outages with the home network up (published)
  data/report.json        summary table and chart data for build_site.py
"""
import csv
import json
import sqlite3
import sys
from collections import defaultdict
from datetime import datetime, timedelta, timezone

DB = sys.argv[1] if len(sys.argv) > 1 else "data/db/kuma.db"
INTERNET_MONITOR = "Internet Available"
GATEWAY_MONITOR = "Default Gateway"
# If the gateway was down from 3 minutes before an internet outage until 3 minutes
# after it, the outage is treated as a home network problem and left out.
GW_MARGIN = timedelta(minutes=3)
# Monitoring began the afternoon of Jul 31, 2026; the report starts on the first full month.
REPORT_START = datetime(2026, 8, 1, 5, tzinfo=timezone.utc)  # Aug 1, midnight Central

con = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)


def utc(s):
    return datetime.fromisoformat(s).replace(tzinfo=timezone.utc)


def nth_sunday(year, month, n):
    d = datetime(year, month, 1)
    d += timedelta(days=(6 - d.weekday()) % 7)
    return d + timedelta(weeks=n - 1)


def central(t):
    """US Central time with daylight saving (2nd Sunday in March to 1st Sunday in November)."""
    y = t.year
    dst_start = (nth_sunday(y, 3, 2) + timedelta(hours=8)).replace(tzinfo=timezone.utc)
    dst_end = (nth_sunday(y, 11, 1) + timedelta(hours=7)).replace(tzinfo=timezone.utc)
    if dst_start <= t < dst_end:
        return t.astimezone(timezone(timedelta(hours=-5), "CDT"))
    return t.astimezone(timezone(timedelta(hours=-6), "CST"))


def monitor_id(name):
    return con.execute("select id from monitor where name=?", (name,)).fetchone()[0]


def outages(mid):
    """Status changes are kept forever as 'important' beats; an outage runs from an
    important DOWN beat to the next important beat that is not DOWN."""
    rows = con.execute(
        "select time, status, msg from heartbeat where monitor_id=? and important=1 order by time",
        (mid,),
    ).fetchall()
    out, cur = [], None
    for t, status, msg in rows:
        if status == 0 and cur is None:
            cur = {"start": utc(t), "msg": msg}
        elif status != 0 and cur is not None:
            cur["end"] = utc(t)
            out.append(cur)
            cur = None
    if cur:
        cur["end"] = None
        out.append(cur)
    return out


def summarize(msg):
    """Ping output is multi-line; keep the line that says who reported the failure."""
    lines = [l.strip() for l in (msg or "").splitlines() if l.strip()]
    for l in lines:
        if l.startswith("From ") or "Unreachable" in l or "timeout" in l.lower():
            return l
    return lines[-1] if lines else ""


def hm(secs):
    """Duration rounded to the nearest minute, shown as hours and minutes."""
    m = round(secs / 60)
    return f"{m // 60}h {m % 60}m"


def length_group(secs):
    # A single failed 60s check reads as a fraction of a second over a minute.
    return "1 min or less" if secs < 90 else "over 1 min"


def local(t):
    return central(t).strftime("%Y-%m-%d %H:%M:%S")


inet_id = monitor_id(INTERNET_MONITOR)
inet = outages(inet_id)
gw = outages(monitor_id(GATEWAY_MONITOR))
first_beat = max(REPORT_START, utc(con.execute(
    "select min(time) from heartbeat where monitor_id=?", (inet_id,)).fetchone()[0]))
last_beat = utc(con.execute("select max(time) from heartbeat where monitor_id=?", (inet_id,)).fetchone()[0])
gw_iv = [(g["start"], g["end"] or last_beat) for g in gw]

all_rows, isp = [], []
for i, o in enumerate(inet, 1):
    s, e = o["start"], o["end"]
    secs = (e - s).total_seconds() if e else None
    gw_near = any(gs <= (e or last_beat) + GW_MARGIN and ge >= s - GW_MARGIN for gs, ge in gw_iv)
    row = {
        "n": i,
        "start_local": local(s),
        "end_local": local(e) if e else "",
        "duration": hm(secs) if e else "ongoing",
        "duration_in_mins": round(secs / 60) if e else "",
        "length_group": length_group(secs) if e else "",
        "gateway_down_within_3_min": "yes" if gw_near else "no",
        "start_utc": s.strftime("%Y-%m-%d %H:%M:%S"),
        "error": summarize(o["msg"]),
    }
    all_rows.append(row)
    if e and not gw_near and s >= first_beat:
        isp.append({**row, "n": len(isp) + 1, "secs": secs, "start": s})

with open("data/all-outages.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=list(all_rows[0]))
    w.writeheader()
    w.writerows(all_rows)

PUBLIC = ["n", "start_local", "end_local", "duration", "duration_in_mins", "length_group", "start_utc", "error"]
with open("docs/internet-outages.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=PUBLIC, extrasaction="ignore")
    w.writeheader()
    w.writerows(isp)

# Summary table: one row per month, plus a total row.
months = []
m = datetime(central(first_beat).year, central(first_beat).month, 1)
while m <= datetime(central(last_beat).year, central(last_beat).month, 1):
    nxt = datetime(m.year + (m.month == 12), m.month % 12 + 1, 1)
    months.append((m, nxt))
    m = nxt


def stats(rows, start, end):
    short = [r for r in rows if r["length_group"] == "1 min or less"]
    long_ = [r for r in rows if r["length_group"] == "over 1 min"]
    mins = lambda rs: sum(r["duration_in_mins"] for r in rs)
    total = mins(rows)
    period = (end - start).total_seconds() / 60
    return {
        "short": [len(short), mins(short)],
        "long": [len(long_), mins(long_)],
        "total": [len(rows), total],
        "avg": round(total / len(rows), 1) if rows else None,
        "reliability": round(100 * (1 - total / period), 2),
    }


summary = []
for ms, me in months:
    rows = [r for r in isp if r["start_local"][:7] == ms.strftime("%Y-%m")]
    # Measure each month only over the time Uptime Kuma was watching.
    start = max(ms.replace(tzinfo=central(first_beat).tzinfo), first_beat)
    end = min(me.replace(tzinfo=central(last_beat).tzinfo), last_beat)
    label = ms.strftime("%b")
    if start > ms.replace(tzinfo=start.tzinfo) or end < me.replace(tzinfo=end.tzinfo):
        a, b = central(start).day, central(end - timedelta(seconds=1)).day
        label += f" ({a})" if a == b else f" ({a}–{b})"
    summary.append({"label": label, **stats(rows, start, end)})
summary.append({"label": "Total", **stats(isp, first_beat, last_beat)})

# Chart data: per day (minutes and counts by length, plus each outage) and per hour.
by_day = defaultdict(lambda: [0, 0, 0, 0])
incidents = defaultdict(list)  # per day: [start "HH:MM", minutes, 1 if 1 min or less]
hours = [[0, 0] for _ in range(24)]
for r in isp:
    k = 0 if r["length_group"] == "1 min or less" else 1
    d = r["start_local"][:10]
    by_day[d][k] += r["secs"] / 60
    by_day[d][2 + k] += 1
    hours[int(r["start_local"][11:13])][k] += 1
    incidents[d].append([r["start_local"][11:16], round(r["secs"] / 60, 1), 1 - k])
days = []
day, last = central(first_beat).date(), central(last_beat).date()
while day <= last:
    v = by_day[day.isoformat()]
    days.append([day.isoformat(), round(v[0], 1), round(v[1], 1), v[2], v[3], incidents[day.isoformat()]])
    day += timedelta(days=1)

longest = max(isp, key=lambda r: r["secs"])
report = {
    "first": central(first_beat).strftime("%b %-d, %Y" if sys.platform != "win32" else "%b %#d, %Y"),
    "last": central(last_beat).strftime("%b %-d, %Y at %-I:%M %p" if sys.platform != "win32" else "%b %#d, %Y at %#I:%M %p"),
    "excluded": sum(o["start"] >= first_beat and o["end"] is not None for o in inet) - len(isp),
    "longest": {"start": longest["start_local"], "duration": longest["duration"]},
    "summary": summary,
    "days": days,
    "hours": hours,
}
json.dump(report, open("data/report.json", "w"), indent=1)

t = summary[-1]
print(f"{report['first']} to {report['last']}: {t['total'][0]} outages, {t['total'][1]} min, "
      f"{t['reliability']}% up; {report['excluded']} left out for home network trouble")
