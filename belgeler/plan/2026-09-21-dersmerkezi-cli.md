# DersMerkezi CLI - Keşif ve Plan Belgesi

Tarih: 2026-09-21
Durum: Uygulandı ve doğrulandı (M1-M5); bağımsız doğrulama turları ve bulgu düzeltmeleri tamamlandı (0.1.1). Görev tetiklemesi ve TUI iş mantığı test kapsamında doğrulandı; yalnızca üretim görevinin ilk takvimli koşusu ve gerçek konsol TUI görünümü kullanıcı tarafında teyit edilecek.
Proje kökü: C:\Users\ardam\Desktop\Yazılım_Siber\DersMerkezi

## Hedef ve Kapsam

Masaüstünde çalışan Python + Rich tabanlı bir konsol uygulaması (CLI/TUI): birden fazla ders için GitHub deposu tanımlarını yönetir, seçilen derslerin haftalık içeriklerini canlı animasyonlu ilerleme çubuğuyla indirir, pypdf ile Markdown bağlamına dönüştürür ve ders bazında haftalık gün + saat seçimiyle Windows Görev Zamanlayıcı otomasyonu kurar.

Kapsananlar:

* Ders listeleme, ekleme, çıkarma (ad, depo, dal, desen).
* Dersleri Çek akışı: listeleme, indirme, Git blob SHA-1 doğrulama, Markdown dönüşümü; canlı yüzde çubuğu, aktarım hızı ve durum animasyonları.
* Ayarlar: hangi derslerin çekileceğinin işaretlenmesi.
* Otomasyon ayarları: ders bazında haftalık gün veya günler ve saat; görev kurma, güncelleme, kaldırma; kaçırılan koşunun telafisi.
* Masaüstü başlatıcı: C:\Users\ardam\Desktop\DersMerkezi.bat.
* Mevcut Dosya Organizasyonu otomasyonunun güvenli sırayla taşınması: ders CLI'ye eklenir, indirilen dosyalar korunur, eski görev ancak yeni görev doğrulandıktan sonra kaldırılır.

## Hedef Dışı Bırakılanlar

* Grafik pencere arayüzü (GUI).
* Belirli tarih listesiyle zamanlama (v1 haftalık gün + saat; şema ileride genişletilebilir).
* OCR ve görüntü tabanlı PDF metin çıkarma.
* git clone tabanlı senkronizasyon (GitHub REST API kullanılır).
* Windows dışı işletim sistemleri, çok kullanıcılı kullanım, bulut senkronizasyonu.

## Kabul Kriterleri ve Doğrulama Yöntemi

1. Ders ekleme: `python dersmerkezi.py --ekle --ad "Dosya Organizasyonu" --depo emirozturk/Dosya-Organizasyonu-2026` komutu ayarlar.json içinde `dosya-organizasyonu` kaydını oluşturur; geçersiz depo adresi hata verir ve kayıt yapmaz. Doğrulama: komut çıktısı ve ayarlar.json içeriği.
2. Çekme: `--cek --ders dosya-organizasyonu --sessiz` komutu `dersler/dosya-organizasyonu/Hafta 1.pdf` (2.618.118 bayt) ve `Hafta 1.md` (28 sayfa) üretir; `git hash-object` çıktısı GitHub blob SHA değeri `4102d7394505f14c3e6c3290deaf2ed88e875bb2` ile eşleşir. İkinci koşu indirme yapmaz ve exit 0 döner.
3. Desen dışı dosyalar (LICENSE, .gitignore) indirilmez; yol kaçışı içeren adlar reddedilir. Doğrulama: birim testleri ve çekme logu.
4. İşareti kaldırılan ders `--cek` akışında atlanır. Doğrulama: `secili=false` senaryosu.
5. Otomasyon: `--otomasyon-kur --ders ... --gunler PZT --saat 09:00` sonrası `Get-ScheduledTask`/`schtasks /Query /TN DersMerkezi_dosya-organizasyonu` haftalık PZT 09:00 gösterir; `--otomasyon-kaldir` görevi siler. Görevin fiili yürütmesi sonraki doğrulama turunda kanıtlandı (elle koşu, tek seferlik ve haftalık tetikleyici; `LastTaskResult=0`, `gunluk.log`); ayrıntılar "Sol Bağımsız Denetimi" ve "Uçtan uca kapanış kontrolleri" bölümlerinde.
6. Taşıma: kopya manifesti (ad, boyut, SHA-256) eşleşir; çekme "yeniden indirme yok" loglar; eski `DosyaOrganizasyonu_HaftalikCek` görevi ancak yeni görev kaydı doğrulandıktan sonra kaldırılır; hata simülasyonunda eski görev çalışır kalır.
7. Masaüstü başlatıcı `DersMerkezi.bat` çift tıklamayla uygulamayı açar; paket içeriği komut satırından smoke test edilir, etkileşimli akışı kullanıcı doğrular.
8. Eşzamanlı ikinci çalışma kilit nedeniyle atlanır; bozuk ayarlar.json yedeklenip yeniden oluşturulur; yarım `.part` dosyaları temizlenir.
9. Tüm modüller `python -m compileall` ile hatasız derlenir; günlükte secret bulunmaz; UTF-8 Türkçe baytları doğrudur.
10. Ağ hatasında (örneğin 404) süreç anlaşılır hata mesajı ve sıfır olmayan çıkış kodu verir.
11. Enjeksiyon testleri: slug, depo, desen ve ders adı alanlarına `;`, `&`, `$(...)`, tırnak, satır sonu ve ayraç içeren girdiler reddedilir; görev eyleminde kullanıcı metni bulunmaz (görev XML'i ile doğrulanır).
12. Bozuk, boş ve sürümü bilinmeyen ayarlar.json / indirilenler.json: zaman damgalı yedek + kurtarma; kesilmiş indirme `.part` bırakır ve sonraki koşu telafi eder.
13. Aynı slug veya yalnızca büyük-küçük harf farkı olan ikinci ders reddedilir; iki eşzamanlı `--cek` çalışmasından ikincisi kilit nedeniyle atlanır.
14. HTTP hata matrisi: 404, 403, 429, 500 için anlaşılır mesaj ve sıfır olmayan çıkış; 429 ve 5xx için sınırlı tekrar.
15. Görev senaryoları: var olan görev güncellenir; aynı adlı yabancı görev reddedilir; eski görev yoksa taşıma uyarı ile devam eder.
16. Uzun yol, Unicode dosya adı, Windows ayrılmış adları ve 180+ karakter ad testleri.
17. `--sessiz` altında Rich çıktısı üretilmez; çıkış kodları 0 (başarı), 1 (hata), 2 (kullanım hatası); stdout/stderr ayrımı korunur.
18. Rapor kategorileri ayrışır: yeni, güncellenen, atlanan, doğrulama hatası, dönüşüm hatası.

## Mimari ve Teknoloji Kararları

* Dil: Python 3.13.9 (Anaconda, `python` PATH üzerinde). Gerekçe: yerel kurulum mevcut; rich, requests, pypdf hazır; msvcrt ile Windows tuş girişi.
* Arayüz: rich 14.2.0 (kurulu). Gerekçe: Live/Progress ile canlı animasyon ve ilerleme çubukları; ek kurulum gerekmez. Textual değerlendirildi; ek bağımlılık ve karmaşıklık nedeniyle kullanıcı Rich'i seçti.
* HTTP: requests 2.32.5 (kurulu). Gerekçe: akışlı indirme ve Content-Length ile yüzde hesabı. Opsiyonel GITHUB_TOKEN ortam değişkeni desteklenir; kamuya açık depolarda gerekmez.
* GitHub listeleme: Contents API tek istekte dizin başına en fazla 1.000 girdi döndürür; `per_page`/`page` ve Link tabanlı sayfalama desteklenmez (yerel prob ve resmi doküman, 2026-09-21). Kurs depoları küçük olduğundan Contents API yeterlidir; 1.000 sınırına ulaşılırsa Git Trees API'ye geçilir veya anlaşılır hata verilir.
* İndirme: `raw.githubusercontent.com` (API kotasından sayılmaz); dosya başına 200 MB üst sınırı.
* PDF dönüşümü: pypdf 6.12.2 (kurulu); mevcut pdf_to_md.py çıktı biçimi (metadata başlığı ve `## Sayfa N`) korunur.
* Zamanlayıcı: Sabit PowerShell betikleri `merkez/ps/gorev_kur.ps1`, `gorev_kaldir.ps1`, `gorev_sorgu.ps1`; Python bu betikleri `subprocess` liste biçimiyle ve `-File` ile, adlandırılmış parametreler üzerinden çağırır. `-Command`, `Invoke-Expression` ve metin birleştirme kullanılmaz. Görev kaydı `Register-ScheduledTask`, silme `Unregister-ScheduledTask`, doğrulama `Get-ScheduledTask` ve görev XML'i iledir; schtasks yalnızca ikincil gösterimdir.
* Görev eylemi: yalnızca sistem yolları (`sys.executable`/`pythonw.exe` mutlak yolu, uygulama betiği) ve doğrulanmış slug içerir; herhangi bir kullanıcı metni gömülmez. Zamanlanmış koşularda `pythonw.exe` kullanılarak konsol penceresi engellenir.
* Eşzamanlılık: Windows adlandırılmış mutex (ctypes CreateMutexW, `Local\DersMerkezi`) tüm yazma işlemlerini kapsar; kapsam aynı kullanıcı oturumudur, farklı kullanıcı oturumları kapsam dışıdır ve belgelenir.
* Durum ve günlük: ders başına `dersler/<slug>/indirilenler.json` (atomik yazım: aynı dizinde `.tmp`, flush, os.fsync, os.replace); `ayarlar.json` için tek nesil yedek; ortak `gunluk.log` (UTF-8, BOM yok, 1 MB üzeri rotasyon; rotasyon mutex altında).
* Şema sürümü: ayarlar.json ve indirilenler.json `surum` alanı taşır; bilinmeyen sürüm hata verir, eksik/eski sürümde migration kancası çalışır.
* Kod düzeni: giriş noktası `dersmerkezi.py`; çekirdek modüller `merkez/` altında (ayarlar, indirici, zamanlayici, arayuz, gunluk); sunum ve iş mantığı ayrıdır.
* Kodlama: tüm dosyalar UTF-8; başlatıcı .bat `chcp 65001` içerir ve yalnızca doğrulanmış mutlak python yolunu kullanır.

## Güvenlik ve Girdi Doğrulama

* Slug: `^[a-z0-9]+(?:-[a-z0-9]+)*$`, 2-40 karakter; `.`, `..`, yol ayraçları, kontrol karakterleri, sonda nokta/boşluk ve ayrılmış aygıt adları (CON, PRN, AUX, NUL, COM1-9, LPT1-9) reddedilir; büyük-küçük harf çakışması reddedilir.
* Depo: `^[A-Za-z0-9][A-Za-z0-9._-]{0,38}/[A-Za-z0-9][A-Za-z0-9._-]{0,99}$`; URL biçimli girdiler ayrıştırılıp yalnızca owner/repo kullanılır; `..` ve sorgu parçaları reddedilir.
* Dal: `^[A-Za-z0-9._/-]{1,100}$` ve `..` yasak. Desen: 64 karaktere kadar, `\x00-\x1f`, `<>:"/\\|?` yasak, joker `*` izinli.
* Gün: kapalı küme; kod içinde .NET enum adlarına eşlenir (Monday-Pazar dahil yedi gün); Türkçe kısaltmalar yalnızca arayüzde gösterilir. Saat: `^([01]\d|2[0-3]):[0-5]\d$`.
* Dosya adları: geçersiz karakter, ayrılmış ad, sonda nokta/boşluk, 180 karakter ve büyük-küçük harf çakışması kuralları korunur; indirme yalnızca doğrulanmış adlarla yapılır.
* Ağ: yalnızca HTTPS; token günlüğe yazılmaz, hata mesajlarında redakte edilir; yanıt boyutu sınırlanır.
* Reparse point/junction: `dersler/<slug>` gerçek yolunun uygulama kökü içinde kaldığı `os.path.realpath` ile doğrulanır.

## Zamanlayıcı Davranış Politikası

* Yerel saat dilimi kullanılır; yaz/kış saati geçişi Windows görev saati tarafından yerel saat olarak yorumlanır.
* `StartWhenAvailable` ile kaçırılan koşu telafi edilir; `-MultipleInstances IgnoreNew` ile üst üste çalışma engellenir; `ExecutionTimeLimit` 30 dakikadır. Bu üç ayarın PS 5.1'de kayıt ve sorgusu yerel testle doğrulandı (haftalık gün kümesi bit maskesi, başlangıç saati, ayar değerleri).
* Görev, kullanıcı oturumu açıkken çalışır (Interactive); görev sahipliği kontrol edilir; aynı adlı görev bu uygulamaya ait değilse üzerine yazılmaz.
* Görev güncellemesi `-Force` ile yapılır; mevcut görev XML'i güncelleme öncesi saklanır.

## Taşıma Planı (Güvenli Sıra)

1. Eski durum kaydı: `DosyaOrganizasyonu_HaftalikCek` görev XML'i, `haftalik/` manifesti (ad, boyut, SHA-256) ve `otomasyon/indirilenler.json` kopyası `belgeler/gecmis/` altına alınır.
2. İçerik kopyalama (taşıma değil): `Dosya_Organizasyonu\haftalik\*` → `DersMerkezi\dersler\dosya-organizasyonu\`; kaynak yol yoksa taşıma uyarı ile durur; kopya sonrası manifest karşılaştırılır; Git blob SHA'sı API ile eşleşen dosyalar durum dosyasına yazılır (yeniden indirme yok), eşleşmeyenler sonraki çekmede yeniden indirilir; mevcut `Hafta 1.md` doğrulanır, bozuksa `md=false` bırakılır.
3. Ders kaydı eklenir; `--cek --ders dosya-organizasyonu --sessiz` çalıştırılır ve "yeniden indirme yok" kanıtı logdan alınır.
4. Yeni görev `DersMerkezi_dosya-organizasyonu` adıyla kurulur; eylem ve tetikleyici `Get-ScheduledTask` + XML ile doğrulanır.
5. Tüm adımlar başarılıysa eski görev `Unregister-ScheduledTask` ile kaldırılır ve kaldırıldığı doğrulanır.
6. Herhangi bir adımda hata: eski görev çalışır kalır; yeni görev ve ders kaydı geri alınır; kopyalanan dosyalar zararsız olduğu için silinmez; hata raporlanır.
7. Eski görev yoksa taşıma uyarı ile devam eder; mevcut içerik yine doğrulanır.
8. Taşıma tek oturumda ve kısa bir zaman penceresinde yapılır; eski görev ancak yeni görev doğrulandıktan sonra kaldırıldığından çakışma riski sınırlıdır.

## İndirme Hata Modeli

* Connect 10 sn, read 30 sn zaman aşımı; dosya başına 200 MB üst sınır.
* Contents API dizin listesinde sayfalama yoktur; dizin başına 1.000 girdi sınırı vardır (resmi doküman ve yerel prob ile doğrulandı). Sınıra ulaşılırsa Git Trees API veya anlaşılır hata.
* 404, 401, 403 anlaşılır hata; 429 ve 5xx için `Retry-After` destekli en fazla 2 tekrar (artan bekleme); her hata günlüğe yazılır.
* İkinci koşuda durum dosyasına güvenilmez: yerel dosyanın varlığı, boyutu ve Git blob SHA'sı yeniden doğrulanır; uyuşmazlıkta yeniden indirilir.
* Git blob SHA'sı ham baytlar üzerinden `blob <uzunluk>\0<veri>` biçiminde streaming hesaplanır; SHA doğrulanmadan dosya nihai adına taşınmaz. Python streaming sonucu beklenen değerle birebir eşleşti (yerel prob).
* `os.replace` kilitli/açık hedefte `PermissionError` verir (yerel prob ile doğrulandı); sınırlı tekrar (3 deneme, artan bekleme) ve sonrasında anlaşılır HATA + `.tmp`/`.part` temizliği uygulanır.
* 1-100 MB arası dosyalarda Contents API yalnızca raw/object media type destekler; indirme raw.githubusercontent.com üzerinden yapıldığından bu sınır meta veri sorgusunu etkiler, indirmeyi engellemez.

## Arayüz (TUI) Kararları

* Girdi katmanı `msvcrt.getwch()` ile geniş karakter ve kaçış dizisi ayrıştırma kullanır (ok tuşları, Enter, Boşluk, sayı tuşları).
* Ctrl-C yakalanır; terminal durumu (alternatif ekran, imleç) `finally` ile geri yüklenir.
* `sys.stdout.isatty()` yanlışsa TUI yerine başsız mod; `--sessiz` Rich çıktısını kapatır.
* Arayüz yalnızca sunum ve girdi katmanıdır; tüm iş mantığı ayrı işlevlerde olduğundan gerçek girdi olmadan test edilebilir.
* Renk desteklemeyen konsol ve dar pencere için rich fallback; pencere yeniden boyutlandırma güvenli biçimde ele alınır.

## Netleştirilen Kararlar (DeepSeek Flash + Yerel Doğrulama + Resmi Doküman)

1. Durum şeması v2 ve eski şema eşlemesi: eski `surum=1` kaydındaki `surum, guncelleme, dosyalar.{sha, boyut, indirildi, md}` alanları korunur; dosya kaydına `kaynak_url, md_sha, md_boyut, md_uretildi` eklenir; eski şema okunduğunda migration kancası alanları taşır. Durum dosyası ders klasöründe `indirilenler.json` adını korur.
2. Ayarlar şeması: ders kaydı `ad, slug, depo, dal, desen, secili, otomasyon{aktif, gunler, saat, gorevAdi}`; kökte `surum` alanı.
3. Slug türetme: Türkçe karakterler ASCII'ye indirgenir (ç→c, ğ→g, ı→i, İ→i, ö→o, ş→s, ü→u), küçük harfe çevrilir, boşluk/alt çizgi tireye dönüşür, ardışık tireler teklenir, regex doğrulanır, casefold çakışma reddedilir; `--slug` ile elle geçersiz kılınabilir.
4. Dosya adı doğrulama kuralları eski otomasyondan birebir taşınır: boş ad, yol ayırıcı, `<>:"/\\|?*`, kontrol karakterleri, sonda nokta/boşluk, 180 karakter sınırı, ayrılmış aygıt adları ve casefold çakışma; hem liste hem indirme aşamasında kapı olarak uygulanır.
5. md şablonu ve konumu: mevcut şablon birebir korunur (`# stem — Ders Bağlamı`, kaynak/SHA/tarih/sayfa satırları, `---`, `## Sayfa N`, metin yoksa uyarı); çıktı PDF ile aynı klasörde aynı kök ad + `.md`; geçici ada yazılır, doğrulanır, nihai ada taşınır; md eksik/bozuksa sonraki çekmede yeniden üretilir.
6. Atomik yazım: aynı dizinde `.tmp`, flush, `os.fsync`, `os.replace`; kilitli hedefte PermissionError için 3 deneme artan bekleme; başarısızlıkta HATA ve geçici dosya temizliği; `ayarlar.json` tek nesil yedek.
7. Günlük biçimi ve kategoriler: `[YYYY-MM-DD HH:MM:SS] [BILGI|UYARI|HATA] mesaj`, UTF-8 BOM'suz, 1 MB üzeri `.old` rotasyonu mutex altında; rapor sayaçları: yeni, güncellenen, atlanan, bağlam, doğrulama hatası, dönüşüm hatası.
8. `--otomatik` modu: başsız, TUI ve Rich çıktısı yok, yalnız `gunluk.log`; çıkış kodları 0/1/2; zamanlanmış görevlerde `pythonw.exe` kullanılır. `pythonw` altında stdout/stderr görev bağlamında `None` olabilir (yerel gözlem: konsol sahipliğinde cp1254 TextIOWrapper); tüm çıktı dosyaya yazılır ve güvenli sarmalayıcı kullanılır; `pythonw.exe` yoksa `python.exe` ile devam edilir ve konsol penceresi riski belgelenir.
9. `.bat` başlatıcı: `@echo off`, `chcp 65001>nul`, mutlak python + dersmerkezi.py, `ERRORLEVEL` döndürme, hata halinde `pause`; masaüstü konumu `C:\Users\ardam\Desktop\DersMerkezi.bat`.
10. Görev adı ve tetikleyici: `DersMerkezi_<slug>`; haftalık gün kümesi + saat; `StartWhenAvailable`, `ExecutionTimeLimit 30 dk`, `MultipleInstances IgnoreNew` (yerel kayıt/sorgu testiyle doğrulandı); güncelleme öncesi mevcut görev XML'i saklanır.
11. Taşıma kanıtları `belgeler/gecmis/` altında saklanır: eski görev XML'i, haftalik manifesti (ad/boyut/SHA-256), eski durum kopyası, yeni manifest, blob doğrulama çıktısı ve ilgili günlük satırları.
12. Mutex: tek global `Local\DersMerkezi`; eski görev taşıma tamamlanana kadar çalışır kalır, taşıma tek oturumda yapılır ve eski görev ancak yeni görev doğrulandıktan sonra kaldırılır.
13. Contents API sınırı: tek istekte 1.000 girdi; sayfalama yok; 1.000'e ulaşılırsa Git Trees API veya hata; raw indirme API kotasından sayılmaz.
14. Python yolu: kurulumda `sys.executable` ve `pythonw.exe` varlığı doğrulanır; yol yoksa görev kurulumu reddedilir.

## İş Kırılımı ve Kilometre Taşları

* M1 Çekirdek: ayarlar.py (şema, CRUD, doğrulama, atomik yazım, migration), gunluk.py (günlük, mutex), indirici.py (Contents API listeleme, akışlı indirme ve ilerleme callback, blob SHA doğrulama, dönüşüm, hata modeli).
* M2 Headless CLI: `--listele`, `--ekle`, `--sil`, `--cek`, `--otomasyon-kur`, `--otomasyon-kaldir`, `--durum`, `--otomatik`, `--sessiz`; çıkış kodları.
* M3 Arayüz: ana menü, ders yönetimi, ayarlar (işaretleme), otomasyon ekranı, canlı çekme animasyonu.
* M4 Entegrasyon: sabit PS betikleri, görev kurulumu, masaüstü başlatıcı, güvenli taşıma.
* M5 Doğrulama: kabul kriteri testleri, README, plan güncellemesi.

Bağımlılık: M3, M1-M2 üzerine kurulur; M4, M1 ve taşıma planı üzerine. Geri alınabilirlik: her adım öncesi durum kaydı; eski görev son adımda kaldırılır; eski otomasyon klasörü silinmez.

## Riskler ve Azaltma Önlemleri

* Zamanlanmış görev yürütmesi tetikleyici testleriyle doğrulandı; üretim koşusu kullanıcı tarafında `gunluk.log` ile teyit edilir; uygulama manuel başlatıcıyla da tam çalışır.
* Anaconda python yolu değişebilir: görevler kayıt anındaki mutlak yolu kullanır; yol yoksa görev kurulumu reddedilir; otomasyon kur yeniden çalıştırılarak güncellenir.
* Komut enjeksiyonu: kapalı küme doğrulama, sabit PS betikleri, `-File` ve parametre bağlama, görev eyleminde kullanıcı metni bulunmaması ile azaltılır.
* Yarıda kalma ve yarış: mutex, `.part` indirme, fsync + atomik değiştirme, tek nesil yedek ile azaltılır.
* Kilitli hedef dosya (açık PDF okuyucu, antivirüs): `os.replace` PermissionError'ı sınırlı tekrar ve anlaşılır hata ile ele alınır.
* Kimliksiz API limiti saatte 60 istek: indirme raw URL'den yapıldığı için istek sayısı küçük; 403 durumunda anlaşılır hata; opsiyonel token desteği.
* Yerelleştirme: gün adları .NET numaralandırmasıyla verilir; schtasks metin çıktısı ayrıştırılmaz; slug ve çakışma tespiti yerel ayardan bağımsız ASCII/casefold ile yapılır.
* Konsol uyumluluğu: kod sayfası 857 gözlemlendi; chcp 65001 ve rich fallback; Windows Terminal önerilir.
* Taşıma kaybı: eski görev ve içerik, yeni görev doğrulanmadan değiştirilmez; manifest ve durum eşleşmesi kanıtlanır.

## Doğrulanamayan veya Açık Noktalar

* Zamanlanmış görev yürütmesi test kapsamında doğrulandı (elle koşu, tek seferlik ve haftalık tetikleyici; `LastTaskResult=0`). Üretim görevinin kendi takvimli koşusu kullanıcı tarafında `gunluk.log` ile teyit edilir.
* TUI iş mantığı scriptli tuş girdisiyle test edildi (gezinme, çoklu seçim, çekme ekranı); gerçek konsol etkileşimi ve görsel kalite kullanıcı deneyimiyle doğrulanır.
* Rich animasyonunun kullanıcının varsayılan konsolundaki görsel kalitesi.
* Disk dolması ve yazma izni hatalarının gerçek ortamda üretilmesi sınırlı ölçekte denenebilir; kod yolu gözden geçirilir.
* pythonw altında stdout/stderr davranışı görev bağlamına göre değişir; kod tarafı güvenli yazıldığı için risk düşüktür, görev testi kullanıcı tarafında görülecektir.

## Sınırlamalar ve Atlanan Adımlar

* Gemini 3.8 Flash (3 deneme) ve Gemini Pro (1 deneme) web rotaları `web_evidence_invalid` ile başarısız oldu; dış doğrulama GitHub resmi dokümanı ve yerel prob ile yapıldı.
* DeepSeek Flash, izinli kök `C:\Users\ardam\Desktop\Yazılım_Siber` belirlendikten sonra başarıyla çalıştı (22 bulgu, 10 adım, 8 karar sorusu; maliyet ~0,012 USD).
* Sol için model seçilebilen salt-okunur rota yok; denetimler kanonik codex salt-okunur rotasıyla yapıldı.
* Luna edit rotası "pilot file path must be relative" hatasıyla çalışmadı; plan belgesi kullanıcı tarafından açıkça yetkilendirilen yola orkestratör tarafından yazıldı ve revize edildi.

## Kaynaklar

Doğrulanan:

* Yerel ortam: python 3.13.9 (Anaconda), rich 14.2.0, requests 2.32.5, pypdf 6.12.2, msvcrt mevcut; pythonw.exe mevcut (importlib.metadata ve dosya kontrolleri, 2026-09-21).
* GitHub API ve doküman: Hafta 1.pdf blob SHA `4102d7394505f14c3e6c3290deaf2ed88e875bb2`, 2.618.118 bayt; Contents API dizin başına 1.000 dosya sınırı ve sayfalama desteğinin bulunmaması (docs.github.com/en/rest/repos/contents, yerel prob: `page=1` == `page=2`, Link yok).
* Yerel problar: Python streaming blob SHA beklenen değerle eşleşti; `os.replace` kilitli hedefte PermissionError, kilit kalkınca başarılı; pythonw altında stdout cp1254 TextIOWrapper (konsol sahipliğinde).
* PowerShell: `New-ScheduledTaskSettingsSet` (StartWhenAvailable, ExecutionTimeLimit, MultipleInstances), `New-ScheduledTaskTrigger` (Weekly, DaysOfWeek, At) PS 5.1'de mevcut; haftalık gün kümesi kaydı ve sorgusu doğrulandı.
* Görev Zamanlayıcı kayıt, sorgu ve silme akışı bu oturumda çalıştırılan betiklerle kanıtlandı.
* Zamanlanmış görev yürütme kısıtı: 30 saniyelik ping testi süreç üretmedi (oturum komut kanıtı).
* DeepSeek Flash çıktısı: 2026-09-21, run `e118616f-9509-48d6-84e9-4f179af0b22c`, 22 kanıtlı bulgu; önerileri Netleştirilen Kararlar bölümüne işlendi.

Doğrulanamayan:

* Textual kütüphanesinin bu makinedeki davranışı (kurulu değil, seçilmedi).
* Rich'in eski cmd.exe üzerindeki tam davranışı.
* Antigravity web rotasının (Gemini) web kanıtı üretimi; tüm denemeler reddedildi.

## Sol Denetim Özeti ve Kapatılan Bulgular

Birinci denetim (kanonik codex salt-okunur rota): 2 kritik, 6 orta, 4 düşük bulgu. Kapatma durumu:

* Kritik, komut enjeksiyonu: Sabit PS betikleri, `-File` ve parametre bağlama, kapalı küme doğrulama, görev eyleminde yalnızca doğrulanmış slug kullanımı plana eklendi (Güvenlik ve Girdi Doğrulama bölümü, kabul kriteri 11).
* Kritik, güvensiz taşıma sırası: Manifest kaydı, kopyalama, yeni görev doğrulaması sonrası eski görevin kaldırılması ve hata halinde geri alma adımları plana eklendi (Taşıma Planı, kabul kriteri 6).
* Orta, zamanlayıcı doğrulaması: Kapalı gün kümesi, katı saat biçimi, davranış politikası ve XML tabanlı doğrulama eklendi (Zamanlayıcı Davranış Politikası, kabul kriterleri 5 ve 15).
* Orta, Anaconda yolu: Kurulumda sys.executable/pythonw doğrulaması ve yol yoksa reddetme eklendi (Riskler, Netleştirilen Karar 14).
* Orta, kilit ve atomik yazım kapsamı: Mutex kapsamı, `.part`, fsync, tek nesil yedek ve kurtarma davranışları eklendi (Mimari, İndirme Hata Modeli, kabul kriteri 12).
* Orta, indirme hata modeli: Zaman aşımı, boyut sınırı, 429/5xx tekrarı, yerel dosya yeniden doğrulaması ve os.replace tekrarı eklendi (İndirme Hata Modeli, kabul kriteri 14).
* Orta, taşıma durumu tanımsız: Kaynak-hedef eşleme, şema sürümü, manifest karşılaştırması ve reparse point kontrolü eklendi (Taşıma Planı, Güvenlik).
* Orta, kabul testleri yetersiz: 11-18 arası kriterler eklendi (bozuk JSON, çakışan ad, eşzamanlı çekme, kesilen indirme, HTTP matrisi, görev senaryoları, uzun/Unicode adlar).
* Orta, Rich/msvcrt tuzakları: getwch tabanlı girdi katmanı, Ctrl-C, isatty fallback, sunum-mantık ayrımı eklendi (Arayüz Kararları).
* Düşük bulgular: Günlük rotasyonu mutex altına alındı; şema sürümü; `--sessiz` çıktı bastırma ve exit kodu standardı; rapor kategorileri kabul kriterlerine eklendi.
* Kapanış doğrulaması (ikinci denetim): Revize planın uygulama için yeterli bir hedef tanımladığı doğrulandı; kalan maddeler M1-M5 iş kırılımı ve kabul kriterlerine bağlandı. Plan düzeyinde açık blocker yoktur.

## Uygulama ve Doğrulama Kanıtları (2026-09-21)

* Derleme: `python -m compileall merkez dersmerkezi.py` hatasız (exit 0).
* Ders ekleme: `--ekle` ile `dosya-organizasyonu` kaydı oluştu; geçersiz depo girdisi exit 2 verdi.
* Çekme: `dersler/dosya-organizasyonu/Hafta 1.pdf` 2.618.118 bayt; `git hash-object` çıktısı GitHub blob SHA `4102d7394505f14c3e6c3290deaf2ed88e875bb2` ile eşleşti; `Hafta 1.md` 28/28 sayfa ile üretildi.
* İdempotans: ikinci koşu `yeni=0 atlanan=1 baglam=1` ve exit 0.
* Durum şeması: `indirilenler.json` sürüm 2 alanları (sha, boyut, indirildi, md, kaynak_url, md_uretildi) doğrulandı.
* Kilit: mutex tutulurken ikinci çalışma "Baska bir calisma suruyor" uyarısıyla atlandı, exit 0.
* Hata modeli: olmayan depo 404 ile exit 1 ve anlaşılır günlük satırı.
* TUI fallback: TTY olmayan ortamda yardım çıktısı ve exit 2.
* Birim kontroller: slug Türkçe indirgeme, dosya adı reddi (yol kaçışı, ayrılmış ad, 180+), saat ve gün doğrulaması geçti.
* Görev kur/kaldır: `DersMerkezi_test-ders` haftalık PZT,SAL 09:00 kuruldu; eylem `pythonw.exe` + `"dersmerkezi.py" --otomatik --ders ... --sessiz`; `MultipleInstances IgnoreNew` ve `StartWhenAvailable` doğrulandı; kaldırma görevi sildi.
* Zamanlanmış komut simülasyonu: `pythonw.exe` ile birebir görev komutu çalıştırıldı ve `gunluk.log` kanıtı alındı.
* Taşıma: kuru çalışma kanıtları yazdı; uygulama kopyalama, manifest doğrulaması, yeniden indirme olmaması kanıtı ve yeni görev kaydını tamamladı; `--onayla` ile eski `DosyaOrganizasyonu_HaftalikCek` görevi kaldırıldı ve yokluğu doğrulandı; kanıtlar `belgeler/gecmis/` altında.
* Dokümantasyon: README ve plan güncellendi; `AGENTS.md`, `CLAUDE.md` ve `CHANGELOG.md` oluşturuldu.
* Bu turda doğrulanamayan (sonraki turlarda kapatıldı): etkileşimli TUI akışı ve Görev Zamanlayıcı tetiklemesinin fiili yürütmesi bu ortamda test edilememişti; TUI iş mantığı scriptli girdiyle, tetikleme ise elle/tek seferlik/haftalık koşularla sonradan doğrulandı (bkz. son bölümler).

### Bağımsız Doğrulama ve Düzeltme Turu (2026-09-21, ikinci tur)

Yöntem: Projenin geçici klasöre kopyası (`%TEMP%\opencode\dm-test\durum` içerikli, `fresh` temiz) üzerinde istenen davranışı tanımlayan iki test paketi koşturuldu; gerçek proje dosyalarına test sırasında dokunulmadı. Gerçek proje yalnızca doğrulama kapısı ve zorunlu kanıt komutları için kullanıldı.

Bulgu ve düzeltmeler:

* Markdown bütünlüğü: durum şeması v2'de `md_sha`/`md_boyut` alanları yazılmıyordu ve md yeniden kullanımı yalnızca varlık kontrolüne dayanıyordu (Netleştirilen Karar 1 ve "md eksik/bozuksa yeniden üretilir" kuralı eksik uygulanmıştı). Alanlar eklendi; md dosyası boyut ve SHA-256 ile doğrulanıyor, bozuk/eksikse yeniden üretiliyor, `md_uretildi` gereksiz güncellenmiyor.
* Mutex kapsamı: kilit yalnızca CLI `--cek` akışını tutuyordu; `ayarlar.json` ve durum yazımları, oku-değiştir-yaz işlemleri ve günlük rotasyonu kapsam dışıydı (plan: "tüm yazma işlemlerini kapsar", Netleştirilen Karar 7). Yazma yolları `Local\DersMerkezi` altına alındı; TUI çekme ekranı kilit alıyor; kilit sahibi iş parçacığında özyinelemeli alma desteklendi; `kilitle()` ile `__enter__` çift alımından kaynaklanan kilit sızıntısı düzeltildi.
* Atomik yazım: `_json_yaz` üç denemede de `PermissionError` alırsa `.tmp` dosyası kalıyordu (Netleştirilen Karar 6). Hata halinde `.tmp` ve geçici md dosyaları temizlenir.
* Listeleme hata modeli: Contents API listeleme çağrısında 429/5xx tekrarı yoktu (İndirme Hata Modeli). `Retry-After` destekli 3 deneme eklendi; kalıcı 5xx sonrası anlaşılır hata korunur.
* Görev/ayar tutarlılığı: `--otomasyon-kur` görev kurulmadan ayarı `aktif=true` yazıyordu; görev kurulumu başarısız olursa ayar yanlış durumda kalıyordu. Sıra görev → ayar olarak değiştirildi; görev kurulamazsa ayar `aktif` kalmaz (kabul 15).
* Öksüz görev: `--sil` ders kaydını silerken varsa zamanlanmış görevi bırakıyordu (haftalık hata üretirdi). Ders silinmeden önce görev kaldırılır; görev kaldırılamazsa ders silinmez (fail-closed). TUI ders çıkarma aynı davranışı uygular.
* Taşıma kanıtı: `--tasima --kuru` gerçek taşıma kanıtı olan `belgeler/gecmis/tasima-dogrulama.txt` dosyasının üzerine yazıyordu. Kuru çalışma artık `tasima-dogrulama-kuru.txt` yazar; gerçek kanıt hash'i değişmedi.
* Girdi doğrulama boşlukları (kabul 11): ders adı alanı `;`, `&`, `$(...)`, tırnak, satır sonu, köşeli parantez gibi girdileri kabul ediyordu; slug alt sınırı (2) uygulanmıyordu; dal deseni boşluk kabul ediyordu; URL biçimli depo girdisi ayrıştırılmıyordu ("URL biçimli girdiler ayrıştırılır" kuralı). Ad 2-120 karakter ve güvenli karakter kümesiyle doğrulanır; slug 2-40; dal boşluksuz; `https://github.com/owner/repo[.git]` ayrıştırılır, sorgu/parça ve fazla yol reddedilir.
* TUI markup: Rich çıktısında dinamik değerler (`[`, `]` içerebilen dosya/ders adları) markup olarak yorumlanıp hata üretebilirdi. Dinamik metinlere `rich.markup.escape` uygulandı.
* Taşıma geri alma: Taşıma Planı adım 6 "yeni görev ve ders kaydı geri alınır" uygulanmamıştı; görev kurulumu başarısız olduğunda otomasyon ayarı `aktif=true` kalıyordu. Hata halinde yeni kurulan görev (yalnızca bu kuruluma ait olduğu doğrulanarak) ve yeni ders kaydı geri alınır; mevcut kaydın otomasyon ayarı önceki değerine döner; eski görev çalışır kalır.

Test ve doğrulama kanıtları:

* Birim paketi (89 kontrol): ad/slug/depo/dal/desen/saat/gün/doğrudosya adı doğrulaması, Türkçe slug indirgeme, büyük-küçük harf çakışması, `.tmp` temizliği ve hata yükseltme, mutex alma/zaman aşımı/özyineleme, listeleme 5xx tekrarı ve kalıcı hata, görev kurulamazsa ayar, görev kaldırılamazsa ders silinmeme, görev varken silme, kuru taşıma kanıtı, bozuk/bilinmeyen sürüm ayarlar kurtarma. Sonuç: 89/89 geçti.
* Akış paketi (43 kontrol, ağ dahil): `--ekle` (geçerli, yinelenen, enjeksiyon), `--listele`, `--durum`, ilk çekme (`yeni=1`, 2.618.118 bayt, blob SHA eşleşmesi, md 28 sayfa, şablon satırları), ikinci çekme (`atlanan=1`, pdf mtime ve `md_uretildi` korunur), bozuk md ve eksik md yeniden üretimi, `.part` temizliği, bozuk pdf yeniden indirme (`guncellenen=1`), kilit doluyken çekme atlama, olmayan ders/404 hata kodları, `--sessiz` stdout boşluğu, test dersiyle görev kur/kaldir + ayar tutarlılığı, `--sil` ile görev kaldırma, yabancı görev reddi, günlükte secret bulunmaması. Sonuç: 43/43 geçti.
* Gerçek proje doğrulama kapısı (düzeltmelerden sonra): `compileall` exit 0; `--cek --ders dosya-organizasyonu --sessiz` iki kez exit 0 ve `atlanan=1 baglam=1`; `--durum` → `gorev=kayitli (Ready)`; durum dosyasında `md_sha`/`md_boyut` yazıldı ve md dosyası hash'i ile eşleşti (19907 bayt, SHA-256 `9793978260d14fa0442a2ccf2caaf27b585737b3af000c564998290afff0e19b`); ikinci koşuda `md_uretildi` korundu.
* Zamanlayıcı: test dersi `zamanlayici-test` ile `--otomasyon-kur --gunler SAL,CAR --saat 10:30` → görev `DersMerkezi_zamanlayici-test` kuruldu (Ready), sorgu gün maskesi 12 (Sal+Çar) ve 10:30 döndü; `--otomasyon-kaldir` görevi sildi ve ayar `aktif=false` oldu; yeniden kurulum sonrası `--sil` hem görevi hem kaydı kaldırdı. Aynı adlı yabancı görev (`DersMerkezi_yabanci-test`) reddedildi (exit 1) ve ayar `aktif` kalmadı.
* Taşıma: yalnızca `--tasima --kuru` koşuldu (exit 0); `tasima-dogrulama.txt` SHA-256'sı değişmedi, ayrı `tasima-dogrulama-kuru.txt` üretildi; eski görev yokluğu uyarısı beklendiği gibi.
* Görev listesi kontrolü: yalnızca üretim görevi `DersMerkezi_dosya-organizasyonu` (Ready) kaldı; test görevleri temizlendi.

Uçtan uca kapanış kontrolleri (ek tur):

* Taşıma hata senaryoları (11 kontrol): mevcut kayıt varken görev kurulumu başarısız → kayıt korunur, otomasyon eski değerine döner, eski görev durur; yeni kayıtla başarısız → kayıt geri alınır; görev kurulup sonra hata → yalnızca bu kuruluma ait görev kaldırılır, eski görev ve üretim görevi korunur. Sonuç: 11/11 geçti.
* HTTP hata matrisi (4 kontrol): 429 + `Retry-After` tekrarı ve kalıcı 429, 403 limit mesajı, 401 mesajı. Sonuç: 4/4 geçti (404 ve 500 daha önceki turlarda).
* Kapsam (3 kontrol): depo kökünde desen dışı `.gitignore`/`LICENSE` indirilmez; `secili=false` ders `--cek` akışında atlanır (rapor `atlanan=1`).
* Başlatıcı zinciri: `C:\Users\ardam\Desktop\DersMerkezi.bat` → `baslat.cmd --durum` exit 0; etkileşimli TUI kullanıcı tarafında.
* Uzun yol: 320 karakterlik proje yolunda `--durum`, `--ekle`, `--listele` exit 0 ve dosyalar oluştu (LongPathsEnabled=1).
* Görev güncelleme: aynı ders için `PZT 09:00` kurulduktan sonra `SAL,CAR 10:30` ile güncellendi; sorgu gün maskesi 12 ve başlangıç 10:30 döndü; kaldırma görevi sildi.
* `--otomatik` ve `--sessiz`: her ikisinde stdout boş, exit 0, özet `gunluk.log`'a yazıldı; kullanım hatası stderr'e yazıldı ve stdout boş kaldı (exit 2).
* Zamanlanmış komut simülasyonu (düzeltmelerden sonra): `pythonw.exe "…\dersmerkezi.py" --otomatik --ders dosya-organizasyonu --sessiz` exit 0 ve log satırı üretildi.
* Görev Zamanlayıcı fiili yürütme: elle `Start-ScheduledTask` çalıştırması (`LastTaskResult=0`) ve tek seferlik tetikleyici (19:22:00) ile haftalık tetikleyici (PZT 19:24) fiilen ateşlendi; her koşuda `gunluk.log` satırı üretildi, test görevleri kaldırıldı. Böylece "zamanlanmış yürütme doğrulanamıyor" kısıtı kapatıldı; üretim görevinin 28.09.2026 09:00 koşusu `gunluk.log` ile teyit edilir.
* TUI iş mantığı (7 kontrol): scriptli tuş girdisiyle ana menü gezinme ve geri dönüş, ayarlar çoklu seçim/kaydetme, seçili derslerin çekme ekranına aktarılması, ilerleme geri bildirimi, tamamlanma ve uyarı çıktıları doğrulandı. Gerçek konsol görünümü kullanıcı tarafında.

### Sol Bağımsız Denetimi ve Kapatılan Bulgular (2026-09-21)

Kanonik codex köprüsü üzerinden GPT-5.6 Sol ile salt-okunur denetim yapıldı; rapor 9 bulgu ile `SONUC: BULGULAR` döndü. Tüm bulgular geçerli kabul edilip düzeltildi:

* Orta — `--otomasyon-kur` ders varlığını ve slug sınırını görev kurulumundan önce doğrulamıyordu; ayar yazımı başarısız olursa öksüz görev kalabiliyordu. Ders varlığı (`ders_getir`) ve slug 2-40 (Python + PS) ön koşul oldu; ayar yazımı başarısızsa yalnızca bu kuruluma ait görev geri alınır.
* Orta — Görev sahipliği yalnızca betik yolu alt dizesiyle belirleniyordu. Artık execute + tam argüman birebir karşılaştırılır; yol argümanda geçse bile yabancı/taklit görev reddedilir.
* Orta — `.part` indirmesi fsync olmadan nihai ada taşınıyordu. flush + os.fsync eklendi.
* Orta — `gunluk.kayit` kilit alınamazsa yine de yazıyordu. Fail-closed: 10 sn beklenir, alınamazsa dosya/rotasyon değiştirilmez; RuntimeError mesajı `--sessiz` dışında stderr'e de yazılır.
* Düşük — `yukle()` bozuk dosyayı kilitsiz karantinaya alıyordu. `_bozuk_yedekle` mutex altında; kilit alınamazsa karantina yapılmaz.
* Düşük — URL depo girdisinde şema/ana makine doğrulanmıyordu. Yalnızca `https` + `github.com`, kimlik/port/sorgu/parça/fazla yol reddedilir.
* Düşük — Ders adı kümesi tek tırnak kabul ediyordu (kabul 11 tırnak reddi der). Tırnak kümeden çıkarıldı.
* Düşük — Görev güncellemesi öncesi XML yedeği alınmıyordu. `belgeler/gecmis/gorev_<slug>_onceki.xml` yazılır.
* Düşük — Plan belgesindeki eski "tetikleme doğrulanamıyor" ifadeleri güncel sonuçla çelişiyordu. İlgili maddeler güncellendi.
* Risk listesinden kapatılanlar: `Kilit.__enter__` artık fail-closed; liste meta verisinde 200 MB üstü dosya indirilmeden reddedilir; `--sil` yalnızca bu kuruluma ait görevi kaldırır.

Düzeltme sonrası kanıtlar: birim 101/101, akış 50/50, taşıma hata 11/11, HTTP 4/4, kapsam 3/3, TUI 7/7; taklit ve yabancı görev reddi; yabancı görev varken ders silme reddi; üretim görevi yeni sahiplik kontrolüyle güncellendi ve XML yedeği yazıldı; doğrulama kapısı (compileall, `--cek` atlanan=1, `--durum` Ready) geçti.

İkinci denetim turu (aynı rota): 3 yeni bulgu (2 orta, 1 düşük). Kapatıldı: (1) otomasyon güncellemesinde geri alma artık yeni kurulan görevi silmekle mevcut görevi XML yedeğinden geri yüklemek arasında ayrım yapar ve geri alma hatasını gizlemez; (2) görev sahipliği `Execute` + tam `Arguments` birebir karşılaştırmayla `--sil`, `--otomasyon-kaldir`, TUI kaldırma, taşıma geri alma ve yeni `gorev_kaldir.ps1` katmanında uygulanır; argümanı eksik taklit görev de reddedilir; (3) planın eski tetikleme ifadeleri güncellendi. Yeni kanıtlar: birim 101/101 (XML'den geri yükleme, PS sahiplik reddi), akış 50/50 (taklit görev varyantları), taşıma 11/11, HTTP 4/4, kapsam 3/3, TUI 7/7.

Üçüncü denetim turu (aynı rota): 3 orta fail-closed boşluğu. Kapatıldı: (1) `gorev_durumu` ile mutasyon öncesi yok/bizim/yabancı ayrımı; sorgu hatası artık `False`'a indirgenmez, işlem yapılmadan yükseltilir; (2) `gorev_kaldir.ps1` beklenen execute + argümanı zorunlu parametre yapar; (3) `gorev_yukle.ps1` yedeği kaydettikten sonra eylemi beklenen execute + tam argümanla karşılaştırır, uyuşmazsa görevi kaldırıp geri yüklemeyi iptal eder. Kanıtlar: birim 102/102 (bozuk yedek geri yüklenmez), akış 50/50, taşıma 11/11, HTTP 4/4, kapsam 3/3, TUI 7/7; üretim görevi durumu `bizim`.

Dördüncü denetim turu (aynı rota): 2 orta boşluk. Kapatıldı: (1) görev sorgusu `Get-CimInstance` (TaskScheduler namespace) ile yapılır; yalnızca gerçek bulunamama `yok` sayılır, diğer sorgu hataları yükseltilir; (2) görevler tek eylem şartına bağlanır — `gorev_kur.ps1`, `gorev_kaldir.ps1`, `gorev_sorgu.ps1` eylem sayısını denetler, çok eylemli görev sahiplenilmez; `gorev_yukle.ps1` XML'i kayıt öncesinde ayrıştırıp tek eylem ve beklenen execute + tam argüman doğrular, kayıt sonrasında eylem sayısı ve içeriği yeniden denetler. Kanıtlar: birim 104/104 (çok eylemli görev reddi dahil), akış 50/50, taşıma 11/11, HTTP 4/4, kapsam 3/3, TUI 7/7; üretim görevi güncellemesi ve doğrulama kapısı geçti.

Beşinci denetim turu (aynı rota): 2 orta boşluk. Kapatıldı: (1) `gorev_kur.ps1` ve `gorev_kaldir.ps1` varlık sorgusunu da CIM ile yapar; yalnızca gerçek bulunamama "yok" sayılır, sorgu hatası mutasyondan önce fail-closed yükseltilir; (2) `gorev_yukle.ps1` ön denetimi `Actions` altındaki tüm eylem düğümlerini sayar ve yalnızca tek `Exec` düğümünü kabul eder (Exec+ComHandler gibi karışık yedekler kayıt öncesi reddedilir). Kanıtlar: birim 106/106 (karışık eylem yedeği reddi dahil), akış 50/50, taşıma 11/11, HTTP 4/4, kapsam 3/3, TUI 7/7.

Altıncı denetim turu (aynı rota): Tur 5 düzeltmeleri doğrulandı; yeni regresyon veya kalan fail-closed boşluğu bildirilmedi ve rapor `SONUC: ONAY` ile kapandı. Sol denetim raporu ve tur geçmişi: `belgeler/gecmis/sol-denetim-2026-09-21.md`.

Pil politikası kök nedeni ve üretim görevi elle tetikleme kanıtı (2026-09-21 akşamı):

* Üretim görevi elle tetiklendiğinde durum "Queued"da kalıyor, süreç üretmiyor ve `gunluk.log` satırı yazılmıyordu. Kök neden: makinenin pilde olması (`PowerOnline=False`) ve `New-ScheduledTaskSettingsSet` varsayılanının `DisallowStartIfOnBatteries=true` olması; bu, önceki denetimlerdeki "tetikleyici süreç üretmedi" gözlemini de açıklar.
* Düzeltme: `gorev_kur.ps1` görevi `-AllowStartIfOnBatteries -DontStopIfGoingOnBatteries` ile kaydeder. Üretim görevi yeniden kurulduğunda XML'de `DisallowStartIfOnBatteries=false` ve `StopIfGoingOnBatteries=false` doğrulandı.
* Kanıt: pildeyken `Start-ScheduledTask` sonrası `LastRunTime=21:02:43`, `LastTaskResult=0`, görev durumu `Ready` ve `gunluk.log` satırı `dosya-organizasyonu: yeni=0 guncellenen=0 atlanan=1 baglam=1 dogrulama_hatasi=0 donusum_hatasi=0`. Akış paketine "pilde calisma ayari" kontrolü eklendi (51/51).

### Depo ve Dökümantasyon (2026-09-21 akşamı)

* Türkçe dökümanlar eklendi: `belgeler/kurulum.md` (gereksinimler, kurulum, kullanım, doğrulama, sorun giderme) ve `belgeler/mimari.md` (modül haritası, veri akışı, şemalar, güvenlik değişmezleri, görev yaşam döngüsü); README döküman bağlantıları ve depo bilgisiyle güncellendi.
* `.gitignore` (dersler/, gunluk.log, ayarlar.json, geçici/yedek dosyalar hariç) ve `.gitattributes` (LF normalizasyonu, ikili dosyalar) eklendi.
* Private depo oluşturuldu ve ilk push yapıldı: <https://github.com/mecik-arda/DersMerkezi>. Komut: `gh repo create DersMerkezi --private --source . --remote origin --push` (gh 2.95, hesap `mecik-arda`, `repo` kapsamı).
* Araştırma için Gemini rotaları (3.8 Flash ve Pro) denendi; ikisi de `web_evidence_invalid` verdi (AGENTS'teki bilinen sınırlama). `gh repo create` söz dizimi yerel `gh repo create --help` çıktısı ve `gh auth status` ile doğrulandı.

Kabul kriterleri durumu: 1-18 fiili doğrulama dahil tamamlandı; kalan yalnızca üretim görevinin takvimli ilk koşusunun ve gerçek konsol TUI görünümünün kullanıcı tarafında teyidi.
