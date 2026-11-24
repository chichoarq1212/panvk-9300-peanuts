#!/usr/bin/env python3
"""Check that two ordinary logs actually exercise P01, without uploading logs."""
import argparse, json, re, statistics
from pathlib import Path
from analyze import PACE

ENV=re.compile(r'^\[nxlaunch\] env ([A-Za-z_][A-Za-z_0-9]*)=(.*)$')
REPLAY=re.compile(r'replay up to frame (\d+): per frame (\d+) draws, (\d+) render passes, .*?(\d+) full barriers, .*?([\d.]+) submissions \(([\d.]+) parts\)')
DRAW=re.compile(r'replay recording [\d.]+ ms a frame \(its CPU [\d.]+\), (\d+) draws')
def extract(lines,lo,hi):
    env={}; driver=None; pace=[]; replay=[]; diagnostic=False
    for line in lines:
        m=ENV.match(line)
        if m and m[1].startswith('DM_VK_') and m[1]!='DM_VK_DRIVER':env[m[1]]=m[2].strip()
        if '[vk] driver:' in line:driver=line.split('[vk] driver:',1)[1].strip()
        if 'gpu prof: frame ' in line or 'DM_VK_NANSCAN: every pass' in line or 'DM_VK_NANSCAN=2: passes split' in line:diagnostic=True
        m=PACE.search(line); d=DRAW.search(line)
        if m and d and lo<=int(m[1])<=hi:pace.append(tuple(map(float,(m[2],m[3],d[1]))))
        m=REPLAY.search(line)
        if m and lo<=int(m[1])<=hi:replay.append(tuple(map(float,m.groups()[1:])))
    def med(rows,keys):return dict(zip(keys,map(statistics.median,zip(*rows)))) if rows else None
    return dict(driver=driver,env=env,diagnostic=diagnostic,windows=len(pace),replay_windows=len(replay),pace=med(pace,('fps','gpu_ms','draws')),replay=med(replay,('draws','passes','barriers','submissions','parts')))
def compare(a,b):
    if not a['driver'] or a['driver']!=b['driver'] or 'faux123 v1.1.8' not in a['driver'].lower():raise ValueError('Both runs must identify Faux123 v1.1.8')
    if a['diagnostic'] or b['diagnostic']:raise ValueError('Use ordinary runs, not diagnostics')
    if min(a['windows'],b['windows'])<3:raise ValueError('At least 3 pace windows required per run')
    x,y=a['env'],b['env']
    if x.get('DM_VK_CHUNK_PASS','150')!='150' or y.get('DM_VK_CHUNK_PASS')!='600':raise ValueError('Expected baseline 150/default and candidate 600')
    if {k:v for k,v in x.items() if k!='DM_VK_CHUNK_PASS'}!={k:v for k,v in y.items() if k!='DM_VK_CHUNK_PASS'}:raise ValueError('Other logged Vulkan environment values differ')
    if not a['pace']['draws'] or abs(b['pace']['draws']/a['pace']['draws']-1)>.15:raise ValueError('Draw workload differs; repeat same scene')
    def pct(k):return round(100*(b['pace'][k]/a['pace'][k]-1),2) if a['pace'][k]>0 else None
    return {'fps_change_pct':pct('fps'),'gpu_ms_change_pct':pct('gpu_ms'),'note':'Verify same scene, resolution, temperature and image correctness manually. A timing gain alone is not acceptance.'}
def read(p,r):
    with Path(p).open(encoding='utf-8',errors='replace') as f:return extract(f,*r)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('baseline');p.add_argument('candidate');p.add_argument('--baseline-frames',nargs=2,type=int,required=True);p.add_argument('--candidate-frames',nargs=2,type=int,required=True);a=p.parse_args()
    x=read(a.baseline,a.baseline_frames);y=read(a.candidate,a.candidate_frames)
    print(json.dumps(dict(baseline=x,candidate=y,comparison=compare(x,y)),indent=2))
