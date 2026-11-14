"""External Ollama tree sampler shared by explicit benchmarks, never resident polling."""
import threading
import time
import psutil


def ollama_tree():
    selected={}
    for p in psutil.process_iter(['pid','name']):
        if (p.info['name'] or '').lower().startswith('ollama'):
            selected[p.pid]=p
            try:selected.update({child.pid:child for child in p.children(recursive=True)})
            except (psutil.NoSuchProcess,psutil.AccessDenied):pass
    rows={}
    for pid,p in selected.items():
        try:
            cpu=p.cpu_times();rows[pid]={'cpu':cpu.user+cpu.system,'rss':p.memory_info().rss}
        except (psutil.NoSuchProcess,psutil.AccessDenied):pass
    return rows


class OllamaMeasurement:
    def __enter__(self):
        self.before=ollama_tree();self.previous=self.before;self.started=time.perf_counter();self.last=self.started
        self.peak_cpu=0;self.peak_rss=sum(row['rss'] for row in self.before.values());self.stop=threading.Event()
        self.thread=threading.Thread(target=self._sample,daemon=True);self.thread.start();return self
    def _sample(self):
        while not self.stop.wait(.1):
            rows=ollama_tree();now=time.perf_counter()
            delta=sum(max(0,row['cpu']-self.previous.get(pid,row)['cpu']) for pid,row in rows.items())
            self.peak_cpu=max(self.peak_cpu,100*delta/max(now-self.last,.001)/(psutil.cpu_count() or 1))
            self.peak_rss=max(self.peak_rss,sum(row['rss'] for row in rows.values()))
            self.previous=rows;self.last=now
    def __exit__(self,*args):
        after=ollama_tree();elapsed=time.perf_counter()-self.started;self.stop.set();self.thread.join()
        delta=sum(max(0,row['cpu']-self.before.get(pid,{'cpu':0})['cpu']) for pid,row in after.items())
        self.report={'elapsed_seconds':elapsed,'cpu_machine_mean_percent':100*delta/elapsed/(psutil.cpu_count() or 1),
            'cpu_machine_peak_sampled_percent':self.peak_cpu,'rss_peak_sampled_bytes':max(self.peak_rss,sum(row['rss'] for row in after.values()))}
