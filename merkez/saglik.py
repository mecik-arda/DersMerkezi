import importlib.metadata
import json
import os
import sys

from . import ayarlar, gunluk, indirici, zamanlayici

PAKETLER = ("rich", "requests", "pypdf")
AG_DERS_SINIRI = 10
AYRINTILI_DERS_SINIRI = 20


def _ayarlari_oku():
    yol = ayarlar.AYAR_YOLU
    if not yol.exists():
        return ayarlar.bos_veri(), None
    try:
        veri = json.loads(yol.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None, "okunamadı veya bozuk JSON"
    gecerli, neden = ayarlar.veri_dogrula(veri)
    if not gecerli:
        return None, neden
    return veri, None


def denetle(ders=None, ag=False, ayrintili=False):
    kontroller = []
    sorunlar = []
    uyarilar = []
    kota = {}

    def ekle(seviye, ad, mesaj):
        kontroller.append({"ad": ad, "durum": seviye, "mesaj": mesaj})
        if seviye == "sorun":
            sorunlar.append("{}: {}".format(ad, mesaj))
        elif seviye == "uyari":
            uyarilar.append("{}: {}".format(ad, mesaj))

    ekle("ok", "python", "Python {}".format(sys.version.split()[0]))
    for paket in PAKETLER:
        try:
            surum = importlib.metadata.version(paket)
            ekle("ok", "paket:" + paket, "{} {}".format(paket, surum))
        except importlib.metadata.PackageNotFoundError:
            ekle("sorun", "paket:" + paket, "{} kurulu değil".format(paket))

    veri, ayar_hatasi = _ayarlari_oku()
    if ayar_hatasi:
        ekle("sorun", "ayarlar.json", ayar_hatasi)
    else:
        ekle("ok", "ayarlar.json", "şema geçerli ({} ders)".format(len(veri["dersler"])))
        for kimlik, kayit in veri["dersler"].items():
            sorun = ayarlar.ders_dogrula(kimlik, kayit)
            if sorun:
                ekle("sorun", "ders:" + kimlik, sorun)

    if gunluk.kilit_dolu():
        ekle("uyari", "kilit", "başka bir çalışma sürüyor")
    else:
        ekle("ok", "kilit", "boş")

    log_yolu = gunluk.LOG_YOLU
    if log_yolu.exists():
        if os.access(str(log_yolu), os.W_OK):
            ekle("ok", "günlük", "{} yazılabilir".format(log_yolu.name))
        else:
            ekle("sorun", "günlük", "{} yazılamaz".format(log_yolu.name))
    elif os.access(str(log_yolu.parent), os.W_OK):
        ekle("ok", "günlük", "dosya yok; dizin yazılabilir")
    else:
        ekle("sorun", "günlük", "dizin yazılamaz: {}".format(log_yolu.parent))

    if not ayar_hatasi:
        for kimlik in veri["dersler"]:
            yol = ayarlar.KOK / "dersler" / kimlik / "indirilenler.json"
            if not yol.exists():
                ekle("uyari", "durum:" + kimlik, "indirilenler.json yok")
                continue
            try:
                durum_verisi = json.loads(yol.read_text(encoding="utf-8"))
                dosyalar = durum_verisi.get("dosyalar")
                if not isinstance(dosyalar, dict):
                    raise ValueError("dosyalar bölümü geçersiz")
                ekle("ok", "durum:" + kimlik, "{} dosya".format(len(dosyalar)))
            except (OSError, ValueError) as hata:
                ekle("sorun", "durum:" + kimlik, "okunamadı: {}".format(hata))

    hedef_dersler = []
    if ders:
        if not ayar_hatasi and ders not in veri["dersler"]:
            ekle("sorun", "ders:" + ders, "kayıtlı değil")
        else:
            hedef_dersler = [ders]
    elif ayrintili and not ayar_hatasi:
        hedef_dersler = sorted(veri["dersler"])[:AYRINTILI_DERS_SINIRI]
        if len(veri["dersler"]) > AYRINTILI_DERS_SINIRI:
            ekle("uyari", "görev", "{} dersin yalnızca ilk {} tanesi sorgulandı".format(
                len(veri["dersler"]), AYRINTILI_DERS_SINIRI))
    for kimlik in hedef_dersler:
        try:
            sorgu = zamanlayici.gorev_sorgu(kimlik)
        except RuntimeError as hata:
            ekle("sorun", "görev:" + kimlik, "sorgulanamadı: {}".format(hata))
            continue
        if not sorgu.get("var"):
            ekle("ok", "görev:" + kimlik, "kurulu değil")
        elif not zamanlayici.sorgu_bizim(sorgu, kimlik):
            ekle("sorun", "görev:" + kimlik, "görev bu kuruluma ait değil")
        else:
            ekle("ok", "görev:" + kimlik, "{} ({})".format(
                sorgu.get("durum", ""), zamanlayici.sonuc_metni(sorgu.get("sonSonuc"))))

    ag_dersler = []
    if ag and not ayar_hatasi:
        tumu = sorted(veri["dersler"])
        ag_dersler = tumu[:AG_DERS_SINIRI]
        if len(tumu) > AG_DERS_SINIRI:
            ekle("uyari", "ağ", "{} dersin yalnızca ilk {} tanesi kontrol edildi".format(len(tumu), AG_DERS_SINIRI))
    elif ders and not ayar_hatasi and ders in veri["dersler"]:
        ag_dersler = [ders]
    for kimlik in ag_dersler:
        kayit = veri["dersler"][kimlik]
        try:
            _liste, kota_bilgi = indirici.depo_listele(
                kayit["depo"], kayit.get("dal", "main"), indirici.token_al(), meta=True)
            if not kota:
                kota = kota_bilgi
            ekle("ok", "depo:" + kimlik, "{} erişilebilir".format(kayit["depo"]))
        except indirici.IndirmeHatasi as hata:
            ekle("sorun", "depo:" + kimlik, str(hata))
    if ag_dersler:
        ekle("ok", "kimlik", "GITHUB_TOKEN tanımlı" if indirici.token_al() else "GITHUB_TOKEN tanımlı değil")

    genel = "sorun var" if sorunlar else "sorun yok"
    return {"genel": genel, "kontroller": kontroller, "sorunlar": sorunlar, "uyarilar": uyarilar, "kota": kota}


def satirlar(sonuc):
    isaretler = {"ok": "[OK]", "uyari": "[UYARI]", "sorun": "[SORUN]"}
    cikti = []
    for kontrol in sonuc["kontroller"]:
        cikti.append("{} {}: {}".format(isaretler.get(kontrol["durum"], "[?]"), kontrol["ad"], kontrol["mesaj"]))
    if sonuc["kota"]:
        cikti.append("Kota: limit={} kalan={} sifirlama={}".format(
            sonuc["kota"].get("limit"), sonuc["kota"].get("kalan"), sonuc["kota"].get("sifirla")))
    cikti.append("Sonuç: {} (sorun={}, uyarı={})".format(
        sonuc["genel"], len(sonuc["sorunlar"]), len(sonuc["uyarilar"])))
    return cikti
