import argparse
import sys
from pathlib import Path

KOK = Path(__file__).resolve().parent
if str(KOK) not in sys.path:
    sys.path.insert(0, str(KOK))

from merkez import ayarlar, arayuz, gunluk, indirici, tasima, zamanlayici


def _cek(anahtarlar, otomatik=False):
    hata_var = False
    for anahtar in anahtarlar:
        try:
            rapor = indirici.indir_ders(anahtar, secili_zorunlu=not otomatik)
            gunluk.kayit("BILGI", "{}: yeni={} guncellenen={} atlanan={} baglam={} dogrulama_hatasi={} donusum_hatasi={}".format(
                anahtar, rapor["yeni"], rapor["guncellenen"], rapor["atlanan"], rapor["baglam"],
                rapor["dogrulama_hatasi"], rapor["donusum_hatasi"]))
            for mesaj in rapor["hatalar"]:
                gunluk.kayit("UYARI", "{}: {}".format(anahtar, mesaj))
            if rapor["dogrulama_hatasi"] or rapor["donusum_hatasi"]:
                hata_var = True
        except (indirici.IndirmeHatasi, ValueError, OSError) as hata:
            gunluk.kayit("HATA", "{}: {}".format(anahtar, hata))
            hata_var = True
    return 1 if hata_var else 0


def main(argv=None):
    ayristirici = argparse.ArgumentParser(prog="dersmerkezi", description="DersMerkezi - cok dersli icerik cekme araci")
    ayristirici.add_argument("--listele", action="store_true", help="Kayitli dersleri listeler")
    ayristirici.add_argument("--ekle", action="store_true", help="Yeni ders ekler (--ad ve --depo gerekli)")
    ayristirici.add_argument("--sil", action="store_true", help="Ders kaydini siler (--ders gerekli)")
    ayristirici.add_argument("--cek", action="store_true", help="Isaretli derslerin iceriklerini ceker")
    ayristirici.add_argument("--durum", action="store_true", help="Ders ve gorev durumunu gosterir")
    ayristirici.add_argument("--otomasyon-kur", dest="otomasyon_kur", action="store_true", help="Ders icin haftalik gorev kurar")
    ayristirici.add_argument("--otomasyon-kaldir", dest="otomasyon_kaldir", action="store_true", help="Dersin gorevini kaldirir")
    ayristirici.add_argument("--otomatik", action="store_true", help="Zamanlanmis gorev modu (--cek ile, secili kontrolunu atlar)")
    ayristirici.add_argument("--tasima", action="store_true", help="Eski dosya organizasyonu otomasyonunu guvenli sirayla tasir")
    ayristirici.add_argument("--kuru", action="store_true", help="--tasima icin kuru calisma (kopyalama ve gorev islemi yapmaz)")
    ayristirici.add_argument("--onayla", action="store_true", help="--tasima sonunda eski gorevi kaldirmayi onaylar")
    ayristirici.add_argument("--sessiz", action="store_true", help="Konsol ciktisini kapatir")
    ayristirici.add_argument("--ad", help="Ders adi")
    ayristirici.add_argument("--depo", help="Depo (owner/repo)")
    ayristirici.add_argument("--dal", default="main", help="Dal adi")
    ayristirici.add_argument("--desen", default="Hafta*.pdf", help="Dosya deseni")
    ayristirici.add_argument("--slug", help="Ders kimligi (otomatik uretilir)")
    ayristirici.add_argument("--ders", help="Ders kimligi")
    ayristirici.add_argument("--gunler", default="PZT", help="Virgullu gun listesi (PZT,SAL,...)")
    ayristirici.add_argument("--saat", default="09:00", help="Saat (SS:DD)")
    secenekler = ayristirici.parse_args(argv)

    if secenekler.sessiz or secenekler.otomatik:
        gunluk.SESSIZ = True

    try:
        if secenekler.listele:
            veri = ayarlar.yukle()
            if not veri["dersler"]:
                print("Kayitli ders yok.")
            for kimlik, ders in veri["dersler"].items():
                oto = ders.get("otomasyon", {}) or {}
                if oto.get("aktif"):
                    oto_metin = "{} {}".format(",".join(oto.get("gunler", [])), oto.get("saat", ""))
                else:
                    oto_metin = "kapali"
                print("{}\t{}\t{}\tsecili={}\totomasyon={}".format(
                    kimlik, ders.get("ad", ""), ders.get("depo", ""), ders.get("secili", True), oto_metin))
            return 0

        if secenekler.ekle:
            if not secenekler.ad or not secenekler.depo:
                sys.stderr.write("--ekle icin --ad ve --depo gerekli\n")
                return 2
            kimlik = ayarlar.ders_ekle(secenekler.ad, secenekler.depo, secenekler.dal, secenekler.desen, secenekler.slug)
            gunluk.kayit("BILGI", "Ders eklendi: {}".format(kimlik))
            return 0

        if secenekler.sil:
            if not secenekler.ders:
                sys.stderr.write("--sil icin --ders gerekli\n")
                return 2
            try:
                sorgu = zamanlayici.gorev_sorgu(secenekler.ders)
            except RuntimeError as hata:
                gunluk.kayit("HATA", "Gorev sorgulanamadi: {}".format(hata))
                return 1
            if sorgu.get("var"):
                if not zamanlayici.gorev_bizim(secenekler.ders):
                    gunluk.kayit("HATA", "Gorev bu kuruluma ait degil, ders silinmedi: {}".format(secenekler.ders))
                    return 1
                try:
                    zamanlayici.gorev_kaldir(secenekler.ders)
                except RuntimeError as hata:
                    gunluk.kayit("HATA", "Gorev kaldirilamadi, ders silinmedi: {}".format(hata))
                    return 1
                gunluk.kayit("BILGI", "Gorev kaldirildi: {}".format(secenekler.ders))
            ayarlar.ders_sil(secenekler.ders)
            gunluk.kayit("BILGI", "Ders silindi: {}".format(secenekler.ders))
            return 0

        if secenekler.durum:
            veri = ayarlar.yukle()
            print("Ders sayisi: {}".format(len(veri["dersler"])))
            for kimlik in veri["dersler"]:
                try:
                    sorgu = zamanlayici.gorev_sorgu(kimlik)
                    gorev_durumu = "kayitli ({})".format(sorgu.get("durum", "")) if sorgu.get("var") else "yok"
                except RuntimeError as hata:
                    gorev_durumu = "sorgulanamadi ({})".format(hata)
                print("{}: gorev={}".format(kimlik, gorev_durumu))
            return 0

        if secenekler.otomasyon_kur:
            if not secenekler.ders:
                sys.stderr.write("--otomasyon-kur icin --ders gerekli\n")
                return 2
            gunler = secenekler.gunler.split(",")
            ayarlar.gun_listesi_coz(gunler)
            if not ayarlar.saat_gecerli(secenekler.saat):
                raise ValueError("Saat SS:DD biciminde olmali")
            ayarlar.ders_getir(secenekler.ders)
            sonuc = zamanlayici.gorev_kur_guvenli(secenekler.ders, gunler, secenekler.saat)
            gunluk.kayit("BILGI", "Gorev kuruldu: {} {} {}".format(sonuc.get("gorev"), sonuc.get("gunler"), sonuc.get("saat")))
            return 0

        if secenekler.otomasyon_kaldir:
            if not secenekler.ders:
                sys.stderr.write("--otomasyon-kaldir icin --ders gerekli\n")
                return 2
            try:
                sorgu = zamanlayici.gorev_sorgu(secenekler.ders)
            except RuntimeError as hata:
                gunluk.kayit("HATA", "Gorev sorgulanamadi: {}".format(hata))
                return 1
            if sorgu.get("var") and not zamanlayici.gorev_bizim(secenekler.ders):
                gunluk.kayit("HATA", "Gorev bu kuruluma ait degil, kaldirilmadi: {}".format(secenekler.ders))
                return 1
            zamanlayici.gorev_kaldir(secenekler.ders)
            veri = ayarlar.yukle()
            oto = (veri["dersler"].get(secenekler.ders, {}) or {}).get("otomasyon", {}) or {}
            ayarlar.otomasyon_ayarla(secenekler.ders, oto.get("gunler") or ["PZT"], oto.get("saat", "09:00"), False)
            gunluk.kayit("BILGI", "Gorev kaldirildi: {}".format(secenekler.ders))
            return 0

        if secenekler.tasima:
            rapor = tasima.calistir(kuru=secenekler.kuru, onayla=secenekler.onayla,
                                    gunler=secenekler.gunler.split(","), saat=secenekler.saat)
            return 0 if rapor["ok"] else 1

        if secenekler.cek or secenekler.otomatik:
            if secenekler.ders:
                anahtarlar = [secenekler.ders]
            else:
                anahtarlar = ayarlar.secili_dersler()
            if not anahtarlar:
                gunluk.kayit("UYARI", "Cekilecek ders yok.")
                return 0
            kilit = gunluk.Kilit()
            if not kilit.al():
                gunluk.kayit("UYARI", "Baska bir calisma suruyor; bu kosu atlandi.")
                return 0
            try:
                return _cek(anahtarlar, otomatik=secenekler.otomatik)
            finally:
                kilit.birak()

        if not sys.stdout.isatty():
            ayristirici.print_help()
            return 2
        return arayuz.baslat()
    except ValueError as hata:
        sys.stderr.write("Hata: {}\n".format(hata))
        return 2
    except (RuntimeError, indirici.IndirmeHatasi, OSError) as hata:
        gunluk.kayit("HATA", str(hata))
        if not gunluk.SESSIZ and sys.stderr is not None:
            sys.stderr.write("Hata: {}\n".format(hata))
        return 1


if __name__ == "__main__":
    sys.exit(main())
