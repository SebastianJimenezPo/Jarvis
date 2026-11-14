"""Development-only text microbenchmark. No voice, remote service or model load.

Runs each architecture in a fresh child with the SAME fixed scripted utterances.
Legacy is deliberately rules-only (LLM/semantic disabled), not its hybrid profile.
This does not measure generalization, resident idle, acoustic quality or API speed.
"""
import argparse
import json
import statistics
import subprocess
import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
CASES = ['Abre Steam', 'Volumen al 30%', 'Pausa la música', 'Silencia el audio', 'Cancela', 'Olvida todo lo anterior']


def worker(mode):
    import psutil
    process = psutil.Process()
    before = process.memory_info().rss
    started = time.perf_counter()
    with tempfile.TemporaryDirectory(prefix='jarvis-next-text-bench-') as directory:
        if mode == 'next':
            from jarvis.next.engine import NextEngine
            engine = NextEngine()
            engine.begin_session('benchmark')
            def interpret(text, index):
                result = engine.interpret(text, 'benchmark', str(index))
                return {'operation': result.decision.operation if result.decision else None,
                        'disposition': result.disposition, 'route': result.route,
                        'actions': [a.tool for a in result.decision.actions] if result.decision else []}
        else:
            from dataclasses import replace
            from jarvis.intelligence.dialogue_manager import DialogueManager
            from jarvis.intelligence.settings import IntelligenceConfig
            engine = DialogueManager(Path(directory), replace(IntelligenceConfig(), llm_enabled=False, semantic_enabled=False))
            engine.begin_session('benchmark')
            def interpret(text, index):
                result, _ = engine.interpret(text, 'benchmark', str(index))
                return {'operation': result.interpretation.kind.value, 'route': result.route,
                        'actions': [a.intent for a in result.interpretation.actions]}
        initialization = time.perf_counter()-started
        loaded = process.memory_info().rss
        rows = []
        try:
            # Five warmup turns, identical across processes, before 30 cycles.
            for i, text in enumerate(CASES[:5]):
                interpret(text, i)
            cpu = process.cpu_times()
            cpu_before = cpu.user+cpu.system
            started = time.perf_counter()
            for cycle in range(30):
                for index, text in enumerate(CASES):
                    turn_start = time.perf_counter()
                    outcome = interpret(text, cycle*len(CASES)+index+5)
                    rows.append({'text': text, 'cycle': cycle, 'seconds': time.perf_counter()-turn_start, **outcome})
            elapsed = time.perf_counter()-started
            cpu = process.cpu_times()
            rss_after = process.memory_info().rss
            report = {'mode': mode, 'initialization_seconds_single_sample': initialization,
                'rss_before_engine_import_bytes': before, 'rss_after_initialization_bytes': loaded,
                'rss_after_180_turns_bytes': rss_after,
                'cpu_seconds_delta': (cpu.user+cpu.system)-cpu_before, 'elapsed_seconds': elapsed,
                'peak_cpu': None, 'gpu': None, 'rows': rows, 'summary': {}}
            for text in CASES:
                values = sorted(row['seconds'] for row in rows if row['text'] == text)
                report['summary'][text] = {'count': len(values), 'median_seconds': statistics.median(values),
                    'p95_seconds_nearest_rank': values[28], 'outcome': [row for row in rows if row['text'] == text][-1]}
            return report
        finally:
            engine.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--worker', choices=['next', 'legacy'])
    parser.add_argument('--output', type=Path, default=Path('docs/reports/phase32-foundation-benchmark.json'))
    args = parser.parse_args()
    if args.worker:
        print(json.dumps(worker(args.worker), ensure_ascii=True))
        return
    if args.output.exists():
        raise RuntimeError('Preserve earlier results; select another output')
    reports = []
    for mode in ('legacy', 'next'):
        run = subprocess.run([sys.executable, __file__, '--worker', mode], capture_output=True, text=True,
                             timeout=45, check=True)
        reports.append(json.loads(run.stdout))
    data = {'method': __doc__, 'commit': subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip(),
            'python': sys.version.split()[0], 'cases': CASES, 'runs': reports,
            'limits': 'Single process per mode, fixed order, warm microbenchmark on known development commands. No accuracy, model inference, voice or idle claims; RSS values are snapshots, not sampled peaks.'}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(data, indent=2, ensure_ascii=False)+'\n', encoding='utf-8')
    for report in reports:
        print(report['mode'], report['rss_after_initialization_bytes'], report['rss_after_180_turns_bytes'])


if __name__ == '__main__':
    main()
