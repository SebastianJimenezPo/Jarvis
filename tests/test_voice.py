import json
import time
from dataclasses import replace
import numpy as np
import pytest
from jarvis.speech.settings import VoiceConfig,load_voice,save_voice
from jarvis.audio.turn_segmenter import SpeechTurnSegmenter
from jarvis.speech.recognition import TranscriptManager
from jarvis.dialogue.bridge import DialogueBridge,UserUtterance,strip_wake_prefix
from jarvis.speech.evaluation import error_counts


def test_voice_config_backward_compatibility(tmp_path):
    assert not load_voice(tmp_path).enabled
    config=replace(VoiceConfig(),enabled=True,engine='moonshine-tiny')
    save_voice(tmp_path,config)
    assert load_voice(tmp_path)==config


def test_corrupt_voice_configuration_preserves_core(tmp_path):
    from jarvis.core.voice_session import VoiceSessionManager
    (tmp_path/'voice.json').write_text('{broken',encoding='utf-8')
    manager=VoiceSessionManager(tmp_path,lambda event:None)
    assert not manager.available()
    assert 'núcleo Fase 1 conservado' in manager.error
    assert (tmp_path/'voice.json').read_text()=='{broken'


@pytest.mark.parametrize('field,value',[('vad_threshold',float('nan')),('volume',2),('speech_start_ms',0),
    ('engine','fictional'),('first_wait_seconds',0),('tts_enabled','yes'),('retain_seconds',-1)])
def test_voice_config_invalid(field,value):
    with pytest.raises(ValueError):
        replace(VoiceConfig(),**{field:value}).validate()


def test_segmenter_onset_pause_and_trailing_silence():
    seg=SpeechTurnSegmenter(VoiceConfig())
    frame=np.zeros(512,dtype=np.float32)
    for _ in range(6):
        audio,reason,started=seg.feed(frame,1)
        assert audio is None and not started
    audio,reason,started=seg.feed(frame,1)
    assert started and len(audio)==7*512
    for _ in range(10):
        assert seg.feed(frame,0)[1] is None
    assert seg.feed(frame,1)[1] is None
    for _ in range(20):
        assert seg.feed(frame,0)[1] is None
    assert seg.feed(frame,0)[1]=='silence'


def test_maximum_turn_even_continuous_noise():
    seg=SpeechTurnSegmenter(replace(VoiceConfig(),max_turn_seconds=1))
    reasons=[seg.feed(np.zeros(512,dtype=np.float32),1)[1] for _ in range(45)]
    assert 'max_duration' in reasons


def test_only_one_final_per_turn():
    events=[]
    manager=TranscriptManager('session','fake',events.append)
    manager.publish('turn','hola',False)
    manager.publish('turn','hola mundo',True)
    manager.publish('turn','duplicated',True)
    manager.publish('turn','stale partial',False)
    assert len(events)==2 and events[-1].final
    assert events[-1].session_id=='session'


@pytest.mark.parametrize('text,reply,end',[
    ('Jarvis, hola','Hola',False),('¿Me escuchas bien?','Sí, te escucho',False),
    ('Gracias, Jarvis','Con gusto',False),('Adiós','Hasta luego',True),
    ('Jarvis','',False),('Perfecto','Listo',False)])
def test_deterministic_dialogue(text,reply,end):
    result=DialogueBridge().respond(UserUtterance('s','t',text,'es',0))
    assert result.text==reply and result.end_session==end


def test_no_arbitrary_wake_word_removal_or_actions():
    assert strip_wake_prefix('Quiero llamar a Jarvis mañana')=='Quiero llamar a Jarvis mañana'
    result=DialogueBridge().respond(UserUtterance('s','t','abre Chrome','es',0))
    assert 'todavía no está habilitado' in result.text


def test_error_metrics():
    assert error_counts('Hola mundo','hola, mundo!')['word_errors']==0
    assert error_counts('abre Chrome','abre')['word_errors']==1
    assert error_counts('','inventado')['word_errors']==1


def test_real_voice_worker_silence_and_release(tmp_path):
    from jarvis.core.config import data_dir
    from jarvis.speech.models import registry
    from jarvis.core.voice_session import VoiceSessionManager
    root=data_dir()
    if not all(k in registry(root) for k in ('moonshine-tiny','silero')):
        pytest.skip('Explicit speech installation needed')
    events=[]
    config=replace(VoiceConfig(),enabled=True,engine='moonshine-tiny',tts_enabled=False,
                   first_wait_seconds=1,retain_seconds=0)
    manager=VoiceSessionManager(root,events.append,config)
    try:
        manager.start('smoke',bytes(32000))
        deadline=time.monotonic()+20
        while time.monotonic()<deadline:
            manager.poll()
            if any(e['kind'] in ('session_end','voice_error') for e in events):
                break
            manager.feed(bytes(640),time.monotonic())
            time.sleep(0.02)
        assert any(e['kind']=='stt_ready' for e in events),events
        assert any(e['kind']=='session_end' and e['reason']=='inactivity' for e in events),events
        assert not any(e['kind']=='voice_error' for e in events),events
        manager.poll()
        assert manager.process is None
    finally:
        manager.close()
