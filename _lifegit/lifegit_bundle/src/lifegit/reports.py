from __future__ import annotations

import html
import json
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

from lifegit.db import LifeDB
from lifegit.util import stable_id

CSS="""
:root{font-family:Inter,system-ui,sans-serif;color:#171717;background:#f6f6f2}body{max-width:1120px;margin:0 auto;padding:32px}
a{color:inherit}.nav{display:flex;gap:10px;flex-wrap:wrap;margin:18px 0 28px}.nav a,.pill{background:white;border:1px solid #ddd;border-radius:999px;padding:8px 12px;text-decoration:none}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:12px}.card{background:white;border:1px solid #ddd;border-radius:16px;padding:18px;margin:10px 0}.big{font-size:42px;font-weight:700}.muted{color:#666}.timeline{border-left:2px solid #ccc;padding-left:18px}.item{margin:14px 0}.evidence{font-size:12px;color:#666}table{width:100%;border-collapse:collapse}td,th{padding:9px;border-bottom:1px solid #ddd;text-align:left}.bar{height:10px;background:#ddd;border-radius:10px;overflow:hidden}.bar>i{display:block;height:100%;background:#222}code{font-size:12px}
"""
NAV=[("index.html","Wrapped"),("ideas.html","Idea Cemetery"),("questions.html","My Questions"),("problems.html","Problem Ledger"),("career.html","CareerGit"),("timeline.html","Timeline"),("pastme.html","Past Me"),("diff.html","Memory Diff")]

def page(title:str,body:str)->str:
    nav="".join(f'<a href="{u}">{html.escape(n)}</a>' for u,n in NAV)
    return f'<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>{html.escape(title)}</title><style>{CSS}</style><body><h1>{html.escape(title)}</h1><div class="nav">{nav}</div>{body}</body>'

def _rows(db:LifeDB, typ:str|None=None, work:bool=False):
    with db.connect() as con:
        q="SELECT * FROM semantic_objects WHERE 1=1"; args=[]
        if typ: q+=" AND object_type=?"; args.append(typ)
        if work: q+=" AND work_relevance>=0.45 AND privacy_class='WORK_CANDIDATE'"
        q+=" ORDER BY first_observed_at"
        return [dict(r) for r in con.execute(q,args)]

def _activity(db):
    with db.connect() as con:
        return [dict(r) for r in con.execute("SELECT substr(created_at,1,10) day,count(*) n FROM messages WHERE role='user' AND is_current_path=1 AND created_at IS NOT NULL GROUP BY day ORDER BY day")]

def generate_all(db:LifeDB,outdir:str|Path)->dict:
    out=Path(outdir); out.mkdir(parents=True,exist_ok=True)
    stats=db.stats(); activity=_activity(db); allobj=_rows(db)
    counts=Counter(x["object_type"] for x in allobj)
    first=activity[0]["day"] if activity else "—"; last=activity[-1]["day"] if activity else "—"
    cards="".join(f'<div class="card"><div class="big">{stats[k]}</div><div>{k.replace("_"," ")}</div></div>' for k in ["conversations","messages","semantic_objects"])
    objcards="".join(f'<div class="card"><div class="big">{counts[k]}</div><div>{k.title()}</div></div>' for k in ["QUESTION","IDEA","PROJECT","PROBLEM","DISCOVERY"])
    body=f'<p class="muted">Evidence-backed local report. Period {first} → {last}. Derived objects always retain source message IDs.</p><div class="grid">{cards}</div><h2>Your year in objects</h2><div class="grid">{objcards}</div>'
    if activity:
        maxn=max(x["n"] for x in activity)
        body+='<h2>Most active days</h2>'+''.join(f'<div class="card"><b>{x["day"]}</b> — {x["n"]} user messages<div class="bar"><i style="width:{100*x["n"]/maxn:.0f}%"></i></div></div>' for x in sorted(activity,key=lambda x:x["n"],reverse=True)[:12])
    (out/'index.html').write_text(page('Life Wrapped',body),encoding='utf-8')

    ideas=_rows(db,'IDEA')
    with db.connect() as con: links=[dict(r) for r in con.execute("SELECT * FROM object_links WHERE predicate='REDISCOVERS'")]
    redis=Counter(l['object_object_id'] for l in links)
    idea_body=f'<p>{len(ideas)} explicit/candidate ideas detected; {len(links)} probable rediscovery links.</p>'
    for x in sorted(ideas,key=lambda z:(redis[z['object_id']],z['first_observed_at'] or ''),reverse=True)[:250]:
        idea_body+=f'<div class="card"><b>{html.escape(x["canonical_text"][:260])}</b><p class="muted">{x["first_observed_at"] or "unknown date"} · rediscovered {redis[x["object_id"]]} times</p><div class="evidence">evidence message: <code>{x["evidence_message_id"]}</code></div></div>'
    (out/'ideas.html').write_text(page('Idea Cemetery',idea_body),encoding='utf-8')

    qs=_rows(db,'QUESTION'); qbody=f'<p>{len(qs)} questions detected from your own messages.</p>'
    for x in reversed(qs[-300:]): qbody+=f'<div class="card"><b>{html.escape(x["canonical_text"][:420])}</b><div class="evidence">{x["first_observed_at"] or ""} · {x["evidence_message_id"]}</div></div>'
    (out/'questions.html').write_text(page('My Questions',qbody),encoding='utf-8')

    probs=_rows(db,'PROBLEM')
    with db.connect() as con: tensions=[dict(r) for r in con.execute("SELECT * FROM tensions ORDER BY evidence_count DESC,last_observed_at DESC")]
    pbody=f'<p>{len(probs)} explicit problem/friction messages; {len(tensions)} tension clusters.</p>'
    for t in tensions[:200]: pbody+=f'<div class="card"><b>{html.escape(t["current_state"][:350])}</b><p class="muted">first {t["first_observed_at"] or "?"} · last {t["last_observed_at"] or "?"} · evidence {t["evidence_count"]}</p></div>'
    (out/'problems.html').write_text(page('Problem Ledger',pbody),encoding='utf-8')

    work=_rows(db,work=True); wc=Counter(x['object_type'] for x in work)
    cbody='<p><strong>Work-safe candidate projection.</strong> Nothing here should be shared without review. Raw chats are never included.</p>'
    cbody+='<div class="grid">'+''.join(f'<div class="card"><div class="big">{n}</div><div>{k.title()}</div></div>' for k,n in wc.most_common())+'</div>'
    for x in reversed(work[-250:]): cbody+=f'<div class="card"><span class="pill">{x["object_type"]}</span> {html.escape(x["canonical_text"][:420])}<div class="evidence">work score {x["work_relevance"]:.2f} · evidence {x["evidence_message_id"]}</div></div>'
    (out/'career.html').write_text(page('CareerGit',cbody),encoding='utf-8')

    with db.connect() as con:
        timeline=[dict(r) for r in con.execute("SELECT object_type,canonical_text,first_observed_at,evidence_message_id FROM semantic_objects WHERE first_observed_at IS NOT NULL ORDER BY first_observed_at")]
    tbody='<div class="timeline">'+''.join(f'<div class="item"><b>{html.escape(x["object_type"])}</b> · {html.escape((x["first_observed_at"] or "")[:10])}<br>{html.escape(x["canonical_text"][:400])}<div class="evidence">{x["evidence_message_id"]}</div></div>' for x in timeline[-500:])+'</div>'
    (out/'timeline.html').write_text(page('LifeGit Timeline',tbody),encoding='utf-8')

    # Past Me: a deterministic midpoint snapshot for the static report; CLI supports any date.
    if dated := [x for x in allobj if x['first_observed_at']]:
        ds=sorted(x['first_observed_at'] for x in dated); cutoff=ds[len(ds)//2]
        past=[x for x in dated if x['first_observed_at']<=cutoff]
        pc=Counter(x['object_type'] for x in past)
        pm='<p>Static example snapshot as of <b>'+html.escape(cutoff[:10])+'</b>. Use <code>lifegit past-me --at YYYY-MM-DD</code> for any date.</p>'
        pm+='<div class="grid">'+''.join(f'<div class="card"><div class="big">{n}</div><div>{k.title()}</div></div>' for k,n in pc.most_common())+'</div>'
        for x in reversed(past[-150:]): pm+=f'<div class="card"><span class="pill">{x["object_type"]}</span> {html.escape(x["canonical_text"][:400])}<div class="evidence">{x["first_observed_at"]} · {x["evidence_message_id"]}</div></div>'
    else:
        pm='<p>No dated semantic objects yet.</p>'
    (out/'pastme.html').write_text(page('Past Me',pm),encoding='utf-8')

    # Diff uses first vs second half of observed date range.
    dated=[x for x in allobj if x['first_observed_at']]
    dbody='<p>V0 semantic diff compares object counts in the first and second halves of your imported timeline.</p>'
    if len(dated)>=2:
        dates=sorted(x['first_observed_at'] for x in dated); mid=dates[len(dates)//2]
        a=Counter(x['object_type'] for x in dated if x['first_observed_at']<mid); b=Counter(x['object_type'] for x in dated if x['first_observed_at']>=mid)
        dbody+=f'<p>Split point: <b>{html.escape(mid[:10])}</b></p><table><tr><th>Type</th><th>Earlier</th><th>Later</th><th>Δ</th></tr>'+''.join(f'<tr><td>{k}</td><td>{a[k]}</td><td>{b[k]}</td><td>{b[k]-a[k]:+d}</td></tr>' for k in sorted(set(a)|set(b)))+'</table>'
    (out/'diff.html').write_text(page('Memory Diff',dbody),encoding='utf-8')

    # Machine-readable outputs.
    (out/'semantic_objects.json').write_text(json.dumps(allobj,indent=2,ensure_ascii=False),encoding='utf-8')
    manifest={"stats":stats,"reports":[u for u,_ in NAV],"privacy":"local/private by default"}
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    with db.connect() as con:
        for report in manifest['reports']:
            rid=stable_id('report',report,str(out/report))
            con.execute("INSERT OR REPLACE INTO report_runs(report_run_id,report_type,space_id,output_path) VALUES(?,?,?,?)",(rid,report,'life:default',str(out/report)))
    return manifest
