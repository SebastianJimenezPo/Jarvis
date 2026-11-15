import argparse
import json
import logging
import sys
from dataclasses import replace
from datetime import datetime
from pathlib import Path
from .core.config import Config, data_dir, load, save


def main():
    parser = argparse.ArgumentParser(description="JARVIS — Voice Engine")
    parser.add_argument("--debug", action="store_true")
    parser.add_argument("--data-dir", type=Path, default=data_dir())
    commands = parser.add_mutually_exclusive_group()
    commands.add_argument("--diagnostics", action="store_true")
    commands.add_argument("--list-devices", action="store_true")
    commands.add_argument("--select-device", metavar="NAME_OR_AUTO")
    commands.add_argument("--calibrate-wakeword", action="store_true")
    commands.add_argument("--reset-config", action="store_true")
    commands.add_argument("--enable-voice", action="store_true")
    commands.add_argument("--disable-voice", action="store_true")
    commands.add_argument("--set-stt", choices=['moonshine-small','moonshine-tiny','whisper-base','whisper-small'])
    commands.add_argument("--set-voice", choices=['es_MX-ald-medium','es_ES-davefx-medium'])
    commands.add_argument("--set-wake-threshold",type=float,metavar='0..1')
    commands.add_argument('--enable-intelligence',action='store_true')
    commands.add_argument('--disable-intelligence',action='store_true')
    commands.add_argument('--set-llm',choices=['qwen3.5:2b','qwen3:1.7b'])
    commands.add_argument('--set-semantic',choices=['minilm','e5-small'])
    parser.add_argument("--samples", type=int, choices=range(5, 9), default=6)
    parser.add_argument("--exit-after", type=float, help="Cierre automático para pruebas, en segundos")
    parser.add_argument('--profile',choices=['legacy','next'],default='legacy')
    parser.add_argument('--allow-remote',action='store_true')
    parser.add_argument('--free-tier',action='store_true')
    parser.add_argument('--next-reasoning',choices=['low','medium'],default='medium')
    parser.add_argument('--next-timeout',type=float,default=4.0)
    parser.add_argument('--next-stt',choices=['moonshine-small','moonshine-tiny','whisper-base','whisper-small'],help='Temporary Next STT override; does not save voice.json')
    args = parser.parse_args()
    if args.next_stt and args.profile!='next':parser.error('--next-stt requiere --profile next.')
    if (args.allow_remote or args.free_tier) and (args.profile!='next' or not (args.allow_remote and args.free_tier)):
        parser.error('Next remoto requiere --profile next --allow-remote --free-tier.')
    root = args.data_dir.resolve()
    root.mkdir(parents=True, exist_ok=True)
    from .core.logging import configure
    logger = configure(root, debug=args.debug)
    try:
        if args.reset_config:
            path = root / "config.json"
            if path.exists():
                path.replace(root / f"config.backup-{datetime.now():%Y%m%d-%H%M%S-%f}.json")
            save(root, Config())
            print("Configuración restaurada; se conservó el archivo anterior.")
            return 0
        config = load(root)
        selected_voice=None
        if args.profile=='next':
            from .speech.settings import load_voice
            selected_voice=replace(load_voice(root),enabled=True,dialogue_profile='next',next_remote=args.allow_remote,
                next_reasoning=args.next_reasoning,next_timeout_seconds=args.next_timeout).validate()
            if args.next_stt:selected_voice=replace(selected_voice,engine=args.next_stt).validate()
        logger.setLevel("DEBUG" if args.debug else config.log_level)
        if args.enable_intelligence or args.disable_intelligence or args.set_llm or args.set_semantic:
            from .intelligence.settings import load_intelligence,save_intelligence
            intelligence=load_intelligence(root)
            changes=({'enabled':True} if args.enable_intelligence else {'enabled':False} if args.disable_intelligence else
                     {'model':args.set_llm} if args.set_llm else {'semantic_model':args.set_semantic})
            save_intelligence(root,replace(intelligence,**changes))
            print('Configuración de inteligencia guardada. Reinicia Jarvis para aplicarla.')
            return 0
        if args.set_wake_threshold is not None:
            save(root,replace(config,threshold=args.set_wake_threshold))
            print('Umbral guardado. Reinicia Jarvis para aplicarlo; un valor mayor reduce sensibilidad.')
            return 0
        if args.enable_voice or args.disable_voice or args.set_stt or args.set_voice:
            from .speech.settings import load_voice,save_voice
            voice=load_voice(root)
            changes=({'enabled':True} if args.enable_voice else {'enabled':False} if args.disable_voice
                     else {'engine':args.set_stt} if args.set_stt else {'voice':args.set_voice})
            save_voice(root,replace(voice,**changes))
            print('Configuración de voz guardada. Reinicia Jarvis para aplicarla.')
            return 0
        if args.select_device:
            save(root, replace(config, device=args.select_device))
            print("Preferencia guardada; reinicia Jarvis para aplicarla.")
            return 0
        if args.diagnostics:
            from .interface.diagnostics import environment
            from .wakeword.rustpotter_adapter import engine_path
            from .speech.settings import load_voice
            from .speech.models import registry
            from dataclasses import asdict
            if args.profile!='next':
                from .intelligence.settings import load_intelligence
            print(json.dumps({**environment(), "engine_exists": engine_path().exists(),
                              "reference_exists": config.reference_path(root).exists(),
                              "config": str(root / "config.json"), "voice":asdict(selected_voice or load_voice(root)),
                              "installed_models":list(registry(root)),
                              "intelligence":asdict(load_intelligence(root)) if args.profile!='next' else None,
                              'profile':args.profile}, indent=2))
            return 0
        from .core.single_instance import SingleInstance
        with SingleInstance():
            if args.list_devices:
                from .audio.capture import devices
                print(json.dumps(devices(), indent=2, ensure_ascii=False))
                return 0
            if args.calibrate_wakeword:
                from .wakeword.calibration import calibrate
                calibrate(config, root, args.samples)
                return 0
            from .core.lifecycle import LifecycleManager
            from .interface.tray import run
            try:
                if args.profile!='next':
                    from .intelligence.settings import load_intelligence
                if args.profile!='next' and load_intelligence(root).enabled:
                    from .intelligence.service import ensure_service
                    logger.info('ollama_service_'+ensure_service())
            except Exception:
                logger.exception('intelligence_service_unavailable_voice_core_preserved')
            logger.info('application_start profile='+args.profile)
            return run(LifecycleManager(config, root,voice_config=selected_voice), root, args.exit_after)
    except Exception as exc:
        logger.exception("application_failed")
        message = f"{exc}\nRegistros: {root / 'logs'}\nConfiguración dañada: usa --reset-config para reparar."
        if sys.stderr is not None:
            print(message, file=sys.stderr)
        else:
            import ctypes
            ctypes.windll.user32.MessageBoxW(None, message, "Jarvis — Error de inicio", 0x10)
        return 1
    finally:
        logging.shutdown()


if __name__ == "__main__":
    raise SystemExit(main())
