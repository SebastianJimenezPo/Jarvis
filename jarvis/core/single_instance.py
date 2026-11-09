import ctypes
import hashlib
import os
from ctypes import wintypes


class SingleInstance:
    """Session-local, user-scoped mutex held for the complete audio-owning lifetime."""
    def __init__(self, namespace="JarvisCore"):
        self.namespace = namespace

    def __enter__(self):
        if os.name != "nt":
            raise RuntimeError("Jarvis Core requiere Windows")
        self.api = ctypes.WinDLL("kernel32", use_last_error=True)
        self.api.CreateMutexW.argtypes = (ctypes.c_void_p, wintypes.BOOL, wintypes.LPCWSTR)
        self.api.CreateMutexW.restype = wintypes.HANDLE
        self.api.CloseHandle.argtypes = (wintypes.HANDLE,)
        user = hashlib.sha256(os.environ["USERPROFILE"].casefold().encode()).hexdigest()[:24]
        self.handle = self.api.CreateMutexW(None, False, "Local\\" + self.namespace + "-" + user)
        error = ctypes.get_last_error()
        if not self.handle:
            raise ctypes.WinError(error)
        if error == 183:
            self.api.CloseHandle(self.handle)
            self.handle = None
            raise RuntimeError("Jarvis ya está ejecutándose; ciérralo desde la bandeja antes de calibrar")
        return self

    def __exit__(self, *_):
        if self.handle:
            self.api.CloseHandle(self.handle)
            self.handle = None
