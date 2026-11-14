import json
import time
import pytest
from jarvis.next.contracts import ContextView, InterpretationRequest
from jarvis.next.engine import NextEngine
from jarvis.next.groq import GroqProvider, MODEL, PATH, strict_schema
from jarvis.next.providers import ProviderError, RequestControl
from jarvis.next.tools import default_registry

SECRET = 'fake-groq-credential-unit-test-only'
TEXT = 'Arranca Steam, que voy a jugar'


def request(text=TEXT):
    return InterpretationRequest(request_id='local-request', session_id='local-session', turn_id='local-turn',
        text=text, context=ContextView(), capabilities=default_registry().capabilities())


def wire(**updates):
    data = dict(operation='create_plan', plan_id=None, expected_revision=0, temporal='now', evidence_text=TEXT,
        actions=[dict(tool='applications.open', target='steam', value=None, muted=None, evidence_text=TEXT)],
        changes=[], action_ids=[])
    return {**data, **updates}


def completion(content=None, **updates):
    data = dict(model=MODEL, choices=[{'finish_reason': 'stop', 'message': {'content': json.dumps(content or wire())}}],
                usage={'prompt_tokens': 120, 'completion_tokens': 80})
    return json.dumps({**data, **updates}).encode()


class Response:
    def __init__(self, body=None, status=200):
        self.status = status
        self.body = completion() if body is None else body
    def read1(self, size):
        chunk, self.body = self.body[:size], self.body[size:]
        return chunk


class Connection:
    sock = None
    def __init__(self, responses):
        self.responses = list(responses)
        self.requests = []
        self.closed = False
    def request(self, method, path, body, headers):
        self.requests.append((method, path, json.loads(body), headers))
    def getresponse(self):
        return self.responses.pop(0)
    def close(self):
        self.closed = True


def provider(conn, **options):
    return GroqProvider(SECRET, enabled=True, free_tier_confirmed=True,
                        connection_factory=lambda timeout: conn, **options)


def test_groq_strict_request_minimizes_data_and_reuses_connection():
    conn = Connection([Response(), Response()])
    p = provider(conn)
    try:
        for _ in range(2):
            result = p.interpret(request(), RequestControl(time.monotonic()+2))
            assert json.loads(result.decision_json)['actions'][0]['target'] == 'steam'
            assert result.usage.input_tokens == 120 and result.usage.output_tokens == 80
        method, path, payload, headers = conn.requests[0]
        assert method == 'POST' and path == PATH
        assert headers['Authorization'] == 'Bearer '+SECRET
        assert payload['response_format']['json_schema']['strict'] is True
        assert payload['model'] == MODEL and payload['reasoning_effort'] == 'low'
        assert not payload['stream'] and not payload.get('tools')
        user = json.loads(payload['messages'][1]['content'])
        assert set(user) == {'text', 'context', 'capabilities'}
        assert SECRET not in json.dumps(payload)
        assert 'local-session' not in json.dumps(payload) and 'local-turn' not in json.dumps(payload)
        assert len(conn.requests) == 2 and not conn.closed
    finally:
        p.close()
    assert conn.closed and SECRET not in repr(p)


def test_strict_schema_closes_all_objects_and_requires_all_fields():
    def check(node):
        if isinstance(node, dict):
            if node.get('type') == 'object':
                assert node['additionalProperties'] is False
                assert set(node['required']) == set(node['properties'])
            for child in node.values():
                check(child)
        elif isinstance(node, list):
            for child in node:
                check(child)
    check(strict_schema())


@pytest.mark.parametrize('enabled,free,key', [(False, False, SECRET), (True, False, SECRET), (True, True, '')])
def test_missing_opt_in_free_attestation_or_key_never_opens_connection(enabled, free, key):
    def forbidden(*_):
        pytest.fail('Unexpected network connection')
    p = GroqProvider(key, enabled=enabled, free_tier_confirmed=free, connection_factory=forbidden)
    with pytest.raises(ProviderError) as caught:
        p.interpret(request(), RequestControl(time.monotonic()+1))
    assert caught.value.code == ('authentication' if enabled and free else 'unavailable')
    p.close()


@pytest.mark.parametrize('status,expected', [(301, 'connection'), (400, 'invalid_response'), (401, 'authentication'),
    (403, 'authentication'), (404, 'model_unavailable'), (408, 'timeout'), (429, 'quota'), (503, 'connection')])
def test_http_failures_are_redacted_without_retries_or_redirects(status, expected, caplog, capsys):
    conn = Connection([Response(('error: '+SECRET).encode(), status)])
    p = provider(conn)
    with pytest.raises(ProviderError) as caught:
        p.interpret(request(), RequestControl(time.monotonic()+1))
    assert caught.value.code == expected and SECRET not in str(caught.value)
    assert conn.closed and len(conn.requests) == 1
    assert SECRET not in caplog.text + str(capsys.readouterr())
    p.close()


@pytest.mark.parametrize('body', [b'not JSON', b'x'*65537,
    completion(model='unrequested-model'), completion(choices=[]),
    completion(choices=[{'finish_reason': 'length', 'message': {'content': '{}'}}]),
    completion(choices=[{'finish_reason': 'stop', 'message': {'tool_calls': [{}], 'content': '{}'}}]),
    completion(content=wire(evidence_text='invented evidence')),
    completion(content={**wire(), 'response': 'Steam está arrancado'}),
    completion(content={k: v for k, v in wire().items() if k != 'plan_id'}),
], ids=['bad-json', 'oversized', 'wrong-model', 'no-choice', 'truncated', 'tool-call', 'invented-evidence', 'free-response', 'missing-field'])
def test_malformed_truncated_or_manipulated_response_is_rejected(body):
    conn = Connection([Response(body)])
    p = provider(conn)
    with pytest.raises(ProviderError) as caught:
        p.interpret(request(), RequestControl(time.monotonic()+1))
    assert caught.value.code == 'invalid_response' and conn.closed
    p.close()


def test_expired_or_cancelled_control_never_sends():
    conn = Connection([])
    p = provider(conn)
    control = RequestControl(time.monotonic()-1)
    with pytest.raises(ProviderError):
        p.interpret(request(), control)
    control = RequestControl(time.monotonic()+1)
    control.cancelled.set()
    with pytest.raises(ProviderError):
        p.interpret(request(), control)
    assert not conn.requests
    p.close()


def test_known_credential_in_text_is_not_sent_to_model():
    conn = Connection([])
    p = provider(conn)
    with pytest.raises(ProviderError):
        p.interpret(request('Mi clave es '+SECRET), RequestControl(time.monotonic()+1))
    assert not conn.requests
    p.close()


def test_offline_commands_do_not_call_configured_remote_and_json_is_not_permission():
    conn = Connection([Response()])
    p = provider(conn)
    e = NextEngine(p)
    e.begin_session('cli')
    try:
        assert e.interpret('Abre Steam').disposition == 'simulated' and not conn.requests
        e.begin_session('cli')
        result = e.interpret(TEXT)
        assert result.disposition == 'withheld' and not result.results and not result.plan.items
        assert len(conn.requests) == 1
    finally:
        e.close()


def test_app_target_correction_uses_local_action_id_and_no_arbitrary_parameters():
    content = wire(operation='modify_plan', plan_id='p', expected_revision=2, actions=[],
        changes=[dict(action_id='a', target='spotify', value=None, muted=None)])
    from jarvis.next.groq import decision_from_wire
    parsed = decision_from_wire(json.dumps(content), request())
    assert parsed.changes[0].target == 'spotify' and parsed.changes[0].parameters == {}


def test_changed_target_must_be_registered_and_match_resource():
    from jarvis.next.contracts import ActionChange, Decision, ProviderReply
    from jarvis.next.providers import FakeProvider
    def forge(req, _):
        decision = Decision(operation='modify_plan', plan_id=req.context.plan_id,
            expected_revision=req.context.revision, changes=(ActionChange(
                action_id=req.context.items[0].action_id, target='invented'),))
        return ProviderReply(decision_json=decision.model_dump_json())
    e = NextEngine(FakeProvider(forge))
    e.begin_session('cli')
    try:
        first = e.interpret('Abre Steam')
        result = e.interpret('No, mejor otra aplicación')
        assert result.disposition == 'rejected' and result.plan == first.plan
    finally:
        e.close()


def test_credential_store_is_used_only_after_remote_opt_in(monkeypatch):
    from jarvis.next import credentials
    calls = []
    monkeypatch.delenv('GROQ_API_KEY', raising=False)
    monkeypatch.setattr(credentials, 'read_windows_key', lambda: calls.append(1) or SECRET)
    disabled = GroqProvider()
    assert not calls
    enabled = GroqProvider(enabled=True, free_tier_confirmed=True)
    assert calls == [1]
    enabled.close()
    disabled.close()


def test_environment_overrides_store_without_reading_or_logging_it(monkeypatch, capsys):
    from jarvis.next import credentials
    monkeypatch.setenv('GROQ_API_KEY', SECRET)
    monkeypatch.setattr(credentials, 'read_windows_key', lambda: pytest.fail('Store should not be read'))
    assert credentials.read_groq_key() == SECRET
    assert SECRET not in str(capsys.readouterr())


def test_credential_store_error_is_not_exposed(monkeypatch, capsys, caplog):
    from jarvis.next import credentials
    monkeypatch.delenv('GROQ_API_KEY', raising=False)
    def fail():
        raise RuntimeError(SECRET)
    monkeypatch.setattr(credentials, 'read_windows_key', fail)
    assert credentials.read_groq_key() is None
    assert SECRET not in str(capsys.readouterr())+caplog.text


def test_invalid_credential_never_touches_windows_store(monkeypatch):
    from jarvis.next import credentials
    monkeypatch.setattr(credentials, '_windows_api', lambda: pytest.fail('Invalid secret reached Windows'))
    with pytest.raises(ValueError):
        credentials.store_groq_key('invalid key')
