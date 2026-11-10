"""Explicit short hardware benchmark. Synthetic reference, real mic, no saved mic audio."""
import argparse
import json
import sys
import tempfile
import subprocess
import wave
import time
from dataclasses import replace
from pathlib import Path
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from jarvis.core.config import Config, save
from jarvis.wakeword.rustpotter_adapter import engine_path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seconds", type=int, default=60)
    parser.add_argument("--output", type=Path, default=Path("build/performance.json"))
    parser.add_argument("--voice-enabled", action="store_true")
    parser.add_argument("--intelligence-enabled", action="store_true")
    args = parser.parse_args()
    def ollama_snapshot():
        import psutil
        from jarvis.intelligence.ollama_client import OllamaClient
        from jarvis.intelligence.settings import IntelligenceConfig
        processes=[]
        for process in psutil.process_iter(['pid','name']):
            if (process.info['name'] or '').casefold().startswith('ollama'):
                try:
                    cpu=process.cpu_times()
                    processes.append({'pid':process.pid,'rss_bytes':process.memory_info().rss,'cpu_seconds':cpu.user+cpu.system})
                except (psutil.NoSuchProcess,psutil.AccessDenied):pass
        return {'models':OllamaClient(IntelligenceConfig()).running(),'processes':processes}
    with tempfile.TemporaryDirectory(prefix="jarvis benchmark ") as folder:
        root = Path(folder)
        samples = []
        t = np.arange(12000) / 16000
        tone = (np.sin(2 * np.pi * (280 * t + 800 * t ** 2)) * np.sin(np.pi * t / 0.75) * 12000).astype("<i2")
        for i in range(6):
            path = root / f"synthetic-{i}.wav"
            with wave.open(str(path), "wb") as out:
                out.setnchannels(1)
                out.setsampwidth(2)
                out.setframerate(16000)
                out.writeframes(tone.tobytes())
            samples.append(str(path))
        reference = root / "synthetic.rpw"
        subprocess.run([str(engine_path()), "calibrate", str(reference), *samples], check=True,
                       capture_output=True, timeout=60, creationflags=subprocess.CREATE_NO_WINDOW)
        save(root, replace(Config(), reference=str(reference), confirmation=False))
        if args.voice_enabled:
            from jarvis.core.config import data_dir
            from jarvis.speech.settings import VoiceConfig,save_voice
            from jarvis.speech.models import registry
            entries=registry(data_dir())
            for entry in entries.values():
                entry['path']=str(data_dir()/'models'/entry['path'])
                entry['sha256']={str(data_dir()/'models'/name):value for name,value in entry['sha256'].items()}
            (root/'models').mkdir()
            (root/'models'/'registry.json').write_text(json.dumps(entries),encoding='utf-8')
            save_voice(root,replace(VoiceConfig(),enabled=True))
        if args.intelligence_enabled:
            from jarvis.intelligence.settings import IntelligenceConfig,save_intelligence
            save_intelligence(root,replace(IntelligenceConfig(),enabled=True))
        external_before=ollama_snapshot() if args.intelligence_enabled else None
        started=time.monotonic()
        completed = subprocess.run([sys.executable, "-m", "jarvis", "--data-dir", str(root),
                                    "--exit-after", str(args.seconds)], timeout=args.seconds + 40,
                                   creationflags=subprocess.CREATE_NO_WINDOW)
        if completed.returncode:
            raise RuntimeError("Benchmark failed")
        report = json.loads((root / "diagnostics" / "latest.json").read_text(encoding="utf-8"))
        report["scenario"] = "Real microphone, synthetic chirp reference (not Jarvis), actual Qt tray + Rustpotter. No microphone audio saved."
        report["requested_seconds"] = args.seconds
        if args.intelligence_enabled:
            import psutil
            external_after=ollama_snapshot()
            before={p['pid']:p['cpu_seconds'] for p in external_before['processes']}
            delta=sum(max(0,p['cpu_seconds']-before[p['pid']]) for p in external_after['processes'] if p['pid'] in before)
            report['external_ollama']={'before':external_before,'after':external_after,
                'cpu_machine_percent':100*delta/(time.monotonic()-started)/(psutil.cpu_count() or 1),
                'note':'External shared service, excluded from parent+children resource sampler; CPU delta only for PIDs surviving the interval.'}
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
        print(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
