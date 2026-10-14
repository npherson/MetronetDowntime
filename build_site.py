"""Build docs/index.html (the public report page) from data/report.json."""
import html
import json
from datetime import datetime

R = json.load(open("data/report.json"))


def dur(m):
    return f"{m // 60}h {m % 60}m" if m >= 60 else f"{m} min"


def cell(pair):
    return f"{pair[0]} ({dur(pair[1])})"


rows = []
for s in R["summary"]:
    tag = "th" if s["label"] == "Total" else "td"
    cls = ' class="total"' if s["label"] == "Total" else ""
    avg = f'{s["avg"]} min' if s["avg"] is not None else "&ndash;"
    rows.append(
        f"<tr{cls}><{tag} scope=\"row\">{html.escape(s['label'])}</{tag}>"
        f"<td>{cell(s['short'])}</td><td>{cell(s['long'])}</td><td>{cell(s['total'])}</td>"
        f"<td>{avg}</td><td>{s['reliability']:.2f}%</td></tr>")
total = R["summary"][-1]

page = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Metronet Downtime Report</title>
<meta name="description" content="How often our home internet connection has gone down, measured once a minute.">
<style>
:root{color-scheme:light;--surface:#fcfcfb;--panel:#ffffff;--ink:#0b0b0b;--ink2:#52514e;--muted:#8a8984;--grid:#e6e5e0;--line:#dddcd6;--long:#2a78d6;--short:#eb6834}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){color-scheme:dark;--surface:#141413;--panel:#1a1a19;--ink:#fff;--ink2:#c3c2b7;--muted:#8f8e88;--grid:#2e2e2b;--line:#33332f;--long:#3987e5;--short:#d95926}}
:root[data-theme="dark"]{color-scheme:dark;--surface:#141413;--panel:#1a1a19;--ink:#fff;--ink2:#c3c2b7;--muted:#8f8e88;--grid:#2e2e2b;--line:#33332f;--long:#3987e5;--short:#d95926}
*{box-sizing:border-box}
body{margin:0;background:var(--surface);color:var(--ink);font:15px/1.5 system-ui,-apple-system,"Segoe UI",sans-serif}
main{max-width:820px;margin:0 auto;padding:32px 16px 48px}
h1{font-size:26px;line-height:1.2;margin:0 0 6px}
h2{font-size:18px;margin:32px 0 8px}
p{margin:0 0 12px;color:var(--ink2)}
.lede{font-size:16px;color:var(--ink)}
.stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:12px;margin:20px 0 8px}
.stat{background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:12px 14px}
.stat b{display:block;font-size:24px;font-variant-numeric:tabular-nums}
.stat span{color:var(--ink2);font-size:13px}
.tablewrap{overflow-x:auto;background:var(--panel);border:1px solid var(--line);border-radius:10px}
table{border-collapse:collapse;width:100%;font-size:14px;font-variant-numeric:tabular-nums}
th,td{padding:8px 12px;text-align:right;white-space:nowrap;border-bottom:1px solid var(--line)}
th:first-child,td:first-child{text-align:left}
thead th{color:var(--ink2);font-weight:600}
tr.total th,tr.total td{font-weight:700;border-bottom:0}
.kv{background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:14px;position:relative;font-size:13px;line-height:1.4}
.kv h3{font-size:15px;margin:0 0 2px}.kv p{margin:0 0 8px;font-size:13px}
.kv .lg{display:flex;flex-wrap:wrap;gap:6px 16px;margin:4px 0 6px;color:var(--ink2)}.kv .lg i{display:inline-block;width:10px;height:10px;border-radius:2px;margin-right:6px;vertical-align:-1px}
.kv svg{width:100%;height:auto;display:block}.kv text{fill:var(--ink2);font-size:11px}
.kv .tip{position:absolute;pointer-events:none;background:var(--panel);border:1px solid var(--grid);border-radius:6px;padding:6px 8px;box-shadow:0 2px 8px rgba(0,0,0,.15);display:none;white-space:nowrap;z-index:2}
.kv .sec{margin-top:22px}
ul{color:var(--ink2);padding-left:20px}li{margin-bottom:6px}
a{color:var(--long)}
footer{margin-top:32px;font-size:13px;color:var(--muted)}
</style>
</head>
<body>
<main>
<h1>Metronet Downtime Report</h1>
<p class="lede">How often our home internet connection has dropped, measured once a minute from __FIRST__ to __LAST__ (Central time).</p>
<div class="stats">
 <div class="stat"><b>__COUNT__</b><span>outages</span></div>
 <div class="stat"><b>__TOTAL__</b><span>total time down</span></div>
 <div class="stat"><b>__LONGEST__</b><span>longest outage (__LONGEST_WHEN__)</span></div>
 <div class="stat"><b>__REL__%</b><span>uptime</span></div>
</div>

<h2>Summary by month</h2>
<div class="tablewrap"><table>
<thead><tr><th scope="col">Month</th><th scope="col">1 min or less</th><th scope="col">Longer than 1 min</th><th scope="col">Total</th><th scope="col">Average outage</th><th scope="col">Reliability</th></tr></thead>
<tbody>
__ROWS__
</tbody></table></div>
<p style="margin-top:8px;font-size:13px">Each cell shows the number of outages and the total time down. Average outage is total time divided by the number of outages. Reliability is the share of the month the connection was up while it was being monitored.</p>

<h2>Charts</h2>
<div class="kv" id="kv">
 <h3>Internet downtime per day</h3>
 <p>Minutes down each day. Each section is one outage, stacked in the order they happened. The line is the trailing 7-day average.</p>
 <div class="lg"><span><i style="background:var(--long)"></i>Longer than 1 min</span><span><i style="background:var(--short)"></i>1 min or less</span><span><i style="background:var(--ink);height:2px;vertical-align:3px"></i>7-day average</span></div>
 <svg id="c1" viewBox="0 0 720 240" role="img" aria-label="Daily downtime minutes"></svg>
 <div class="sec"><h3>Outages per day</h3>
 <p>Number of separate outages each day, with the trailing 7-day average.</p>
 <div class="lg"><span><i style="background:var(--long)"></i>Longer than 1 min</span><span><i style="background:var(--short)"></i>1 min or less</span><span><i style="background:var(--ink);height:2px;vertical-align:3px"></i>7-day average</span></div>
 <svg id="c3" viewBox="0 0 720 200" role="img" aria-label="Outages per day"></svg></div>
 <div class="sec"><h3>When outages start</h3>
 <p>Number of outages by the hour of day they began.</p>
 <div class="lg"><span><i style="background:var(--long)"></i>Longer than 1 min</span><span><i style="background:var(--short)"></i>1 min or less</span></div>
 <svg id="c2" viewBox="0 0 720 220" role="img" aria-label="Outages by hour of day"></svg></div>
 <div class="tip" id="tip"></div>
</div>

<h2>How this is measured</h2>
<ul>
 <li>An <a href="https://github.com/louislam/uptime-kuma">Uptime Kuma</a> monitor on a Raspberry Pi pings a public address (8.8.4.4) once a minute. A failed ping marks the internet as down until the next successful one, so each start and end time can be off by up to about a minute.</li>
 <li>A second monitor pings our own router. Outages where our router was also down within 3 minutes are left out, since those point to a problem inside the house rather than with Metronet.</li>
 <li>Outages of 1 minute or less are a single failed check and could be a dropped ping rather than a real outage, so they are shown separately.</li>
</ul>
<p><a href="internet-outages.csv">Download the full outage list (CSV)</a></p>
<footer>Last updated __LAST__. Source code: <a href="https://github.com/npherson/MetronetDowntime">github.com/npherson/MetronetDowntime</a></footer>
</main>
<script>
(function(){
const D=__DATA__,NS="http://www.w3.org/2000/svg",root=document.getElementById("kv"),tip=document.getElementById("tip");
function el(p,t,a){const e=document.createElementNS(NS,t);for(const k in a)e.setAttribute(k,a[k]);p.appendChild(e);return e}
function show(ev,h){tip.innerHTML=h;tip.style.display="block";const r=root.getBoundingClientRect();let x=ev.clientX-r.left+12;if(x>r.width-190)x=Math.max(4,x-210);tip.style.left=x+"px";tip.style.top=(ev.clientY-r.top+12)+"px"}
function hide(){tip.style.display="none"}
function hover(node,f){node.addEventListener("mousemove",e=>show(e,f()));node.addEventListener("click",e=>{e.stopPropagation();show(e,f())});node.addEventListener("mouseleave",hide)}
document.addEventListener("click",hide);
function bar(p,x,y,w,h,fill,top){if(h<=0)return;const r=Math.min(3,w/2,h);
 const d=top?`M${x},${y+h}V${y+r}Q${x},${y} ${x+r},${y}H${x+w-r}Q${x+w},${y} ${x+w},${y+r}V${y+h}Z`:`M${x},${y}h${w}v${h}h${-w}Z`;
 el(p,"path",{d,fill})}
function fmt(m){m=Math.round(m);return m>=60?Math.floor(m/60)+"h "+(m%60)+"m":m+" min"}
// Round an axis maximum up to a multiple of step, and list its ticks.
function axis(v,step){const max=Math.max(step,Math.ceil(v/step)*step),t=[];for(let i=0;i<=max;i+=step)t.push(i);return [max,t]}
function chart(svg,rows,[maxV,ticks],label,tipf,line){
 const L=40,R=8,T=8,B=28,W=720-L-R,H=+svg.getAttribute("viewBox").split(" ")[3]-T-B,n=rows.length,bw=W/n,g=Math.min(2,bw*.25);
 ticks.forEach(t=>{const y=T+H-t/maxV*H;el(svg,"line",{x1:L,x2:L+W,y1:y,y2:y,stroke:"var(--grid)"});el(svg,"text",{x:L-6,y:y+4,"text-anchor":"end"}).textContent=t});
 rows.forEach((r,i)=>{const x=L+i*bw+g/2,w=bw-g,hl=r.long/maxV*H,hs=r.short/maxV*H;
  const lb=label(r,i);if(lb)el(svg,"text",{x:x+w/2,y:T+H+16,"text-anchor":"middle"}).textContent=lb;
  hover(el(svg,"rect",{x:L+i*bw,y:T,width:bw,height:H,fill:"transparent"}),()=>tipf(r));
  if(r.segs){
   // One section per outage, stacked bottom-up in the order they happened.
   let y=T+H;
   r.segs.forEach((sg,j)=>{const full=sg[1]/maxV*H,h=Math.max(1,full-(j?2:0));y-=j?2:0;y-=h;
    bar(svg,x,y,w,h,sg[2]?"var(--short)":"var(--long)",j==r.segs.length-1);
    hover(el(svg,"rect",{x:L+i*bw,y:y,width:bw,height:h+2,fill:"transparent"}),()=>tipf(r,sg))});
   return}
  bar(svg,x,T+H-hl,w,hl,"var(--long)",hs<=0);
  if(hs>0)bar(svg,x,T+H-hl-hs-(hl>0?2:0),w,hs,"var(--short)",true)});
 el(svg,"line",{x1:L,x2:L+W,y1:T+H,y2:T+H,stroke:"var(--muted)"});
 if(line){const pts=line.map((v,i)=>v==null?null:`${L+i*bw+bw/2},${T+H-v/maxV*H}`).filter(Boolean).join(" ");
  el(svg,"polyline",{points:pts,fill:"none",stroke:"var(--panel)","stroke-width":5,"stroke-linejoin":"round","pointer-events":"none"});
  el(svg,"polyline",{points:pts,fill:"none",stroke:"var(--ink)","stroke-width":2,"stroke-linejoin":"round","pointer-events":"none"})}
}
const mon=["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"];
const days=D.days.map(d=>({date:d[0],short:d[1],long:d[2],ns:d[3],nl:d[4],inc:d[5]}));
const clock=t=>{const h=+t.slice(0,2);return (h%12||12)+":"+t.slice(3)+(h<12?" AM":" PM")};
const dayLabel=r=>{const dd=+r.date.slice(8);return (dd==1||dd==15)?mon[+r.date.slice(5,7)-1]+" "+dd:""};
const head=r=>{const [y,m,d]=r.date.split("-");return `<b>${mon[+m-1]} ${+d}</b><br>`};
// Trailing 7-day averages; they start once 7 full days exist.
const trail=f=>days.map((r,i)=>i<6?null:days.slice(i-6,i+1).reduce((a,d)=>a+f(d),0)/7);
const avgMin=trail(d=>d.short+d.long),avgCnt=trail(d=>d.ns+d.nl);
days.forEach((r,i)=>{r.avgMin=avgMin[i];r.avg=avgCnt[i]});
chart(document.getElementById("c1"),days.map(r=>({...r,segs:r.inc})),axis(Math.max(...days.map(d=>d.short+d.long+2*d.inc.length)),30),dayLabel,
 (r,sg)=>{const t=r.ns+r.nl;return head(r)+`${sg?`Outage at ${clock(sg[0])}: ${fmt(sg[1])}<br>`:""}${t?`Day total: ${fmt(r.short+r.long)} in ${t} outage${t>1?"s":""}`:"No outages"}${r.avgMin!=null?`<br>7-day average: ${fmt(r.avgMin)} a day`:""}`},avgMin);
chart(document.getElementById("c3"),days.map(r=>({...r,short:r.ns,long:r.nl})),axis(Math.max(...days.map(d=>d.ns+d.nl)),2),dayLabel,
 r=>{const t=r.ns+r.nl;return head(r)+`${t?`${t} outage${t>1?"s":""}<br>${r.nl} longer than 1 min, ${r.ns} of 1 min or less`:"No outages"}${r.avg!=null?`<br>7-day average: ${r.avg.toFixed(1)} a day`:""}`},avgCnt);
const hrs=D.hours.map((h,i)=>({hour:i,short:h[0],long:h[1]}));
const hl=h=>(h%12||12)+(h<12?"a":"p");
chart(document.getElementById("c2"),hrs,axis(Math.max(...hrs.map(h=>h.short+h.long)),4),r=>r.hour%3==0?hl(r.hour):"",
 r=>`<b>${hl(r.hour)}m to ${hl((r.hour+1)%24)}m</b><br>${r.long+r.short} outages<br>${r.long} longer than 1 min, ${r.short} of 1 min or less`);
})();
</script>
</body>
</html>
"""

subs = {
    "__FIRST__": R["first"], "__LAST__": R["last"],
    "__COUNT__": str(total["total"][0]), "__TOTAL__": dur(total["total"][1]),
    "__LONGEST__": R["longest"]["duration"].replace("0h ", ""),
    "__LONGEST_WHEN__": (lambda d: f"{d:%b} {d.day}")(datetime.fromisoformat(R["longest"]["start"])), "__REL__": f"{total['reliability']:.2f}",
    "__ROWS__": "\n".join(rows),
    "__DATA__": json.dumps({"days": R["days"], "hours": R["hours"]}),
}
for k, v in subs.items():
    page = page.replace(k, v)
open("docs/index.html", "w", encoding="utf-8").write(page)
print("wrote docs/index.html")
