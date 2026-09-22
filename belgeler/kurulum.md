# Kurulum ve Kullanım Kılavuzu

Bu belge DersMerkezi'nin kurulumunu, ilk kullanımını ve sorun giderme adımlarını içerir. Proje genel bakışı için `README.md`, teknik ayrıntılar için `belgeler/mimari.md`, geliştirme kuralları için `AGENTS.md` dosyasına bakın.

## Gereksinimler

* Windows 10/11 (uzun yol desteği önerilir; bu makinede `LongPathsEnabled=1`).
* Python 3.13 (Anaconda dağıtımı bu makinede kullanılmaktadır: `C:\Users\ardam\anaconda3\python.exe`).
* Python paketleri: `rich`, `requests`, `pypdf`.

```powershell
python -m pip install rich requests pypdf
```

* Opsiyonel: kamuya açık depolarda GitHub token gerekmez; API limiti sorunlarında `GITHUB_TOKEN` ortam değişkeni tanımlanabilir. Token hiçbir zaman günlüğe yazılmaz.

## Kurulum

1. Depoyu klonlayın (private):

```powershell
git clone https://github.com/mecik-arda/DersMerkezi.git
```

2. Proje kökünde başlatıcıyı çalıştırın:

```powershell
.\baslat.cmd
```

Masaüstü kısayolu `C:\Users\ardam\Desktop\DersMerkezi.bat` dosyası proje içindeki `baslat.cmd` dosyasını çağırır; `chcp 65001` ile UTF-8 kod sayfasına geçilir.

## İlk Kullanım

### Ders ekleme

TUI: `Dersler` → `Yeni ders ekle` adımlarını izleyin.

Komut satırı:

```powershell
python dersmerkezi.py --ekle --ad "Dosya Organizasyonu" --depo emirozturk/Dosya-Organizasyonu-2026 --desen "Hafta*.pdf"
```

* Depo adresi `owner/repo` ya da `https://github.com/owner/repo[.git]` biçiminde verilebilir; yalnızca GitHub HTTPS adresleri kabul edilir.
* Ders adı 2-120 karakterdir ve güvenli karakter kümesiyle sınırlıdır (tırnak, noktalı virgül, `&`, `$`, köşeli parantez gibi karakterler reddedilir).
* Aynı kimlik veya yalnızca büyük-küçük harf farkı olan ikinci kayıt reddedilir.

### Çekme

```powershell
python dersmerkezi.py --cek --ders dosya-organizasyonu --sessiz
python dersmerkezi.py --cek --ders dosya-organizasyonu --kuru
python dersmerkezi.py --cek --zorla --sessiz
python dersmerkezi.py --cek --kilit-bekle 60 --sinir 100
```

* İçerikler `dersler/<kimlik>/` altına indirilir; dosyalar Git blob SHA-1 ile doğrulanır.
* Her PDF için aynı adlı bir Markdown bağlam dosyası üretilir (`Hafta 1.md` gibi).
* İkinci koşuda yerel dosyalar yeniden doğrulanır; sağlamsa yeniden indirilmez (`atlanan=1`).
* `--kuru` hiçbir dosya yazmaz (hedef klasör, `.part` ve durum dosyası dâhil); planlanan yeni/güncellenecek/atlanan sayıları ve indirilecek toplam bayt raporlanır.
* `--zorla` indirmeyi ve bağlamı, `--zorla-md` yalnız bağlamı yeniler; SHA ve `md_sha`/`md_boyut` doğrulaması her durumda uygulanır.
* `--sinir 1-200` aralığında yalnız düşürülebilir; varsayılan 200 MB.
* `--kilit-bekle 0-3600` saniye: kilit doluyken sınırlı bekler, alınamazsa uyarıyla atlanır (exit 0).
* 200 MB üstü dosyalar liste aşamasında reddedilir.
* Aynı anda ikinci bir çalışma `Local\DersMerkezi` kilidi nedeniyle atlanır.

### Sağlık kontrolü

```powershell
python dersmerkezi.py --saglik
python dersmerkezi.py --saglik --ders dosya-organizasyonu
python dersmerkezi.py --saglik --ag
python dersmerkezi.py --saglik --ayrintili
```

* Varsayılan çağrı ağ kullanmaz: Python/paket sürümleri, `ayarlar.json` şeması, ders kayıtları, kilit durumu, günlük ve durum dosyası erişimi denetlenir; hiçbir dosya oluşturulmaz veya değiştirilmez.
* `--ders` yalnız o ders için tek depo çağrısı yapar (kota bilgisi yanıttan okunur); `--ag` ilk 10 dersi listeler, atlananları raporlar; `--ag` ile `--ders` birlikte kullanılamaz.
* `--ayrintili` görev sorgularını ekler (ağsız, en fazla 20 ders).
* Sorun yoksa exit 0 (uyarılar 0'ı değiştirmez), en az bir sorun varsa exit 1.

### JSON çıktı

```powershell
python dersmerkezi.py --durum --json
python dersmerkezi.py --cek --ders dosya-organizasyonu --json --sessiz
python dersmerkezi.py --saglik --json
python dersmerkezi.py --surum --json
```

* `--json` şu modlarla geçerlidir: `--durum`, `--listele`, `--cek`, `--saglik`, `--surum`, `--oto-tamamlama`, `--ayarlar`.
* Başarılı koşuda stdout yalnızca tek JSON nesnesi içerir (`json_surum`, `komut`, `uygulama_surum`); insan-okur metinler stderr'e gider.
* Çalışma hatasında (exit 1) stderr'e `{json_surum, komut, hata:{sinif, mesaj}}` ve insan satırı yazılır, stdout boş kalır. Kullanım hatası (exit 2) düz Türkçe metindir, JSON içermez.
* `--json` ile `--ayrintili` birlikte kullanılamaz.

### Zamanlanmış görev

```powershell
python dersmerkezi.py --otomasyon-kur --ders dosya-organizasyonu --gunler PZT,CAR --saat 09:00
python dersmerkezi.py --otomasyon-kur --ders dosya-organizasyonu --hafta-ici
python dersmerkezi.py --otomasyon-kur --ders dosya-organizasyonu --tetikle
python dersmerkezi.py --otomasyon-kaldir --ders dosya-organizasyonu
python dersmerkezi.py --durum --ayrintili
```

* Görev adı `DersMerkezi_<kimlik>` biçimindedir; görevler `pythonw.exe` ile sessiz çalışır.
* `StartWhenAvailable` (kaçırılan koşu telafisi), `MultipleInstances IgnoreNew` (üst üste çalışma engeli), 30 dakika zaman aşımı ve **pilde çalışma** etkindir.
* Güncelleme öncesi mevcut görev XML'i `belgeler/gecmis/gorev_<kimlik>_onceki.xml` olarak yedeklenir.
* Yabancı veya taklit görevler (farklı eylem, çok eylemli görev) reddedilir; ders silme yalnızca bu kuruluma ait görevi kaldırır.
* `--tetikle` görevi bir kez çalıştırıp `LastTaskResult` değerini raporlar: `0` başarı, `267011` hiç çalışmadı; diğer kodlar ham/hex olarak yazılır. Zaman aşımında koşul teşhisi (pil, boşta, ağ, oturum türü) raporlanır ve exit 1 döner; tetikleme hatası kurulumu geri almaz.
* `--her-gun` (yedi gün) ve `--hafta-ici` (PZT-CUM) kısayolları `--gunler` ile birlikte kullanılamaz.

### Ayar görünümü ve seçim

```powershell
python dersmerkezi.py --ayarlar
python dersmerkezi.py --ayarlar --ders dosya-organizasyonu
python dersmerkezi.py --ayarlar --ders dosya-organizasyonu --secili hayir
python dersmerkezi.py --ayarlar --json
```

* `--ayarlar` ders ayarlarını (ad, depo, dal, desen, seçili durumu, otomasyon özeti) salt-okunur gösterir; ağ çağrısı, görev sorgusu ve dosya yazımı yapmaz; bozuk `ayarlar.json` karantinaya alınmaz (exit 1).
* `--secili evet|hayir` yalnız `--ayarlar` ile ve `--ders` ile birlikte kullanılır; seçim değişikliği `Local\DersMerkezi` kilidi, atomik yazım ve tek nesil yedek zincirinden geçer. Bilinmeyen ders exit 2, kullanım hataları dosya izi bırakmaz.
* `--json` çıktısı `{json_surum, komut, uygulama_surum, dersler[]}`; mutasyon sonrası yeni durum döner. `--sessiz` yalnız insan-okur satırları bastırır, JSON stdout'ta kalır.
* TUI'deki "Ayarlar" ekranı aynı ortak işlevi (`ayarlar.secili_ayarla`) kullanır.

### Ders silme

```powershell
python dersmerkezi.py --sil --ders dosya-organizasyonu --onayla
```

* `--sil` yalnızca `--onayla` ile çalışır; onaysız çağrı exit 2 verir ve hiçbir değişiklik yapmaz. TUI'de mevcut `Confirm` akışı korunur.
* Varsa görev önce kaldırılır; görev kaldırılamazsa ders kaydı silinmez.

### Günlük yolu ve tamamlama

```powershell
python dersmerkezi.py --log alt/gunluk.log --durum
python dersmerkezi.py --oto-tamamlama
```

* `--log` yolu `realpath` ile proje kökü içinde olmak zorundadır; hedef mevcut bir dizin olamaz, junction/reparse noktası reddedilir; yazım öncesi yeniden doğrulanır ve aynı 1 MB `.old` rotasyonu uygulanır. Kök dışı yol exit 2, yazılamayan yol exit 1.
* `--oto-tamamlama` bayrak listesini parser'dan türetip `tamamlama/dersmerkezi-tamamlama.ps1` dosyasını atomik yazar; klasör `.gitignore` dışındadır. v1 yalnız PowerShell ve yalnız bayrak tamamlar.
* Sürüm sorgusu: `python dersmerkezi.py --surum` (tek kaynak `merkez/__init__.py`).

## Doğrulama

```powershell
python -m compileall merkez dersmerkezi.py
python dersmerkezi.py --cek --ders dosya-organizasyonu --sessiz
python dersmerkezi.py --durum
python dersmerkezi.py --surum
python dersmerkezi.py --durum --json
python dersmerkezi.py --saglik
```

Beklenen: derleme hatasız; çekme `atlanan=1` ile 0 kodu döner; durum çıktısında görev `kayitli (Ready)` görünür; `--surum` `CHANGELOG.md` son sürümüyle aynı; JSON çıktısı `json.loads` ile ayrıştırılabilir; sağlık kontrolü sorunsuzsa 0 döner. Ayrıntılı günlük: `gunluk.log`.

## Sorun Giderme

* **Görev "Queued" kalıyor ve hiç çalışmıyor:** pil politikası. Görevler `-AllowStartIfOnBatteries -DontStopIfGoingOnBatteries` ile kaydedilir; eski kayıtlar için `--otomasyon-kur` komutunu yeniden çalıştırın.
* **`403` / "GitHub API limiti doldu":** kimliksiz API saati 60 istekle sınırlıdır. Bir süre bekleyin veya `GITHUB_TOKEN` tanımlayın.
* **"Baska bir calisma suruyor" / işlem atlanıyor:** başka bir DersMerkezi örneği `Local\DersMerkezi` kilidini tutuyor; çalışma bitince tekrar deneyin.
* **`ayarlar.json` bozuldu:** dosya zaman damgalı olarak yedeklenir (`ayarlar.json.bozuk-*`) ve uygulama boş ayarla başlar; kayıtları yeniden ekleyin.
* **Kilitli PDF (açık okuyucu/antivirüs):** yazım 3 deneme sonrası anlaşılır hata verir ve geçici dosyalar temizlenir; dosyayı kapatıp yeniden deneyin.
* **`--tasima` komutu:** taşıma bir kez çalıştırılmıştır; normal koşullarda yeniden çalıştırılmaz. Doğrulama için yalnızca `python dersmerkezi.py --tasima --kuru` kullanın; bu komut gerçek kanıtı değiştirmez.

## Günlük ve Durum Dosyaları

* `gunluk.log`: UTF-8, 1 MB üzeri `.old` rotasyonu; `[tarih] [SEVİYE] mesaj` biçimindedir.
* `dersler/<kimlik>/indirilenler.json`: durum şeması sürüm 2 (`sha`, `boyut`, `indirildi`, `md`, `kaynak_url`, `md_sha`, `md_boyut`, `md_uretildi`).
* `ayarlar.json`: ders kayıtları ve otomasyon ayarları (şema sürüm 1); `.gitignore` dışındadır.
