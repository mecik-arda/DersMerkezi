# Mimari

Bu belge DersMerkezi'nin modül yapısını, veri akışını, şemalarını ve güvenlik değişmezlerini özetler. Kurulum adımları için `belgeler/kurulum.md`, bağlayıcı geliştirme kuralları için `AGENTS.md` dosyasına bakın.

## Genel Bakış

DersMerkezi, Windows masaüstünde çalışan Python + Rich tabanlı çok dersli içerik çekme aracıdır. GitHub depolarındaki haftalık ders içeriklerini (ör. `Hafta 1.pdf`) indirir, Git blob SHA-1 ile doğrular, pypdf ile Markdown bağlamı üretir ve ders bazında haftalık Windows Görev Zamanlayıcı görevleri kurar. Sunum (TUI) ile iş mantığı ayrıdır; tüm işlevler başsız (headless) modda da kullanılabilir.

## Modül Haritası

* `dersmerkezi.py`: Giriş noktası; mod işleyicileri, çıkış kodları (0 başarı, 1 hata, 2 kullanım hatası) ve TUI başlatma.
* `merkez/komut.py`: Argüman ayrıştırıcı (`arguman_ayristirici`), mod/bayrak matrisi (`dogrula`), JSON çıktı sözleşmesi (`kok_json`, `json_yaz`, `hata_json_yaz`) ve Türkçe ayrıştırma hata eşlemesi.
* `merkez/ayarlar.py`: `ayarlar.json` şeması (sürüm 1), doğrulama (slug, ad, depo/URL, dal, desen, saat, gün, dosya adı; kaynak/teams/kimlik alanları; `veri_dogrula`/`ders_dogrula`), `yukle_salt`/`gorunum` salt-okunur görünüm, Teams kimlik redaksiyonu (`teams_ozeti`), `secili_ayarla` fail-closed seçim mutasyonu, atomik yazım ve tek nesil yedek.
* `merkez/indirici.py`: GitHub Contents API listeleme (isteğe bağlı kota meta verisi), akışlı indirme (`.part`), Git blob SHA-1 doğrulama, Markdown üretimi, kuru/`zorla`/`zorla-md` modları, durum şeması sürüm 2; Teams kaydı için geçici T0 koruması (T2'de gerçek adaptörle değiştirilir).
* `merkez/durum.py`: Ders ve görev durum kayıtları; isteğe bağlı ayrıntı (son çalışma, son sonuç, eylem, durum dosyası özeti); CLI ve TUI ortak.
* `merkez/saglik.py`: Salt-okunur sağlık denetimi (ortam, ayar şeması, ders kayıtları, kilit, günlük/durum erişimi); `--ders`/`--ag`/`--ayrintili` ile sınırlı ağ ve görev sorgusu.
* `merkez/tamamlama.py`: Parser'dan türetilen bayrak listesiyle PowerShell tamamlama betiği üretimi (atomik yazım).
* `merkez/zamanlayici.py`: PowerShell köprüsü (`-File` + adlandırılmış parametreler); görev kurma, kaldırma, sorgu, geri yükleme, tetikleme (`gorev_tetikle`), sahiplik denetimi ve `ders_sil_guvenli`.
* `merkez/tasima.py`: Eski PowerShell otomasyonunun kanıtlı ve geri alınabilir taşınması.
* `merkez/arayuz.py`: Rich + msvcrt TUI (menü, çoklu seçim, canlı ilerleme, kuru önizleme, Durum/Sağlık ekranı, tetikleme); dinamik metinler `rich.markup.escape` ile kaçışlanır.
* `merkez/gunluk.py`: `gunluk.log` (UTF-8, 1 MB rotasyon), `--log` için kök içi doğrulanmış alternatif yol, `kilit_dolu` yardımcısı ve `Local\DersMerkezi` mutex'i; kilit alınamazsa yazım atlanır (fail-closed).
* `merkez/ps/*.ps1`: Sabit PowerShell betikleri (`gorev_kur`, `gorev_kaldir`, `gorev_sorgu`, `gorev_tetikle`, `gorev_yukle`, `gorev_sil`).

## Veri Akışı

```
CLI/TUI
  -> ayarlar.yukle()            (şema doğrulama, bozuk dosya karantinası)
  -> indirici.depo_listele()    (Contents API, 429/5xx tekrarı)
  -> indirici._indir_akis()     (.part, boyut + blob SHA-1, flush + fsync)
  -> ayarlar._replace_tekrar()  (atomik taşıma, 3 deneme)
  -> indirici._md_uret()        (pypdf, şablon, md_sha/md_boyut)
  -> durum kaydı                 (indirilenler.json, mutex altında)
  -> gunluk.kayit()             (kategori sayaçları)
```

Zamanlanmış koşularda `pythonw.exe` ile `--otomatik --ders <kimlik> --sessiz` çalışır; `--otomatik` seçili olma şartını atlar ve yalnızca günlüğe yazar.

## CLI Sözleşmeleri

* **Mod matrisi:** Aynı anda en fazla bir mod (`--listele`, `--ekle`, `--sil`, `--cek`, `--durum`, `--ayarlar`, `--saglik`, `--otomasyon-kur`, `--otomasyon-kaldir`, `--tasima`, `--surum`, `--oto-tamamlama`); `--otomatik` tek başına zamanlanmış koşu modudur veya `--cek` ile birleşir. Moda özgü seçenekler argparse'ta `None` varsayılanla tanımlanır; gerçek varsayılanlar doğrulama sonrası uygulanır. İhlalde stderr'e Türkçe mesaj + exit 2, hiçbir yan etki yoktur.
* **Kanal politikası:** `--json` başarıda stdout'ta tek JSON nesnesi (`json_surum`, `komut`, `uygulama_surum`); çalışma hatasında stdout boş, stderr'de JSON hata nesnesi + insan satırı; kullanım hatasında düz Türkçe. JSON modunda `gunluk.kayit` insan metnini stderr'e yazar; global çıktı durumu `main` içinde `try/finally` ile geri yüklenir.
* **Kuru çalışma:** `--cek --kuru` hedef klasör oluşturmaz, `.part`/geçici dosya silmez, durum dosyası yazmaz ve bozuk durumu karantinaya almaz; yalnız listeleme + yerel boyut/SHA karşılaştırması yapar, planlanan baytı raporlar.
* **Sağlık:** Varsayılan ağsız ve salt-okunur; hiçbir dosya/dizin/yedek/günlük oluşturmaz. Ağ yalnız `--ders` (tek çağrı) veya `--ag` (ilk 10 ders) ile; görev sorgusu yalnız `--ders`/`--ayrintili` (en fazla 20 ders) ile yapılır. Kota meta verisi `depo_listele(meta=True)` üzerinden `limit/kalan/sifirla` olarak döner.
* **Tetikleme:** `--tetikle` yalnız kurulum başarısından sonra çalışır; öncesinde tek-eylem sahipliği yeniden doğrulanır (sorgu hatası fail-closed, yabancı görev başlatılmaz). Tamamlanma ölçütü: durum `Running`/`Queued` dışına çıkar ve `LastRunTime` referanstan yenidir; 60 sn zaman aşımında koşul teşhisi yazılır ve exit 1 döner.
* **Günlük yolu:** `--log` hedefi `realpath` ile kök içinde olmalı, mevcut dizin veya reparse noktası olamaz; her yazımdan önce yeniden doğrulanır ve 1 MB `.old` rotasyonu korunur.
* **Ayar görünümü/seçim:** `--ayarlar` salt-okunur görünüm (`ayarlar.gorunum`, `yukle_salt`) ve `--secili` mutasyonu (`ayarlar.secili_ayarla`) bozuk ayarda karantina yapmaz; mutasyon kilit + atomik yazım + yedek zincirini kullanır; görünüm ağ/görev/indirme izi bırakmaz.
* **Arayüz eşliği:** CLI ve TUI aynı ortak işlevleri çağırır (`indirici.indir_ders`, `zamanlayici.gorev_kur_guvenli`, `zamanlayici.gorev_tetikle`, `zamanlayici.ders_sil_guvenli`, `durum.kayitlar`, `saglik.denetle`, `ayarlar.gorunum`, `ayarlar.secili_ayarla`); 0/1/2 yalnızca CLI süreç sonucudur, TUI hata sınıflarını Türkçe iletiye dönüştürüp menü döngüsünü korur.

## Şemalar

### ayarlar.json (sürüm 1)

```json
{
  "surum": 1,
  "dersler": {
    "<kimlik>": {
      "ad": "...",
      "kaynak": "github",
      "depo": "owner/repo",
      "dal": "main",
      "desen": "Hafta*.pdf",
      "secili": true,
      "otomasyon": {"aktif": false, "gunler": [], "saat": "09:00", "gorevAdi": "DersMerkezi_<kimlik>"}
    },
    "<teams-kimlik>": {
      "ad": "...",
      "kaynak": "teams",
      "teams": {"tenantId": "<guid>", "driveId": "b!...", "itemId": "01ABC..."},
      "dal": "main",
      "desen": "Hafta*.pdf",
      "secili": true,
      "zayif_dogrulama": false,
      "otomasyon": {"aktif": false, "gunler": [], "saat": "09:00", "gorevAdi": "DersMerkezi_<teams-kimlik>"}
    }
  }
}
```

`kaynak` yoksa `github` kabul edilir; mevcut kayıtlar değişmeden çalışır (şema sürümü artırılmaz). GitHub kaydında `teams` ve `zayif_dogrulama` yasaktır; Teams kaydında `driveId`/`itemId` zorunlu, `tenantId` opsiyonel, `depo` yasaktır. Kimlik alanları güvenli karakter kümesi ve uzunluk sınırıyla doğrulanır; değerler hata mesajına tam yazılmaz. Tam kimlikler yalnız `ayarlar.json`'da bulunur; görünüm ve JSON çıktısında `teams:{ilk6}…/{ilk6}…` biçiminde redakte edilir.

### indirilenler.json (sürüm 2)

```json
{
  "surum": 2,
  "guncelleme": "YYYY-MM-DDTHH:MM:SS",
  "dosyalar": {
    "<dosya>": {
      "sha": "<git blob sha1>",
      "boyut": 0,
      "indirildi": "YYYY-MM-DDTHH:MM:SS",
      "md": true,
      "kaynak_url": "https://raw.githubusercontent.com/...",
      "md_sha": "<sha256>",
      "md_boyut": 0,
      "md_uretildi": "YYYY-MM-DDTHH:MM:SS"
    }
  }
}
```

## Kaynak Soyutlaması (0.2.0 T0 taslağı)

* Kaynak türleri: `github` (mevcut tam akış) ve `teams` (Microsoft Teams kanal dosyaları / SharePoint belge kitaplığı, Microsoft Graph üzerinden). Kaynak ayrımı ders kaydındaki isteğe bağlı `kaynak` alanıyla yapılır; alan yoksa `github` kabul edilir (additive, şema sürümü artmaz).
* T0 (bu dilim): kaynak/teams şema doğrulaması, CLI matrisi, redakte görünüm ve doküman iskeleti hazırdır. Teams kaydıyla indirme çağrısı `indirici.indir_ders` içindeki geçici korumayla fail-closed reddedilir (Türkçe hata + exit 1); bu koruma T2'de gerçek adaptörle değiştirilecek ve T2 kontrol listesinde izlenir.
* T0 sağlık uyumu: `--saglik --ders <teams>` ve `--saglik --ag` Teams girdisini çökmeksizin ağ çağrısı yapmadan uyarı olarak raporlar; gerçek Graph sağlık yoklaması T3'tedir.
* T1: Graph istemcisi (client credentials token, listeleme sayfalama denetimi, 302 takipli indirme, QuickXorHash/SHA1 yerel doğrulama).
* T2: `indirici` içinde kaynak dallanması (`kaynak == "teams"`), ortak akış korunur: 200 MB/liste kapıları, dosya adı doğrulaması, atomik yazım, Markdown üretimi, durum kaydı ve idempotans.
* Sır sınırı: `TEAMS_CLIENT_SECRET` yalnız ortam değişkeninde; `TEAMS_CLIENT_ID` ve `TEAMS_TENANT_ID` ortam değişkeniyle verilebilir. Tenant önceliği: ders kaydı > komut satırı > ortam değişkeni. Token yalnız bellekte tutulur; ön kimlikli indirme URL'si günlük/durum/Markdown'a yazılmaz.
* Kimlik redaksiyonu: tam Teams kimlikleri yalnız `ayarlar.json`'da; `--ayarlar`/`--durum` JSON ve insan çıktısında `teams:<ilk6>…/<ilk6>…` özeti gösterilir. Doğrulama hatalarında kimlik değerleri tam yazılmaz.

## Güvenlik ve Değişmezler

* Girdi doğrulama: slug `^[a-z0-9]+(?:-[a-z0-9]+)*$` (2-40), ders adı 2-120 güvenli küme, depo `owner/repo` veya yalnızca `https://github.com/owner/repo[.git]`, dal `..` ve boşluk yasak, desen 64 karakter, saat `SS:DD`, kapalı gün kümesi, dosya adlarında yol kaçışı/ayrılmış aygıt/180+ reddi.
* Enjeksiyon sertleştirmesi: görev eyleminde kullanıcı metni yoktur; PowerShell çağrıları `-File` ve adlandırılmış parametrelerledir; `subprocess` liste biçimi kullanılır.
* Bütünlük: PDF'ler `blob <boyut>\0<veri>` biçiminde hesaplanan Git blob SHA-1 ile doğrulanır; Markdown bağlamı `md_sha`/`md_boyut` ile denetlenir, bozuk veya eksikse yeniden üretilir.
* Atomik yazım: geçici dosya + `flush` + `os.fsync` + `os.replace`; kilitli hedefte 3 deneme ve temizlik.
* Eşzamanlılık: tüm yazma işlemleri ve günlük rotasyonu `Local\DersMerkezi` mutex'i altındadır; kapsam aynı kullanıcı oturumudur.
* Görev sahipliği: güncelleme, kaldırma ve geri alma yalnızca execute + tam argüman birebir eşleşiyorsa ve görev tek eylem içeriyorsa yapılır; mutasyondan önce durum (yok/bizim/yabancı) sorgulanır, sorgu hatası fail-closed yükseltilir.
* Ağ: yalnızca HTTPS; token loglanmaz; 429/5xx için `Retry-After` destekli sınırlı tekrar.

## Görev Yaşam Döngüsü

1. `gorev_kur_guvenli`: durum sorgusu → yabancıysa ret → kurulum → ayar yazımı.
2. Kurulumda mevcut görev varsa XML yedeği alınır (`belgeler/gecmis/gorev_<kimlik>_onceki.xml`).
3. Ayar yazımı başarısız olursa: yeni görev kaldırılır; mevcut görev XML yedeğinden geri yüklenir ve geri yükleme sonrası eylem birebir doğrulanır; hata gizlenmez.
4. Görev ayarları: `StartWhenAvailable`, `MultipleInstances IgnoreNew`, 30 dakika zaman aşımı, pilde çalışma.
5. Ders silme: yalnızca bu kuruluma ait görev kaldırılır; kaldırılamazsa kayıt silinmez.

## Test ve Doğrulama

* Birim ve akış paketleri geçici klasördeki proje kopyasında koşturulur; repoya test dosyası eklenmez.
* Kapsam: girdi doğrulama, enjeksiyon, idempotans, bozuk md/pdf, `.part` telafisi, kilit ve mutex davranışı, HTTP hata matrisi (404/401/403/429/5xx), görev senaryoları, taşıma geri alma, TUI iş mantığı.
* Kanıtlar ve tur geçmişi: `belgeler/plan/2026-09-21-dersmerkezi-cli.md` ve `belgeler/gecmis/sol-denetim-2026-09-21.md`.

## Bilinen Sınırlamalar

* Gerçek konsol TUI görünümü ve görsel kalite kullanıcı tarafında değerlendirilir; iş mantığı scriptli tuş girdisiyle doğrulanmıştır.
* Antigravity/Gemini web rotası bu ortamda `web_evidence_invalid` verir; dış doğrulamalar yerel kaynak ve resmi dokümanla yapılır.
* Kilit kapsamı aynı kullanıcı oturumudur; farklı kullanıcı oturumları kapsam dışıdır.
