"""Seal the pre-voice internal baseline once; never overwrite or train on it mid-run."""
import ast
import hashlib
import json
from pathlib import Path
import subprocess
from scripts.build_next_reserved import action, turn, selector, normalize


def main():
    path = Path('docs/evaluation/next_consolidation_v1.json')
    if path.exists():
        raise ValueError('Preserve original sealed data')
    subprocess.run(['git', 'diff', '--exit-code', '731917a', '--', 'jarvis/next'], check=True, capture_output=True)
    app = lambda name: action('applications.open', name)
    volume = lambda n: action('system_audio.set_volume', 'system_audio', value=n)
    pause = action('media.pause', 'music_player')
    mute = action('system_audio.set_mute', 'system_audio', muted=True)
    def setup(row): return dict(row, role='control_setup')
    cases = [
        dict(id='apps-consolidation', category='context', turns=[
            setup(turn('Abre Spotify', 'create_plan', [app('spotify')], actions=[app('spotify')])),
            turn('También necesito Discord; deja Spotify en la lista.', 'append_plan', [app('spotify'), app('discord')], actions=[app('discord')]),
            turn('Sustituye la acción de Spotify por Chrome y conserva Discord.', 'modify_plan', [app('chrome'), app('discord')], changes=[dict(match=selector(app('spotify')), target='chrome')]),
            turn('Quita Discord de las propuestas, únicamente ese.', 'cancel_subset', [app('chrome')], remove=[selector(app('discord'))]),
        ]),
        dict(id='audio-consolidation', category='context', turns=[
            setup(turn('Volumen al 42%', 'create_plan', [volume(42)], actions=[volume(42)])),
            turn('Suma una pausa de música a ese ajuste.', 'append_plan', [volume(42), pause], actions=[pause]),
            turn('En el ajuste de audio cambia cuarenta y dos por diecisiete, sin quitar la pausa.', 'modify_plan', [volume(17), pause], changes=[dict(match=selector(volume(42)), parameters={'value':17})]),
            turn('Retén la autorización de lo que hemos preparado.', 'hold'),
        ]),
        dict(id='replace-consolidation', category='context', turns=[
            setup(turn('Abre Chrome', 'create_plan', [app('chrome')], actions=[app('chrome')])),
            turn('Descarta la lista anterior y reemplázala entera por Discord.', 'replace_plan', [app('discord')], actions=[app('discord')]),
            turn('Agrega Steam a Discord, quiero conservar ambos.', 'append_plan', [app('discord'), app('steam')], actions=[app('steam')]),
            turn('Cancela todo lo propuesto en esta sesión.', 'cancel_all', []),
        ]),
    ]
    independent = [
        ('natural', turn('Me vendría bien tener Steam abierto ya mismo.', 'create_plan', [app('steam')], actions=[app('steam')])),
        ('natural', turn('Ajusta ahora el sonido de Windows a sesenta y tres por ciento.', 'create_plan', [volume(63)], actions=[volume(63)])),
        ('natural', turn('Quiero que la reproducción musical quede en pausa ahora.', 'create_plan', [pause], actions=[pause])),
        ('natural', turn('Pon el audio del sistema en silencio en este momento, por favor.', 'create_plan', [mute], actions=[mute])),
        ('negation', turn('Evita iniciar Steam; hoy no lo necesito.', 'negated')),
        ('negation', turn('Por ahora no bajes ni subas el volumen del equipo.', 'negated')),
        ('negation', turn('Te prohíbo detener la música que está sonando.', 'negated')),
        ('negation', turn('No abras Chrome; abre solamente Spotify en este momento.', 'create_plan', [app('spotify')], actions=[app('spotify')])),
        ('quotation', turn('En un tutorial aparece la instrucción «Abre Discord»; te estoy contando lo que leo.', 'conversation')),
        ('quotation', turn('La persona del vídeo acaba de pedir que silencien Windows. Yo solo lo describo.', 'conversation')),
        ('quotation', turn('Estoy dictando el texto "Volumen al 55%" para un documento, no una orden para ti.', 'conversation')),
        ('deferred', turn('Después de que cierre el instalador, quiero Spotify abierto.', 'deferred', temporal='conditional')),
        ('deferred', turn('A las diez de esta noche pausa la reproducción.', 'deferred', temporal='future')),
        ('deferred', turn('Si vuelvo del descanso, entonces cambia el volumen a veintidós por ciento.', 'deferred', temporal='conditional')),
        ('hypothetical', turn('En un caso imaginario, ¿qué propondrías si quisiera abrir Discord?', 'hypothetical')),
        ('hypothetical', turn('Supón por un momento que deseo subir el audio al noventa; es solo una hipótesis.', 'hypothetical')),
        ('ambiguity', turn('Por favor abre alguna aplicación, no he elegido cuál.', 'clarify')),
        ('ambiguity', turn('Cambia eso al valor que prefiero, aunque no te he dicho cuál.', 'clarify')),
        ('unsupported', turn('Necesito que inicies la calculadora de Windows.', 'unsupported')),
        ('unsupported', turn('Ajusta el brillo de la pantalla al cuarenta por ciento.', 'unsupported')),
    ]
    cases += [dict(id=f'consolidation-{i:02}', category=category, turns=[row]) for i,(category,row) in enumerate(independent,1)]
    known=set()
    def collect(obj):
        if isinstance(obj,dict):
            if isinstance(obj.get('text'),str): known.add(normalize(obj['text']))
            for value in obj.values(): collect(value)
        elif isinstance(obj,list):
            for value in obj: collect(value)
    for p in Path('docs').rglob('*.json'): collect(json.loads(p.read_text(encoding='utf-8-sig')))
    for p in Path('tests').glob('test_*.py'):
        for node in ast.walk(ast.parse(p.read_text(encoding='utf-8-sig'))):
            if isinstance(node,ast.Constant) and isinstance(node.value,str): known.add(normalize(node.value))
    fresh=[r for c in cases for r in c['turns'] if r.get('role')!='control_setup']
    assert len(fresh)==29 and len({normalize(r['text']) for r in fresh})==29
    assert not [r['text'] for r in fresh if normalize(r['text']) in known]
    data=dict(method='INTERNAL sealed pre-voice baseline, same author as code, no human independence claim. 32 total turns, 29 new text turns and 3 known direct setup controls. Gold never sent. No tuning during first exposure. Production candidate deadline 4 seconds selected before this run from prior p95 2.476 s plus margin.',
        frozen_engine_commit=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
        engine_sha256={p.as_posix():hashlib.sha256(p.read_bytes().replace(b'\r\n',b'\n')).hexdigest() for p in sorted(Path('jarvis/next').glob('*.py'))},
        configuration=dict(model='openai/gpt-oss-120b',reasoning_effort='medium',timeout=4.0,interval=20.0,max_turns=32),cases=cases)
    raw=(json.dumps(data,ensure_ascii=False,indent=2)+'\n').encode()
    path.write_bytes(raw);path.with_suffix('.sha256').write_bytes((hashlib.sha256(raw).hexdigest()+'\n').encode())
    print('Sealed 32 turns: 29 new, 3 known controls; 4-second candidate deadline')


if __name__=='__main__': main()
