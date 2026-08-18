from __future__ import annotations

import json
import re
from collections import defaultdict
from dataclasses import dataclass

from lifegit.db import LifeDB
from lifegit.util import jaccard, normalize_text, stable_id

EXTRACTOR_VERSION="deterministic-v0.1"

# Intentionally conservative: these are explicit textual signals, not diagnoses.
PATTERNS={
 "IDEA": [r"\b(?:idea|what if|could we|we can|why (?:don['’]t|not) we|imagine if|wouldn['’]t it be cool)\b"],
 "PROBLEM": [r"\b(?:problem|issue|struggl(?:e|ing)|stuck|can['’]t|cannot|doesn['’]t work|annoying|frustrating|pain point|hate that)\b"],
 "PROJECT": [r"\b(?:project|repo|repository|building|build this|working on|product|app|site|domain)\b"],
 "DISCOVERY": [r"\b(?:i (?:just )?(?:realized|realised|discovered|learned|learnt)|oh shit|wait so|i didn['’]t know|that['’]s interesting)\b"],
 "DECISION": [r"\b(?:i(?:'m| am) going to|i decided|we(?:'re| are) going to|let['’]s use|i(?:'ll| will) use|final choice)\b"],
 "GOAL": [r"\b(?:i want to|i need to|goal is|aim is|trying to|plan is)\b"],
 "ACHIEVEMENT": [r"\b(?:finished|completed|shipped|launched|passed|got accepted|solved|fixed|done with)\b"],
}
WORK_TERMS={"api","repo","repository","github","code","python","rust","javascript","typescript","model","llm","agent","product","startup","customer","research","paper","benchmark","deploy","database","server","frontend","backend","mcp","project","build","engineering","company","work","developer","architecture","test","testing"}
PERSONAL_TERMS={"family","relationship","dating","medical","doctor","sexual","religion","private","home address","passport"}

@dataclass
class Candidate:
    object_type:str
    text:str
    confidence:float


def _question_candidates(text:str)->list[Candidate]:
    out=[]
    for sentence in re.split(r"(?<=[?])\s+",text):
        s=sentence.strip()
        if "?" in s and 5 <= len(s) <= 500:
            out.append(Candidate("QUESTION",s[:500],0.98))
    return out[:12]


def candidates(text:str)->list[Candidate]:
    clean=" ".join(text.split())
    if not clean: return []
    out=_question_candidates(clean)
    for typ, pats in PATTERNS.items():
        if any(re.search(p,clean,re.I) for p in pats):
            out.append(Candidate(typ,clean[:700],0.78 if typ in {"IDEA","PROJECT","PROBLEM"} else 0.72))
    return out


def work_relevance(text:str)->float:
    toks=set(normalize_text(text).split())
    w=len(toks & WORK_TERMS)
    p=sum(1 for phrase in PERSONAL_TERMS if phrase in text.lower())
    score=min(1.0,w/5)
    if p: score=max(0.0,score-0.5)
    return score


def run_extraction(db:LifeDB, *, rebuild:bool=True)->dict:
    with db.connect() as con:
        if rebuild:
            con.execute("DELETE FROM object_links")
            con.execute("DELETE FROM events")
            con.execute("DELETE FROM tensions")
            con.execute("DELETE FROM semantic_objects")
        rows=con.execute("""SELECT m.*,c.title FROM messages m JOIN conversations c USING(conversation_id)
                            WHERE m.role='user' AND m.is_current_path=1 AND length(trim(m.text))>0 ORDER BY m.created_at""").fetchall()
        created=[]
        for r in rows:
            for cand in candidates(r["text"]):
                norm=normalize_text(cand.text)
                # Bucket identity is conservative and evidence-specific in V0; clustering happens with links.
                oid=stable_id("sem",cand.object_type,r["message_id"],norm[:200])
                wr=work_relevance(cand.text)
                privacy="WORK_CANDIDATE" if wr>=0.45 else "PRIVATE"
                con.execute("""INSERT OR IGNORE INTO semantic_objects(object_id,space_id,object_type,canonical_text,normalized_key,
                    first_observed_at,last_observed_at,status,confidence,extractor_version,privacy_class,work_relevance,
                    evidence_message_id,evidence_conversation_id,attributes_json) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                    (oid,"life:default",cand.object_type,cand.text,norm[:400],r["created_at"],r["created_at"],"ACTIVE",cand.confidence,
                     EXTRACTOR_VERSION,privacy,wr,r["message_id"],r["conversation_id"],json.dumps({"conversation_title":r["title"]})))
                created.append((oid,cand.object_type,cand.text,r["created_at"],r["message_id"]))
                if cand.object_type in {"PROJECT","ACHIEVEMENT","DISCOVERY","DECISION"}:
                    eid=stable_id("evt",oid,cand.object_type)
                    con.execute("INSERT OR IGNORE INTO events(event_id,space_id,event_type,subject_object_id,occurred_at,confidence,evidence_message_id,attributes_json) VALUES(?,?,?,?,?,?,?,?)",
                                (eid,"life:default",cand.object_type,oid,r["created_at"],cand.confidence,r["message_id"],"{}"))
        # Link likely rediscoveries/recurrences within same semantic type.
        sem=con.execute("SELECT object_id,object_type,canonical_text,first_observed_at FROM semantic_objects ORDER BY first_observed_at").fetchall()
        by=defaultdict(list)
        for s in sem: by[s["object_type"]].append(s)
        links=0
        for typ,items in by.items():
            if typ not in {"IDEA","QUESTION","PROBLEM","PROJECT"}: continue
            for i in range(len(items)):
                for j in range(max(0,i-120),i):
                    sim=jaccard(items[i]["canonical_text"],items[j]["canonical_text"])
                    threshold=0.48 if typ in {"IDEA","QUESTION"} else 0.55
                    if sim>=threshold:
                        pred="REDISCOVERS" if typ=="IDEA" else "RECURS"
                        lid=stable_id("link",items[i]["object_id"],pred,items[j]["object_id"])
                        con.execute("INSERT OR IGNORE INTO object_links(link_id,subject_object_id,predicate,object_object_id,confidence,attributes_json) VALUES(?,?,?,?,?,?)",
                                    (lid,items[i]["object_id"],pred,items[j]["object_id"],sim,json.dumps({"jaccard":sim})))
                        links+=1
        # Tension projection from recurring explicit problems.
        probs=by.get("PROBLEM",[])
        used=set()
        for i,p in enumerate(probs):
            if p["object_id"] in used: continue
            cluster=[p]
            for q in probs[i+1:]:
                if jaccard(p["canonical_text"],q["canonical_text"])>=0.5:
                    cluster.append(q); used.add(q["object_id"])
            tid=stable_id("tension","problem",p["object_id"])
            conf=min(0.95,0.5+0.1*len(cluster))
            con.execute("INSERT OR REPLACE INTO tensions(tension_id,space_id,tension_type,current_state,desired_state,recurrence,intensity,confidence,first_observed_at,last_observed_at,evidence_count,attributes_json) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
                        (tid,"life:default","EXPLICIT_PROBLEM",p["canonical_text"],None,min(1,len(cluster)/5),0.5,conf,
                         cluster[0]["first_observed_at"],cluster[-1]["first_observed_at"],len(cluster),json.dumps({"object_ids":[x["object_id"] for x in cluster]})))
    return {"semantic_objects":len(created),"links":links}
