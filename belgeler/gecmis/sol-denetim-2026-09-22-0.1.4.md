# Sol Denetim Raporu — TUI Düzeltmeleri ve Teyitler 0.1.4 (2026-09-22)

Kapsam: 0.1.4 gerçek konsol turunda saptanan üç TUI kusurunun düzeltilmesi (menü sürüm satırı kalıcılığı, `_secim` ekran temizliğinin üst bilgiyi silmesi, sağlık satırlarında çift stil etiketi), üretim görevi takvim yapılandırması ve test göreviyle takvim ateşlemesi teyitleri ile doküman tutarlılığı. Bu dosyaya yalnızca denetim turu sonuçları eklenir.

## Tur 1

Denetim yalnız belirtilen salt-okunur bağlam dosyaları üzerinden yapıldı; test, build veya betik çalıştırılmadı.

### Bulgular

1. Orta — Dokümantasyon tutarlılığı — `AGENTS.md:13`, `belgeler/plan/2026-09-21-dersmerkezi-cli.md:4`, `belgeler/plan/2026-09-21-dersmerkezi-cli.md:247`, `belgeler/plan/2026-09-21-dersmerkezi-cli.md:253`, `belgeler/plan/2026-09-21-dersmerkezi-cli.md:295`

   Sorun: Üst seviye durum ve kapanış metinleri gerçek konsol TUI görünümünü hâlâ kullanıcı tarafında bekleyen teyit olarak gösteriyor.

   Kanıt: Aynı dosyanın `belgeler/plan/2026-09-21-dersmerkezi-cli.md:326-330` satırları 0.1.4 gerçek konsol akışını ve karakter kod noktalarını doğrulanmış olarak kaydediyor; `AGENTS.md:89` ve `CHANGELOG.md:11` de bu teyidin tamamlandığını söylüyor. Üretim görevinin 28.09.2026 tarihli kendi takvimli koşusunun gelecekte günlükten teyit edilecek olması ayrı ve hâlen geçerli bir sınırlamadır.

   Beklenen düzeltme: Eski durum cümlelerinden gerçek konsol teyidinin beklediği ifadeyi kaldır; 0.1.4 doğrulamasını üst seviye duruma taşı; yalnız üretim görevinin 28.09.2026 tarihli kendi takvimli koşusunu bekleyen teyit olarak bırak.

2. Orta — Doğrulama kanıtı izlenebilirliği — `belgeler/plan/2026-09-21-cli-gelistirme-onerileri.md:203`, `belgeler/plan/2026-09-21-dersmerkezi-cli.md:331`, `CHANGELOG.md:12`

   Sorun: 418/418 dağılımı kaydedilmiş olsa da 0.1.4 gerçek proje kapısı eksiksiz ve sonuçlarıyla belgelenmemiştir.

   Kanıt: İlk konum `--ayarlar`, `--ayarlar --ders ... --json`, `--cek --sessiz` ve `--durum` sonuçlarını özetliyor; ancak `--surum` çıktısının 0.1.4 olduğunu, `--saglik --ders` çağrısını ve çekme komutunun exit 0 sonucunu kaydetmiyor. İkinci ve üçüncü konumlar yalnız “kapı geçti” biçiminde genel iddia içeriyor. `merkez/__init__.py:1` sürüm sabitinin 0.1.4 olduğunu kanıtlar, fakat CLI kapısının gerçekten çalıştırıldığına ilişkin komut sonucu değildir.

   Beklenen düzeltme: 0.1.4 kanıt bölümüne `--cek --sessiz` exit 0 ve `atlanan=1`, `--surum` 0.1.4, `--ayarlar --json`, `--durum` ve `--saglik --ders` komutlarının sonuçlarını ayrı ayrı ekle; genel “kapı geçti” ifadesini bu kayda bağla.

3. Düşük — Kod kalitesi ve TUI yeniden çizimi — `merkez/arayuz.py:235-238`, `merkez/arayuz.py:401`, `merkez/arayuz.py:426-428`, `merkez/arayuz.py:45-47`

   Sorun: Dersler tablosu ve Durum satırları `_secim` çağrısından hemen önce doğrudan basılıyor; `_secim` girişte ekranı temizleyip aynı içeriği `ust` üzerinden yeniden basıyor.

   Kanıt: `dersler_ekrani` tabloyu 237. satırda basıp 238. satırda aynı nesneyi `ust` olarak veriyor. `durum_ekrani` satırları 426. satırda basıp 428. satırda aynı metni `ust` olarak veriyor. `_secim` 45. satırda ilk baskıyı temizlediğinden kalıcı çift görünüm veya içerik kaybı oluşmuyor; 46-47. satırlar içeriği her yeniden çizimde koruyor. Buna rağmen iki içerik de iki kez render ediliyor ve ilk render kısa süreli titreşim ile yakalama tabanlı testlerde çift çıktı üretebilir.

   Beklenen düzeltme: `dersler_ekrani` ve `durum_ekrani` içindeki `_secim` öncesi doğrudan içerik baskılarını kaldır; ilk ve sonraki çizimlerin tek sahibi olarak `_secim(ust=...)` yolunu kullan.

### Doğrulanan maddeler

* `merkez/arayuz.py:438-439` sürümü ana menünün `_secim` açıklamasında gösteriyor; ana menüye özgü ayrı sürüm paneli yok. `Panel` importu gereklidir; `merkez/arayuz.py:48` ve `merkez/arayuz.py:111` tarafından kullanılmaktadır.
* `_secim` `ust` içeriğini her döngüde yeniden basıyor. `_otomasyon_detay` başlık, tetik ve görev durumunu `ust` ile koruyor; dinamik ders, gün, saat ve durum alanları `merkez/arayuz.py:285-288` satırlarında `escape` ile kaçışlıdır.
* Sağlık kontrol satırları `merkez/arayuz.py:388-389` içinde `[renk]ad: mesaj[/renk]` biçimindedir; stil adı metne karışmıyor. Sonuç satırı `merkez/arayuz.py:394-395` içinde aynı açılış ve kapanış etiketi düzenini kullanıyor.
* Sürüm sabiti `merkez/__init__.py:1` içinde 0.1.4'tür ve `CHANGELOG.md:3` en güncel başlığıyla eşleşir. Arayüz sürümü bu sabiti import eder.
* Üretim görevi iddiaları belgeler arasında uyumludur: `CHANGELOG.md:13` ve `belgeler/plan/2026-09-21-dersmerkezi-cli.md:330` haftalık Pazartesi 09:00, `NextRunTime=28.09.2026 09:00`, `LastTaskResult=0`, 20:35:00 test tetiklemesi ve temizliği kaydeder; `belgeler/plan/2026-09-21-cli-gelistirme-onerileri.md:203` üretim seçimi ile görevin değişmediğini belirtir.
* 418/418 toplamı ve 204 + 153 + 47 + 14 dağılımı belgeler arasında tutarlıdır. Gerçek konsol kanıtında kod noktaları ile akış doğrulaması ve tamponun ekranın yalnız bir bölümünü yakaladığı sınırlaması `belgeler/plan/2026-09-21-cli-gelistirme-onerileri.md:200` ve `CHANGELOG.md:11` içinde açıkça kayıtlıdır.
* İncelenen kod değişikliği yüzeyi `_secim` ve onu kullanan TUI sunum akışlarıyla sınırlıdır; kilit, atomik yazım, indirme iş mantığı veya görev eylem dizesini değiştiren bir kod kanıtı yoktur.

### Genel kanı

Kritik bulgu: 0. Orta bulgu: 2. Düşük bulgu: 1. Genel sağlık skoru: 82/100. Sunum davranışının hedeflenen kalıcılık ve Rich biçimleme düzeltmeleri işlevsel görünmektedir; ancak yetkili durum belgelerindeki çelişki ve eksik 0.1.4 kapı kaydı kapanmadan sürüm kanıtı gönderilebilir durumda değildir.

SONUC: BULGULAR

## Tur 2

Denetim yalnız belirtilen salt-okunur bağlam dosyaları üzerinden yapıldı; test, build veya betik çalıştırılmadı.

1. Kapatıldı — Dokümantasyon tutarlılığı

   `belgeler/plan/2026-09-21-dersmerkezi-cli.md:4`, `:253`, `:295` ve `:326-332` gerçek konsol TUI akışını ve karakter kod noktalarını 0.1.4 doğrulaması olarak kaydediyor. Eski kullanıcı teyidi ifadeleri bu doğrulamaya bağlanmış; yalnız üretim görevinin 28.09.2026 tarihli kendi takvimli koşusunun `gunluk.log` ile teyidi bekleyen koşul olarak korunmuş. Bu ayrım Tur 1 beklentisiyle tutarlıdır.

2. Açık — Orta — Doğrulama kanıtı izlenebilirliği

   `belgeler/plan/2026-09-21-dersmerkezi-cli.md:331-332` 418/418 dağılımını ve istenen gerçek proje kapılarını somut sonuçlarıyla içeriyor. `CHANGELOG.md:12` 418/418 dağılımını, çekme exit 0 sonucunu, sürümü ve diğer kapıların özetini kaydediyor; ancak `compileall` exit 0 sonucunu içermiyor. Daha önemlisi `belgeler/plan/2026-09-21-cli-gelistirme-onerileri.md:203` hâlâ eski kaydı taşıyor: çekme sonucu `atlanan=1`, sürüm ve sağlık kapısı yok, `compileall` ile komutların exit 0 sonuçları belirtilmemiş. Böylece kapanış kararındaki “aynı sonuçlar öneri planı ve CHANGELOG'a işlendi” iddiası dosya içeriğiyle doğrulanamıyor.

   Beklenen düzeltme: Öneri planının 0.1.4 kanıt satırını son koşuyla uyumlu olarak `compileall` exit 0, `--cek --ders dosya-organizasyonu --sessiz` exit 0 (`atlanan=2`), `DersMerkezi 0.1.4`, `--ayarlar --json` exit 0, ayrıntılı `--durum` sonucu ve `--saglik --ders dosya-organizasyonu --json` exit 0 bilgileriyle güncelle. CHANGELOG 0.1.4 doğrulamasına da eksik `compileall` exit 0 kanıtını ekle ve çekme komutunu gerçek çağrıyla aynı biçimde kaydet.

3. Kapatıldı — Çift render

   `merkez/arayuz.py:232-236` içinde ders tablosu doğrudan basılmadan yalnız `_secim(..., ust=tablo)` yoluna veriliyor. `merkez/arayuz.py:397-423` içinde Durum satırları da doğrudan baskı veya gereksiz ekran temizliği olmadan yalnız `_secim(..., ust=...)` tarafından çiziliyor. İki ekranda da ilk ve sonraki renderların tek sahibi `_secim` olmuştur.

Kritik bulgu: 0. Orta bulgu: 1. Düşük bulgu: 0. Genel sağlık skoru: 94/100. Kod tarafındaki çift render düzeltmesi gönderilebilir durumdadır; sürüm kanıtının tamamı, öneri planı ve CHANGELOG kaydı kapanış kararındaki somut kapılarla eşleşene kadar bütünüyle onaylanamaz.

SONUC: BULGULAR

## Tur 3

Denetim yalnız belirtilen salt-okunur bağlam dosyaları üzerinden yapıldı; test, build veya betik çalıştırılmadı.

1. Açık — Orta — Doğrulama kanıtı izlenebilirliği

   `belgeler/plan/2026-09-21-cli-gelistirme-onerileri.md:203` ve `belgeler/plan/2026-09-21-dersmerkezi-cli.md:331-332` son koşunun 418/418 dağılımını ve gerçek proje kapısını birbiriyle uyumlu biçimde kaydediyor: `compileall` exit 0, `--cek --ders dosya-organizasyonu --sessiz` exit 0 (`atlanan=2`), `DersMerkezi 0.1.4`, ayarlar, durum ve sağlık sonuçları belgelenmiş. `CHANGELOG.md:12` içine eksik `compileall` exit 0 kanıtı eklenmiş ve diğer sonuçlar özetlenmiş; ancak çekme komutu hâlâ `--cek --sessiz` olarak yazıyor. Bu kayıt, Tur 2'de beklenen ve iki plan belgesinde yer alan gerçek çağrı biçimi `--cek --ders dosya-organizasyonu --sessiz` ile eşleşmediğinden bulgu bütünüyle kapatılmamıştır.

   Beklenen düzeltme: `CHANGELOG.md:12` içindeki çekme çağrısını `--cek --ders dosya-organizasyonu --sessiz` olarak kaydet; `compileall` ifadesini de diğer komutlarla aynı Markdown kod biçimine getir.

Kritik bulgu: 0. Orta bulgu: 1. Düşük bulgu: 0. Öneri planı ve ana plan kanıtları tutarlıdır; CHANGELOG'daki gerçek çağrı biçimi düzeltilene kadar kanıt izlenebilirliği onaylanamaz.

SONUC: BULGULAR

## Tur 4

Kapatıldı — Doğrulama kanıtı izlenebilirliği

`CHANGELOG.md` 0.1.4 doğrulama satırı `compileall` ifadesini Markdown kod biçiminde, çekme çağrısını `--cek --ders dosya-organizasyonu --sessiz` ve sağlık çağrısını `--saglik --ders dosya-organizasyonu --json` olarak kaydediyor. Öneri planı ile ana plan kanıtları aynı çağrı biçimlerini ve sonuçları kullanıyor. Tur 3'te açık kalan çelişki giderilmiştir; kalan bulgu yoktur.

SONUC: ONAY
