import argparse
import json
import re
import sys

from . import __version__

JSON_SURUM = 1

MOD_ADLARI = {
    "listele": "--listele",
    "ekle": "--ekle",
    "sil": "--sil",
    "cek": "--cek",
    "durum": "--durum",
    "saglik": "--saglik",
    "otomasyon_kur": "--otomasyon-kur",
    "otomasyon_kaldir": "--otomasyon-kaldir",
    "tasima": "--tasima",
    "surum": "--surum",
    "oto_tamamlama": "--oto-tamamlama",
    "ayarlar": "--ayarlar",
    "otomatik": "--otomatik",
}

TUM_MODLAR = set(MOD_ADLARI) - {"otomatik"}

BAYRAK_ADLARI = {
    "ad": "--ad",
    "depo": "--depo",
    "dal": "--dal",
    "desen": "--desen",
    "slug": "--slug",
    "ders": "--ders",
    "gunler": "--gunler",
    "saat": "--saat",
    "kuru": "--kuru",
    "onayla": "--onayla",
    "sessiz": "--sessiz",
    "json": "--json",
    "ayrintili": "--ayrintili",
    "ag": "--ag",
    "zorla": "--zorla",
    "zorla_md": "--zorla-md",
    "kilit_bekle": "--kilit-bekle",
    "sinir": "--sinir",
    "her_gun": "--her-gun",
    "hafta_ici": "--hafta-ici",
    "tetikle": "--tetikle",
    "log": "--log",
    "secili": "--secili",
}

IZINLI = {
    "ad": {"ekle"},
    "depo": {"ekle"},
    "dal": {"ekle"},
    "desen": {"ekle"},
    "slug": {"ekle"},
    "ders": {"cek", "sil", "saglik", "otomasyon_kur", "otomasyon_kaldir", "otomatik", "ayarlar"},
    "gunler": {"otomasyon_kur"},
    "saat": {"otomasyon_kur"},
    "kuru": {"tasima", "cek"},
    "onayla": {"tasima", "sil"},
    "sessiz": (set(TUM_MODLAR) | {"otomatik"}) - {"surum"},
    "json": {"durum", "listele", "cek", "saglik", "surum", "oto_tamamlama", "ayarlar"},
    "ayrintili": {"durum", "saglik"},
    "ag": {"saglik"},
    "zorla": {"cek", "otomatik"},
    "zorla_md": {"cek", "otomatik"},
    "kilit_bekle": {"cek", "otomatik"},
    "sinir": {"cek", "otomatik"},
    "her_gun": {"otomasyon_kur"},
    "hafta_ici": {"otomasyon_kur"},
    "tetikle": {"otomasyon_kur"},
    "log": (set(TUM_MODLAR) | {"otomatik"}) - {"surum"},
    "secili": {"ayarlar"},
}


class KullanimHatasi(Exception):
    pass


def _cevir(mesaj):
    kaliplar = (
        (r"^unrecognized arguments: (.+)$", "Bilinmeyen parametre: {0}"),
        (r"^argument (--[\w-]+): expected one argument$", "{0} için değer gerekli"),
        (r"^argument (--[\w-]+): invalid int value: '(.+)'$", "{0} için geçersiz tamsayı: {1}"),
        (r"^argument (--[\w-]+): invalid choice: '(.+)'.*$", "{0} için geçersiz değer: {1}"),
        (r"^ambiguous option: (.+)$", "Belirsiz parametre: {0}"),
        (r"^expected one argument$", "Bir değer gerekli"),
    )
    for kalip, sablon in kaliplar:
        eslesme = re.match(kalip, mesaj)
        if eslesme:
            return sablon.format(*[parca.strip() for parca in eslesme.groups()])
    return "Komut satırı kullanımı geçersiz"


class TurkceParser(argparse.ArgumentParser):
    def error(self, mesaj):
        sys.stderr.write("Kullanım hatası: {}\n".format(_cevir(mesaj)))
        self.print_usage(sys.stderr)
        raise SystemExit(2)


def arguman_ayristirici():
    ayristirici = TurkceParser(prog="dersmerkezi", description="DersMerkezi - cok dersli icerik cekme araci")
    ayristirici.add_argument("--listele", action="store_true", help="Kayitli dersleri listeler")
    ayristirici.add_argument("--ekle", action="store_true", help="Yeni ders ekler (--ad ve --depo gerekli)")
    ayristirici.add_argument("--sil", action="store_true", help="Ders kaydini siler (--ders ve --onayla gerekli)")
    ayristirici.add_argument("--cek", action="store_true", help="Isaretli derslerin iceriklerini ceker")
    ayristirici.add_argument("--durum", action="store_true", help="Ders ve gorev durumunu gosterir")
    ayristirici.add_argument("--ayarlar", action="store_true", help="Ders ayarlarini gosterir veya secim durumunu degistirir")
    ayristirici.add_argument("--saglik", action="store_true", help="Ortam ve erisim on kontrolu yapar")
    ayristirici.add_argument("--otomasyon-kur", dest="otomasyon_kur", action="store_true", help="Ders icin haftalik gorev kurar")
    ayristirici.add_argument("--otomasyon-kaldir", dest="otomasyon_kaldir", action="store_true", help="Dersin gorevini kaldirir")
    ayristirici.add_argument("--otomatik", action="store_true", help="Zamanlanmis gorev modu (tek basina veya --cek ile)")
    ayristirici.add_argument("--tasima", action="store_true", help="Eski dosya organizasyonu otomasyonunu guvenli sirayla tasir")
    ayristirici.add_argument("--surum", action="store_true", help="Surum bilgisini yazar")
    ayristirici.add_argument("--oto-tamamlama", dest="oto_tamamlama", action="store_true", help="PowerShell tamamlama betigi uretir")
    ayristirici.add_argument("--kuru", action="store_true", help="Cekme veya tasima icin kuru calisma")
    ayristirici.add_argument("--onayla", action="store_true", help="--sil ve --tasima icin acik onay")
    ayristirici.add_argument("--sessiz", action="store_true", help="Konsol ciktisini kapatir")
    ayristirici.add_argument("--json", action="store_true", help="Ciktiyi tek JSON nesnesi olarak yazar")
    ayristirici.add_argument("--ayrintili", action="store_true", help="Ayrintili cikti (--durum ve --saglik)")
    ayristirici.add_argument("--ag", action="store_true", help="--saglik icin ag kontrolu (ilk 10 ders)")
    ayristirici.add_argument("--zorla", action="store_true", help="Indirmeyi ve baglami zorla yeniler")
    ayristirici.add_argument("--zorla-md", dest="zorla_md", action="store_true", help="Yalnizca Markdown baglamini zorla yeniler")
    ayristirici.add_argument("--kilit-bekle", dest="kilit_bekle", type=int, metavar="SN", help="Kilit icin en fazla SN saniye bekler (0-3600)")
    ayristirici.add_argument("--sinir", type=int, metavar="MB", help="Indirme boyut siniri MB (1-200, varsayilan 200)")
    ayristirici.add_argument("--her-gun", dest="her_gun", action="store_true", help="Otomasyonu her gun calistirir")
    ayristirici.add_argument("--hafta-ici", dest="hafta_ici", action="store_true", help="Otomasyonu hafta ici gunlerde calistirir")
    ayristirici.add_argument("--tetikle", action="store_true", help="Kurulan gorevi hemen bir kez calistirir")
    ayristirici.add_argument("--log", metavar="YOL", help="Alternatif gunluk dosyasi (proje koku icinde)")
    ayristirici.add_argument("--ad", help="Ders adi")
    ayristirici.add_argument("--depo", help="Depo (owner/repo)")
    ayristirici.add_argument("--dal", default=None, help="Dal adi (varsayilan main)")
    ayristirici.add_argument("--desen", default=None, help="Dosya deseni (varsayilan Hafta*.pdf)")
    ayristirici.add_argument("--slug", help="Ders kimligi (otomatik uretilir)")
    ayristirici.add_argument("--ders", help="Ders kimligi")
    ayristirici.add_argument("--secili", choices=["evet", "hayir"], help="--ayarlar ile cekilme isaretini degistirir (evet/hayir)")
    ayristirici.add_argument("--gunler", default=None, help="Virgullu gun listesi (PZT,SAL,...)")
    ayristirici.add_argument("--saat", default=None, help="Saat (SS:DD)")
    return ayristirici


def _verildi(secenekler, ad):
    deger = getattr(secenekler, ad)
    if isinstance(deger, bool):
        return deger
    return deger is not None


def _verilen_bayraklar(secenekler):
    return [BAYRAK_ADLARI[ad] for ad in BAYRAK_ADLARI if _verildi(secenekler, ad)]


def _mod_belirle(secenekler):
    modlar = [ad for ad in TUM_MODLAR if getattr(secenekler, ad)]
    if len(modlar) > 1:
        raise KullanimHatasi("Aynı anda yalnızca bir mod kullanılabilir: {}".format(
            ", ".join(MOD_ADLARI[ad] for ad in modlar)))
    if modlar:
        mod = modlar[0]
        if secenekler.otomatik and mod != "cek":
            raise KullanimHatasi("--otomatik yalnızca tek başına veya --cek ile kullanılabilir")
        return mod
    if secenekler.otomatik:
        return "otomatik"
    return None


def _bayrak_mod_kontrol(secenekler, mod):
    if mod is None:
        verilen = _verilen_bayraklar(secenekler)
        if verilen:
            raise KullanimHatasi("Bu seçenekler bir mod ile birlikte kullanılmalıdır: {}".format(", ".join(verilen)))
        return
    for ad, izinli in IZINLI.items():
        if _verildi(secenekler, ad) and mod not in izinli:
            raise KullanimHatasi("{} {} ile birlikte kullanılamaz".format(BAYRAK_ADLARI[ad], MOD_ADLARI[mod]))


def _ozel_kontroller(secenekler, mod):
    if mod == "ekle":
        if not secenekler.ad or not secenekler.depo:
            raise KullanimHatasi("--ekle için --ad ve --depo zorunludur")
    if mod == "sil":
        if not secenekler.ders:
            raise KullanimHatasi("--sil için --ders zorunludur")
        if not secenekler.onayla:
            raise KullanimHatasi("--sil yalnızca --onayla ile çalışır; silme geri alınamaz")
    if mod in ("otomasyon_kur", "otomasyon_kaldir") and not secenekler.ders:
        raise KullanimHatasi("{} için --ders zorunludur".format(MOD_ADLARI[mod]))
    if mod == "ayarlar" and secenekler.secili and not secenekler.ders:
        raise KullanimHatasi("--secili için --ders zorunludur")
    if secenekler.kuru and secenekler.onayla:
        raise KullanimHatasi("--kuru ile --onayla birlikte kullanılamaz")
    if secenekler.ag and secenekler.ders:
        raise KullanimHatasi("--ag ile --ders birlikte kullanılamaz")
    if secenekler.her_gun and secenekler.hafta_ici:
        raise KullanimHatasi("--her-gun ile --hafta-ici birlikte kullanılamaz")
    if (secenekler.her_gun or secenekler.hafta_ici) and secenekler.gunler:
        raise KullanimHatasi("--her-gun/--hafta-ici ile --gunler birlikte kullanılamaz")
    if secenekler.json and secenekler.ayrintili:
        raise KullanimHatasi("--json ile --ayrintili birlikte kullanılamaz")
    if secenekler.kilit_bekle is not None and not 0 <= secenekler.kilit_bekle <= 3600:
        raise KullanimHatasi("--kilit-bekle 0-3600 araliginda olmali")
    if secenekler.sinir is not None and not 1 <= secenekler.sinir <= 200:
        raise KullanimHatasi("--sinir 1-200 araliginda olmali (ust sinir degistirilemez)")


def dogrula(secenekler):
    mod = _mod_belirle(secenekler)
    _bayrak_mod_kontrol(secenekler, mod)
    _ozel_kontroller(secenekler, mod)
    return mod


def bayrak_listesi():
    bayraklar = set()
    for eylem in arguman_ayristirici()._actions:
        for secenek in eylem.option_strings:
            if secenek.startswith("--"):
                bayraklar.add(secenek)
    return sorted(bayraklar)


def json_metni(veri):
    return json.dumps(veri, ensure_ascii=False, indent=2)


def _yaz(akis, metin):
    try:
        if akis is None:
            return
        if akis.isatty():
            akis.write(metin)
            akis.flush()
        else:
            akis.buffer.write(metin.encode("utf-8"))
            akis.buffer.flush()
    except Exception:
        try:
            akis.write(metin.encode("ascii", "replace").decode("ascii"))
        except Exception:
            pass


def kok_json(komut_adi, **alanlar):
    veri = {"json_surum": JSON_SURUM, "komut": komut_adi, "uygulama_surum": __version__}
    veri.update(alanlar)
    return veri


def json_yaz(veri):
    _yaz(sys.stdout, json_metni(veri) + "\n")


def hata_json_yaz(komut_adi, mesaj):
    veri = {"json_surum": JSON_SURUM, "komut": komut_adi, "hata": {"sinif": "calisma", "mesaj": mesaj}}
    _yaz(sys.stderr, json_metni(veri) + "\n")
