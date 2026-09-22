import sys
from pathlib import Path

KOK = Path(__file__).resolve().parent
if str(KOK) not in sys.path:
    sys.path.insert(0, str(KOK))

from merkez import __version__, ayarlar, arayuz, durum, gunluk, indirici, komut, saglik, tamamlama, tasima, zamanlayici

RAPOR_ALANLARI = ("yeni", "guncellenen", "atlanan", "baglam", "dogrulama_hatasi", "donusum_hatasi", "hatalar", "planlanan_bayt")


def _gunler(secenekler):
    if secenekler.her_gun:
        return list(ayarlar.HER_GUN)
    if secenekler.hafta_ici:
        return list(ayarlar.HAFTA_ICI)
    if secenekler.gunler:
        return [parca.strip() for parca in secenekler.gunler.split(",") if parca.strip()]
    return ["PZT"]


def _bos_rapor(anahtar, hata=None):
    rapor = {"anahtar": anahtar, "hedef": "", "yeni": 0, "guncellenen": 0, "atlanan": 0, "baglam": 0,
             "dogrulama_hatasi": 0, "donusum_hatasi": 0, "hatalar": [], "planlanan_bayt": 0}
    if hata:
        rapor["hatalar"].append(hata)
    return rapor


def _toplamlar(raporlar):
    toplam = {"yeni": 0, "guncellenen": 0, "atlanan": 0, "baglam": 0,
              "dogrulama_hatasi": 0, "donusum_hatasi": 0, "planlanan_bayt": 0}
    for rapor in raporlar:
        for alan in toplam:
            toplam[alan] += int(rapor.get(alan) or 0)
    return toplam


def _cek(anahtarlar, otomatik=False, kuru=False, zorla=False, zorla_md=False, ust_boyut=indirici.UST_BOYUT):
    raporlar = []
    hata_var = False
    for anahtar in anahtarlar:
        try:
            rapor = indirici.indir_ders(anahtar, secili_zorunlu=not otomatik, kuru=kuru,
                                        zorla=zorla, zorla_md=zorla_md, ust_boyut=ust_boyut)
        except (indirici.IndirmeHatasi, ValueError, OSError) as hata:
            gunluk.kayit("HATA", "{}: {}".format(anahtar, hata))
            raporlar.append(_bos_rapor(anahtar, str(hata)))
            hata_var = True
            continue
        gunluk.kayit("BILGI", "{}: yeni={} guncellenen={} atlanan={} baglam={} dogrulama_hatasi={} donusum_hatasi={}".format(
            anahtar, rapor["yeni"], rapor["guncellenen"], rapor["atlanan"], rapor["baglam"],
            rapor["dogrulama_hatasi"], rapor["donusum_hatasi"]))
        for mesaj in rapor["hatalar"]:
            gunluk.kayit("UYARI", "{}: {}".format(anahtar, mesaj))
        if rapor["dogrulama_hatasi"] or rapor["donusum_hatasi"]:
            hata_var = True
        kayit = {"anahtar": anahtar, "hedef": rapor.get("hedef", "")}
        for alan in RAPOR_ALANLARI:
            if alan == "hatalar":
                kayit[alan] = list(rapor.get(alan) or [])
            else:
                kayit[alan] = int(rapor.get(alan) or 0)
        raporlar.append(kayit)
    return raporlar, hata_var


def _durum_insan(kayitlar, ayrintili):
    print("Ders sayisi: {}".format(len(kayitlar)))
    for kayit in kayitlar:
        gorev = kayit["otomasyon"]["gorev"]
        if gorev["durum"] == "yok":
            gorev_metni = "yok"
        elif gorev["durum"] == "sorgulanamadı":
            gorev_metni = "sorgulanamadi"
        else:
            gorev_metni = "kayitli ({})".format(gorev["durum"])
        print("{}: gorev={}".format(kayit["kimlik"], gorev_metni))
        if not ayrintili:
            continue
        if gorev.get("sonCalisma"):
            print("  son calisma: {}".format(gorev["sonCalisma"]))
        if gorev.get("sonSonuc") is not None:
            print("  son sonuc: {}".format(zamanlayici.sonuc_metni(gorev["sonSonuc"])))
        if gorev.get("eylem"):
            print("  eylem: {}".format(gorev["eylem"]))
        ozet = kayit.get("durum_dosyasi") or {}
        if ozet.get("hata"):
            print("  durum dosyasi: {}".format(ozet["hata"]))
        else:
            print("  durum dosyasi: {} dosya, {} bayt, guncelleme {}".format(
                ozet.get("dosya", 0), ozet.get("bayt", 0), ozet.get("guncelleme") or "-"))


def _calistir(secenekler, mod, ayristirici):
    if mod is None:
        if not sys.stdout.isatty():
            ayristirici.print_help()
            return 2
        return arayuz.baslat()

    if mod == "surum":
        if secenekler.json:
            komut.json_yaz(komut.kok_json("surum"))
        else:
            print("DersMerkezi {}".format(__version__))
        return 0

    if mod == "listele":
        if secenekler.json:
            komut.json_yaz(komut.kok_json("listele", dersler=durum.kayitlar()))
            return 0
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

    if mod == "ayarlar":
        if secenekler.secili:
            ayarlar.secili_ayarla(secenekler.ders, secenekler.secili == "evet")
            gunluk.kayit("BILGI", "Ayar güncellendi: {} secili={}".format(secenekler.ders, secenekler.secili))
        try:
            kayitlar = ayarlar.gorunum(secenekler.ders)
        except RuntimeError as hata:
            if secenekler.json:
                komut.hata_json_yaz("ayarlar", str(hata))
            if not gunluk.SESSIZ:
                sys.stderr.write("Hata: {}\n".format(hata))
            return 1
        if secenekler.json:
            komut.json_yaz(komut.kok_json("ayarlar", dersler=kayitlar))
            return 0
        if not gunluk.SESSIZ:
            if not kayitlar:
                print("Kayitli ders yok.")
                return 0
            for kayit in kayitlar:
                oto = kayit["otomasyon"]
                if oto["aktif"]:
                    oto_metin = "{} {}".format(",".join(oto["gunler"]), oto["saat"])
                else:
                    oto_metin = "kapali"
                print("{}\t{}\t{}\tdal={}\tdesen={}\tsecili={}\totomasyon={}".format(
                    kayit["kimlik"], kayit["ad"], kayit["depo"], kayit["dal"], kayit["desen"],
                    kayit["secili"], oto_metin))
        return 0

    if mod == "durum":
        kayitlar = durum.kayitlar(ayrintili=bool(secenekler.ayrintili))
        if secenekler.json:
            komut.json_yaz(komut.kok_json("durum", dersler=kayitlar))
            return 0
        _durum_insan(kayitlar, bool(secenekler.ayrintili))
        return 0

    if mod == "ekle":
        kimlik = ayarlar.ders_ekle(secenekler.ad, secenekler.depo, secenekler.dal or "main",
                                   secenekler.desen or "Hafta*.pdf", secenekler.slug)
        gunluk.kayit("BILGI", "Ders eklendi: {}".format(kimlik))
        return 0

    if mod == "sil":
        zamanlayici.ders_sil_guvenli(secenekler.ders)
        gunluk.kayit("BILGI", "Ders silindi: {}".format(secenekler.ders))
        return 0

    if mod == "saglik":
        sonuc = saglik.denetle(ders=secenekler.ders, ag=bool(secenekler.ag), ayrintili=bool(secenekler.ayrintili))
        if secenekler.json:
            komut.json_yaz(komut.kok_json(
                "saglik", genel=sonuc["genel"], kontroller=sonuc["kontroller"],
                sorunlar=sonuc["sorunlar"], uyarilar=sonuc["uyarilar"], kota=sonuc["kota"]))
        else:
            for satir in saglik.satirlar(sonuc):
                print(satir)
        return 1 if sonuc["sorunlar"] else 0

    if mod == "otomasyon_kur":
        gunler = _gunler(secenekler)
        saat = secenekler.saat or "09:00"
        ayarlar.gun_listesi_coz(gunler)
        if not ayarlar.saat_gecerli(saat):
            raise ValueError("Saat SS:DD biciminde olmali")
        ayarlar.ders_getir(secenekler.ders)
        sonuc = zamanlayici.gorev_kur_guvenli(secenekler.ders, gunler, saat)
        gunluk.kayit("BILGI", "Gorev kuruldu: {} {} {}".format(
            sonuc.get("gorev"), sonuc.get("gunler"), sonuc.get("saat")))
        if secenekler.tetikle:
            try:
                tetik = zamanlayici.gorev_tetikle(secenekler.ders)
            except RuntimeError as hata:
                gunluk.kayit("HATA", "Gorev tetiklenemedi: {}".format(hata))
                return 1
            son_log = gunluk.son_satir()
            gunluk.kayit("BILGI", "Tetikleme: {} (durum: {}){}".format(
                tetik["metin"], tetik.get("durum", ""),
                " | son gunluk: " + son_log if son_log else ""))
            if not tetik["basarili"]:
                return 1
        return 0

    if mod == "otomasyon_kaldir":
        try:
            sorgu = zamanlayici.gorev_sorgu(secenekler.ders)
        except RuntimeError as hata:
            gunluk.kayit("HATA", "Gorev sorgulanamadi: {}".format(hata))
            return 1
        if sorgu.get("var") and not zamanlayici.sorgu_bizim(sorgu, secenekler.ders):
            gunluk.kayit("HATA", "Gorev bu kuruluma ait degil, kaldirilmadi: {}".format(secenekler.ders))
            return 1
        zamanlayici.gorev_kaldir(secenekler.ders)
        veri = ayarlar.yukle()
        oto = (veri["dersler"].get(secenekler.ders, {}) or {}).get("otomasyon", {}) or {}
        ayarlar.otomasyon_ayarla(secenekler.ders, oto.get("gunler") or ["PZT"], oto.get("saat", "09:00"), False)
        gunluk.kayit("BILGI", "Gorev kaldirildi: {}".format(secenekler.ders))
        return 0

    if mod == "tasima":
        rapor = tasima.calistir(kuru=bool(secenekler.kuru), onayla=bool(secenekler.onayla),
                                gunler=_gunler(secenekler), saat=secenekler.saat or "09:00")
        return 0 if rapor["ok"] else 1

    if mod == "oto_tamamlama":
        hedef, bayraklar = tamamlama.uret()
        if secenekler.json:
            komut.json_yaz(komut.kok_json(
                "oto-tamamlama", hedef=str(hedef), bayrak_sayisi=len(bayraklar), bayraklar=bayraklar))
        else:
            print("Tamamlama betigi yazildi: {}".format(hedef))
            print("Bayrak sayisi: {}".format(len(bayraklar)))
        return 0

    if mod in ("cek", "otomatik"):
        if secenekler.ders:
            anahtarlar = [secenekler.ders]
        elif secenekler.kuru:
            anahtarlar = ayarlar.secili_dersler_salt()
        else:
            anahtarlar = ayarlar.secili_dersler()
        if not anahtarlar:
            gunluk.kayit("UYARI", "Cekilecek ders yok.")
            if secenekler.json:
                komut.json_yaz(komut.kok_json("cek", dersler=[], toplamlar=_toplamlar([])))
            return 0
        kilit = gunluk.Kilit()
        bekle_ms = int(secenekler.kilit_bekle or 0) * 1000
        if not kilit.al(bekle_ms):
            gunluk.kayit("UYARI", "Baska bir calisma suruyor; bu kosu atlandi.", bekle_ms=0)
            if secenekler.json:
                komut.json_yaz(komut.kok_json("cek", dersler=[], toplamlar=_toplamlar([])))
            return 0
        try:
            raporlar, hata_var = _cek(
                anahtarlar,
                otomatik=bool(secenekler.otomatik),
                kuru=bool(secenekler.kuru),
                zorla=bool(secenekler.zorla),
                zorla_md=bool(secenekler.zorla_md),
                ust_boyut=int(secenekler.sinir or 200) * 1024 * 1024,
            )
        finally:
            kilit.birak()
        if secenekler.json:
            komut.json_yaz(komut.kok_json("cek", dersler=raporlar, toplamlar=_toplamlar(raporlar)))
        return 1 if hata_var else 0

    raise komut.KullanimHatasi("Bilinmeyen mod: {}".format(mod))


def main(argv=None):
    eski_sessiz = gunluk.SESSIZ
    eski_akis = gunluk.KONSOL_AKISI
    eski_log = gunluk.LOG_YOLU
    secenekler = None
    mod = None
    try:
        ayristirici = komut.arguman_ayristirici()
        secenekler = ayristirici.parse_args(argv)
        mod = komut.dogrula(secenekler)
        gunluk.SESSIZ = bool(secenekler.sessiz or secenekler.otomatik)
        gunluk.KONSOL_AKISI = "stderr" if secenekler.json else "stdout"
        if secenekler.log:
            gunluk.log_yolu_ayarla(secenekler.log)
        return _calistir(secenekler, mod, ayristirici)
    except komut.KullanimHatasi as hata:
        sys.stderr.write("Kullanım hatası: {}\n".format(hata))
        return 2
    except ValueError as hata:
        sys.stderr.write("Hata: {}\n".format(hata))
        return 2
    except (RuntimeError, indirici.IndirmeHatasi, OSError) as hata:
        try:
            gunluk.kayit("HATA", str(hata))
        except Exception:
            pass
        if secenekler is not None and secenekler.json:
            komut.hata_json_yaz(mod or "bilinmiyor", str(hata))
            if not gunluk.SESSIZ:
                sys.stderr.write("Hata: {}\n".format(hata))
        elif not gunluk.SESSIZ:
            sys.stderr.write("Hata: {}\n".format(hata))
        return 1
    finally:
        gunluk.SESSIZ = eski_sessiz
        gunluk.KONSOL_AKISI = eski_akis
        gunluk.LOG_YOLU = eski_log


if __name__ == "__main__":
    sys.exit(main())
