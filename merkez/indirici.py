import fnmatch
import hashlib
import json
import os
import time
from datetime import datetime
from pathlib import Path

import requests

from . import __version__, ayarlar

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


def _md_uret(pdf, md, kaynak_url, sha):
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
        "> Git blob SHA: {}".format(sha),
        "> Dönüştürme: {}".format(datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
        "> Sayfa: {} (metin içeren: {})".format(len(sayfalar), metinli_sayfa),
        "",
        "---",
        "",
    ]
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
            "dogrulama_hatasi": 0, "donusum_hatasi": 0, "hatalar": [], "hedef": "", "planlanan_bayt": 0}


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
