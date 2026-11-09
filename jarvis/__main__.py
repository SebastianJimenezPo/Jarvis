import argparse
import json
import logging
import sys
from dataclasses import replace
from datetime import datetime
from pathlib import Path
from .core.config import Config, data_dir, load, save


def main():
    parser = argparse.ArgumentParser(description="JARVIS CORE — Fase 1")
    parser.add_argument("--debug", action="store_true")
    parser.add_argument("--data-dir", type=Path, default=data_dir())
    commands = parser.add_mutually_exclusive_group()
    commands.add_argument("--diagnostics", action="store_true")
    commands.add_argument("--list-devices", action="store_true")
    commands.add_argument("--select-device", metavar="NAME_OR_AUTO")
    commands.add_argument("--calibrate-wakeword", action="store_true")
    commands.add_argument("--reset-config", action="store_true")
    parser.add_argument("--samples", type=int, choices=range(5, 9), default=6)
    parser.add_argument("--exit-after", type=float, help="Cierre automático para pruebas, en segundos")
    args = parser.parse_args()
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
        logger.setLevel("DEBUG" if args.debug else config.log_level)
        if args.select_device:
            save(root, replace(config, device=args.select_device))
            print("Preferencia guardada; reinicia Jarvis para aplicarla.")
            return 0
        if args.diagnostics:
            from .interface.diagnostics import environment
            from .wakeword.rustpotter_adapter import engine_path
            print(json.dumps({**environment(), "engine_exists": engine_path().exists(),
                              "reference_exists": config.reference_path(root).exists(),
                              "config": str(root / "config.json")}, indent=2))
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
            logger.info("application_start version=0.1.0 phase=1")
            return run(LifecycleManager(config, root), root, args.exit_after)
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
