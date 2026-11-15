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
    status_path = dataset.with_suffix('.status.json')
    if status_path.exists() and json.loads(status_path.read_text(encoding='utf-8')).get('status') != 'reserved':
        raise ValueError('Dataset retired; use only as development regression')
    if {p.as_posix() for p in Path('jarvis/next').glob('*.py')} != set(data['engine_sha256']):
        raise ValueError('Frozen engine module set changed')
    for name, expected in data['engine_sha256'].items():
        if hashlib.sha256(Path(name).read_bytes().replace(b'\r\n', b'\n')).hexdigest() != expected:
            raise ValueError('Frozen engine changed; retire this set before tuning or bind a NEW reserved set')
    return data, digest


def continuation(data, digest, prior_path, provider):
    """Manual continuation at a case boundary; never retries an attempted turn."""
    raw = prior_path.read_bytes()
    previous = json.loads(raw)
    manifest = previous.get('reserved_manifest', {})
    if (manifest.get('dataset_sha256') != digest or manifest.get('engine_sha256') != data['engine_sha256']
        or previous.get('provider') != provider or previous.get('status') not in ('stopped_on_provider_error', 'completed_limited')):
        raise ValueError('Continuation does not match this frozen evaluation')
    if provider == 'groq' and (previous.get('model') != data['configuration']['model']
        or previous.get('reasoning_effort') != data['configuration']['reasoning_effort']):
        raise ValueError('Continuation provider configuration differs')
    flat = [(case['id'], index, row['text']) for case in data['cases'] for index, row in enumerate(case['turns'])]
    offset = manifest.get('evaluated_offset', 0)
    attempted = previous.get('rows', [])
    actual = [(row['case'], row['turn'], row['text']) for row in attempted]
    if not attempted or actual != flat[offset:offset+len(attempted)]:
        raise ValueError('Attempted prefix does not match the sealed cases')
    start = offset+len(attempted)
    if start >= len(flat) or flat[start][1] != 0:
        raise ValueError('Continuation requires unattempted cases at a session boundary')
    selected = dict(data, cases=data['cases'][[case['id'] for case in data['cases']].index(flat[start][0]):])
    return selected, start, hashlib.sha256(raw.replace(b'\r\n', b'\n')).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dataset', type=Path, default=Path('docs/evaluation/next_reserved_v1.json'))
    parser.add_argument('--provider', choices=['fixture', 'offline', 'groq'], default='fixture')
    parser.add_argument('--allow-remote', action='store_true')
    parser.add_argument('--free-tier', action='store_true')
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--continue-from', type=Path, help='Explicitly continue only untouched cases after a stopped report')
    args = parser.parse_args()
    try:
        data, digest = verify(args.dataset)
        selected, offset, prior_hash = data, 0, None
        if args.continue_from:
            selected, offset, prior_hash = continuation(data, digest, args.continue_from, args.provider)
        config = dict(data['configuration'])
        config['max_turns'] = min(config['max_turns'], sum(len(c['turns']) for c in selected['cases']))
        report = run_pilot(selected, args.provider, output=args.output,
            allow_remote=args.allow_remote, free_tier=args.free_tier,
            detailed_metrics=True, **config)
    except ValueError:
        parser.error('Check immutable dataset/engine seals, output path and remote opt-ins.')
    report['reserved_manifest'] = dict(dataset_sha256=digest,
        frozen_engine_commit=data['frozen_engine_commit'], engine_sha256=data['engine_sha256'],
        evaluated_offset=offset, prior_report_sha256_utf8_lf=prior_hash,
        limits='Internally authored by same agent after freeze. Exact duplicate check only; semantic near-duplicates and author bias remain possible. Fixture run checks infrastructure only.')
    report['evaluation_kind'] = ('internal_reserved_continuation' if args.continue_from else 'internal_reserved_first_pass') if args.provider == 'groq' else 'infrastructure_control'
    args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False)+'\n', encoding='utf-8')
    print(json.dumps({'status': report['status'], 'summary': report.get('detailed_summary')}, indent=2))


if __name__ == '__main__':
    main()
