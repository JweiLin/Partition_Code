#!/usr/bin/env python3
"""Run the packaged Linux MH on all datasets, serially, and compare with Ours."""
import argparse,csv,datetime,hashlib,json,os,re,resource,subprocess,time
from pathlib import Path

def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
    return h.hexdigest()

def main():
    root=Path(__file__).resolve().parent
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data-root',type=Path,default=root/'data')
    parser.add_argument('--run-dir',type=Path,default=None)
    args=parser.parse_args()
    data_root=args.data_root.resolve()
    run_dir=(args.run_dir or root/'run_logs'/datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%d_%H%M%S')).resolve()
    run_dir.mkdir(parents=True,exist_ok=False);(run_dir/'logs').mkdir()
    config=json.loads((root/'benchmark_config.json').read_text(encoding='utf8'))
    manifest=json.loads((root/'runtime_manifest.json').read_text(encoding='utf8'))
    for name in ['MH','MtKaHyPar','libhopart_tbb_limit.so']:
        path=root/name
        if not path.is_file():raise RuntimeError('Missing runtime file: '+name)
        if sha(path)!=manifest['files'][name]['sha256']:raise RuntimeError('Checksum mismatch: '+name)
        r=subprocess.run(['ldd',str(path)],capture_output=True,text=True)
        if r.returncode or 'not found' in r.stdout+r.stderr:raise RuntimeError('Runtime dependencies missing for '+name+'\n'+r.stdout+r.stderr)
    for c in config['cases']:
        for name in ['graph.hgr','design.topo']:
            path=data_root/c['bench']/name
            if not path.is_file():raise RuntimeError('Missing dataset input: '+str(path))
            with path.open('rb') as f:
                if f.read(80).startswith(b'version https://git-lfs.github.com/spec/v1'):raise RuntimeError('Dataset is a Git LFS pointer; run git lfs pull first: '+str(path))
            expected=c['inputs'][name]['sha256']
            if sha(path)!=expected:raise RuntimeError('Dataset checksum mismatch: '+str(path))
    env=os.environ.copy()
    for k in list(env):
        if k.startswith('HOPART_'):env.pop(k)
    env['TERM']='xterm-256color'
    rows=[]
    def save():
        temp=run_dir/'results.tmp';temp.write_text(json.dumps(rows,indent=2)+'\n',encoding='utf8');temp.replace(run_dir/'results.json')
        if rows:
            with (run_dir/'ours_comparison.csv').open('w',encoding='utf8',newline='') as f:
                w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    for c in config['cases']:
        bench=c['bench'];data=data_root/bench
        # Isolate the program's ../output.dis diagnostic and the relative partitioner.
        work=run_dir/'work'/bench/'cwd';work.mkdir(parents=True)
        (work/'MtKaHyPar').symlink_to(root/'MtKaHyPar')
        output=data/'output_packaged.txt';log=run_dir/'logs'/f'{bench}.log'
        command=[str(root/'MH'),'-t',str(data),'-s',str(output),'-imbalance',str(config['imbalance']),'-alpha',str(config['alpha']),'-max-hop',str(c['max_hop'])]
        print('START',bench,flush=True)
        usage0=resource.getrusage(resource.RUSAGE_CHILDREN);started=time.perf_counter()
        try:
            with log.open('w',encoding='utf8') as f:proc=subprocess.run(command,cwd=work,env=env,stdout=f,stderr=subprocess.STDOUT,timeout=config['timeout_seconds'])
            rc=proc.returncode
        except subprocess.TimeoutExpired:rc=124
        wall=time.perf_counter()-started;usage1=resource.getrusage(resource.RUSAGE_CHILDREN)
        cpu=usage1.ru_utime+usage1.ru_stime-usage0.ru_utime-usage0.ru_stime
        text=log.read_text(encoding='utf8',errors='replace')
        if rc:raise RuntimeError(f'{bench} exited with {rc}; see {log}')
        assert '[GY] ALl FINISH' in text and 'MtKaHyPar TBB concurrency limit: 1' in text
        assert 'Karlsruhe Shared Memory Hypergraph Partitioning Framework' in text
        assert 'refine gain: '+('precise' if c['precise_gain'] else 'quantized') in text
        delay=int(re.findall(r'=+\s*Max delay:\s*(\d+)\s*=+',text)[-1])
        cut=int(re.findall(r'cut_size:\s*(\d+)',text)[-1])
        reported=float(re.findall(r'\[GY\]\s*ALl FINISH @ time\s*([0-9.]+)',text)[-1])
        route=data/f"path.max_hop{c['max_hop']-1}"
        hops=max(len(re.findall(r'FPGA\d+',line))-1 for line in route.open())
        partitions=list(data.glob('graph.hgr.part*.KaHyPar'));assert len(partitions)==1
        row=dict(index=c['index'],benchmark=c['dataset'],bench=bench,ours_cut=c['ours_cut'],cut=cut,
            ours_delay=c['ours_delay'],delay=delay,delay_delta=delay-c['ours_delay'],
            delay_comparison='better' if delay<c['ours_delay'] else 'worse' if delay>c['ours_delay'] else 'equal',
            ours_runtime_s=c['ours_runtime_s'],wall_seconds=round(wall,3),reported_seconds=reported,cpu_seconds=round(cpu,3),
            wall_over_ours=round(wall/c['ours_runtime_s'],6),reported_over_ours=round(reported/c['ours_runtime_s'],6),
            defined_max_hop=c['max_hop'],route_max_hop=hops,hop_pass=hops<=c['max_hop'],
            partition_sha256=sha(partitions[0]),route_sha256=sha(route),exit_code=rc)
        rows.append(row);save();print('END',json.dumps(row),flush=True)
    summary=dict(cases=len(rows),delay_better=sum(r['delay_comparison']=='better' for r in rows),
        delay_equal=sum(r['delay_comparison']=='equal' for r in rows),delay_worse=sum(r['delay_comparison']=='worse' for r in rows),
        hop_pass=sum(r['hop_pass'] for r in rows),wall_seconds_sum=sum(r['wall_seconds'] for r in rows),
        reported_seconds_sum=sum(r['reported_seconds'] for r in rows),ours_seconds_sum=sum(r['ours_runtime_s'] for r in rows),
        wall_below_ours=sum(r['wall_seconds']<r['ours_runtime_s'] for r in rows),wall_above_ours=sum(r['wall_seconds']>r['ours_runtime_s'] for r in rows),
        timing_note='Serial full-process wall time; reference R is historical, so ratios are observational, not a controlled speedup claim.')
    (run_dir/'summary.json').write_text(json.dumps(summary,indent=2)+'\n',encoding='utf8')
    (run_dir/'DONE').write_text('complete\n');print('SUMMARY',json.dumps(summary),flush=True)

if __name__=='__main__':main()
