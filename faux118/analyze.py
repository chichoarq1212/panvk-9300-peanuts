#!/usr/bin/env python3
"""Extract Peanuts 0.1.7 GPU diagnostics; never edits the input log."""
import argparse, json, re, statistics
from pathlib import Path

PACE = re.compile(r'pace up to frame (\d+) .*?; ([\d.]+) fps; GPU busy p50/p90 ([\d.]+)/([\d.]+) ms')
PIPE = re.compile(r'pipelines up to frame (\d+): (\d+) graphics \+ (\d+) compute pipelines \((\d+) failed.*?draws skipped waiting (\d+)')
NAN = re.compile(r'NaN scan: frame (\d+) pass (\d+): (\d+) NaN \+ (\d+) infinite texels in serial (\d+).*?vertex/fragment(.*)')
PROF = re.compile(r'gpu prof: frame (\d+): \d+ timestamps, ([\d.]+) ms GPU: passes ([\d.]+) ms \(\d+\), dispatches ([\d.]+) ms \(\d+\), clears / copies ([\d.]+) ms, steps with nothing recorded .*? ([\d.]+) ms')

def analyze(lines):
    pace=[]; pipes=[]; nan=[]; prof=[]; drivers=[]; scan=False; cache_denied=False
    for line in lines:
        if '[vk] driver:' in line: drivers.append(line.split('[vk] driver:',1)[1].strip())
        if 'DM_VK_NANSCAN: every pass' in line or 'DM_VK_NANSCAN=2: passes split' in line: scan=True
        if 'shader cache (Permission denied)' in line: cache_denied=True
        m=PACE.search(line)
        if m: pace.append(dict(frame=int(m[1]),fps=float(m[2]),gpu_p50_ms=float(m[3]),gpu_p90_ms=float(m[4])))
        m=PIPE.search(line)
        if m: pipes.append(dict(zip(('frame','graphics','compute','failed','draws_skipped_waiting'),map(int,m.groups()))))
        m=NAN.search(line)
        if m: nan.append(dict(frame=int(m[1]),render_pass=int(m[2]),nan=int(m[3]),infinite=int(m[4]),serial=int(m[5]),shader_pairs=re.findall(r'[0-9a-f]{16}/[0-9a-f]{16}',m[6],re.I)))
        m=PROF.search(line)
        if m: prof.append(dict(frame=int(m[1]),**dict(zip(('total_ms','passes_ms','dispatches_ms','copies_ms','other_ms'),map(float,m.groups()[1:])))))
    tail=pace[-12:]
    return {'driver':drivers[-1] if drivers else None,'cache_permission_error':cache_denied,'pace_samples':len(pace),'last_12_windows':{'fps_median':statistics.median(x['fps'] for x in tail),'gpu_p50_median_ms':statistics.median(x['gpu_p50_ms'] for x in tail)} if tail else None,'last_pipeline_summary':pipes[-1] if pipes else None,'nan_scan_enabled':scan,'nan_events':len(nan),'first_nan_event':min(nan,key=lambda x:(x['frame'],x['render_pass'])) if nan else None,'gpu_profiles':prof,'note':'No NaN events without an enabled scan is not evidence of correct rendering. Profiling changes timing; compare ordinary runs separately.'}

if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('log',type=Path); args=p.parse_args()
    with args.log.open(encoding='utf-8',errors='replace') as f: print(json.dumps(analyze(f),indent=2))
