"""Combine disjoint first exposures, verifying seals, order and continuation links."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import statistics


def canonical_hash(raw):
    return hashlib.sha256(raw.replace(b'\r\n', b'\n')).hexdigest()


def combine(dataset, paths):
    raw = dataset.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    if digest != dataset.with_suffix('.sha256').read_text().strip():
        raise ValueError('Dataset seal mismatch')
    data = json.loads(raw)
    expected = [(c['id'], i, r['text'], r.get('role', 'evaluation'), c['category'])
                for c in data['cases'] for i,r in enumerate(c['turns'])]
    rows, sources, offset, previous_hash = [], [], 0, None
    for path in paths:
        blob = path.read_bytes()
        part = json.loads(blob)
        seal = part.get('reserved_manifest', {})
        if (seal.get('dataset_sha256') != digest or seal.get('engine_sha256') != data['engine_sha256']
            or seal.get('evaluated_offset', 0) != offset or part.get('provider') != 'groq'
            or part.get('model') != data['configuration']['model']
            or part.get('reasoning_effort') != data['configuration']['reasoning_effort']
            or seal.get('prior_report_sha256_utf8_lf') != previous_hash):
            raise ValueError('Non-contiguous or incompatible first-pass reports')
        current = part['rows']
        keys = [(r['case'], r['turn'], r['text'], r['role'], r['category']) for r in current]
        if not current or keys != expected[offset:offset+len(current)]:
            raise ValueError('Repeated, changed or out-of-order cases')
        rows.extend(current)
        sources.append(dict(path=path.as_posix(), sha256_utf8_lf=canonical_hash(blob),
            offset=offset, turns=len(current), source_status=part['status'], source_commit=part['commit']))
        offset += len(current)
        previous_hash = canonical_hash(blob)
    fresh = [r for r in rows if r['role']=='evaluation']
    observed = [r for r in fresh if r['provider_contract_valid'] is True]
    critical = [r for r in fresh if r['category']=='critical']
    categories = {}
    for category in sorted({r['category'] for r in fresh}):
        selected = [r for r in fresh if r['category']==category]
        categories[category] = dict(turns=len(selected), matches=sum(r['semantic_and_plan_match'] for r in selected))
    latency = {}
    for route in ('direct', 'provider'):
        values = sorted(r['seconds'] for r in rows if r['route']==route)
        latency[route] = dict(count=len(values), median=statistics.median(values) if values else None,
            p95=values[math.ceil(.95*len(values))-1] if values else None)
    return dict(dataset_sha256=digest, frozen_engine_commit=data['frozen_engine_commit'], sources=sources,
        complete=offset==len(expected), rows=rows, category_summary=categories, route_latency=latency,
        summary=dict(new_turns=len(fresh), known_control_turns=len(rows)-len(fresh),
            pipeline_matches=sum(r['semantic_and_plan_match'] for r in fresh),
            observed_provider_decisions=len(observed), unobserved_provider_decisions=len(fresh)-len(observed),
            provider_operation_matches=sum(r['provider_operation_match'] is True for r in observed),
            catalog_proposals=sum(r['provider_catalog_valid'] is not None for r in observed),
            valid_catalog_proposals=sum(r['provider_catalog_valid'] is True for r in observed),
            valid_provider_references=sum(r['provider_references_valid'] is True for r in observed),
            identity_or_no_mutation_checks=sum(r['identity_preserved'] is not None for r in fresh),
            identity_or_no_mutation_passed=sum(r['identity_preserved'] is True for r in fresh),
            critical_turns=len(critical), critical_matches=sum(r['semantic_and_plan_match'] for r in critical),
            critical_unexpected_drafts=sum(r['unexpected_action_draft'] for r in critical),
            unreviewed_provider_results=sum(r['unreviewed_provider_results'] for r in rows),
            physical_execution_claims=sum(r['executed'] for r in rows)),
        limits='Consolidation of disjoint first exposures under one frozen engine, not a second evaluation. Manual continuation restarted TLS/session processing only at untouched case boundaries. setup_succeeded means every previous check passed, not proof that actual context was wrong. Same author, internal reserved set, no universal accuracy/safety claim.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dataset', type=Path, default=Path('docs/evaluation/next_reserved_v1.json'))
    parser.add_argument('--reports', nargs='+', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error('Preserve earlier consolidation')
    try:
        report = combine(args.dataset, args.reports)
    except ValueError:
        parser.error('Dataset or first-pass provenance check failed')
    args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False)+'\n', encoding='utf-8')
    print(json.dumps({'complete': report['complete'], 'summary': report['summary'], 'categories': report['category_summary']}, indent=2))


if __name__ == '__main__':
    main()
