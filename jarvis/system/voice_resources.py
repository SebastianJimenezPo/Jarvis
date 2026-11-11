"""Limit only the heavy voice subprocess; the microphone owner stays unrestricted."""
import os
import psutil


def configure_voice_process(cpu_threads):
    process=psutil.Process()
    if os.name!='nt':return
    # Moonshine's native binding has no thread setting in our adapter. Affinity
    # bounds the entire worker, including native pools, before models are loaded.
    allowed=process.cpu_affinity()
    process.cpu_affinity(allowed[:max(1,min(cpu_threads,len(allowed)))])
    process.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
