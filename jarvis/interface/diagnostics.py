import json
import os
import platform
import time
from datetime import datetime, timezone
import psutil
from jarvis import __version__


def environment():
    return {"version": __version__, "python": platform.python_version(), "windows": platform.platform(),
            "logical_cpus": psutil.cpu_count(), "ram_total_bytes": psutil.virtual_memory().total,
            "gpu_usage": None, "gpu_note": "No medido; el núcleo no carga modelos GPU"}


def write_report(root, snapshot):
    folder = root / "diagnostics"
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / "latest.json"
    path.write_text(json.dumps({"time_utc": datetime.now(timezone.utc).isoformat(),
                               **environment(), **snapshot}, indent=2, ensure_ascii=False), encoding="utf-8")
    return path


class ResourceSampler:
    def __init__(self):
        self.last = time.monotonic()
        self.previous = {}
        self.samples = []

    def sample(self):
        now = time.monotonic()
        parent = psutil.Process()
        current, rss = {}, 0
        for process in [parent, *parent.children(recursive=True)]:
            try:
                cpu = process.cpu_times()
                current[(process.pid, process.create_time())] = cpu.user + cpu.system
                rss += process.memory_info().rss
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        delta = sum(max(0, value - self.previous[key]) for key, value in current.items() if key in self.previous)
        percent = 100 * delta / (now - self.last) / (psutil.cpu_count() or 1) if self.previous else None
        self.previous, self.last = current, now
        item = {"cpu_machine_percent": percent, "rss_tree_bytes": rss, "processes": len(current)}
        self.samples.append(item)
        self.samples = self.samples[-720:]
        return item

    def report(self):
        values = [s["cpu_machine_percent"] for s in self.samples if s["cpu_machine_percent"] is not None]
        return {"samples": len(values), "cpu_mean_machine_percent": sum(values) / len(values) if values else None,
                "cpu_max_machine_percent": max(values) if values else None,
                "rss_tree_bytes": self.samples[-1]["rss_tree_bytes"] if self.samples else None,
                "rss_peak_sampled_bytes": max((s["rss_tree_bytes"] for s in self.samples), default=None),
                "method": "CPU delta(user+kernel), parent+children / wall seconds / logical CPUs; 5s sampling, last hour; RSS summed"}
