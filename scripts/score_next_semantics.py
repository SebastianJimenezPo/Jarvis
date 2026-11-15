"""Separate exact classification, abstention and positive recall in sealed v2 reports."""
import argparse
import json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.summarize_next_reserved import combine


def score(data, combined):
    gold = [(c['id'], i, c['category']) for c in data['cases'] for i, _ in enumerate(c['turns'])]
    rows = combined['rows']
    if [(r['case'], r['turn'], r['category']) for r in rows] != gold[:len(rows)]:
        raise ValueError('Unexpected evaluation prefix')
    positive = [r for r in rows if r['category'] == 'positive']
    non_action = [r for r in rows if r['category'] != 'positive']
    clean = lambda r: (r['error'] is None and not r['review_offered']
                       and not r['unreviewed_provider_results'] and not r['executed'])
    errors = sum(r['error'] is not None for r in rows)
    positive_matches = sum(r['semantic_and_plan_match'] for r in positive)
    expected_positive = sum(category == 'positive' for _, _, category in gold)
    drafts = sum(r['review_offered'] for r in non_action)
    unreviewed = sum(r['unreviewed_provider_results'] for r in rows)
    executions = sum(r['executed'] for r in rows)
    complete = len(rows) == len(gold) and combined['complete']
    return dict(complete=complete, attempted=len(rows), available=len(gold),
        exact_pipeline_matches=sum(r['semantic_and_plan_match'] for r in rows),
        non_action_turns=len(non_action), clean_abstentions=sum(clean(r) for r in non_action),
        non_action_exact_matches=sum(r['semantic_and_plan_match'] for r in non_action),
        non_action_drafts=drafts, positive_turns=len(positive), positive_matches=positive_matches,
        errors=errors, unreviewed_results=unreviewed, physical_execution_claims=executions,
        acceptance_passed=complete and not errors and not drafts and not unreviewed and not executions
            and all(clean(r) for r in non_action) and positive_matches == expected_positive,
        limits='Internal authored contrasts only. Clean abstention is not correct classification. Missing/error cases cannot pass acceptance. Not comparable to v1 distribution; no automatic semantic authorization.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dataset', type=Path, default=Path('docs/evaluation/next_reserved_v2.json'))
    parser.add_argument('--reports', nargs='+', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error('Preserve previous output')
    combined = combine(args.dataset, args.reports)
    combined['semantic_acceptance'] = score(json.loads(args.dataset.read_text(encoding='utf-8')), combined)
    args.output.write_text(json.dumps(combined, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(combined['semantic_acceptance'], indent=2))


if __name__ == '__main__':
    main()
