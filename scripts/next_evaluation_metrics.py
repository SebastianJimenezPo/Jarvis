"""Evaluation-only observation. No raw responses, unknown targets or secrets exported."""
from jarvis.next.contracts import Decision


class PredictionObserver:
    def __init__(self, inner):
        self.inner = inner
        self.capabilities = inner.capabilities
        self.reset()

    def reset(self):
        self.request_id = None
        self.prediction = None
        self.reply_received = False
        self.contract_valid = None

    def interpret(self, request, control):
        reply = self.inner.interpret(request, control)
        self.request_id = request.request_id
        self.reply_received = True
        try:
            self.prediction = Decision.model_validate_json(reply.decision_json)
            self.contract_valid = True
        except ValueError:
            self.contract_valid = False
        return reply  # The engine, not the observer, validates and authorizes.

    def close(self):
        self.reset()
        self.inner.close()


def prediction_metrics(observer, outcome, before, registry, accepted_operations, operation_matches):
    result = dict(provider_reply_received=False, provider_contract_valid=None,
        provider_operation_match=None, provider_catalog_valid=None, provider_references_valid=None)
    if observer is None or observer.request_id != outcome.request_id:
        return result
    result.update(provider_reply_received=observer.reply_received, provider_contract_valid=observer.contract_valid)
    prediction = observer.prediction
    if prediction is None:
        return result
    result['provider_operation_match'] = any(operation_matches(prediction.operation, op) for op in accepted_operations)
    known = {item.action_id: item.call for item in before.items}
    references = [*prediction.action_ids, *(change.action_id for change in prediction.changes),
                  *(dep for call in prediction.actions for dep in call.depends_on)]
    result['provider_references_valid'] = (prediction.plan_id == before.plan_id
        and prediction.expected_revision == before.revision and all(ref in known for ref in references))
    try:
        for call in prediction.actions:
            registry.validate(call)
        for change in prediction.changes:
            if change.action_id in known:
                call = known[change.action_id]
                registry.validate(call.model_copy(update={'target': change.target or call.target,
                    'parameters': {**call.parameters, **change.parameters}}))
        result['provider_catalog_valid'] = (True if (prediction.actions or prediction.changes)
            and all(change.action_id in known for change in prediction.changes) else None)
    except ValueError:
        result['provider_catalog_valid'] = False
    return result


def identity_preserved(spec, before, after):
    """Independent ID invariants; semantic tool/target/values are scored separately."""
    op = spec['operation']
    old_ids = tuple(item.action_id for item in before.items)
    new_ids = tuple(item.action_id for item in after.items)
    if len(set(new_ids)) != len(new_ids):
        return False
    if op in ('create_plan', 'replace_plan'):
        return bool(after.plan_id) and after.plan_id != before.plan_id and not set(old_ids).intersection(new_ids)
    if op in ('append_plan', 'modify_plan'):
        return after.plan_id == before.plan_id and new_ids[:len(old_ids)] == old_ids
    if op in ('cancel_subset', 'remove_actions'):
        selected = {(s['tool'], s['target']) for s in spec.get('remove', [])}
        expected = tuple(item for item in before.items if (item.call.tool, item.call.target) not in selected)
        return after.plan_id == before.plan_id and after.items == expected
    if op == 'cancel_all':
        return after.plan_id == before.plan_id and not after.items and after.status == 'cancelled'
    if op == 'hold':
        return after.plan_id == before.plan_id and after.items == before.items and after.status == 'withheld'
    return after == before
