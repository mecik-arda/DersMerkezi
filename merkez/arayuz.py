import msvcrt

from rich.console import Console
from rich.markup import escape
from rich.panel import Panel
from rich.progress import BarColumn, Progress, SpinnerColumn, TextColumn, TimeElapsedColumn
from rich.prompt import Confirm, Prompt
from rich.table import Table

from . import __version__, ayarlar, durum, gunluk, indirici, saglik, zamanlayici

KONSOL = Console()

GUN_ETIKET = [("PZT", "Pazartesi"), ("SAL", "Sali"), ("CAR", "Carsamba"), ("PER", "Persembe"),
              ("CUM", "Cuma"), ("CMT", "Cumartesi"), ("PAZ", "Pazar")]


def _tus():
    olay = msvcrt.getwch()
    if olay in ("\x00", "\xe0"):
        ikinci = msvcrt.getwch()
        return {"H": "yukari", "P": "asagi", "K": "geri", "M": "ileri"}.get(ikinci, "yok")
    if olay == "\r":
        return "enter"
    if olay == " ":
        return "bosluk"
    if olay == "\x1b":
        return "cikis"
    if olay == "\x03":
        raise KeyboardInterrupt
    return olay.lower()


def _bekle_enter():
    while True:
        if _tus() == "enter":
            return


def _secim(baslik, secenekler, aciklama=None, ust=None):
    imlec = 0
    KONSOL.show_cursor(False)
    try:
        while True:
            KONSOL.clear()
            if ust is not None:
                KONSOL.print(ust)
            KONSOL.print(Panel.fit("[bold]{}[/bold]".format(baslik), border_style="cyan"))
            if aciklama:
                KONSOL.print("[dim]{}[/dim]".format(aciklama))
            KONSOL.print()
            for sira, secenek in enumerate(secenekler):
                im = "[bold green]>[/bold green] " if sira == imlec else "  "
                KONSOL.print(im + secenek)
            olay = _tus()
            if olay == "yukari":
                imlec = (imlec - 1) % len(secenekler)
            elif olay == "asagi":
                imlec = (imlec + 1) % len(secenekler)
            elif olay == "enter":
                return imlec
            elif olay == "cikis":
                return None
    finally:
        KONSOL.show_cursor(True)


def _coklu_secim(baslik, ogeler, secili_kume):
    imlec = 0
    secili = set(secili_kume)
    KONSOL.show_cursor(False)
    try:
        while True:
            KONSOL.clear()
            KONSOL.print(Panel.fit("[bold]{}[/bold]".format(baslik), border_style="cyan"))
            KONSOL.print("[dim]Bosluk: isaretle, Enter: kaydet, ESC: vazgec[/dim]\n")
            for sira, (kimlik, etiket) in enumerate(ogeler):
                im = "[bold green]>[/bold green] " if sira == imlec else "  "
                kutu = "[green][x][/green]" if kimlik in secili else "[ ]"
                KONSOL.print("{} {} {}".format(im, kutu, etiket))
            olay = _tus()
            if olay == "yukari":
                imlec = (imlec - 1) % len(ogeler)
            elif olay == "asagi":
                imlec = (imlec + 1) % len(ogeler)
            elif olay == "bosluk":
                kimlik = ogeler[imlec][0]
                if kimlik in secili:
                    secili.discard(kimlik)
                else:
                    secili.add(kimlik)
            elif olay == "enter":
                return secili
            elif olay == "cikis":
                return None
    finally:
        KONSOL.show_cursor(True)


def _cek_ekrani(anahtarlar, kuru=False, zorla=False, zorla_md=False, kilit=None):
    if kilit is None:
        kilit = gunluk.Kilit()
        if not kilit.al():
            KONSOL.print("[yellow]Baska bir calisma suruyor; cekme atlandi.[/yellow]")
            _bekle_enter()
            return
    KONSOL.show_cursor(False)
    try:
        KONSOL.clear()
        baslik = "Ders icerikleri onizleniyor (kuru calisma)" if kuru else "Ders icerikleri cekiliyor"
        KONSOL.print(Panel.fit("[bold]{}[/bold]".format(baslik), border_style="cyan"))
        for anahtar in anahtarlar:
            with Progress(SpinnerColumn(), TextColumn("[bold]{task.description}"), BarColumn(bar_width=None),
                          TextColumn("{task.percentage:>3.0f}%"), TimeElapsedColumn(), console=KONSOL) as ilerleme:
                gorev = ilerleme.add_task(anahtar, total=100)

                def geri_bildirim(asama, etiket, okunan=0, toplam=0, _g=gorev, _i=ilerleme, _a=anahtar):
                    if asama == "liste":
                        _i.update(_g, description="{}: depo listeleniyor".format(escape(_a)), completed=2)
                    elif asama == "indir" and toplam:
                        _i.update(_g, description="{}: indiriliyor {}".format(escape(_a), escape(str(etiket))),
                                  completed=min(99.0, okunan / toplam * 100.0))
                    elif asama == "donustur":
                        _i.update(_g, description="{}: baglam uretiliyor {}".format(escape(_a), escape(str(etiket))),
                                  completed=99)

                try:
                    rapor = indirici.indir_ders(anahtar, ilerleme=geri_bildirim, kuru=kuru, zorla=zorla, zorla_md=zorla_md)
                    ilerleme.update(gorev, completed=100, description="{}: tamam (yeni={} guncel={} atlanan={} baglam={} zayif={} hata={})".format(
                        escape(anahtar), rapor["yeni"], rapor["guncellenen"], rapor["atlanan"], rapor["baglam"],
                        rapor.get("zayif_dogrulama", 0), rapor["dogrulama_hatasi"] + rapor["donusum_hatasi"]))
                    if kuru and rapor.get("planlanan_bayt"):
                        KONSOL.print("  [cyan]- indirilecek toplam: {} bayt[/cyan]".format(rapor["planlanan_bayt"]))
                    for hata in rapor["hatalar"]:
                        KONSOL.print("  [yellow]- {}[/yellow]".format(escape(str(hata))))
                    for uyari in rapor.get("uyarilar", []):
                        KONSOL.print("  [yellow]- {}[/yellow]".format(escape(str(uyari))))
                except (indirici.IndirmeHatasi, RuntimeError, ValueError, OSError) as hata:
                    ilerleme.update(gorev, completed=100, description="{}: HATA".format(escape(anahtar)))
                    KONSOL.print("  [red]{}: {}[/red]".format(escape(anahtar), escape(str(hata))))
        KONSOL.print()
        KONSOL.print("[bold green]Islem tamamlandi.[/bold green]")
        _bekle_enter()
    finally:
        KONSOL.show_cursor(True)
        kilit.birak()


def _cek_menu():
    veri = ayarlar.yukle()
    secililer = [k for k, d in veri["dersler"].items() if d.get("secili", True)]
    if not secililer:
        KONSOL.print("[yellow]Cekilecek ders yok. Ayarlar menusunden isaretleyin.[/yellow]")
        _bekle_enter()
        return
    secim = _secim("Dersleri Cek", ["Cekmeyi baslat", "Onizleme (kuru calisma)", "Geri"],
                   "{} ders secili".format(len(secililer)))
    if secim is None or secim == 2:
        return
    kuru = secim == 1
    zorla = False
    zorla_md = False
    if not kuru:
        yenileme = _secim("Yenileme", ["Normal (gerekirse)", "Zorla yeniden indir", "Yalniz baglami yenile", "Geri"])
        if yenileme is None or yenileme == 3:
            return
        zorla = yenileme == 1
        zorla_md = yenileme == 2
    kilit = gunluk.Kilit()
    if not kilit.al():
        if Confirm.ask("Baska bir calisma suruyor. 10 sn beklensin mi?", default=False):
            if not kilit.al(10000):
                KONSOL.print("[yellow]Kilit alinamadi; cekme atlandi.[/yellow]")
                _bekle_enter()
                return
        else:
            KONSOL.print("[yellow]Baska bir calisma suruyor; cekme atlandi.[/yellow]")
            _bekle_enter()
            return
    _cek_ekrani(secililer, kuru=kuru, zorla=zorla, zorla_md=zorla_md, kilit=kilit)


def _ders_tablosu(veri):
    tablo = Table(title="Dersler")
    tablo.add_column("Kimlik")
    tablo.add_column("Ad")
    tablo.add_column("Kaynak")
    tablo.add_column("Depo")
    tablo.add_column("Cekilecek")
    tablo.add_column("Otomasyon")
    for kimlik, ders in veri["dersler"].items():
        oto = ders.get("otomasyon", {}) or {}
        if oto.get("aktif"):
            oto_metin = "{} {}".format(",".join(oto.get("gunler", [])), oto.get("saat", ""))
        else:
            oto_metin = "kapali"
        kaynak = ayarlar.kaynak_coz(ders)
        depo = ayarlar.teams_ozeti(ders.get("teams")) if kaynak == "teams" else str(ders.get("depo", ""))
        tablo.add_row(escape(str(kimlik)), escape(str(ders.get("ad", ""))), escape(kaynak), escape(depo or ""),
                      "evet" if ders.get("secili", True) else "hayir", escape(oto_metin))
    return tablo


def _ders_ekle_ekrani():
    KONSOL.clear()
    try:
        kaynak = Prompt.ask("Kaynak (github/teams)", choices=["github", "teams"], default="github")
        ad = Prompt.ask("Ders adi")
        depo = None
        dal = "main"
        desen = "Hafta*.pdf"
        teams_kaydi = None
        zayif_dogrulama = False
        if kaynak == "github":
            depo = Prompt.ask("Depo (owner/repo)")
            dal = Prompt.ask("Dal", default="main")
            desen = Prompt.ask("Dosya deseni", default="Hafta*.pdf")
        else:
            teams_kaydi = {
                "driveId": Prompt.ask("Teams drive kimligi"),
                "itemId": Prompt.ask("Teams klasor item kimligi"),
            }
            tenant = Prompt.ask("Teams tenant kimligi (bos birakilabilir)", default="")
            if tenant:
                teams_kaydi["tenantId"] = tenant
            desen = Prompt.ask("Dosya deseni", default="Hafta*.pdf")
            zayif_dogrulama = Confirm.ask(
                "Risk uyarisi: saglayici hash'i yoksa zayif dogrulamaya izin verilsin mi?", default=False)
        kimlik = ayarlar.ders_ekle(ad, depo, dal, desen, kaynak=kaynak, teams=teams_kaydi,
                                   zayif_dogrulama=zayif_dogrulama)
        KONSOL.print("[green]Eklendi: {}[/green]".format(escape(kimlik)))
    except (ValueError, RuntimeError, OSError) as hata:
        KONSOL.print("[red]{}[/red]".format(escape(str(hata))))
    _bekle_enter()


def _ders_sil_ekrani(veri):
    if not veri["dersler"]:
        KONSOL.print("[yellow]Kayitli ders yok.[/yellow]")
        _bekle_enter()
        return
    ogeler = [(k, "{} ({})".format(escape(str(d.get("ad", k))), k)) for k, d in veri["dersler"].items()]
    secim = _secim("Silinecek dersi sec", [etiket for _, etiket in ogeler] + ["Geri"])
    if secim is None or secim == len(ogeler):
        return
    kimlik = ogeler[secim][0]
    if Confirm.ask("'{}' kaydi silinsin mi? (indirilen dosyalar korunur)".format(kimlik), default=False):
        try:
            zamanlayici.ders_sil_guvenli(kimlik)
            KONSOL.print("[green]Silindi: {}[/green]".format(escape(kimlik)))
        except (ValueError, RuntimeError, OSError) as hata:
            KONSOL.print("[red]{}[/red]".format(escape(str(hata))))
        _bekle_enter()


def dersler_ekrani():
    while True:
        veri = ayarlar.yukle()
        tablo = _ders_tablosu(veri)
        secim = _secim("Dersler", ["Yeni ders ekle", "Ders cikar", "Geri"], ust=tablo)
        if secim is None or secim == 2:
            return
        if secim == 0:
            _ders_ekle_ekrani()
        else:
            _ders_sil_ekrani(veri)


def ayarlar_ekrani():
    try:
        kayitlar = ayarlar.gorunum()
    except RuntimeError as hata:
        KONSOL.print("[red]{}[/red]".format(escape(str(hata))))
        _bekle_enter()
        return
    if not kayitlar:
        KONSOL.print("[yellow]Once ders ekleyin.[/yellow]")
        _bekle_enter()
        return
    ogeler = [(k["kimlik"], "{} ({})".format(escape(k["ad"] or k["kimlik"]), escape(k["kimlik"]))) for k in kayitlar]
    secili = {k["kimlik"] for k in kayitlar if k["secili"]}
    sonuc = _coklu_secim("Cekilecek dersleri isaretle", ogeler, secili)
    if sonuc is None:
        return
    try:
        for kayit in kayitlar:
            ayarlar.isaretle(kayit["kimlik"], kayit["kimlik"] in sonuc)
        KONSOL.print("[green]Kaydedildi.[/green]")
    except (ValueError, RuntimeError, OSError) as hata:
        KONSOL.print("[red]{}[/red]".format(escape(str(hata))))
    _bekle_enter()


def _otomasyon_detay(kimlik):
    while True:
        veri = ayarlar.yukle()
        ders = veri["dersler"].get(kimlik, {})
        oto = ders.get("otomasyon", {}) or {}
        durum = "kapali"
        try:
            sorgu = zamanlayici.gorev_sorgu(kimlik)
            if sorgu.get("var"):
                durum = "kayitli ({})".format(sorgu.get("durum", ""))
        except RuntimeError:
            durum = "sorgulanamadi"
        ust = "[bold]{}[/bold]\nTetik: {} {}\nGorev durumu: {}".format(
            escape(str(ders.get("ad", kimlik))),
            escape(",".join(str(gun) for gun in oto.get("gunler", []))) or "-",
            escape(str(oto.get("saat", ""))),
            escape(str(durum)))
        secim = _secim("Otomasyon", ["Kur / guncelle", "Kur ve hemen dene", "Kaldir", "Geri"], ust=ust)
        if secim is None or secim == 3:
            return
        if secim in (0, 1):
            gun_secim = _secim("Gun secimi", ["Gunleri tek tek sec", "Tumu (her gun)", "Hafta ici (PZT-CUM)", "Geri"])
            if gun_secim is None or gun_secim == 3:
                continue
            if gun_secim == 1:
                secili_gunler = set(ayarlar.HER_GUN)
            elif gun_secim == 2:
                secili_gunler = set(ayarlar.HAFTA_ICI)
            else:
                ogeler = GUN_ETIKET
                mevcut = set(oto.get("gunler", []))
                mevcut_kisa = {k for k, ing in ayarlar.GUNLER.items() if ing in mevcut}
                secili_gunler = _coklu_secim("Haftalik gunleri sec", [(k, tam) for k, tam in ogeler], mevcut_kisa)
                if not secili_gunler:
                    continue
            try:
                saat = Prompt.ask("Saat (SS:DD)", default=oto.get("saat", "09:00"))
                ayarlar.gun_listesi_coz(sorted(secili_gunler))
                if not ayarlar.saat_gecerli(saat):
                    raise ValueError("Saat SS:DD biciminde olmali")
                sonuc = zamanlayici.gorev_kur_guvenli(kimlik, sorted(secili_gunler), saat)
                KONSOL.print("[green]Gorev kuruldu: {} {}[/green]".format(
                    escape(",".join(str(gun) for gun in sonuc.get("gunler", []))), escape(str(sonuc.get("saat", "")))))
                if secim == 1:
                    try:
                        tetik = zamanlayici.gorev_tetikle(kimlik)
                        renk = "green" if tetik["basarili"] else "red"
                        KONSOL.print("[{}]Tetikleme: {} (durum: {})[/{}]".format(
                            renk, escape(tetik["metin"]), escape(str(tetik.get("durum", ""))), renk))
                    except RuntimeError as hata:
                        KONSOL.print("[red]Tetikleme hatasi: {}[/red]".format(escape(str(hata))))
            except (ValueError, RuntimeError, OSError) as hata:
                KONSOL.print("[red]{}[/red]".format(escape(str(hata))))
            _bekle_enter()
        else:
            try:
                sorgu = zamanlayici.gorev_sorgu(kimlik)
                if sorgu.get("var") and not zamanlayici.gorev_bizim(kimlik):
                    raise RuntimeError("Gorev bu kuruluma ait degil; kaldirilmadi")
                zamanlayici.gorev_kaldir(kimlik)
                veri = ayarlar.yukle()
                oto = veri["dersler"].get(kimlik, {}).get("otomasyon", {}) or {}
                ayarlar.otomasyon_ayarla(kimlik, oto.get("gunler") or ["PZT"], oto.get("saat", "09:00"), False)
                KONSOL.print("[green]Gorev kaldirildi.[/green]")
            except (ValueError, RuntimeError, OSError) as hata:
                KONSOL.print("[red]{}[/red]".format(escape(str(hata))))
            _bekle_enter()


def otomasyon_ekrani():
    while True:
        veri = ayarlar.yukle()
        if not veri["dersler"]:
            KONSOL.print("[yellow]Once ders ekleyin.[/yellow]")
            _bekle_enter()
            return
        etiketler = ["{} ({})".format(escape(str(d.get("ad", k))), k) for k, d in veri["dersler"].items()] + ["Geri"]
        secim = _secim("Otomasyon Ayarla", etiketler)
        if secim is None or secim == len(etiketler) - 1:
            return
        kimlik = list(veri["dersler"])[secim]
        _otomasyon_detay(kimlik)


def _saglik_ekrani():
    secenekler = ["Varsayilan (agusiz)", "Ag kontrolu (ilk 10 ders)"]
    veri, hata = ayarlar.yukle_salt()
    dersler = sorted((veri or {}).get("dersler", {}))
    if dersler:
        secenekler.append("Tek ders icin ag kontrolu")
    secenekler.append("Geri")
    secim = _secim("Saglik kontrolu", secenekler)
    if secim is None or secim == len(secenekler) - 1:
        return
    ders = None
    ag = False
    if secim == 1:
        ag = True
    elif secim == 2:
        ders_secim = _secim("Ders sec", dersler + ["Geri"])
        if ders_secim is None or ders_secim == len(dersler):
            return
        ders = dersler[ders_secim]
    KONSOL.clear()
    if hata:
        KONSOL.print("[yellow]UYARI: {}[/yellow]".format(escape(hata)))
    KONSOL.print("[dim]Denetleniyor...[/dim]")
    try:
        sonuc = saglik.denetle(ders=ders, ag=ag)
    except Exception as hata_kontrol:
        KONSOL.print("[red]Saglik kontrolu yapilamadi: {}[/red]".format(escape(str(hata_kontrol))))
        _bekle_enter()
        return
    renkler = {"ok": "green", "uyari": "yellow", "sorun": "red"}
    for kontrol in sonuc["kontroller"]:
        renk = renkler.get(kontrol["durum"], "white")
        KONSOL.print("[{}]{}: {}[/{}]".format(
            renk, escape(str(kontrol["ad"])), escape(str(kontrol["mesaj"])), renk))
    if sonuc["kota"]:
        KONSOL.print("Kota: limit={} kalan={} sifirla={}".format(
            sonuc["kota"].get("limit"), sonuc["kota"].get("kalan"), sonuc["kota"].get("sifirla")))
    renk = "red" if sonuc["sorunlar"] else "green"
    KONSOL.print("[{}]Sonuc: {} (sorun={}, uyari={})[/{}]".format(
        renk, escape(str(sonuc["genel"])), len(sonuc["sorunlar"]), len(sonuc["uyarilar"]), renk))
    _bekle_enter()


def durum_ekrani():
    while True:
        kayitlar, hata = durum.kayitlar_salt(ayrintili=True)
        satirlar = []
        if hata:
            satirlar.append("[red]Ayarlar okunamadi: {}[/red]".format(escape(hata)))
            satirlar.append("[dim]Saglik kontrolu bozuk ayarlarla da calisir.[/dim]")
        elif not kayitlar:
            satirlar.append("[yellow]Kayitli ders yok.[/yellow]")
        else:
            satirlar.append("Ders sayisi: {}".format(len(kayitlar)))
            for kayit in kayitlar:
                gorev = kayit["otomasyon"]["gorev"]
                if kayit.get("kaynak") == "teams":
                    ozet = (kayit.get("teams") or {}).get("ozet") or "teams"
                    satirlar.append("{}: kaynak=teams {} gorev={}".format(
                        escape(str(kayit["kimlik"])), escape(ozet), escape(str(gorev["durum"]))))
                else:
                    satirlar.append("{}: gorev={}".format(escape(str(kayit["kimlik"])), escape(str(gorev["durum"]))))
                if gorev.get("sonCalisma"):
                    satirlar.append("  son calisma: {}".format(escape(str(gorev["sonCalisma"]))))
                if gorev.get("sonSonuc") is not None:
                    satirlar.append("  son sonuc: {}".format(escape(zamanlayici.sonuc_metni(gorev["sonSonuc"]))))
                if gorev.get("eylem"):
                    satirlar.append("  eylem: {}".format(escape(str(gorev["eylem"]))))
                ozet = kayit.get("durum_dosyasi") or {}
                if ozet.get("hata"):
                    satirlar.append("  durum dosyasi: {}".format(escape(str(ozet["hata"]))))
                else:
                    satirlar.append("  durum dosyasi: {} dosya, {} bayt, guncelleme {}".format(
                        ozet.get("dosya", 0), ozet.get("bayt", 0), escape(str(ozet.get("guncelleme") or "-"))))
        secim = _secim("Durum", ["Saglik kontrolu", "Geri"], ust="\n".join(satirlar))
        if secim == 0:
            _saglik_ekrani()
        else:
            return


def ana_menu():
    while True:
        KONSOL.clear()
        secim = _secim("Ana menu", ["Dersleri Cek", "Dersler", "Ayarlar", "Otomasyon Ayarla", "Durum / Saglik", "Cikis"],
                       "Yon tuslari + Enter | surum {}".format(__version__))
        if secim is None or secim == 5:
            return 0
        if secim == 0:
            _cek_menu()
        elif secim == 1:
            dersler_ekrani()
        elif secim == 2:
            ayarlar_ekrani()
        elif secim == 3:
            otomasyon_ekrani()
        elif secim == 4:
            durum_ekrani()


def baslat():
    try:
        return ana_menu()
    except KeyboardInterrupt:
        return 0
    finally:
        try:
            KONSOL.show_cursor(True)
        except Exception:
            pass
