import ctypes
import os
import stat as stat_modulu
import sys
from ctypes import wintypes
from datetime import datetime
from pathlib import Path

KOK = Path(__file__).resolve().parent.parent
VARSAYILAN_LOG = KOK / "gunluk.log"
LOG_YOLU = VARSAYILAN_LOG
MUTEX_ADI = "Local\\DersMerkezi"
UST_LOG_BAYT = 1024 * 1024

SESSIZ = False
KONSOL_AKISI = "stdout"

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
_FILE_ATTRIBUTE_REPARSE_POINT = getattr(stat_modulu, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)


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


def kilit_dolu():
    kilit = Kilit()
    if kilit.al(0):
        kilit.birak()
        return False
    return True


def log_yolu_dogrula(yol):
    aday = Path(yol)
    if not aday.is_absolute():
        aday = KOK / aday
    kok = Path(os.path.realpath(KOK))
    gercek = Path(os.path.realpath(aday))
    if gercek != kok and kok not in gercek.parents:
        raise ValueError("Günlük yolu proje kökü dışında olamaz: {}".format(aday))
    if gercek.exists() and gercek.is_dir():
        raise ValueError("Günlük yolu mevcut bir dizin olamaz: {}".format(aday))
    try:
        bilgi = aday.lstat()
    except OSError:
        bilgi = None
    if bilgi is not None and getattr(bilgi, "st_file_attributes", 0) & _FILE_ATTRIBUTE_REPARSE_POINT:
        raise ValueError("Günlük yolu yeniden ayrıştırma noktası olamaz: {}".format(aday))
    return gercek


def log_yolu_ayarla(yol):
    global LOG_YOLU
    hedef = log_yolu_dogrula(yol)
    hedef.parent.mkdir(parents=True, exist_ok=True)
    gercek = Path(os.path.realpath(hedef))
    kok = Path(os.path.realpath(KOK))
    if gercek != kok and kok not in gercek.parents:
        raise ValueError("Günlük yolu proje kökü dışında olamaz: {}".format(yol))
    with open(gercek, "a", encoding="utf-8"):
        pass
    LOG_YOLU = gercek
    return gercek


def _hedef_dogrula():
    gercek = log_yolu_dogrula(LOG_YOLU)
    if gercek != LOG_YOLU:
        raise ValueError("Günlük yolu denetim sırasında değişti: {}".format(LOG_YOLU))


def _rotasyon():
    try:
        if LOG_YOLU.exists() and LOG_YOLU.stat().st_size > UST_LOG_BAYT:
            eski = LOG_YOLU.with_name(LOG_YOLU.name + ".old")
            if eski.exists():
                eski.unlink()
            LOG_YOLU.replace(eski)
    except OSError:
        if LOG_YOLU != VARSAYILAN_LOG:
            raise


def son_satir():
    try:
        with open(LOG_YOLU, "r", encoding="utf-8", errors="replace") as dosya:
            satirlar = [satir.strip() for satir in dosya if satir.strip()]
        return satirlar[-1] if satirlar else ""
    except OSError:
        return ""


def _konsol(satir):
    if SESSIZ:
        return
    akis = {"stdout": sys.stdout, "stderr": sys.stderr}.get(KONSOL_AKISI)
    if akis is None:
        return
    try:
        print(satir, file=akis)
    except Exception:
        pass


def kayit(seviye, mesaj, bekle_ms=10000):
    satir = "[{}] [{}] {}".format(datetime.now().strftime("%Y-%m-%d %H:%M:%S"), seviye, mesaj)
    kilit = Kilit()
    alindi = kilit.al(bekle_ms)
    try:
        if alindi:
            try:
                _hedef_dogrula()
                _rotasyon()
                with open(LOG_YOLU, "a", encoding="utf-8", newline="\n") as dosya:
                    dosya.write(satir + "\n")
            except (OSError, ValueError) as hata:
                if LOG_YOLU != VARSAYILAN_LOG:
                    raise OSError("Günlük yazılamadı ({}): {}".format(LOG_YOLU, hata))
    finally:
        kilit.birak()
    _konsol(satir)
