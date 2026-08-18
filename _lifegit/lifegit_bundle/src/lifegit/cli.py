from __future__ import annotations

import argparse
import json
from pathlib import Path

from lifegit.db import LifeDB
from lifegit.extract import run_extraction
from lifegit.providers import PROVIDERS
from lifegit.qdw_export import export_qdw_jsonl
from lifegit.enrichment import export_batches, apply_results
from lifegit.pastme import write_snapshot
from lifegit.api import serve as serve_api
from lifegit.reports import generate_all


def import_one(args):
    provider=PROVIDERS[args.provider]()
    conversations,sha,member=provider.parse(Path(args.input))
    db=LifeDB(args.db)
    result=db.import_conversations(conversations,artifact_sha=sha,provider=args.provider,source_path=str(args.input),member_name=member)
    print(json.dumps(result,indent=2))

def extract(args):
    db=LifeDB(args.db); print(json.dumps(run_extraction(db,rebuild=not args.incremental),indent=2))

def reports(args):
    db=LifeDB(args.db); print(json.dumps(generate_all(db,args.out),indent=2))

def build_all(args):
    provider=PROVIDERS[args.provider]()
    conversations,sha,member=provider.parse(Path(args.input)); db=LifeDB(args.db)
    print(json.dumps(db.import_conversations(conversations,artifact_sha=sha,provider=args.provider,source_path=str(args.input),member_name=member),indent=2))
    print(json.dumps(run_extraction(db,rebuild=True),indent=2)); print(json.dumps(generate_all(db,args.out),indent=2))

def stats(args): print(json.dumps(LifeDB(args.db).stats(),indent=2))
def qdw_export(args): print(json.dumps(export_qdw_jsonl(LifeDB(args.db),args.out,space_id=args.space),indent=2))
def llm_batch(args): print(json.dumps(export_batches(LifeDB(args.db),args.out),indent=2))
def apply_enrichment(args): print(json.dumps(apply_results(LifeDB(args.db),args.input,extractor_version=args.version),indent=2))
def past_me(args): print(json.dumps(write_snapshot(LifeDB(args.db),args.at,args.out),indent=2))
def serve_cmd(args): serve_api(args.db,args.host,args.port)

def main(argv=None):
    p=argparse.ArgumentParser(prog='lifegit'); sub=p.add_subparsers(dest='cmd',required=True)
    s=sub.add_parser('import'); s.add_argument('input'); s.add_argument('--provider',choices=sorted(PROVIDERS),required=True); s.add_argument('--db',default='life.db'); s.set_defaults(func=import_one)
    s=sub.add_parser('extract'); s.add_argument('--db',default='life.db'); s.add_argument('--incremental',action='store_true'); s.set_defaults(func=extract)
    s=sub.add_parser('reports'); s.add_argument('--db',default='life.db'); s.add_argument('--out',default='reports'); s.set_defaults(func=reports)
    s=sub.add_parser('build-all'); s.add_argument('input'); s.add_argument('--provider',choices=sorted(PROVIDERS),required=True); s.add_argument('--db',default='life.db'); s.add_argument('--out',default='reports'); s.set_defaults(func=build_all)
    s=sub.add_parser('stats'); s.add_argument('--db',default='life.db'); s.set_defaults(func=stats)
    s=sub.add_parser('qdw-export'); s.add_argument('--db',default='life.db'); s.add_argument('--out',default='qdw_personal.jsonl'); s.add_argument('--space',default='life:default'); s.set_defaults(func=qdw_export)
    s=sub.add_parser('llm-batch'); s.add_argument('--db',default='life.db'); s.add_argument('--out',default='enrichment_input.jsonl'); s.set_defaults(func=llm_batch)
    s=sub.add_parser('apply-enrichment'); s.add_argument('input'); s.add_argument('--db',default='life.db'); s.add_argument('--version',default='llm-v0.1'); s.set_defaults(func=apply_enrichment)
    s=sub.add_parser('past-me'); s.add_argument('--at',required=True); s.add_argument('--db',default='life.db'); s.add_argument('--out',default='past_me.json'); s.set_defaults(func=past_me)
    s=sub.add_parser('serve'); s.add_argument('--db',default='life.db'); s.add_argument('--host',default='127.0.0.1'); s.add_argument('--port',type=int,default=8787); s.set_defaults(func=serve_cmd)
    args=p.parse_args(argv); args.func(args)
if __name__=='__main__': main()
