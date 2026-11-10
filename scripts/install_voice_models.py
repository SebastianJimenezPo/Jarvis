"""Explicit speech-model installation. Never called by resident."""
import argparse
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from jarvis.core.config import data_dir
from jarvis.speech.models import install

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('models',nargs='+',choices=['moonshine-small','moonshine-tiny','whisper-base','whisper-small','silero','es_MX-ald-medium','es_ES-davefx-medium'])
    p.add_argument('--data-dir',type=Path,default=data_dir())
    args=p.parse_args()
    install(args.data_dir,args.models)
