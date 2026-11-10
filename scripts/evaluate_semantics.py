"""Calibrate on development utterances only; report held-out and polarity stress separately."""
import json
import sys
import time
from dataclasses import replace
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))

DATA={
 'decrease_volume':(['Ese volumen está muy alto','La música está re fuerte','Bájale que está durísimo','El sonido me está dejando sordo'],
                    ['Me estás dejando sordo con ese volumen','El audio está muy duro para mí']),
 'increase_volume':(['Se escucha demasiado bajito','Súbele algo al sonido','La música casi no se escucha','Necesito más volumen'],
                    ['No se oye casi nada de música','Ese audio está demasiado bajo']),
 'set_light_brightness':(['La iluminación me molesta en los ojos','Pon más tenue la luz','Que no alumbre tan fuerte','Esa luz está demasiado brillante'],
                         ['Me encandila la luz del escritorio','Quiero el brillo de la luz más suave']),
 'pause_music':(['Para un momento la canción','Interrumpe la música un ratito','Detén lo que está sonando','Pausa esa canción'],
                ['Dale pausa a la canción','Que no siga sonando la música un momento']),
 'turn_off_light':(['Quiero que quede oscuro','Deja de iluminar el cuarto','Quita la iluminación','Apaga todas las luces'],
                   ['Deja el cuarto a oscuras','Quiero la habitación sin iluminación']),
 'turn_on_light':(['Quiero que se ilumine el cuarto','Enciende las luces del cuarto','Dale luz a esta habitación','Prende todas las luces'],
                  ['Alumbra este cuarto','Necesito luz para ver en la habitación'])}
NEGATIVE=['Quiero tomar café','Mi hermano estudia medicina','Abre Steam','Gracias por ayudarme','¿Qué es una variable?',
          'Cierra Chrome','Estoy hablando con mi amigo','Busca una canción de Queen','Mañana voy a estudiar','Prefiero el color verde']
STRESS=['No bajes el volumen','No apagues las luces','Cuando termine de jugar apaga las luces','¿Qué pasaría si subiera el volumen?',
        'Ayer bajé el volumen','No quiero que cierres Chrome']


def main():
    import argparse,subprocess
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--model',choices=['minilm','e5-small'])
    p.add_argument('--output',type=Path,default=Path('docs/reports/semantic-comparison.json'))
    args=p.parse_args()
    if args.model is None:
        reports=[]
        for name in ('minilm','e5-small'):
            output=args.output.with_name('semantic-'+name+'.json')
            subprocess.run([sys.executable,__file__,'--model',name,'--output',str(output)],check=True,
                            creationflags=subprocess.CREATE_NO_WINDOW,timeout=180)
            reports.extend(json.loads(output.read_text(encoding='utf-8')))
        args.output.write_text(json.dumps(reports,indent=2,ensure_ascii=False),encoding='utf-8')
        return
    import numpy as np
    import psutil
    from jarvis.core.config import data_dir
    from jarvis.intelligence.settings import IntelligenceConfig
    from jarvis.intelligence.semantic import SemanticRouter
    reports=[]
    for name in (args.model,):
        router=SemanticRouter(data_dir(),replace(IntelligenceConfig(),semantic_model=name))
        t=time.perf_counter();router.load();load=time.perf_counter()-t
        rows=[]
        for label,(dev,test) in DATA.items():
            for split,phrases in [('development',dev),('heldout',test)]:
                for text in phrases:
                    t=time.perf_counter();ranked=router.rank(text)
                    rows.append({'text':text,'expected':label,'split':split,'top':ranked[0][0],
                                 'score':ranked[0][1],'margin':ranked[0][1]-ranked[1][1],'seconds':time.perf_counter()-t})
        for index,text in enumerate(NEGATIVE):
            ranked=router.rank(text);rows.append({'text':text,'expected':None,'split':'development' if index%2==0 else 'heldout',
                'top':ranked[0][0],'score':ranked[0][1],'margin':ranked[0][1]-ranked[1][1],'seconds':None})
        thresholds={}
        for label in DATA:
            candidates=[]
            for score in np.arange(0.4,0.99,0.01):
                for margin in (0,0.02,0.04,0.06,0.08,0.1):
                    selected=[r for r in rows if r['split']=='development' and r['top']==label and r['score']>=score and r['margin']>=margin]
                    if selected and all(r['expected']==label for r in selected):
                        candidates.append((len(selected),-float(score),-margin))
            if candidates:
                count,score,margin=max(candidates);thresholds[label]={'score':-score,'margin':-margin,'development_hits':count}
        calibration={'model':name,'source':'development only; no heldout or negation tuning','intents':thresholds}
        (data_dir()/'intelligence_models'/f'calibration-{name}.json').write_text(json.dumps(calibration,indent=2),encoding='utf-8')
        for row in rows:
            threshold=thresholds.get(row['top']);row['accepted']=bool(threshold and row['score']>=threshold['score'] and row['margin']>=threshold['margin'])
        stress=[]
        from jarvis.intelligence.language import clause_kind,normalize
        for text in STRESS:
            stress.append({'text':text,'raw_top':router.rank(text)[0],'guard':clause_kind(normalize(text)),'authorized':False})
        heldout=[r for r in rows if r['split']=='heldout']
        reports.append({'model':name,'load_seconds':load,'rss_process_bytes':psutil.Process().memory_info().rss,
            'heldout_correct_top':sum(r['top']==r['expected'] for r in heldout if r['expected']),
            'heldout_positive_count':sum(r['expected'] is not None for r in heldout),
            'heldout_accepted':sum(r['accepted'] for r in heldout),
            'heldout_wrong_acceptances':sum(r['accepted'] and r['top']!=r['expected'] for r in heldout),
            'calibration':calibration,'rows':rows,'polarity_stress':stress})
        router.provider.unload();print(name,'done',flush=True)
    args.output.write_text(json.dumps(reports,indent=2,ensure_ascii=False),encoding='utf-8')


if __name__=='__main__':main()
