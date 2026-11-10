"""Heavy CPU voice work, isolated so idle model memory can really be released."""
import queue
import time
from dataclasses import asdict
from pathlib import Path


def voice_worker(inbox,outbox,cancel,root,config):
    import numpy as np
    from .recognition import make_engine,TranscriptManager
    from .piper_adapter import PiperAdapter
    from jarvis.audio.vad import SpeechActivityDetector
    from jarvis.audio.turn_segmenter import SpeechTurnSegmenter
    from jarvis.audio.playback import SpeechPlaybackManager
    from jarvis.dialogue.bridge import DialogueBridge,UserUtterance,strip_wake_prefix,activation_only_candidate
    root=Path(root)
    stt=vad=tts=None
    session_id=None
    turn_id=''
    def emit(kind,**fields):
        outbox.put({'kind':kind,'session_id':session_id,'turn_id':turn_id,'monotonic':time.monotonic(),**fields},timeout=2)
    def state(value):
        emit('voice_state',state=value)
    try:
        while True:
            command=inbox.get()
            if command[0]=='stop':
                return
            if command[0] not in ('session','test_tts'):
                continue
            session_id,preroll=command[1],command[2]
            acoustic_activation=bool(command[3]) if len(command)>3 else False
            turn_id=''
            try:
                load_start=time.monotonic()
                if command[0]=='test_tts':
                    if tts is None:
                        tts=PiperAdapter(root,config.voice,config.cpu_threads,config.volume)
                        tts.load()
                    state('SPEAKING')
                    SpeechPlaybackManager(config.output_device).play(tts.synthesize('Hola. El motor de voz de Jarvis está funcionando.'),cancel,emit)
                    time.sleep(config.echo_guard_seconds)
                    emit('session_end',reason='tts_test')
                    continue
                if stt is None:
                    stt=make_engine(root,config,lambda text: transcripts.publish(turn_id,text,False) if turn_id else None)
                    stt.load()
                    vad=SpeechActivityDetector(root)
                emit('stt_ready',load_seconds=time.monotonic()-load_start,engine=config.engine)
                transcripts=TranscriptManager(session_id,config.engine,lambda event:emit('transcript',**{
                    'text':event.text,'final':event.final,'engine':event.engine}))
                segmenter=SpeechTurnSegmenter(config)
                vad.reset()
                state('WAITING_FOR_SPEECH')
                deadline=time.monotonic()+config.first_wait_seconds
                session_deadline=time.monotonic()+config.max_session_seconds
                accept_after=0
                pending=np.frombuffer(preroll,dtype='<i2').astype(np.float32)/32768
                activation_sample=len(pending)
                processed_samples=0
                last_voiced_sample=0
                turn_start_sample=0
                turn=0
                end=False
                turn_started=None
                voice_end=None
                while not end:
                    if time.monotonic()>=session_deadline:
                        emit('session_end',reason='session_cap')
                        break
                    if cancel.is_set():
                        stt.cancel_turn()
                        emit('cancelled')
                        cancel.clear()
                        segmenter.reset();vad.reset();pending=np.zeros(0,dtype=np.float32)
                        accept_after=time.monotonic()+config.echo_guard_seconds
                        deadline=accept_after+config.followup_seconds
                        state('WAITING_FOR_FOLLOWUP')
                    if len(pending)<512:
                        try:
                            message=inbox.get(timeout=0.05)
                        except queue.Empty:
                            if not segmenter.active and time.monotonic()>=deadline:
                                emit('session_end',reason='inactivity')
                                break
                            continue
                        if message[0]=='stop':
                            return
                        if message[0]!='audio' or message[1]!=session_id or message[2]<accept_after:
                            continue
                        incoming=np.frombuffer(message[3],dtype='<i2').astype(np.float32)/32768
                        pending=np.concatenate([pending,incoming])
                    if len(pending)<512:
                        continue
                    frame,pending=pending[:512],pending[512:]
                    processed_samples+=len(frame)
                    probability=vad.probability(frame)
                    if probability>=config.vad_threshold:
                        last_voiced_sample=processed_samples
                    audio,reason,started=segmenter.feed(frame,probability)
                    if started:
                        turn_start_sample=processed_samples-len(audio)
                        turn+=1
                        turn_id=f'{session_id}:{turn}'
                        turn_started=time.monotonic()
                        emit('speech_started',vad_probability=probability)
                        state('LISTENING')
                        stt.start_turn(turn_id)
                    if audio is not None:
                        stt.feed_audio(audio)
                    if reason:
                        voice_end=time.monotonic()-segmenter.silent_ms/1000
                        emit('speech_ended',reason=reason,estimated_voice_end_monotonic=voice_end)
                        state('FINALIZING_TRANSCRIPT')
                        t0=time.monotonic()
                        text=strip_wake_prefix(stt.finish_turn())
                        transcripts.publish(turn_id,text,True)
                        emit('transcription_timing',finalize_seconds=time.monotonic()-t0,
                             voice_end_to_final_seconds=time.monotonic()-voice_end)
                        wake_audio_only=(acoustic_activation and turn==1 and
                            turn_start_sample<activation_sample and
                            last_voiced_sample<=activation_sample+config.activation_tail_ms*16)
                        emit('turn_audio_boundary',acoustic_activation=acoustic_activation,
                             activation_sample=activation_sample,turn_start_sample=turn_start_sample,
                             last_voiced_sample=last_voiced_sample,wake_audio_only=wake_audio_only)
                        if not config.diagnostic_echo and (wake_audio_only or activation_only_candidate(text,first_turn=turn==1)):
                            emit('activation_only_or_ambiguous',reason='wake_audio_boundary' if wake_audio_only else 'first_turn_isolated_token')
                            text=''
                        if text:
                            state('PROCESSING_RESPONSE')
                            t0=time.monotonic()
                            reply=DialogueBridge().respond(UserUtterance(session_id,turn_id,text,'es',time.monotonic()),config.diagnostic_echo)
                            emit('dialogue_timing',seconds=time.monotonic()-t0)
                            if config.tts_enabled and reply.text:
                                # Gate the mic before synthesis, including cold TTS load.
                                state('SPEAKING')
                                t0=time.monotonic()
                                if tts is None:
                                    tts=PiperAdapter(root,config.voice,config.cpu_threads,config.volume)
                                    tts.load()
                                emit('synthesis_started')
                                first=[True]
                                def chunks():
                                    for chunk in tts.synthesize(reply.text):
                                        if first[0]:
                                            emit('synthesis_first_chunk',seconds=time.monotonic()-t0)
                                            first[0]=False
                                        yield chunk
                                SpeechPlaybackManager(config.output_device).play(chunks(),cancel,emit)
                                emit('playback_ended',cancelled=cancel.is_set())
                                cancel.clear()
                            if reply.end_session:
                                time.sleep(config.echo_guard_seconds)
                                emit('session_end',reason='farewell')
                                end=True
                            emit('turn_completed',seconds=time.monotonic()-turn_started)
                        else:
                            emit('empty_transcript')
                        # Discard all audio captured during finalization and output, plus echo tail.
                        accept_after=time.monotonic()+config.echo_guard_seconds
                        pending=np.zeros(0,dtype=np.float32)
                        segmenter.reset();vad.reset()
                        if not end:
                            deadline=accept_after+(config.followup_seconds if text else config.first_wait_seconds)
                            state('WAITING_FOR_FOLLOWUP' if text else 'WAITING_FOR_SPEECH')
                    if not segmenter.active and time.monotonic()>=deadline and not end:
                        emit('session_end',reason='inactivity')
                        break
                if stt:
                    stt.cancel_turn()
            except Exception as exc:
                emit('voice_error',error=f'{type(exc).__name__}: {exc}')
                if stt:
                    stt.unload()
                stt=vad=tts=None
    finally:
        if stt:
            stt.unload()
        if tts:
            tts.unload()
