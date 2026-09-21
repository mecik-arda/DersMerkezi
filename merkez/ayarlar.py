import json
import os
import re
import shutil
import time
from pathlib import Path
from urllib.parse import urlsplit

from . import gunluk

KOK = Path(__file__).resolve().parent.parent
AYAR_YOLU = KOK / "ayarlar.json"
YEDEK_YOLU = KOK / "ayarlar.json.yedek"
SURUM = 1

SLUG_DESENI = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
DEPO_DESENI = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,38}/[A-Za-z0-9][A-Za-z0-9._-]{0,99}$")
DAL_DESENI = re.compile(r"^[A-Za-z0-9._/-]{1,100}$")
DESEN_YASAK = re.compile(r"[\x00-\x1f<>:\"/\\|?]")
SAAT_DESENI = re.compile(r"^([01]\d|2[0-3]):[0-5]\d$")
YASAK_DOSYA = re.compile(r"[<>:\"/\\|?*\x00-\x1f]")
AD_YASAK = re.compile(r"[^\w .,()!+-]")
AYGIT_ADLARI = {"CON", "PRN", "AUX", "NUL"} | {"COM%d" % i for i in range(1, 10)} | {"LPT%d" % i for i in range(1, 10)}

TR_HARF = str.maketrans({
    "ç": "c", "Ç": "c", "ğ": "g", "Ğ": "g", "ı": "i", "İ": "i",
    "ö": "o", "Ö": "o", "ş": "s", "Ş": "s", "ü": "u", "Ü": "u",
})

GUNLER = {
    "PZT": "Monday",
    "SAL": "Tuesday",
    "CAR": "Wednesday",
    "PER": "Thursday",
    "CUM": "Friday",
    "CMT": "Saturday",
    "PAZ": "Sunday",
}
GUN_ADLARI = tuple(GUNLER.values())


def bos_veri():
    return {"surum": SURUM, "dersler": {}}


def slug_uret(ad):
    metin = ad.translate(TR_HARF).lower()
    metin = re.sub(r"[^a-z0-9]+", "-", metin)
    return metin.strip("-")


def depo_coz(depo):
    metin = (depo or "").strip()
    if metin.startswith("https://") or metin.startswith("http://"):
        parcalar = urlsplit(metin)
        if parcalar.scheme != "https" or parcalar.netloc.lower() != "github.com":
            raise ValueError("Yalnızca https://github.com/owner/repo desteklenir")
        if parcalar.query or parcalar.fragment:
            raise ValueError("Depo adresinde sorgu veya parça bulunamaz")
        yol = parcalar.path.strip("/")
        if yol.endswith(".git"):
            yol = yol[:-4]
        parca_listesi = [p for p in yol.split("/") if p]
        if len(parca_listesi) != 2:
            raise ValueError("Depo adresi 'owner/repo' biçiminde olmalı")
        metin = "/".join(parca_listesi)
    if not DEPO_DESENI.match(metin):
        raise ValueError("Depo 'owner/repo' biçiminde olmalı")
    return metin


def ad_gecerli(ad):
    if not ad or not ad.strip():
        return False, "boş ad"
    if len(ad) < 2 or len(ad) > 120:
        return False, "ad 2-120 karakter olmalı"
    if AD_YASAK.search(ad):
        return False, "geçersiz karakter içeriyor"
    return True, ""


def dosya_adi_gecerli(ad):
    if not ad or not ad.strip():
        return False, "boş ad"
    if ad != Path(ad).name:
        return False, "yol ayırıcı içeriyor"
    if YASAK_DOSYA.search(ad):
        return False, "geçersiz karakter içeriyor"
    if ad.endswith(".") or ad.endswith(" "):
        return False, "sonda nokta veya boşluk var"
    if len(ad) > 180:
        return False, "ad çok uzun"
    taban = ad.split(".")[0].upper()
    if taban in AYGIT_ADLARI:
        return False, "ayrılmış aygıt adı"
    return True, ""


def saat_gecerli(saat):
    return bool(SAAT_DESENI.match(saat or ""))


def gun_listesi_coz(gunler):
    sonuc = []
    for gun in gunler:
        anahtar = str(gun).strip().upper()
        if anahtar in GUNLER:
            sonuc.append(GUNLER[anahtar])
            continue
        eslesme = None
        for ad in GUN_ADLARI:
            if anahtar == ad.upper() or anahtar == ad.upper()[:3]:
                eslesme = ad
                break
        if not eslesme:
            raise ValueError("Geçersiz gün: {}".format(gun))
        sonuc.append(eslesme)
    if not sonuc:
        raise ValueError("En az bir gün seçilmeli")
    return sonuc


def _bozuk_yedekle(yol):
    kilit = gunluk.Kilit()
    if not kilit.al(10000):
        return
    try:
        hedef = yol.with_name(yol.name + ".bozuk-{}".format(time.strftime("%Y%m%d-%H%M%S")))
        yol.replace(hedef)
    except OSError:
        pass
    finally:
        kilit.birak()


def _replace_tekrar(kaynak, hedef, deneme=3, bekleme=0.5):
    for deneme_no in range(deneme):
        try:
            os.replace(kaynak, hedef)
            return
        except PermissionError:
            if deneme_no == deneme - 1:
                raise
            time.sleep(bekleme * (2 ** deneme_no))


def _json_yaz(yol, veri):
    kilit = gunluk.kilitle()
    try:
        gecici = yol.with_name(yol.name + ".tmp")
        metin = json.dumps(veri, ensure_ascii=False, indent=2) + "\n"
        try:
            with open(gecici, "w", encoding="utf-8", newline="\n") as dosya:
                dosya.write(metin)
                dosya.flush()
                os.fsync(dosya.fileno())
            _replace_tekrar(gecici, yol)
        except OSError:
            try:
                gecici.unlink()
            except OSError:
                pass
            raise
    finally:
        kilit.birak()


def yukle():
    if not AYAR_YOLU.exists():
        return bos_veri()
    try:
        veri = json.loads(AYAR_YOLU.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        _bozuk_yedekle(AYAR_YOLU)
        return bos_veri()
    if not isinstance(veri, dict) or not isinstance(veri.get("dersler"), dict):
        _bozuk_yedekle(AYAR_YOLU)
        return bos_veri()
    surum = veri.get("surum", 1)
    if surum != SURUM:
        _bozuk_yedekle(AYAR_YOLU)
        return bos_veri()
    return veri


def kaydet(veri):
    veri = dict(veri)
    veri["surum"] = SURUM
    if AYAR_YOLU.exists():
        try:
            shutil.copy2(AYAR_YOLU, YEDEK_YOLU)
        except OSError:
            pass
    _json_yaz(AYAR_YOLU, veri)


def ders_ekle(ad, depo, dal="main", desen="Hafta*.pdf", slug=None):
    ad = (ad or "").strip()
    gecerli, neden = ad_gecerli(ad)
    if not gecerli:
        raise ValueError("Geçersiz ders adı: {}".format(neden))
    depo = depo_coz(depo)
    dal = (dal or "main").strip()
    if not DAL_DESENI.match(dal) or ".." in dal:
        raise ValueError("Geçersiz dal adı")
    desen = (desen or "Hafta*.pdf").strip()
    if len(desen) > 64 or DESEN_YASAK.search(desen) or "/" in desen or "\\" in desen:
        raise ValueError("Geçersiz desen")
    kimlik = (slug or slug_uret(ad)).strip().lower()
    if len(kimlik) < 2 or len(kimlik) > 40 or not SLUG_DESENI.match(kimlik):
        raise ValueError("Geçersiz ders kimliği (slug)")
    with gunluk.kilitle():
        veri = yukle()
        for mevcut in veri["dersler"]:
            if mevcut.casefold() == kimlik.casefold():
                raise ValueError("Bu ders zaten kayıtlı: {}".format(mevcut))
        veri["dersler"][kimlik] = {
            "ad": ad,
            "depo": depo,
            "dal": dal,
            "desen": desen,
            "secili": True,
            "otomasyon": {"aktif": False, "gunler": [], "saat": "09:00", "gorevAdi": "DersMerkezi_" + kimlik},
        }
        kaydet(veri)
    return kimlik


def ders_sil(slug):
    with gunluk.kilitle():
        veri = yukle()
        if slug not in veri["dersler"]:
            raise ValueError("Ders bulunamadı: {}".format(slug))
        del veri["dersler"][slug]
        kaydet(veri)


def ders_getir(slug):
    veri = yukle()
    ders = veri["dersler"].get(slug)
    if not ders:
        raise ValueError("Ders bulunamadı: {}".format(slug))
    return ders


def isaretle(slug, secili):
    with gunluk.kilitle():
        veri = yukle()
        if slug not in veri["dersler"]:
            raise ValueError("Ders bulunamadı: {}".format(slug))
        veri["dersler"][slug]["secili"] = bool(secili)
        kaydet(veri)


def secili_dersler():
    veri = yukle()
    return [k for k, d in veri["dersler"].items() if d.get("secili", True)]


def otomasyon_ayarla(slug, gunler, saat, aktif=True):
    gun_adlari = gun_listesi_coz(gunler)
    if not saat_gecerli(saat):
        raise ValueError("Saat SS:DD biçiminde olmalı")
    with gunluk.kilitle():
        veri = yukle()
        if slug not in veri["dersler"]:
            raise ValueError("Ders bulunamadı: {}".format(slug))
        veri["dersler"][slug]["otomasyon"] = {
            "aktif": bool(aktif),
            "gunler": gun_adlari,
            "saat": saat,
            "gorevAdi": "DersMerkezi_" + slug,
        }
        kaydet(veri)
    return gun_adlari
