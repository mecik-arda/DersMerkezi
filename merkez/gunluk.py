import ctypes
import sys
from ctypes import wintypes
from datetime import datetime
from pathlib import Path

KOK = Path(__file__).resolve().parent.parent
LOG_YOLU = KOK / "gunluk.log"
MUTEX_ADI = "Local\\DersMerkezi"
UST_LOG_BAYT = 1024 * 1024

SESSIZ = False

_kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
_kernel32.CreateMutexW.restype = wintypes.HANDLE
_kernel32.CreateMutexW.argtypes = [wintypes.LPVOID, wintypes.BOOL, wintypes.LPCWSTR]
_kernel32.WaitForSingleObject.restype = wintypes.DWORD
_kernel32.WaitForSingleObject.argtypes = [wintypes.HANDLE, wintypes.DWORD]
_kernel32.ReleaseMutex.restype = wintypes.BOOL
_kernel32.ReleaseMutex.argtypes = [wintypes.HANDLE]
_kernel32.CloseHandle.restype = wintypes.BOOL
_kernel32.CloseHandle.argtypes = [wintypes.HANDLE]

_WAIT_OBJECT_0 = 0
_WAIT_ABANDONED = 0x80


class Kilit:
    def __init__(self, ad=MUTEX_ADI):
        self.ad = ad
        self.tutamac = None
        self.sahip = False

    def al(self, bekle_ms=0):
        self.tutamac = _kernel32.CreateMutexW(None, False, self.ad)
        if not self.tutamac:
            return False
        sonuc = _kernel32.WaitForSingleObject(self.tutamac, bekle_ms)
        if sonuc in (_WAIT_OBJECT_0, _WAIT_ABANDONED):
            self.sahip = True
            return True
        _kernel32.CloseHandle(self.tutamac)
        self.tutamac = None
        return False

    def birak(self):
        if self.tutamac:
            if self.sahip:
                _kernel32.ReleaseMutex(self.tutamac)
            _kernel32.CloseHandle(self.tutamac)
        self.tutamac = None
        self.sahip = False

    def __enter__(self):
        if not self.sahip and not self.al():
            raise RuntimeError("Kilit alınamadı")
        return self

    def __exit__(self, *args):
        self.birak()
        return False


def kilitle(bekle_ms=30000):
    kilit = Kilit()
    if not kilit.al(bekle_ms):
        raise RuntimeError("Başka bir çalışma sürüyor; kayıt yapılamadı")
    return kilit


def _rotasyon():
    try:
        if LOG_YOLU.exists() and LOG_YOLU.stat().st_size > UST_LOG_BAYT:
            eski = LOG_YOLU.with_name(LOG_YOLU.name + ".old")
            if eski.exists():
                eski.unlink()
            LOG_YOLU.replace(eski)
    except OSError:
        pass


def kayit(seviye, mesaj):
    satir = "[{}] [{}] {}".format(datetime.now().strftime("%Y-%m-%d %H:%M:%S"), seviye, mesaj)
    kilit = Kilit()
    alindi = kilit.al(10000)
    try:
        if alindi:
            try:
                _rotasyon()
                with open(LOG_YOLU, "a", encoding="utf-8", newline="\n") as dosya:
                    dosya.write(satir + "\n")
            except OSError:
                pass
    finally:
        kilit.birak()
    if not SESSIZ and sys.stdout is not None:
        try:
            print(satir)
        except Exception:
            pass
