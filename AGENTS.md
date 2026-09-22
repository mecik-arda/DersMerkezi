# DersMerkezi - Ajan Kuralları ve Proje Bağlamı

Bu dosya, bu projede çalışan tüm kod ajanları için bağlayıcı bağlam ve kuralları içerir. Değişiklik yapmadan önce okuyun.

## Proje Özeti

DersMerkezi, Windows masaüstünde çalışan Python + Rich tabanlı çok dersli içerik çekme aracıdır. GitHub depolarındaki haftalık ders içeriklerini (ör. `Hafta 1.pdf`) indirir, Git blob SHA-1 ile doğrular, pypdf ile Markdown bağlamı üretir ve ders bazında haftalık Windows Görev Zamanlayıcı görevleri kurar.

* Proje kökü: `C:\Users\ardam\Desktop\Yazılım_Siber\DersMerkezi`
* Private depo: `https://github.com/mecik-arda/DersMerkezi` (tüm içerik Türkçe; sürüm kontrolü dışı: `dersler/`, `gunluk.log`, `ayarlar.json`, geçici/yedek dosyalar).
* Plan belgesi: `belgeler/plan/2026-09-21-dersmerkezi-cli.md` (sonunda uygulama ve doğrulama kanıtları)
* CLI geliştirme önerileri: `belgeler/plan/2026-09-21-cli-gelistirme-onerileri.md` (öncelikli maddeler, mimari kararlar ve kaynaklar; Sol denetiminden ONAY aldı, uygulanmadı)
* Durum: M1-M5 uygulandı ve doğrulandı; bağımsız doğrulama turu ve 6 turluk Sol denetimi (toplam 19 bulgu kapatıldı, son turda ONAY) tamamlandı (sürüm 0.1.1). Görev tetiklemesi ve TUI iş mantığı test kapsamında doğrulandı; gerçek konsol görünümü ve üretim görevinin ilk takvimli koşusu kullanıcı tarafında teyit edilecek.
* Kayıtlı ders: `dosya-organizasyonu` (`emirozturk/Dosya-Organizasyonu-2026`, desen `Hafta*.pdf`); görev `DersMerkezi_dosya-organizasyonu` haftalık PZT 09:00.
* Eski PowerShell otomasyonu taşındı; eski `DosyaOrganizasyonu_HaftalikCek` görevi kaldırıldı.

## Ortam Gerçekleri

* Windows 11, PowerShell 5.1, Python 3.13.9 (Anaconda: `C:\Users\ardam\anaconda3\python.exe`; `pythonw.exe` mevcut).
* Kurulu paketler: rich 14.2.0, requests 2.32.5, pypdf 6.12.2.
* Konsol kod sayfası gözlemi 857; başlatıcılar `chcp 65001` kullanır.
* Uzun yol desteği açık (LongPathsEnabled=1).
* Subagent köprüsü izinli kökü: `C:\Users\ardam\Desktop\Yazılım_Siber` (bu proje izinlidir; eski proje klasörü değildir).

## Dosya Haritası

* `dersmerkezi.py`: Giriş noktası; CLI argümanları ve TUI başlatma.
* `merkez/ayarlar.py`: `ayarlar.json` şeması (surum=1), doğrulama (slug/depo/dal/desen/saat/gün), atomik yazım, tek nesil yedek.
* `merkez/indirici.py`: Contents API listeleme, akışlı indirme (`.part`), blob SHA-1 doğrulama, Markdown üretimi, durum şeması v2.
* `merkez/zamanlayici.py`: PowerShell köprüsü (`gorev_kur`, `gorev_kaldir`, `gorev_sorgu`, `gorev_sil_genel`).
* `merkez/tasima.py`: Eski otomasyonun güvenli taşınması (kanıt, manifest, doğrulama).
* `merkez/arayuz.py`: Rich + msvcrt TUI (menü, çoklu seçim, canlı ilerleme).
* `merkez/gunluk.py`: `gunluk.log` (UTF-8, 1 MB rotasyon) ve `Local\DersMerkezi` mutex.
* `merkez/ps/*.ps1`: Sabit PowerShell betikleri; Python bunları `-File` ve bağlanan parametrelerle çağırır.
* `dersler/<slug>/`: İndirilen içerik ve `indirilenler.json`.
* `belgeler/`: plan, referans (eski otomasyon kopyaları), gecmis (taşıma ve denetim kanıtları), kurulum.md, mimari.md.

## Kod Kuralları

* Yorum satırı yazma; mevcut kod kendini açıklayıcı stilde kalır.
* Python ve Markdown dosyaları UTF-8 (BOM'suz); Türkçe karakterler doğru kullanılır.
* PowerShell betiklerinde kullanıcı metinleri ASCII'ye indirgenir (kod sayfası uyumsuzluğu).
* Kullanıcıya dönük tüm metinler Türkçe.
* Girdi doğrulaması zorunlu: slug `^[a-z0-9]+(?:-[a-z0-9]+)*$` (2-40); depo `owner/repo` deseni (URL biçimli girdiler yalnızca `https://github.com/owner/repo[.git]` olarak ayrıştırılır); dal `..` ve boşluk yasak; desen 64 karakter, yol ayracı yasak; ders adı 2-120 karakter ve güvenli karakter kümesi (tırnak ve enjeksiyon karakterleri reddedilir); saat `SS:DD` (00:00-23:59); gün kapalı küme; dosya adlarında yol kaçışı, ayrılmış aygıt adı ve 180+ karakter reddi; liste meta verisinde 200 MB üstü dosyalar indirilmeden reddedilir.
* Görev ayarları: `StartWhenAvailable`, `MultipleInstances IgnoreNew`, 30 dakika zaman aşımı, pilde çalışma (`AllowStartIfOnBatteries`, `DontStopIfGoingOnBatteries`) ve zamanlanmış koşularda `pythonw.exe`.
* Zamanlanmış görev eylemlerine kullanıcı metni gömülmez; yalnızca doğrulanmış slug ve sistem yolları bulunur; PowerShell çağrıları `-File` ve adlandırılmış parametrelerledir.
* Görev güncellemesi, kaldırma ve geri alma yalnızca eylem (execute + tam argüman) birebir eşleşiyorsa ve görev tam olarak tek eylem içeriyorsa yapılır; bu denetim Python ve PowerShell katmanında uygulanır; mutasyondan önce görev durumu (yok/bizim/yabancı) sorgulanır, yalnızca gerçek bulunamama "yok" sayılır ve sorgu hatası fail-closed yükseltilir; güncelleme öncesi mevcut görev XML'i `belgeler/gecmis/gorev_<slug>_onceki.xml` olarak saklanır, geri alma gerekirse görev bu XML'den yüklenir ve yüklenen görevin eylemi birebir doğrulanır (uyuşmazsa geri yükleme iptal edilip görev kaldırılır); ders silme yalnızca bu kuruluma ait görevi kaldırır.
* Ağ çağrıları yalnızca HTTPS; token loglanmaz, hata mesajlarında redakte edilir; 429/5xx için sınırlı tekrar uygulanır.
* Dosya yazımları atomik: aynı dizinde `.tmp`/`.part`, flush, `os.fsync`, `os.replace` (kilitli hedefte 3 deneme, artan bekleme); başarısızlıkta geçici dosya temizlenir.
* `ayarlar.json` ve durum dosyası yazımları, oku-değiştir-yaz işlemleri ve günlük rotasyonu `Local\DersMerkezi` mutex'i altında yapılır; TUI çekme akışı da kilidi alır; kilit alınamazsa günlük yazımı atlanır (fail-closed).

## Değişmezler

* İkinci koşuda durum dosyasına güvenilmez: yerel varlık, boyut ve Git blob SHA yeniden doğrulanır.
* Markdown bağlamı durum kaydındaki `md_sha`/`md_boyut` ile doğrulanır; md eksik veya bozuksa yeniden üretilir.
* Git blob SHA'sı `blob <boyut>\0<veri>` biçiminde streaming hesaplanır; SHA doğrulanmadan dosya nihai adına taşınmaz.
* Markdown şablonu korunur: başlık, kaynak/SHA/tarih/sayfa satırları, `---`, `## Sayfa N`, OCR uyarısı.
* Eski proje klasörü `C:\Users\ardam\Desktop\dersler3-1\Dosya_Organizasyonu` yalnızca referanstır; üzerinde değişiklik yapılmaz.
* `--tasima --onayla` bir kez çalıştırıldı (eski görev kaldırıldı); normal koşullarda yeniden çalıştırılmaz; `--tasima --kuru` çıktısı `tasima-dogrulama-kuru.txt` dosyasına yazılır ve gerçek kanıtı ezmez.
* Görev adı şeması: `DersMerkezi_<slug>`; zamanlanmış koşular `pythonw.exe` ile ve `--otomatik --ders <slug> --sessiz` argümanlarıyla çalışır.
* Ders kaydı silinirken varsa `DersMerkezi_<slug>` görevi de kaldırılır; görev kaldırılamazsa ders silinmez.
* Taşıma hata halinde geri alınır: yeni kurulan görev (bu kuruluma aitse) ve yeni ders kaydı silinir, mevcut kaydın otomasyon ayarı eski değerine döner; eski görev çalışır kalır.
* Otomasyon güncellemesinde ayar yazımı başarısız olursa yeni görev kaldırılır, güncellenmiş mevcut görev XML yedeğinden geri yüklenir; geri alma hatası gizlenmez (fail-closed).
* Çıkış kodları: 0 başarı, 1 hata, 2 kullanım hatası.

## Doğrulama Kapısı

Her değişiklikten sonra en az:

1. `python -m compileall merkez dersmerkezi.py`
2. `python dersmerkezi.py --cek --ders dosya-organizasyonu --sessiz` → logda `atlanan=1`, exit 0 (yeniden indirme olmamalı)
3. `python dersmerkezi.py --durum`
4. Zamanlayıcı değiştiyse: test dersiyle `--otomasyon-kur` / `--otomasyon-kaldir` denenir ve `Get-ScheduledTask` / `schtasks /Query` ile doğrulanır.
5. Taşıma değiştiyse: yalnızca `--tasima --kuru` çalıştırılır; onaylı taşıma tekrarlanmaz.
6. Girdi doğrulaması değiştiyse: birim kontroller (slug, ders adı, depo/URL, dosya adı, saat, gün) yeniden çalıştırılır.
7. Markdown/durum şeması değiştiyse: `md_sha`/`md_boyut` alanları ve bozuk md yeniden üretimi doğrulanır.
8. Kilit/yazma davranışı değiştiyse: kilit dolu senaryosu ve özyinelemeli alma (kilit sızıntısı) kontrol edilir. Birim ve akış paketleri geçici klasördeki proje kopyasında koşturulur; repoya test dosyası eklenmez.

Başarısız doğrulama geçmiş sayılmaz; hata sınıfı (izin/şema/ağ/zaman aşımı) ayrıştırılır ve rapor edilir.

## Bilinen Sınırlamalar

* Görev Zamanlayıcı tetiklemesi test kapsamında doğrulandı: elle koşu, tek seferlik tetikleyici ve haftalık tetikleyici fiilen ateşlendi (`LastTaskResult=0`, `gunluk.log` satırı). İlk gözlemde tetiklenmemenin kök nedeni pil politikasıydı (`DisallowStartIfOnBatteries`); `gorev_kur.ps1` artık pilde çalışacak şekilde kayıt yapar ve üretim görevi elle tetiklemeyle fiilen koştu. Üretim görevinin kendi takvimli koşusu `gunluk.log` üzerinden teyit edilir.
* TUI iş mantığı scriptli tuş girdisiyle (gezinme, çoklu seçim, çekme ekranı) doğrulandı; gerçek konsol etkileşimi ve görsel kalite kullanıcı tarafında.
* Antigravity/Gemini web rotası `web_evidence_invalid` verir; DeepSeek workspace yalnızca bu proje kökünde çalışır.

## Sık Kullanılan Komutlar

* TUI: `baslat.cmd` veya masaüstü `DersMerkezi.bat`
* Yeni ders: `python dersmerkezi.py --ekle --ad "<ad>" --depo <owner/repo> [--desen "<desen>"]`
* Çekme: `python dersmerkezi.py --cek [--ders <slug>] --sessiz`
* Görev kur: `python dersmerkezi.py --otomasyon-kur --ders <slug> --gunler PZT,CAR --saat 09:00`
* Durum: `gunluk.log` ve `dersler/<slug>/indirilenler.json`
