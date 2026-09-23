import base64
from email.utils import parsedate_to_datetime
import hashlib
import json
import os
import time
from datetime import timezone
from pathlib import Path
from urllib.parse import quote, unquote, urljoin, urlsplit

import requests

from . import __version__, ayarlar

GRAPH_ROOT = "https://graph.microsoft.com/v1.0"
LOGIN_ROOT = "https://login.microsoftonline.com"
UA = "DersMerkezi/{}".format(__version__)
ZAMAN_ASIMI = (10, 30)
PARCA = 64 * 1024
TEKRAR_SINIRI = 3
SAYFA_BOYUTU = 200
SAYFA_SINIRI = 50
OGE_SINIRI = 10000
YONLENDIRME_SINIRI = 5
GRAPH_YONLENDIRME_SINIRI = 3
INDIRME_ALAN_ADLARI = (
    "1drv.com",
    "sharepoint.com",
    "sharepointonline.com",
    "blob.core.windows.net",
)


class TeamsHatasi(Exception):
    pass


class _BearerKimlik(requests.auth.AuthBase):
    def __init__(self, token):
        self._token = token

    def __call__(self, istek):
        istek.headers["Authorization"] = "Bearer " + self._token
        return istek


class _KimlikYok(requests.auth.AuthBase):
    def __call__(self, istek):
        istek.headers.pop("Authorization", None)
        return istek


class QuickXorHash:
    def __init__(self):
        self._deger = 0
        self._uzunluk = 0
        self._bekleyen = bytearray()

    def _xorla(self, bayt, konum):
        donmus = (bayt << konum) | (bayt >> (160 - konum))
        self._deger ^= donmus & ((1 << 160) - 1)

    @staticmethod
    def _katla(baytlar):
        deger = int.from_bytes(baytlar, "little")
        kaydirma = 8
        while kaydirma < deger.bit_length():
            deger ^= deger >> kaydirma
            kaydirma <<= 1
        return deger & 0xff

    def _blok_isle(self, veri):
        uzunluk = len(veri)
        for sira in range(160):
            bayt = self._katla(veri[sira:uzunluk:160])
            if bayt:
                self._xorla(bayt, (sira * 11) % 160)

    def update(self, veri):
        if not veri:
            return
        self._uzunluk += len(veri)
        self._bekleyen.extend(veri)
        kullanilabilir = len(self._bekleyen) // 160 * 160
        while kullanilabilir >= 1024 * 1024:
            blok_boyutu = (1024 * 1024) // 160 * 160
            self._blok_isle(self._bekleyen[:blok_boyutu])
            del self._bekleyen[:blok_boyutu]
            kullanilabilir -= blok_boyutu
        if kullanilabilir:
            self._blok_isle(self._bekleyen[:kullanilabilir])
            del self._bekleyen[:kullanilabilir]

    def digest(self):
        deger = self._deger
        for sira, bayt in enumerate(self._bekleyen):
            konum = (sira * 11) % 160
            donmus = (bayt << konum) | (bayt >> (160 - konum))
            deger ^= donmus & ((1 << 160) - 1)
        deger ^= self._uzunluk << 96
        return (deger & ((1 << 160) - 1)).to_bytes(20, "little")

    def hexdigest(self):
        return self.digest().hex()

    def base64(self):
        return base64.b64encode(self.digest()).decode("ascii")


def _bekleme_suresi(basliklar, deneme):
    deger = (basliklar or {}).get("Retry-After")
    try:
        return min(max(float(deger), 0.0), 10.0)
    except (TypeError, ValueError):
        try:
            hedef_tarihi = parsedate_to_datetime(deger)
            if hedef_tarihi.tzinfo is None:
                hedef_tarihi = hedef_tarihi.replace(tzinfo=timezone.utc)
            hedef = hedef_tarihi.timestamp()
            return min(max(hedef - time.time(), 0.0), 10.0)
        except (TypeError, ValueError, OverflowError):
            return min(1.5 * (deneme + 1), 10.0)


def _hata_durumu(kod, islem):
    if kod == 401:
        return TeamsHatasi("Teams kimlik doğrulaması başarısız (401)")
    if kod == 403:
        return TeamsHatasi("Teams kaynağına erişim reddedildi (403); uygulama iznini ve yönetici onayını denetleyin")
    if kod == 404:
        return TeamsHatasi("Teams kaynağı bulunamadı veya erişilemiyor (404)")
    if kod == 429:
        return TeamsHatasi("Microsoft Graph istek sınırına ulaşıldı (429)")
    if kod >= 500:
        return TeamsHatasi("Microsoft Graph sunucu hatası ({})".format(kod))
    return TeamsHatasi("{} başarısız ({})".format(islem, kod))


def _yanit_kapat(yanit):
    kapat = getattr(yanit, "close", None)
    if kapat:
        kapat()


def _tenant_coz(tenant_id):
    tenant = tenant_id if tenant_id is not None else os.environ.get("TEAMS_TENANT_ID")
    if not isinstance(tenant, str) or not ayarlar.TEAMS_TENANT_DESENI.fullmatch(tenant):
        raise TeamsHatasi("Teams kiracı kimliği yok veya biçimi geçersiz; TEAMS_TENANT_ID tanımlayın")
    return tenant


def token_al(tenant_id=None):
    tenant = _tenant_coz(tenant_id)
    istemci = (os.environ.get("TEAMS_CLIENT_ID") or "").strip()
    sir = os.environ.get("TEAMS_CLIENT_SECRET") or ""
    if not istemci or not sir:
        raise TeamsHatasi("Teams kimlik doğrulaması için TEAMS_CLIENT_ID ve TEAMS_CLIENT_SECRET tanımlanmalıdır")
    url = "{}/{}/oauth2/v2.0/token".format(LOGIN_ROOT, quote(tenant, safe=".-"))
    veri = {
        "client_id": istemci,
        "client_secret": sir,
        "grant_type": "client_credentials",
        "scope": "https://graph.microsoft.com/.default",
    }
    for deneme in range(TEKRAR_SINIRI):
        try:
            yanit = requests.post(url, data=veri, headers={"User-Agent": UA}, timeout=ZAMAN_ASIMI,
                                 allow_redirects=False, auth=_KimlikYok())
        except requests.RequestException:
            if deneme < TEKRAR_SINIRI - 1:
                time.sleep(1.5 * (deneme + 1))
                continue
            raise TeamsHatasi("Teams kimlik hizmetine ulaşılamadı") from None
        try:
            kod = yanit.status_code
            if kod == 429 or kod >= 500:
                if deneme < TEKRAR_SINIRI - 1:
                    time.sleep(_bekleme_suresi(yanit.headers, deneme))
                    continue
            if kod != 200:
                raise _hata_durumu(kod, "Teams kimlik doğrulaması")
            try:
                sonuc = yanit.json()
            except ValueError:
                raise TeamsHatasi("Teams kimlik hizmetinden geçersiz yanıt alındı") from None
            erisim = sonuc.get("access_token") if isinstance(sonuc, dict) else None
            if not isinstance(erisim, str) or not erisim:
                raise TeamsHatasi("Teams kimlik hizmeti erişim anahtarı döndürmedi")
            return erisim
        finally:
            _yanit_kapat(yanit)
    raise TeamsHatasi("Teams kimlik doğrulaması tamamlanamadı")


def _kimlik_kontrol(kimlik):
    if not isinstance(kimlik, str) or not ayarlar.TEAMS_ID_DESENI.fullmatch(kimlik):
        raise TeamsHatasi("Teams öğe kimliği geçersiz")
    return kimlik


def _graf_url(drive_id, oge_yolu, sorgu=""):
    drive = quote(_kimlik_kontrol(drive_id), safe="")
    return "{}/drives/{}/{}{}".format(GRAPH_ROOT, drive, oge_yolu, ("?" + sorgu) if sorgu else "")


def _graf_url_kontrol(url, drive_id):
    try:
        parcalar = urlsplit(url)
        port = parcalar.port
        yol = unquote(parcalar.path)
    except (TypeError, ValueError):
        return False
    beklenen = "/v1.0/drives/{}/".format(_kimlik_kontrol(drive_id))
    if (parcalar.scheme.lower() != "https" or parcalar.hostname is None
            or parcalar.hostname.lower() != "graph.microsoft.com" or port not in (None, 443)
            or parcalar.username is not None or parcalar.password is not None or parcalar.fragment
            or not yol.startswith(beklenen) or "\\" in yol
            or any(parca in (".", "..") for parca in yol.split("/"))):
        return False
    return True


def _onceden_imzali_url_kontrol(url):
    try:
        parcalar = urlsplit(url)
        port = parcalar.port
    except (TypeError, ValueError):
        return False
    ana_makine = (parcalar.hostname or "").lower()
    if (parcalar.scheme.lower() != "https" or not ana_makine or port not in (None, 443)
            or parcalar.username is not None or parcalar.password is not None or parcalar.fragment):
        return False
    return any(ana_makine == alan or ana_makine.endswith("." + alan) for alan in INDIRME_ALAN_ADLARI)


def _graf_istek(url, drive_id, token, akis=False, yonlendirme=True):
    mevcut = url
    gorulen_url = set()
    graf_yonlendirmeleri = 0
    while True:
        if not _graf_url_kontrol(mevcut, drive_id):
            raise TeamsHatasi("Microsoft Graph bağlantısı güvenli değil")
        if mevcut in gorulen_url:
            raise TeamsHatasi("Microsoft Graph yönlendirme döngüsü algılandı")
        gorulen_url.add(mevcut)
        yanit = None
        for deneme in range(TEKRAR_SINIRI):
            try:
                yanit = requests.get(mevcut, headers={"User-Agent": UA}, auth=_BearerKimlik(token),
                                     timeout=ZAMAN_ASIMI, stream=akis, allow_redirects=False)
            except requests.RequestException:
                if deneme < TEKRAR_SINIRI - 1:
                    time.sleep(1.5 * (deneme + 1))
                    continue
                raise TeamsHatasi("Microsoft Graph bağlantısında ağ hatası") from None
            if yanit.status_code == 429 or yanit.status_code >= 500:
                if deneme < TEKRAR_SINIRI - 1:
                    time.sleep(_bekleme_suresi(yanit.headers, deneme))
                    _yanit_kapat(yanit)
                    yanit = None
                    continue
            break
        if yanit is None:
            raise TeamsHatasi("Microsoft Graph isteği tamamlanamadı")
        kod = yanit.status_code
        if yonlendirme and kod in (301, 302, 303, 307, 308):
            konum = yanit.headers.get("Location")
            _yanit_kapat(yanit)
            if not konum or graf_yonlendirmeleri >= GRAPH_YONLENDIRME_SINIRI:
                raise TeamsHatasi("Microsoft Graph yönlendirmesi geçersiz")
            yeni = urljoin(mevcut, konum)
            if not _graf_url_kontrol(yeni, drive_id):
                raise TeamsHatasi("Microsoft Graph yönlendirmesi güvenli değil")
            mevcut = yeni
            graf_yonlendirmeleri += 1
            continue
        return yanit


def _json_getir(url, drive_id, token):
    yanit = _graf_istek(url, drive_id, token)
    try:
        if yanit.status_code != 200:
            raise _hata_durumu(yanit.status_code, "Microsoft Graph isteği")
        try:
            veri = yanit.json()
        except ValueError:
            raise TeamsHatasi("Microsoft Graph geçersiz JSON yanıtı döndürdü") from None
        if not isinstance(veri, dict):
            raise TeamsHatasi("Microsoft Graph yanıt biçimi geçersiz")
        return veri
    finally:
        _yanit_kapat(yanit)


def _sonraki_url_kontrol(url, drive_id):
    if not isinstance(url, str) or not _graf_url_kontrol(url, drive_id):
        raise TeamsHatasi("Microsoft Graph sayfalama bağlantısı güvenli değil")
    return url


def _ozgecmis(url):
    parcalar = urlsplit(url)
    return "{}://{}{}?{}".format(parcalar.scheme.lower(), (parcalar.hostname or "").lower(),
                                 parcalar.path, parcalar.query)


def _oge_donustur(oge):
    if not isinstance(oge, dict):
        raise TeamsHatasi("Microsoft Graph liste öğesi geçersiz")
    ad = oge.get("name")
    if not isinstance(ad, str):
        raise TeamsHatasi("Microsoft Graph dosya adı geçersiz")
    dosya = oge.get("file")
    klasor = oge.get("folder")
    tur = "file" if isinstance(dosya, dict) else "dir" if isinstance(klasor, dict) else "other"
    sonuc = {"name": ad, "type": tur, "id": oge.get("id"), "eTag": oge.get("eTag"), "size": oge.get("size")}
    if tur == "file":
        hashler = dosya.get("hashes")
        sonuc["hashes"] = {} if hashler is None else hashler
    return sonuc


def cocuklari_listele(drive_id, item_id, token):
    drive = _kimlik_kontrol(drive_id)
    item = quote(_kimlik_kontrol(item_id), safe="")
    sorgu = "$top={}&$select=id,name,size,eTag,file,folder".format(SAYFA_BOYUTU)
    url = _graf_url(drive, "items/{}/children".format(item), sorgu)
    ziyaret_edilen = set()
    sonuc = []
    sayfa = 0
    while url:
        url = _sonraki_url_kontrol(url, drive)
        anahtar = _ozgecmis(url)
        if anahtar in ziyaret_edilen:
            raise TeamsHatasi("Microsoft Graph sayfalama döngüsü algılandı")
        ziyaret_edilen.add(anahtar)
        sayfa += 1
        if sayfa > SAYFA_SINIRI:
            raise TeamsHatasi("Teams klasörü sayfa sınırını aşıyor (en fazla 50)")
        veri = _json_getir(url, drive, token)
        ogeler = veri.get("value")
        if not isinstance(ogeler, list):
            raise TeamsHatasi("Microsoft Graph liste yanıtı geçersiz")
        sonuc.extend(_oge_donustur(oge) for oge in ogeler)
        if len(sonuc) > OGE_SINIRI:
            raise TeamsHatasi("Teams klasörü öğe sınırını aşıyor (en fazla 10000)")
        sonraki = veri.get("@odata.nextLink")
        if sonraki is not None:
            url = _sonraki_url_kontrol(sonraki, drive)
        else:
            url = None
    return sonuc


def oge_getir(drive_id, item_id, token):
    oge = quote(_kimlik_kontrol(item_id), safe="")
    url = _graf_url(drive_id, "items/{}".format(oge), "$select=id,eTag,size,file")
    veri = _json_getir(url, drive_id, token)
    dosya = veri.get("file")
    return {"id": veri.get("id"), "type": "file" if isinstance(dosya, dict) else "other",
            "eTag": veri.get("eTag"), "size": veri.get("size")}


def yetki_yokla(drive_id, item_id, token):
    oge = quote(_kimlik_kontrol(item_id), safe="")
    url = _graf_url(drive_id, "items/{}/children".format(oge), "$top=1&$select=id")
    veri = _json_getir(url, drive_id, token)
    if not isinstance(veri.get("value"), list):
        raise TeamsHatasi("Teams klasör yetki yanıtı geçersiz")
    return True


def _yanit_getir(url, basliklar, akis):
    mevcut = url
    ziyaret_edilen = set()
    for _ in range(YONLENDIRME_SINIRI + 1):
        if not _onceden_imzali_url_kontrol(mevcut):
            raise TeamsHatasi("Teams indirme yönlendirmesi izinli HTTPS alan adında değil")
        if mevcut in ziyaret_edilen or len(ziyaret_edilen) >= YONLENDIRME_SINIRI:
            raise TeamsHatasi("Teams indirme yönlendirme sınırı aşıldı")
        ziyaret_edilen.add(mevcut)
        yanit = None
        for deneme in range(TEKRAR_SINIRI):
            try:
                yanit = requests.get(mevcut, headers=basliklar, timeout=ZAMAN_ASIMI, stream=akis,
                                     allow_redirects=False, auth=_KimlikYok())
            except requests.RequestException:
                if deneme < TEKRAR_SINIRI - 1:
                    time.sleep(1.5 * (deneme + 1))
                    continue
                raise TeamsHatasi("Teams dosya aktarımında ağ hatası") from None
            if yanit.status_code == 429 or yanit.status_code >= 500:
                if deneme < TEKRAR_SINIRI - 1:
                    time.sleep(_bekleme_suresi(yanit.headers, deneme))
                    _yanit_kapat(yanit)
                    yanit = None
                    continue
            break
        if yanit is None:
            raise TeamsHatasi("Teams dosya aktarımı tamamlanamadı")
        if yanit.status_code in (301, 302, 303, 307, 308):
            konum = yanit.headers.get("Location")
            _yanit_kapat(yanit)
            if not konum or len(ziyaret_edilen) >= YONLENDIRME_SINIRI:
                raise TeamsHatasi("Teams indirme yönlendirmesi geçersiz")
            yeni = urljoin(mevcut, konum)
            if not _onceden_imzali_url_kontrol(yeni):
                raise TeamsHatasi("Teams indirme yönlendirmesi izinli HTTPS alan adında değil")
            mevcut = yeni
            continue
        return yanit
    raise TeamsHatasi("Teams dosya aktarımı tamamlanamadı")


def icerik_indir(drive_id, item_id, token, hedef, ust_boyut, beklenen_boyut=None, ilerleme=None, etiket=""):
    oge = quote(_kimlik_kontrol(item_id), safe="")
    url = _graf_url(drive_id, "items/{}/content".format(oge))
    graf_yaniti = _graf_istek(url, drive_id, token, akis=False, yonlendirme=False)
    try:
        if graf_yaniti.status_code not in (301, 302, 303, 307, 308):
            if graf_yaniti.status_code != 200:
                raise _hata_durumu(graf_yaniti.status_code, "Teams dosya bağlantısı")
            raise TeamsHatasi("Microsoft Graph beklenen ön kimlikli indirme yönlendirmesini döndürmedi")
        konum = graf_yaniti.headers.get("Location")
    finally:
        _yanit_kapat(graf_yaniti)
    if not konum:
        raise TeamsHatasi("Microsoft Graph indirme yönlendirmesi eksik")
    hedef_url = urljoin(url, konum)
    if not _onceden_imzali_url_kontrol(hedef_url):
        raise TeamsHatasi("Teams indirme yönlendirmesi izinli HTTPS alan adında değil")
    yanit = _yanit_getir(hedef_url, {"User-Agent": UA}, akis=True)
    gecici = Path(hedef)
    try:
        if yanit.status_code != 200:
            raise _hata_durumu(yanit.status_code, "Teams dosya indirmesi")
        try:
            content_length = yanit.headers.get("Content-Length")
            if content_length is not None:
                content_length = int(content_length)
                if content_length < 0:
                    raise TeamsHatasi("Teams dosya boyutu başlığı geçersiz")
                if content_length > ust_boyut:
                    raise TeamsHatasi("Dosya üst boyut sınırını aşıyor")
        except (TypeError, ValueError):
            raise TeamsHatasi("Teams dosya boyutu başlığı geçersiz") from None
        qx = QuickXorHash()
        sha1 = hashlib.sha1()
        okunan = 0
        with open(gecici, "wb") as dosya:
            for parca in yanit.iter_content(PARCA):
                if not parca:
                    continue
                okunan += len(parca)
                if okunan > ust_boyut:
                    raise TeamsHatasi("Dosya üst boyut sınırını aşıyor")
                if beklenen_boyut is not None and okunan > beklenen_boyut:
                    raise TeamsHatasi("İndirilen dosya beklenen boyutu aşıyor")
                qx.update(parca)
                sha1.update(parca)
                dosya.write(parca)
                if ilerleme:
                    ilerleme("indir", etiket, okunan, beklenen_boyut or ust_boyut)
            dosya.flush()
            os.fsync(dosya.fileno())
        if beklenen_boyut is not None and okunan != beklenen_boyut:
            raise TeamsHatasi("İndirilen dosyanın boyutu liste bilgisiyle eşleşmiyor")
        return {"boyut": okunan, "quickxor": qx.base64(), "sha1": sha1.hexdigest()}
    except OSError as hata:
        try:
            gecici.unlink()
        except OSError:
            pass
        raise TeamsHatasi("Teams dosyası geçici hedefe yazılamadı") from hata
    except requests.RequestException:
        try:
            gecici.unlink()
        except OSError:
            pass
        raise TeamsHatasi("Teams dosya aktarımında ağ hatası") from None
    except TeamsHatasi:
        try:
            gecici.unlink()
        except OSError:
            pass
        raise
    finally:
        _yanit_kapat(yanit)


def kimlik_kisalt(kimlik):
    return ayarlar.teams_kimlik_kisalt(kimlik)


def kaynak_yolu(drive_id, item_id, dosya_adi):
    drive = kimlik_kisalt(_kimlik_kontrol(drive_id))
    item = kimlik_kisalt(_kimlik_kontrol(item_id))
    return "teams://{}/{}/{}".format(drive, item, quote(dosya_adi, safe=""))
