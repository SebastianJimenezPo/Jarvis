"""Manual resource profiles. Preserves audio devices, wake threshold, VAD and privacy."""
import argparse
import sys
from pathlib import Path
from dataclasses import replace
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))

PROFILES={'gaming':{'threads':2,'llm_keep':30,'voice_keep':20.0},
          'balanced':{'threads':3,'llm_keep':60,'voice_keep':30.0},
          'saving':{'threads':2,'llm_keep':0,'voice_keep':0.0}}


def apply_profile(root,name):
    from jarvis.intelligence.settings import load_intelligence,save_intelligence
    from jarvis.speech.settings import load_voice,save_voice
    chosen=PROFILES[name]
    intelligence=replace(load_intelligence(root),cpu_threads=chosen['threads'],keep_alive_seconds=chosen['llm_keep']).validate()
    voice=replace(load_voice(root),cpu_threads=2,retain_seconds=chosen['voice_keep']).validate()
    save_intelligence(root,intelligence);save_voice(root,voice)


def main():
    from jarvis.core.config import data_dir
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('profile',choices=PROFILES)
    args=parser.parse_args();apply_profile(data_dir(),args.profile)
    print('Perfil guardado:',args.profile,'. Reinicia Jarvis para aplicarlo. No hay detección automática de juegos.')


if __name__=='__main__':main()
