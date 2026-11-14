"""Process environment or the current user's Windows Credential Manager.

No key files, shell arguments, transcript logging or automatic network access.
"""
import os

TARGET = 'JarvisNext/Groq'


def _windows_api():
    import ctypes
    from ctypes import wintypes
    class Credential(ctypes.Structure):
        _fields_ = [('Flags', wintypes.DWORD), ('Type', wintypes.DWORD), ('TargetName', wintypes.LPWSTR),
            ('Comment', wintypes.LPWSTR), ('LastWritten', wintypes.FILETIME),
            ('CredentialBlobSize', wintypes.DWORD), ('CredentialBlob', ctypes.POINTER(ctypes.c_ubyte)),
            ('Persist', wintypes.DWORD), ('AttributeCount', wintypes.DWORD), ('Attributes', ctypes.c_void_p),
            ('TargetAlias', wintypes.LPWSTR), ('UserName', wintypes.LPWSTR)]
    api = ctypes.WinDLL('Advapi32.dll', use_last_error=True)
    pointer = ctypes.POINTER(Credential)
    api.CredReadW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD, ctypes.POINTER(pointer)]
    api.CredReadW.restype = wintypes.BOOL
    api.CredWriteW.argtypes = [pointer, wintypes.DWORD]
    api.CredWriteW.restype = wintypes.BOOL
    api.CredFree.argtypes = [ctypes.c_void_p]
    api.CredFree.restype = None
    return ctypes, Credential, api


def read_windows_key():
    if os.name != 'nt':
        return None
    ctypes, Credential, api = _windows_api()
    pointer = ctypes.POINTER(Credential)()
    if not api.CredReadW(TARGET, 1, 0, ctypes.byref(pointer)):
        return None
    try:
        item = pointer.contents
        if not 1 <= item.CredentialBlobSize <= 256:
            return None
        return ctypes.string_at(item.CredentialBlob, item.CredentialBlobSize).decode('utf-8')
    finally:
        api.CredFree(pointer)


def read_groq_key():
    value = os.environ.get('GROQ_API_KEY')
    if value:
        return value
    try:
        return read_windows_key()
    except Exception:
        return None


def store_groq_key(value):
    if os.name != 'nt' or not isinstance(value, str) or not value.startswith('gsk_') or not 8 <= len(value) <= 256 or any(c.isspace() for c in value):
        raise ValueError('Invalid credential or unsupported credential store')
    ctypes, Credential, api = _windows_api()
    raw = value.encode('utf-8')
    buffer = ctypes.create_string_buffer(raw)
    item = Credential(Type=1, TargetName=TARGET, UserName='JarvisNext', Persist=2,
        CredentialBlobSize=len(raw), CredentialBlob=ctypes.cast(buffer, ctypes.POINTER(ctypes.c_ubyte)))
    try:
        if not api.CredWriteW(ctypes.byref(item), 0):
            raise RuntimeError('Credential store unavailable')
    finally:
        ctypes.memset(buffer, 0, len(raw))
