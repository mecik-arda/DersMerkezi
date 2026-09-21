# Mimari

Bu belge DersMerkezi'nin modül yapısını, veri akışını, şemalarını ve güvenlik değişmezlerini özetler. Kurulum adımları için `belgeler/kurulum.md`, bağlayıcı geliştirme kuralları için `AGENTS.md` dosyasına bakın.

## Genel Bakış

DersMerkezi, Windows masaüstünde çalışan Python + Rich tabanlı çok dersli içerik çekme aracıdır. GitHub depolarındaki haftalık ders içeriklerini (ör. `Hafta 1.pdf`) indirir, Git blob SHA-1 ile doğrular, pypdf ile Markdown bağlamı üretir ve ders bazında haftalık Windows Görev Zamanlayıcı görevleri kurar. Sunum (TUI) ile iş mantığı ayrıdır; tüm işlevler başsız (headless) modda da kullanılabilir.

## Modül Haritası

* `dersmerkezi.py`: Giriş noktası; komut satırı argümanları, çıkış kodları (0 başarı, 1 hata, 2 kullanım hatası) ve TUI başlatma.
* `merkez/ayarlar.py`: `ayarlar.json` şeması (sürüm 1), doğrulama (slug, ad, depo/URL, dal, desen, saat, gün, dosya adı), atomik yazım ve tek nesil yedek.
* `merkez/indirici.py`: GitHub Contents API listeleme, akışlı indirme (`.part`), Git blob SHA-1 doğrulama, Markdown üretimi, durum şeması sürüm 2.
* `merkez/zamanlayici.py`: PowerShell köprüsü (`-File` + adlandırılmış parametreler); görev kurma, kaldırma, sorgu, geri yükleme, sahiplik denetimi.
* `merkez/tasima.py`: Eski PowerShell otomasyonunun kanıtlı ve geri alınabilir taşınması.
* `merkez/arayuz.py`: Rich + msvcrt TUI (menü, çoklu seçim, canlı ilerleme); dinamik metinler `rich.markup.escape` ile kaçışlanır.
* `merkez/gunluk.py`: `gunluk.log` (UTF-8, 1 MB rotasyon) ve `Local\DersMerkezi` mutex'i; kilit alınamazsa yazım atlanır (fail-closed).
* `merkez/ps/*.ps1`: Sabit PowerShell betikleri (`gorev_kur`, `gorev_kaldir`, `gorev_sorgu`, `gorev_yukle`, `gorev_sil`).

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

## Şemalar

### ayarlar.json (sürüm 1)

```json
{
  "surum": 1,
  "dersler": {
    "<kimlik>": {
      "ad": "...",
      "depo": "owner/repo",
      "dal": "main",
      "desen": "Hafta*.pdf",
      "secili": true,
      "otomasyon": {"aktif": false, "gunler": [], "saat": "09:00", "gorevAdi": "DersMerkezi_<kimlik>"}
    }
  }
}
```

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
