#!/usr/bin/env python3
import argparse, json, sys, subprocess, tempfile, os
from datetime import datetime, UTC
def main():
    p = argparse.ArgumentParser(description="Integration Contract Regression Gate")
    p.add_argument('command', choices=['run'])
    p.add_argument('--contract', required=True, help='Contract ID (looks in contracts/{id}.json) or path to JSON')
    p.add_argument('--change', required=True, help='Path to trace corpus JSON file')
    p.add_argument('--env', required=True, help='Target environment profile')
    a = p.parse_args()
    try: s = json.load(open(f"snapshots/{a.contract}/approved.json"))
    except: s = {}
    cf = a.contract if a.contract.endswith('.json') else f"contracts/{a.contract}.json"
    if not os.path.exists(cf): print(f"[ERROR] Contract file not found: {cf}", file=sys.stderr); return 2
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as tmp: rp = tmp.name
    rpth = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'create-a-tool-call-sandbox-replayer-for', 'main.py'))
    if not os.path.exists(rpth): print(f"[ERROR] Sandbox replayer not found at {rpth}", file=sys.stderr); return 2
    cmd = ['python3', rpth, '--contract', cf, '--trace', a.change, '--report', rp, '--seed', '42']
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode not in (0,1,2): print(f"[ERROR] Replay failed: {r.stderr}", file=sys.stderr); return 2
    try: c = json.load(open(rp))
    except Exception as e: print(f"[ERROR] Failed to read replay report: {e}", file=sys.stderr); return 2
    passed = (c.get('successful_calls',0) >= s.get('successful_calls',0) and len(c.get('schema_violations',[])) <= len(s.get('schema_violations',[])) and len(c.get('idempotency_violations',[])) <= len(s.get('idempotency_violations',[])))
    diffs = {}
    if not passed:
        if c.get('successful_calls',0) < s.get('successful_calls',0): diffs['successful_calls'] = {'current': c.get('successful_calls'), 'baseline': s.get('successful_calls')}
        cs, ss = len(c.get('schema_violations',[])), len(s.get('schema_violations',[]))
        if cs > ss: diffs['schema_violations'] = {'current': cs, 'baseline': ss}
        ci, si = len(c.get('idempotency_violations',[])), len(s.get('idempotency_violations',[]))
        if ci > si: diffs['idempotency_violations'] = {'current': ci, 'baseline': si}
    rep = {'contract_id': a.contract, 'environment': a.env, 'change': a.change, 'decision': 'PASS' if passed else 'FAIL', 'diffs': diffs, 'generated_at': datetime.now(UTC).isoformat()}
    plan = {'gate_decision': rep['decision'], 'required_actions': [] if passed else [{'action': 'review', 'details': diffs}]}
    json.dump(rep, open('gate_report.json','w'), indent=2)
    json.dump(plan, open('remediation_plan.json','w'), indent=2)
    print(f"\nGate Decision: {rep['decision']}\n")
    return 0 if passed else 1
if __name__ == '__main__': sys.exit(main())
