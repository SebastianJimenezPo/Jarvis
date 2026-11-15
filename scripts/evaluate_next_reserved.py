"""First-pass reserved evaluation; verifies the frozen engine and never overwrites."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.evaluate_next_pilot import run_pilot


def verify(dataset):
    raw = dataset.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    if digest != dataset.with_suffix('.sha256').read_text(encoding='ascii').strip():
        raise ValueError('Dataset seal mismatch')
    data = json.loads(raw)
    if {p.as_posix() for p in Path('jarvis/next').glob('*.py')} != set(data['engine_sha256']):
        raise ValueError('Frozen engine module set changed')
    for name, expected in data['engine_sha256'].items():
        if hashlib.sha256(Path(name).read_bytes().replace(b'\r\n', b'\n')).hexdigest() != expected:
            raise ValueError('Frozen engine changed; retire this set before tuning or bind a NEW reserved set')
    return data, digest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dataset', type=Path, default=Path('docs/evaluation/next_reserved_v1.json'))
    parser.add_argument('--provider', choices=['fixture', 'offline', 'groq'], default='fixture')
    parser.add_argument('--allow-remote', action='store_true')
    parser.add_argument('--free-tier', action='store_true')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    try:
        data, digest = verify(args.dataset)
        config = data['configuration']
        report = run_pilot(data, args.provider, output=args.output,
            allow_remote=args.allow_remote, free_tier=args.free_tier,
            detailed_metrics=True, **config)
    except ValueError:
        parser.error('Check immutable dataset/engine seals, output path and remote opt-ins.')
    report['reserved_manifest'] = dict(dataset_sha256=digest,
        frozen_engine_commit=data['frozen_engine_commit'], engine_sha256=data['engine_sha256'],
        limits='Internally authored by same agent after freeze. Exact duplicate check only; semantic near-duplicates and author bias remain possible. Fixture run checks infrastructure only.')
    report['evaluation_kind'] = 'internal_reserved_first_pass' if args.provider == 'groq' else 'infrastructure_control'
    args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False)+'\n', encoding='utf-8')
    print(json.dumps({'status': report['status'], 'summary': report.get('detailed_summary')}, indent=2))


if __name__ == '__main__':
    main()
