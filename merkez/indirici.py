import fnmatch
import base64
import hmac
import hashlib
import json
import os
import re
import time
from datetime import datetime
from pathlib import Path

import requests

from . import __version__, ayarlar, teams

UA = "DersMerkezi/{}".format(__version__)
ZAMAN_ASIMI = (10, 30)
UST_BOYUT = 200 * 1024 * 1024
PARCA = 64 * 1024
API_KOK = "https://api.github.com/repos"
RAW_KOK = "https://raw.githubusercontent.com"


class IndirmeHatasi(Exception):
    pass


def token_al():
    return (os.environ.get("GITHUB_TOKEN") or "").strip() or None


def blob_sha1(yol):
    boyut = Path(yol).stat().st_size
    ozet = hashlib.sha1()
    ozet.update(b"blob %d\0" % boyut)
    with open(yol, "rb") as akis:
        for parca in iter(lambda: akis.read(1 << 20), b""):
            ozet.update(parca)
    return ozet.hexdigest()


def dosya_sha256(yol):
    ozet = hashlib.sha256()
    with open(yol, "rb") as akis:
        for parca in iter(lambda: akis.read(1 << 20), b""):
            ozet.update(parca)
    return ozet.hexdigest()


def _desene_uyar(ad, desen):
    return fnmatch.fnmatch(ad.casefold(), desen.casefold())


def _raw_url(depo, dal, ad):
    dal_parca = requests.utils.quote(dal, safe="/")
    ad_parca = requests.utils.quote(ad, safe="")
    return "{}/{}/{}/{}".format(RAW_KOK, depo, dal_parca, ad_parca)


def _bekleme_suresi(yanit, deneme):
    try:
        return min(float(yanit.headers.get("Retry-After") or (1.5 * (deneme + 1))), 10)
    except (TypeError, ValueError):
        return 1.5 * (deneme + 1)


def _istek_getir(url, basliklar):
    son_hata = None
    for deneme in range(3):
        try:
            yanit = requests.get(url, headers=basliklar, timeout=ZAMAN_ASIMI)
        except requests.RequestException as hata:
            son_hata = IndirmeHatasi("Ağ hatası: {}".format(hata))
            if deneme < 2:
                time.sleep(1.5 * (deneme + 1))
                continue
            raise son_hata from hata
        if yanit.status_code == 429 or yanit.status_code >= 500:
            if deneme < 2:
                time.sleep(_bekleme_suresi(yanit, deneme))
                continue
        return yanit
    raise son_hata or IndirmeHatasi("İstek başarısız")


def _kota(basliklar):
    def _sayi(ad):
        try:
            return int(basliklar.get(ad))
        except (TypeError, ValueError):
            return None
    return {
        "limit": _sayi("X-RateLimit-Limit"),
        "kalan": _sayi("X-RateLimit-Remaining"),
        "sifirla": _sayi("X-RateLimit-Reset"),
    }


def depo_listele(depo, dal, token=None, meta=False):
    basliklar = {"User-Agent": UA, "Accept": "application/vnd.github+json"}
    if token:
        basliklar["Authorization"] = "Bearer " + token
    url = "{}/{}/contents/?ref={}".format(API_KOK, depo, requests.utils.quote(dal, safe=""))
    yanit = _istek_getir(url, basliklar)
    if yanit.status_code == 404:
        raise IndirmeHatasi("Depo bulunamadı (404): {}/{}".format(depo, dal))
    if yanit.status_code in (401, 403):
        if yanit.headers.get("X-RateLimit-Remaining") == "0":
            raise IndirmeHatasi("GitHub API limiti doldu; GITHUB_TOKEN tanımlayın veya sonra deneyin")
        raise IndirmeHatasi("Erişim reddedildi ({})".format(yanit.status_code))
    if yanit.status_code >= 500:
        raise IndirmeHatasi("Sunucu hatası ({})".format(yanit.status_code))
    if yanit.status_code != 200:
        raise IndirmeHatasi("Beklenmeyen yanıt ({})".format(yanit.status_code))
    try:
        liste = yanit.json()
    except ValueError as hata:
        raise IndirmeHatasi("API yanıtı okunamadı") from hata
    if not isinstance(liste, list):
        raise IndirmeHatasi("Beklenen dizin listesi alınamadı")
    if len(liste) >= 1000:
        raise IndirmeHatasi("Depo kökü çok büyük (1000+ girdi); Git Trees API gerekli")
    if meta:
        return liste, _kota(yanit.headers)
    return liste


def _indir_akis(url, hedef, beklenen_boyut, beklenen_sha, ilerleme=None, etiket="", ust_boyut=UST_BOYUT):
    son_hata = None
    for deneme in range(3):
        try:
            with requests.get(url, headers={"User-Agent": UA}, stream=True, timeout=ZAMAN_ASIMI) as yanit:
                if yanit.status_code == 429 or yanit.status_code >= 500:
                    son_hata = IndirmeHatasi("İndirme başarısız ({})".format(yanit.status_code))
                    if deneme < 2:
                        time.sleep(_bekleme_suresi(yanit, deneme))
                        continue
                    raise son_hata
                if yanit.status_code != 200:
                    raise IndirmeHatasi("İndirme başarısız ({})".format(yanit.status_code))
                ozet = hashlib.sha1()
                ozet.update(b"blob %d\0" % beklenen_boyut)
                okunan = 0
                with open(hedef, "wb") as dosya:
                    for parca in yanit.iter_content(PARCA):
                        if not parca:
                            continue
                        okunan += len(parca)
                        if okunan > ust_boyut:
                            raise IndirmeHatasi("Dosya üst boyut sınırını aştı")
                        ozet.update(parca)
                        dosya.write(parca)
                        if ilerleme:
                            ilerleme("indir", etiket, okunan, beklenen_boyut)
                    dosya.flush()
                    os.fsync(dosya.fileno())
            if okunan != beklenen_boyut:
                raise IndirmeHatasi("Boyut uyuşmuyor ({}/{})".format(okunan, beklenen_boyut))
            if ozet.hexdigest() != beklenen_sha:
                raise IndirmeHatasi("Git blob SHA doğrulaması başarısız")
            return
        except requests.RequestException as hata:
            son_hata = IndirmeHatasi("Ağ hatası: {}".format(hata))
            if deneme < 2:
                time.sleep(1.5 * (deneme + 1))
                continue
            raise son_hata from hata
    raise son_hata or IndirmeHatasi("İndirme başarısız")


def _yedekle(yol):
    try:
        hedef = yol.with_name(yol.name + ".bozuk-{}".format(time.strftime("%Y%m%d-%H%M%S")))
        yol.replace(hedef)
    except OSError:
        pass


def _durum_yukle(yol):
    if not yol.exists():
        return {"surum": 2, "guncelleme": "", "dosyalar": {}}
    try:
        veri = json.loads(yol.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        _yedekle(yol)
        return {"surum": 2, "guncelleme": "", "dosyalar": {}}
    if not isinstance(veri, dict) or veri.get("surum") not in (None, 1, 2):
        _yedekle(yol)
        return {"surum": 2, "guncelleme": "", "dosyalar": {}}
    veri["surum"] = 2
    if not isinstance(veri.get("dosyalar"), dict):
        veri["dosyalar"] = {}
    return veri


def _durum_yukle_salt(yol):
    if not yol.exists():
        return {"surum": 2, "guncelleme": "", "dosyalar": {}}, None
    try:
        veri = json.loads(yol.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {"surum": 2, "guncelleme": "", "dosyalar": {}}, "Durum dosyası okunamadı veya bozuk: {}".format(yol.name)
    if not isinstance(veri, dict) or not isinstance(veri.get("dosyalar"), dict):
        return {"surum": 2, "guncelleme": "", "dosyalar": {}}, "Durum dosyası şeması geçersiz: {}".format(yol.name)
    veri["surum"] = 2
    return veri, None


def _durum_kaydet(yol, veri):
    ayarlar._json_yaz(yol, veri)


def _md_uret(pdf, md, kaynak_url, sha, saglayici=None, dogrulama=None):
    import logging
    logging.getLogger("pypdf").setLevel(logging.ERROR)
    try:
        from pypdf import PdfReader
    except ImportError:
        return False
    try:
        okuyucu = PdfReader(str(pdf))
        sayfalar = list(okuyucu.pages)
    except Exception:
        return False
    metinler = []
    metinli_sayfa = 0
    for numara, sayfa in enumerate(sayfalar, start=1):
        try:
            metin = (sayfa.extract_text() or "").strip()
        except Exception:
            metin = ""
        if metin:
            metinli_sayfa += 1
        metinler.append((numara, metin))
    satirlar = [
        "# {} — Ders Bağlamı".format(Path(pdf).stem),
        "",
        "> Kaynak: {}".format(kaynak_url),
    ]
    if saglayici:
        satirlar.extend(["> Sağlayıcı: {}".format(saglayici), "> Doğrulama: {}".format(dogrulama or "")])
    else:
        satirlar.append("> Git blob SHA: {}".format(sha))
    satirlar.extend([
        "> Dönüştürme: {}".format(datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
        "> Sayfa: {} (metin içeren: {})".format(len(sayfalar), metinli_sayfa),
        "",
        "---",
        "",
    ])
    if metinli_sayfa == 0:
        satirlar.append("> UYARI: PDF içinde çıkarılabilir metin katmanı bulunamadı; dosya görüntü tabanlı olabilir ve OCR gerektirir.")
        satirlar.append("")
    for numara, metin in metinler:
        satirlar.append("## Sayfa {}".format(numara))
        satirlar.append("")
        satirlar.append(metin if metin else "_Bu sayfada çıkarılabilir metin bulunamadı._")
        satirlar.append("")
    gecici = Path(md).with_name(Path(md).name + ".uretiliyor.tmp")
    try:
        with open(gecici, "w", encoding="utf-8", newline="\n") as dosya:
            dosya.write("\n".join(satirlar))
            dosya.flush()
            os.fsync(dosya.fileno())
        ayarlar._replace_tekrar(gecici, Path(md))
    except OSError:
        try:
            gecici.unlink()
        except OSError:
            pass
        return False
    return True


def _rapor():
    return {"yeni": 0, "guncellenen": 0, "atlanan": 0, "baglam": 0,
            "dogrulama_hatasi": 0, "donusum_hatasi": 0, "zayif_dogrulama": 0,
            "hatalar": [], "uyarilar": [], "hedef": "", "planlanan_bayt": 0}


def _teams_hashleri_coz(oge):
    hashler = oge.get("hashes")
    if hashler is None:
        hashler = {}
    if not isinstance(hashler, dict):
        raise teams.TeamsHatasi("Teams sağlayıcı hash bilgisi geçersiz")
    sonuc = {}
    qx = hashler.get("quickXorHash")
    if qx is not None:
        if not isinstance(qx, str):
            raise teams.TeamsHatasi("Teams quickXorHash biçimi geçersiz")
        if not qx:
            raise teams.TeamsHatasi("Teams quickXorHash boş")
        try:
            ham = base64.b64decode(qx, validate=True)
        except (ValueError, TypeError):
            raise teams.TeamsHatasi("Teams quickXorHash biçimi geçersiz") from None
        if len(ham) != 20:
            raise teams.TeamsHatasi("Teams quickXorHash uzunluğu geçersiz")
        sonuc["quickxor"] = base64.b64encode(ham).decode("ascii")
    sha1 = hashler.get("sha1Hash")
    if sha1 is not None:
        if not isinstance(sha1, str) or not re.fullmatch(r"[A-Fa-f0-9]{40}", sha1):
            raise teams.TeamsHatasi("Teams sha1Hash biçimi geçersiz")
        sonuc["sha1"] = sha1.lower()
    return sonuc


def _teams_dogrulama_yolu(hashler):
    if "quickxor" in hashler and "sha1" in hashler:
        return "quickxor+sha1"
    if "quickxor" in hashler:
        return "quickxor"
    if "sha1" in hashler:
        return "sha1"
    return "zayif"


def _teams_yerel_hashler(yol, algoritmalar):
    qx = teams.QuickXorHash() if "quickxor" in algoritmalar else None
    sha1 = hashlib.sha1() if "sha1" in algoritmalar else None
    try:
        with open(yol, "rb") as akis:
            for parca in iter(lambda: akis.read(1 << 20), b""):
                if qx:
                    qx.update(parca)
                if sha1:
                    sha1.update(parca)
    except OSError:
        return None
    sonuc = {}
    if qx:
        sonuc["quickxor"] = qx.base64()
    if sha1:
        sonuc["sha1"] = sha1.hexdigest()
    return sonuc


def _teams_local_dogrula(yol, boyut, oge, onceki, hashler, zayif):
    if not onceki or not Path(yol).is_file():
        return False
    try:
        if Path(yol).stat().st_size != boyut:
            return False
    except OSError:
        return False
    yol_ad = _teams_dogrulama_yolu(hashler)
    if yol_ad == "zayif":
        if not zayif or onceki.get("dogrulama") != "zayif":
            return False
        etag = oge.get("eTag")
        if not isinstance(etag, str) or not etag or onceki.get("teams_etag") != etag:
            return False
        sha = onceki.get("yerel_sha256")
        try:
            return isinstance(sha, str) and len(sha) == 64 and dosya_sha256(yol) == sha
        except OSError:
            return False
    if onceki.get("dogrulama") != yol_ad or onceki.get("saglayici_hashler") != hashler:
        return False
    hesaplanan = _teams_yerel_hashler(yol, hashler)
    return bool(hesaplanan) and all(
        hmac.compare_digest(hesaplanan.get(algoritma, ""), beklenen)
        for algoritma, beklenen in hashler.items()
    )


def _teams_oge_uyusur(guncel, listelenen):
    return (isinstance(guncel, dict) and guncel.get("id") == listelenen.get("id")
            and guncel.get("eTag") == listelenen.get("eTag")
            and guncel.get("size") == listelenen.get("size") and guncel.get("type") == "file")


def _teams_dogrulama_satiri(yol, hashler, yerel_sha256):
    if yol == "quickxor":
        return "quickXorHash={}".format(hashler["quickxor"])
    if yol == "sha1":
        return "sha1={}".format(hashler["sha1"])
    if yol == "quickxor+sha1":
        return "quickXorHash={}; sha1={}".format(hashler["quickxor"], hashler["sha1"])
    return "zayif (yerel sha256) {}".format((yerel_sha256 or "")[:12])


def _teams_indir_ders(anahtar, ders, ilerleme, kuru, zorla, zorla_md, ust_boyut, rapor):
    teams_kaydi = ders.get("teams") or {}
    drive_id = teams_kaydi.get("driveId")
    item_id = teams_kaydi.get("itemId")
    hedef_klasor = ayarlar.KOK / "dersler" / anahtar
    kok = ayarlar.KOK.resolve()
    if not hedef_klasor.resolve().is_relative_to(kok):
        raise IndirmeHatasi("Hedef klasör uygulama kökü dışında: {}".format(hedef_klasor))
    rapor["hedef"] = str(hedef_klasor)
    durum_yolu = hedef_klasor / "indirilenler.json"
    if kuru:
        durum, durum_hatasi = _durum_yukle_salt(durum_yolu)
        if durum_hatasi:
            rapor["dogrulama_hatasi"] += 1
            rapor["hatalar"].append(durum_hatasi)
    else:
        hedef_klasor.mkdir(parents=True, exist_ok=True)
        for kalinti in list(hedef_klasor.glob("*.part")) + list(hedef_klasor.glob("*.uretiliyor.tmp")):
            try:
                kalinti.unlink()
            except OSError:
                pass
        durum = _durum_yukle(durum_yolu)
    if ilerleme:
        ilerleme("liste", anahtar)
    try:
        token = teams.token_al(teams_kaydi.get("tenantId"))
        girdiler = teams.cocuklari_listele(drive_id, item_id, token)
    except teams.TeamsHatasi as hata:
        raise IndirmeHatasi(str(hata)) from None
    desen = ders.get("desen", "Hafta*.pdf")
    hedefler = sorted(
        [oge for oge in girdiler if oge.get("type") == "file" and _desene_uyar(str(oge.get("name", "")), desen)],
        key=lambda oge: str(oge.get("name", "")),
    )
    zayif_izinli = ders.get("zayif_dogrulama", False) is True
    gorulen = set()
    for oge in hedefler:
        ad = str(oge.get("name", ""))
        if ad.casefold() in gorulen:
            rapor["dogrulama_hatasi"] += 1
            rapor["hatalar"].append("Büyük/küçük harf çakışması: {}".format(ad))
            continue
        gorulen.add(ad.casefold())
        gecerli, neden = ayarlar.dosya_adi_gecerli(ad)
        if not gecerli:
            rapor["dogrulama_hatasi"] += 1
            rapor["hatalar"].append("Dosya adı reddedildi ({}): {}".format(neden, ad))
            continue
        try:
            child_id = teams._kimlik_kontrol(oge.get("id"))
            boyut = oge.get("size")
            if type(boyut) is not int or boyut < 0:
                raise teams.TeamsHatasi("Teams dosya boyutu geçersiz")
            if boyut > ust_boyut:
                raise teams.TeamsHatasi("Dosya üst boyut sınırını aşıyor")
            hashler = _teams_hashleri_coz(oge)
            yol = _teams_dogrulama_yolu(hashler)
            etag = oge.get("eTag")
            if yol == "zayif" and (not zayif_izinli or not isinstance(etag, str) or not etag):
                raise teams.TeamsHatasi("Sağlayıcı hash'i yok; zayıf doğrulama kapalı veya eTag eksik")
        except teams.TeamsHatasi as hata:
            rapor["dogrulama_hatasi"] += 1
            rapor["hatalar"].append("{}: {}".format(ad, hata))
            continue
        yerel = hedef_klasor / ad
        md_yolu = yerel.with_suffix(".md")
        kayitli = durum["dosyalar"].get(ad)
        indir_gerek = zorla or not _teams_local_dogrula(yerel, boyut, oge, kayitli, hashler, zayif_izinli)
        source_url = teams.kaynak_yolu(drive_id, item_id, ad)
        if yol == "zayif":
            rapor["zayif_dogrulama"] += 1
            rapor["uyarilar"].append("{}: sağlayıcı hash'i olmadığından eTag ve yerel SHA-256 kullanıldı".format(ad))
        if indir_gerek and kuru:
            rapor["planlanan_bayt"] += boyut
            if kayitli is None:
                rapor["yeni"] += 1
            else:
                rapor["guncellenen"] += 1
            continue
        if indir_gerek:
            gecici = yerel.with_name(yerel.name + ".part")
            try:
                if yol == "zayif":
                    onceki = teams.oge_getir(drive_id, child_id, token)
                    if not _teams_oge_uyusur(onceki, oge):
                        raise teams.TeamsHatasi("Teams eTag veya boyut indirme öncesinde değişti")
                hashes = teams.icerik_indir(drive_id, child_id, token, gecici, ust_boyut,
                                            beklenen_boyut=boyut, ilerleme=ilerleme, etiket=ad)
                if hashes.get("boyut") != boyut:
                    raise teams.TeamsHatasi("İndirilen dosyanın boyutu liste bilgisiyle eşleşmiyor")
                yerel_sha256 = ""
                if yol == "zayif":
                    sonraki = teams.oge_getir(drive_id, child_id, token)
                    if not _teams_oge_uyusur(sonraki, oge):
                        raise teams.TeamsHatasi("Teams eTag veya boyut indirme sırasında değişti")
                    yerel_sha256 = dosya_sha256(gecici)
                else:
                    if any(not hmac.compare_digest(hashes.get(algoritma, ""), beklenen)
                           for algoritma, beklenen in hashler.items()):
                        raise teams.TeamsHatasi("Teams sağlayıcı hash doğrulaması başarısız")
                ayarlar._replace_tekrar(gecici, yerel)
            except (teams.TeamsHatasi, OSError) as hata:
                try:
                    gecici.unlink()
                except OSError:
                    pass
                rapor["dogrulama_hatasi"] += 1
                rapor["hatalar"].append("{}: {}".format(ad, hata))
                continue
            if kayitli is None:
                rapor["yeni"] += 1
            else:
                rapor["guncellenen"] += 1
        else:
            rapor["atlanan"] += 1
            yerel_sha256 = str((kayitli or {}).get("yerel_sha256") or "")
        if kuru:
            if not indir_gerek and _md_gecerli(md_yolu, kayitli):
                rapor["baglam"] += 1
            continue
        md_hazir = False
        md_sha = ""
        md_boyut = 0
        md_uretildi = ""
        if not (zorla or zorla_md) and not indir_gerek and _md_gecerli(md_yolu, kayitli):
            md_hazir = True
            md_sha = str(kayitli.get("md_sha"))
            md_boyut = int(kayitli.get("md_boyut"))
            md_uretildi = str(kayitli.get("md_uretildi") or "")
        if not md_hazir:
            if ilerleme:
                ilerleme("donustur", ad)
            dogrulama_satiri = _teams_dogrulama_satiri(yol, hashler, yerel_sha256)
            if _md_uret(yerel, md_yolu, source_url, hashler.get("sha1", ""),
                        saglayici="Microsoft Teams", dogrulama=dogrulama_satiri):
                try:
                    md_boyut = md_yolu.stat().st_size
                    md_sha = dosya_sha256(md_yolu)
                    md_uretildi = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
                    md_hazir = True
                except OSError:
                    md_hazir = False
            if not md_hazir:
                rapor["donusum_hatasi"] += 1
                rapor["hatalar"].append("Markdown dönüşümü başarısız: {}".format(ad))
        if md_hazir:
            rapor["baglam"] += 1
        durum["dosyalar"][ad] = {
            "sha": hashler.get("sha1", ""),
            "boyut": boyut,
            "indirildi": datetime.now().strftime("%Y-%m-%dT%H:%M:%S") if indir_gerek else str((kayitli or {}).get("indirildi") or ""),
            "md": bool(md_hazir),
            "kaynak_url": source_url,
            "md_sha": md_sha,
            "md_boyut": md_boyut,
            "md_uretildi": md_uretildi,
            "dogrulama": yol,
            "saglayici_hashler": hashler,
            "teams_etag": etag or "",
            "yerel_sha256": yerel_sha256,
        }
        durum["guncelleme"] = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
        _durum_kaydet(durum_yolu, durum)
    if ilerleme:
        ilerleme("bitti", anahtar)
    return rapor


def _md_gecerli(md_yolu, kayitli):
    if not kayitli:
        return False
    if not (kayitli.get("md") and kayitli.get("md_sha") and md_yolu.exists()):
        return False
    try:
        return (md_yolu.stat().st_size == int(kayitli.get("md_boyut") or -1)
                and dosya_sha256(md_yolu) == str(kayitli.get("md_sha")))
    except (OSError, ValueError):
        return False


def indir_ders(anahtar, ilerleme=None, secili_zorunlu=True, kuru=False, zorla=False,
               zorla_md=False, ust_boyut=UST_BOYUT):
    ust_boyut = int(ust_boyut)
    if not 1 <= ust_boyut <= UST_BOYUT:
        raise IndirmeHatasi("Geçersiz boyut sınırı: {} (1-200 MB aralığında olmalı)".format(ust_boyut))
    if kuru:
        veri, ayar_hatasi = ayarlar.yukle_salt()
        if ayar_hatasi:
            raise IndirmeHatasi("{} (kuru çalışmada dosya değiştirilmedi)".format(ayar_hatasi))
    else:
        veri = ayarlar.yukle()
    ders = veri["dersler"].get(anahtar)
    if not ders:
        raise IndirmeHatasi("Ders bulunamadı: {}".format(anahtar))
    rapor = _rapor()
    if secili_zorunlu and not ders.get("secili", True):
        rapor["atlanan"] += 1
        rapor["hatalar"].append("Ders seçili değil: {}".format(anahtar))
        return rapor
    if ayarlar.kaynak_coz(ders) == "teams":
        return _teams_indir_ders(anahtar, ders, ilerleme, kuru, zorla, zorla_md, ust_boyut, rapor)
    kok = ayarlar.KOK.resolve()
    hedef_klasor = ayarlar.KOK / "dersler" / anahtar
    if not hedef_klasor.resolve().is_relative_to(kok):
        raise IndirmeHatasi("Hedef klasör uygulama kökü dışında: {}".format(hedef_klasor))
    rapor["hedef"] = str(hedef_klasor)
    durum_yolu = hedef_klasor / "indirilenler.json"
    if kuru:
        durum, durum_hatasi = _durum_yukle_salt(durum_yolu)
        if durum_hatasi:
            rapor["dogrulama_hatasi"] += 1
            rapor["hatalar"].append(durum_hatasi)
    else:
        hedef_klasor.mkdir(parents=True, exist_ok=True)
        for kalinti in list(hedef_klasor.glob("*.part")) + list(hedef_klasor.glob("*.uretiliyor.tmp")):
            try:
                kalinti.unlink()
            except OSError:
                pass
        durum = _durum_yukle(durum_yolu)
    if ilerleme:
        ilerleme("liste", anahtar)
    girdiler = depo_listele(ders["depo"], ders.get("dal", "main"), token_al())
    desen = ders.get("desen", "Hafta*.pdf")
    hedefler = sorted(
        [g for g in girdiler if g.get("type") == "file" and _desene_uyar(str(g.get("name", "")), desen)],
        key=lambda g: str(g.get("name", "")),
    )
    gorulen = {}
    for girdi in hedefler:
        ad = str(girdi.get("name", ""))
        if ad.casefold() in gorulen:
            rapor["dogrulama_hatasi"] += 1
            rapor["hatalar"].append("Büyük/küçük harf çakışması: {}".format(ad))
            continue
        gorulen[ad.casefold()] = True
        gecerli, neden = ayarlar.dosya_adi_gecerli(ad)
        if not gecerli:
            rapor["dogrulama_hatasi"] += 1
            rapor["hatalar"].append("Dosya adı reddedildi ({}): {}".format(neden, ad))
            continue
        beklenen_sha = str(girdi.get("sha", ""))
        beklenen_boyut = int(girdi.get("size") or 0)
        if beklenen_boyut > ust_boyut:
            rapor["dogrulama_hatasi"] += 1
            rapor["hatalar"].append("{}: dosya boyut sınırı aşıyor ({} bayt)".format(ad, beklenen_boyut))
            continue
        yerel = hedef_klasor / ad
        md_yolu = yerel.with_suffix(".md")
        kayitli = durum["dosyalar"].get(ad)
        indir_gerek = True
        if kayitli and str(kayitli.get("sha", "")) == beklenen_sha and yerel.exists():
            try:
                if yerel.stat().st_size == beklenen_boyut and blob_sha1(yerel) == beklenen_sha:
                    indir_gerek = False
            except OSError:
                indir_gerek = True
        if zorla:
            indir_gerek = True
        kaynak_url = _raw_url(ders["depo"], ders.get("dal", "main"), ad)
        if indir_gerek:
            if kuru:
                rapor["planlanan_bayt"] += beklenen_boyut
                if kayitli is None:
                    rapor["yeni"] += 1
                else:
                    rapor["guncellenen"] += 1
            else:
                gecici = yerel.with_name(yerel.name + ".part")
                try:
                    _indir_akis(kaynak_url, gecici, beklenen_boyut, beklenen_sha, ilerleme, ad, ust_boyut=ust_boyut)
                    ayarlar._replace_tekrar(gecici, yerel)
                except (IndirmeHatasi, PermissionError, OSError) as hata:
                    try:
                        gecici.unlink()
                    except OSError:
                        pass
                    rapor["dogrulama_hatasi"] += 1
                    rapor["hatalar"].append("{}: {}".format(ad, hata))
                    continue
                if kayitli is None:
                    rapor["yeni"] += 1
                else:
                    rapor["guncellenen"] += 1
        else:
            rapor["atlanan"] += 1
        if kuru:
            if not indir_gerek and _md_gecerli(md_yolu, kayitli):
                rapor["baglam"] += 1
            continue
        md_hazir = False
        md_sha = ""
        md_boyut = 0
        md_uretildi = ""
        if not (zorla or zorla_md) and not indir_gerek and _md_gecerli(md_yolu, kayitli):
            md_hazir = True
            md_sha = str(kayitli.get("md_sha"))
            md_boyut = int(kayitli.get("md_boyut"))
            md_uretildi = str(kayitli.get("md_uretildi") or "")
        if not md_hazir:
            if ilerleme:
                ilerleme("donustur", ad)
            if _md_uret(yerel, md_yolu, kaynak_url, beklenen_sha):
                try:
                    md_boyut = md_yolu.stat().st_size
                    md_sha = dosya_sha256(md_yolu)
                    md_uretildi = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
                    md_hazir = True
                except OSError:
                    md_hazir = False
            if not md_hazir:
                rapor["donusum_hatasi"] += 1
                rapor["hatalar"].append("Markdown dönüşümü başarısız: {}".format(ad))
        if md_hazir:
            rapor["baglam"] += 1
        durum["dosyalar"][ad] = {
            "sha": beklenen_sha,
            "boyut": beklenen_boyut,
            "indirildi": datetime.now().strftime("%Y-%m-%dT%H:%M:%S") if indir_gerek else str((kayitli or {}).get("indirildi") or ""),
            "md": bool(md_hazir),
            "kaynak_url": kaynak_url,
            "md_sha": md_sha,
            "md_boyut": md_boyut,
            "md_uretildi": md_uretildi,
        }
        durum["guncelleme"] = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
        _durum_kaydet(durum_yolu, durum)
    if ilerleme:
        ilerleme("bitti", anahtar)
    return rapor
