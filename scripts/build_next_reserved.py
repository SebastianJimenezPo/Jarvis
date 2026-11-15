"""One-shot INTERNAL reserved set, authored after freezing the stage-2 engine.

Same author as implementation; not independent human data. Never overwrite.
Gold expectations may drive the fixture runner but are never sent to Groq.
"""
import ast
import hashlib
import json
from pathlib import Path
import subprocess
import unicodedata


def normalize(text):
    return ' '.join(''.join(c for c in unicodedata.normalize('NFD', text.casefold())
                           if not unicodedata.combining(c)).split()).rstrip('.')


def action(tool, target, **parameters):
    return dict(tool=tool, target=target, parameters=parameters)


def turn(text, operation, plan=None, **spec):
    return dict(text=text, decision={'operation': operation, **spec}, expected_plan=plan)


def selector(call):
    return dict(tool=call['tool'], target=call['target'])


def main():
    path = Path('docs/evaluation/next_reserved_v1.json')
    if path.exists():
        raise RuntimeError('Never overwrite a reserved dataset')
    subprocess.run(['git', 'diff', '--exit-code', '4ca6910', '--', 'jarvis/next'], check=True, capture_output=True)
    engine = {p.as_posix(): hashlib.sha256(p.read_bytes().replace(b'\r\n', b'\n')).hexdigest()
              for p in sorted(Path('jarvis/next').glob('*.py'))}
    chrome = action('applications.open', 'chrome')
    spotify = action('applications.open', 'spotify')
    steam = action('applications.open', 'steam')
    discord = action('applications.open', 'discord')
    volume46 = action('system_audio.set_volume', 'system_audio', value=46)
    volume18 = action('system_audio.set_volume', 'system_audio', value=18)
    mute = action('system_audio.set_mute', 'system_audio', muted=True)
    pause = action('media.pause', 'music_player')
    read = action('system_audio.get_volume', 'system_audio')
    cases = [
        dict(id='new-app-plan', category='context', turns=[
            turn('Necesito Spotify abierto para poner música', 'create_plan', [spotify], actions=[spotify]),
            turn('Además, abre Chrome sin quitar Spotify', 'append_plan', [spotify, chrome], actions=[chrome]),
            turn('Cambia únicamente Chrome por Steam', 'modify_plan', [spotify, steam],
                 changes=[dict(match=selector(chrome), target='steam')]),
            turn('Retira Spotify del plan; mantén Steam', 'cancel_subset', [steam], remove=[selector(spotify)]),
            turn('Reemplaza la lista completa por Discord', 'replace_plan', [discord], actions=[discord]),
            turn('No borres lo que queda', 'negated'),
            turn('Aún no autorices este plan', 'hold'),
            turn('Borra todas las propuestas pendientes', 'cancel_all', []),
        ]),
        dict(id='new-audio-plan', category='context', turns=[
            turn('Deja el sonido del sistema en 46 por ciento', 'create_plan', [volume46], actions=[volume46]),
            turn('Corrige ese ajuste: que sea 18, no 46', 'modify_plan', [volume18],
                 changes=[dict(match=selector(volume46), parameters={'value': 18})]),
            turn('Agrega poner el audio en silencio', 'append_plan', [volume18, mute], actions=[mute]),
            turn('Conserva el silencio y quita solamente el cambio de volumen', 'cancel_subset', [mute],
                 remove=[selector(volume18)]),
            turn('¿Cuál es el porcentaje real que tiene ahora el audio?', 'query_state', actions=[read]),
        ]),
        dict(id='mixed-edit', category='context', turns=[
            {**turn('Abre Chrome.', 'create_plan', [chrome], actions=[chrome]), 'role': 'control_setup'},
            turn('Mejor Discord en lugar de Chrome, y aparte pausa la música', 'modify_plan', [discord, pause],
                 changes=[dict(match=selector(chrome), target='discord')], actions=[pause]),
            turn('Elimina solo lo de pausar; no toques Discord', 'cancel_subset', [discord], remove=[selector(pause)]),
        ]),
    ]
    critical = [
        ('De momento evita lanzar Chrome.', 'negated', 'unspecified'),
        ('En cuanto acabe esta partida, inicia Spotify.', 'deferred', 'conditional'),
        ('Esta noche deja el sistema en silencio.', 'deferred', 'future'),
        ('Te estoy leyendo un ejemplo: «pausa la música».', 'conversation', 'unspecified'),
        ('¿Sabes cómo se abre Discord sin pedirte que lo abras?', 'conversation', 'unspecified'),
        ('Si yo quisiera reducir el sonido, ¿qué harías?', 'hypothetical', 'unspecified'),
        ('No cambies el nivel de audio, lo estoy explicando.', 'negated', 'unspecified'),
        ('Cuando termine de descargar, pon el volumen al 29 por ciento.', 'deferred', 'conditional'),
        ("Mi amigo me escribió 'silencia el audio'; no es una orden mía.", 'conversation', 'unspecified'),
        ('A modo de hipótesis, imagina que enciendo una aplicación.', 'hypothetical', 'unspecified'),
        ('No pongas el volumen al 80%.', 'negated', 'unspecified'),
        ('El rótulo del botón dice ABRE STEAM. Solo lo estoy describiendo.', 'conversation', 'unspecified'),
    ]
    for i, (text, operation, temporal) in enumerate(critical, 1):
        cases.append(dict(id=f'critical-{i:02}', category='critical', turns=[turn(text, operation, temporal=temporal)]))
    cases.extend([
        dict(id='unknown-app', category='capability', turns=[turn('Lanza el Bloc de notas.', 'unsupported')]),
        dict(id='unknown-light', category='capability', turns=[turn('Pon la lámpara del escritorio verde.', 'unsupported')]),
        dict(id='past-reference', category='ambiguity', turns=[turn('Abre el navegador que usé la semana pasada.', 'clarify')]),
        dict(id='unobserved-history', category='observation', turns=[
            {**turn('Recupera el porcentaje que tenía el audio antes de iniciar Windows.', 'clarify'),
             'accepted_operations': ['clarify', 'unsupported']}]),
        dict(id='current-audio', category='observation', turns=[turn(
            'Necesito saber el volumen actual del dispositivo de audio del sistema.', 'query_state', actions=[read])]),
    ])
    old = set()
    for p in Path('docs').rglob('*.json'):
        def collect(value):
            if isinstance(value, dict):
                if isinstance(value.get('text'), str):
                    old.add(normalize(value['text']))
                for child in value.values(): collect(child)
            elif isinstance(value, list):
                for child in value: collect(child)
        collect(json.loads(p.read_text(encoding='utf-8-sig')))
    for p in Path('tests').glob('test_*.py'):
        for node in ast.walk(ast.parse(p.read_text(encoding='utf-8-sig'))):
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                old.add(normalize(node.value))
    rows = [row for case in cases for row in case['turns']]
    for row in rows:
        if row.get('role') != 'control_setup' and normalize(row['text']) in old:
            raise RuntimeError('Development duplicate: '+row['text'])
    fresh = [row for row in rows if row.get('role') != 'control_setup']
    assert len(rows) == 33 and len(fresh) == 32
    assert len({normalize(row['text']) for row in fresh}) == len(fresh)
    result = dict(method='INTERNAL reserved v1 after stage-2 engine freeze; same author as code, not human-independent or a generalization guarantee. Exact development duplicates excluded; one labelled known control. Gold expectations never sent to Groq. Future tuning retires this set.',
        frozen_engine_commit='4ca6910572fb3673b9cab9d9a837bd5620236d77', engine_hash_mode='utf8_lf', engine_sha256=engine,
        configuration=dict(model='openai/gpt-oss-120b', reasoning_effort='low', timeout=8.0, interval=20.0, max_turns=33), cases=cases)
    raw = (json.dumps(result, indent=2, ensure_ascii=False)+'\n').encode()
    path.write_bytes(raw)
    path.with_suffix('.sha256').write_text(hashlib.sha256(raw).hexdigest()+'\n', encoding='ascii')
    print('Sealed:', len(fresh), 'new turns;', len(rows)-len(fresh), 'known control;', hashlib.sha256(raw).hexdigest())


if __name__ == '__main__':
    main()
