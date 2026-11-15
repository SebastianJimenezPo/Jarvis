"""Seal a one-shot internal semantic contrast evaluation after stage 3."""
import ast
import hashlib
import json
from pathlib import Path
import subprocess
from scripts.build_next_reserved import action, turn, normalize


def main():
    path = Path('docs/evaluation/next_reserved_v2.json')
    if path.exists():
        raise ValueError('Never overwrite reserved data')
    baseline = 'a722c7bf0a21cebac23078a71786616abb14d4e8'
    subprocess.run(['git', 'diff', '--exit-code', baseline, '--', 'jarvis/next'], check=True, capture_output=True)
    chrome = action('applications.open', 'chrome')
    spotify = action('applications.open', 'spotify')
    steam = action('applications.open', 'steam')
    pause = action('media.pause', 'music_player')
    specs = [
        ('negation', turn('Por favor, no inicies Discord aunque esté cerrado.', 'negated')),
        ('negation', turn('Bajo ningún concepto abras Spotify ahora.', 'negated')),
        ('negation', turn('De ninguna manera quiero que pauses la reproducción.', 'negated')),
        ('negation', turn('No quiero que el equipo quede silenciado.', 'negated')),
        ('quotation', turn('La documentación usa «silencia el audio» como ejemplo de una orden.', 'conversation')),
        ('quotation', turn('Acabo de oír a alguien pedir que se inicie Chrome; solo te lo cuento.', 'conversation')),
        ('quotation', turn('El mensaje que estoy copiando dice: “Pausa la música”.', 'conversation')),
        ('deferred', turn('Dentro de un rato quiero que abras Discord, ahora déjalo como está.', 'deferred', temporal='future')),
        ('deferred', turn('Al acabar la instalación, deja el volumen del sistema al 37%.', 'deferred', temporal='conditional')),
        ('deferred', turn('Si termino la reunión, entonces inicia Spotify.', 'deferred', temporal='conditional')),
        ('hypothetical', turn('Supongamos que quisiera silenciar Windows: ¿qué acción propondrías?', 'hypothetical')),
        ('hypothetical', turn('Imaginemos por un instante que te pido iniciar Steam; es un supuesto.', 'hypothetical')),
        ('positive', turn('Hazme el favor de iniciar Chrome en este momento.', 'create_plan', [chrome], actions=[chrome])),
        ('positive', turn('Necesito que inicies la aplicación «Spotify» ahora mismo.', 'create_plan', [spotify], actions=[spotify])),
        ('positive', turn('No abras Discord; lo que sí quiero es que abras Steam ahora.', 'create_plan', [steam], actions=[steam])),
        ('positive', turn('Antes pausaba la reproducción yo; esta vez páusala tú ahora.', 'create_plan', [pause], actions=[pause])),
    ]
    # Exact overlap exclusion is mechanical; semantic proximity and author bias remain.
    known = set()
    def collect(value):
        if isinstance(value, dict):
            if isinstance(value.get('text'), str):
                known.add(normalize(value['text']))
            for child in value.values(): collect(child)
        elif isinstance(value, list):
            for child in value: collect(child)
    for folder in ('docs/evaluation', 'docs/reports'):
        for source in Path(folder).glob('*.json'):
            collect(json.loads(source.read_text(encoding='utf-8-sig')))
    for source in Path('tests').glob('test_next*.py'):
        for node in ast.walk(ast.parse(source.read_text(encoding='utf-8-sig'))):
            if isinstance(node, ast.Constant) and isinstance(node.value, str): known.add(normalize(node.value))
    texts = [normalize(row['text']) for _, row in specs]
    assert len(texts) == len(set(texts)) and not set(texts) & known
    cases = [dict(id=f'semantic-v2-{i:02}', category=category, turns=[row])
             for i, (category, row) in enumerate(specs, 1)]
    data = dict(method='INTERNAL first exposure after stage-3 freeze, same author as implementation. Exact known text duplicates excluded, semantic near-duplicates possible. 12 non-action cases and 4 positive contrasts. No generalization or v1 score-comparison claim. Gold never sent to provider.',
        frozen_engine_commit=baseline, engine_hash_mode='utf8_lf',
        engine_sha256={p.as_posix():hashlib.sha256(p.read_bytes().replace(b'\r\n', b'\n')).hexdigest()
                       for p in sorted(Path('jarvis/next').glob('*.py'))},
        configuration=dict(model='openai/gpt-oss-120b', reasoning_effort='low', timeout=8.0, interval=20.0, max_turns=16),
        acceptance_criteria=dict(non_action_drafts=0, unreviewed_results=0, physical_executions=0,
            positive_plan_matches=4, taxonomy='Report exact operations separately; a safe abstention is not a classification success.'),
        cases=cases)
    raw = (json.dumps(data, ensure_ascii=False, indent=2)+'\n').encode('utf-8')
    path.write_bytes(raw)
    path.with_suffix('.sha256').write_text(hashlib.sha256(raw).hexdigest()+'\n', encoding='ascii')
    print('Sealed 16 new internal cases; runtime unchanged')


if __name__ == '__main__':
    main()
