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
```

* İçerikler `dersler/<kimlik>/` altına indirilir; dosyalar Git blob SHA-1 ile doğrulanır.
* Her PDF için aynı adlı bir Markdown bağlam dosyası üretilir (`Hafta 1.md` gibi).
* İkinci koşuda yerel dosyalar yeniden doğrulanır; sağlamsa yeniden indirilmez (`atlanan=1`).
* 200 MB üstü dosyalar liste aşamasında reddedilir.
* Aynı anda ikinci bir çalışma `Local\DersMerkezi` kilidi nedeniyle atlanır.

### Zamanlanmış görev

```powershell
python dersmerkezi.py --otomasyon-kur --ders dosya-organizasyonu --gunler PZT,CAR --saat 09:00
python dersmerkezi.py --otomasyon-kaldir --ders dosya-organizasyonu
python dersmerkezi.py --durum
```

* Görev adı `DersMerkezi_<kimlik>` biçimindedir; görevler `pythonw.exe` ile sessiz çalışır.
* `StartWhenAvailable` (kaçırılan koşu telafisi), `MultipleInstances IgnoreNew` (üst üste çalışma engeli), 30 dakika zaman aşımı ve **pilde çalışma** etkindir.
* Güncelleme öncesi mevcut görev XML'i `belgeler/gecmis/gorev_<kimlik>_onceki.xml` olarak yedeklenir.
* Yabancı veya taklit görevler (farklı eylem, çok eylemli görev) reddedilir; ders silme yalnızca bu kuruluma ait görevi kaldırır.

## Doğrulama

```powershell
python -m compileall merkez dersmerkezi.py
python dersmerkezi.py --cek --ders dosya-organizasyonu --sessiz
python dersmerkezi.py --durum
```

Beklenen: derleme hatasız; çekme `atlanan=1` ile 0 kodu döner; durum çıktısında görev `kayitli (Ready)` görünür. Ayrıntılı günlük: `gunluk.log`.

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
