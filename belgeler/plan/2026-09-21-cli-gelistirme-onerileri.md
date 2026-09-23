# DersMerkezi CLI Geliştirme Önerileri - Plan Belgesi

Tarih: 2026-09-21
Durum: Uygulandı (Öncelik 1-4; sürüm 0.1.2-0.1.5; Sol denetimlerinden ONAY; depo public)
Kapsam: `dersmerkezi.py` komut satırı arayüzünün genişletilmesi
İlgili belgeler: `belgeler/plan/2026-09-21-dersmerkezi-cli.md` (ana plan ve kanıtlar), `belgeler/mimari.md`, `AGENTS.md`

## Amaç

Mevcut CLI seçeneklerini ( `--listele`, `--ekle`, `--sil`, `--cek`, `--durum`, `--otomasyon-kur`, `--otomasyon-kaldir`, `--otomatik`, `--tasima`, `--kuru`, `--onayla`, `--sessiz`, `--ad`, `--depo`, `--dal`, `--desen`, `--slug`, `--ders`, `--gunler`, `--saat` ) kullanıcı deneyimi, otomasyon uyumu ve güvenlik açısından iyileştirmek; yeni seçenekleri projenin değişmezleriyle (çıkış kodları, enjeksiyon sertleştirmesi, mutex, atomik yazım, Türkçe arayüz) uyumlu biçimde tanımlamak.

Bu belge, öncelik sırasına göre uygulanmış maddeleri ve her maddenin kabul kriteri ile doğrulama yöntemini içerir.

## Kapsam İlkesi: Arayüz Eşliği

* Her kullanıcıya dönük özellik CLI arayüzüne eklenir: argparse seçeneği, mevcut `-h/--help` çıktısında Türkçe açıklama ve dokümantasyon (README, `belgeler/kurulum.md`) aynı dilimde tamamlanır; özellik yalnız iç işlev olarak bırakılmaz (`--yardim` diye ayrı bir bayrak eklenmez; mevcut yardım yüzeyi kullanılır).
* Ortak işlev kuralı: CLI ve TUI aynı iş mantığı işlevlerini çağırır (ör. `indirici.indir_ders`, `zamanlayici.gorev_kur_guvenli`, `ayarlar.*`, yeni `merkez/saglik.py`); TUI hiçbir iş mantığını kopyalamaz. Ortak işlevler sonuç/hata sınıfı döndürür; 0/1/2 çıkış kodları yalnızca CLI süreç sonucudur, TUI bu sınıfları Türkçe ve kaçışlı iletiye dönüştürüp menü döngüsünü korur.
* Salt CLI seçenekleri ve çıktı kipleri: etkileşimsiz veya makine tüketimli yüzeyler (`--json`, `--oto-tamamlama`, `--log`, `--sessiz`) TUI'ye taşınmaz; TUI'de bunların yokluğu varsayılan davranıştır. `--log` bir çıktı biçimi değil günlük hedefi seçeneğidir; dışlama ölçütü "makine tüketimli/etkileşimsiz yüzey" olmasıdır.
* Arayüz eşliği, mevcut değişmezleri değiştirmez: TUI de aynı mutex, atomik yazım, sahiplik denetimi, Türkçe sunum ve `rich.markup.escape` kurallarına uyar.

### Eşlik Listesi (bağlayıcı)

| Plan maddesi | CLI seçeneği | TUI karşılığı | Sınıf | Ortak işlev |
|---|---|---|---|---|
| 1.1 JSON | `--json` | — (TUI tablo/panel gösterir) | Salt CLI | ortak serileştirme noktası |
| 1.2 Kuru çekme | `--cek --kuru` | Dersleri Çek menüsünde "Önizleme (kuru çalışma)" | TUI eşli | `indirici.indir_ders(kuru=True)` |
| 1.3 Silme onayı | `--sil --onayla` | Ders çıkar ekranındaki mevcut `Confirm` | TUI eşli | `ayarlar.ders_sil` + görev kaldırma zinciri |
| 1.4 Kombinasyon doğrulaması | tüm seçenekler için `_dogrula` | Menüler geçersiz kombinasyon üretmez; ilke TUI akışlarında da geçerlidir | TUI eşli (dolaylı) | ortak `_dogrula(secenekler)` sonuç/hata sınıfı |
| 1.5 Sürüm | `--surum` | Ana menü başlığında sürüm satırı | TUI eşli | `merkez.__version__` |
| 2.1 Zorlama | `--zorla`, `--zorla-md` | Dersleri Çek onayında "Zorla yeniden indir/bağlam üret" | TUI eşli | `indirici.indir_ders(zorla=..., zorla_md=...)` |
| 2.2 Sağlık | `--saglik` (+`--ders`, `--ag`) | Otomasyon/Durum menüsünde "Sağlık kontrolü" ekranı | TUI eşli | yeni `merkez/saglik.py` |
| 2.3 Kilit bekleme | `--kilit-bekle` | Çekme başlatmadan önce kilit doluysa "Bekle/Atla" sorusu | TUI eşli | `gunluk.Kilit.al(bekle_ms=...)` |
| 2.4 Ayrıntılı durum | `--durum --ayrintili` | Ana menü "Durum" ekranında ayrıntı satırları | TUI eşli | `zamanlayici.gorev_sorgu` + durum dosyası |
| 3.1 Boyut sınırı | `--sinir` | — (TUI varsayılan 200 MB kullanır) | Gerekçeli salt CLI (ileri düzey) | `indirici.indir_ders(ust_boyut=...)` |
| 3.2 Tetikleme | `--otomasyon-kur --tetikle` | Otomasyon detayında "Kur ve hemen dene" | TUI eşli | `zamanlayici.gorev_kur_guvenli` + tetikleme işlevi |
| 3.3 Gün kısayolları | `--her-gun`, `--hafta-ici` | Gün seçim ekranında "Tümü"/"Hafta içi" düğmesi | TUI eşli | `ayarlar.gun_listesi_coz` |
| 3.4 Günlük yolu | `--log` | — | Salt CLI | `gunluk` yol parametresi |
| 3.5 Tamamlama | `--oto-tamamlama` | — | Salt CLI | `merkez/tamamlama.py` |
| 4.1 Ayar görünümü ve seçim | `--ayarlar [--ders] [--secili evet|hayir]` | Mevcut Ayarlar ekranındaki çoklu seçim | TUI eşli | `ayarlar.gorunum` + `ayarlar.secili_ayarla` (`isaretle` bunu çağırır) |

### Arayüz Eşliği Kabul Kontrolleri (her dilimde çalıştırılabilir)

1. `python dersmerkezi.py -h` çıktısında ilgili seçenek ve Türkçe açıklaması görünür.
2. README ve `belgeler/kurulum.md` ilgili seçeneği içerir.
3. Eşlik listesindeki TUI girdileri menüden erişilebilir; ekran metni Türkçe ve kaçışlıdır.
4. CLI ve TUI adaptörleri aynı ortak işlevi eşdeğer girdilerle çağırır (kod incelemesi + birim kontrolü).
5. Eşdeğer hatalar aynı sınıfa düşer; TUI menü döngüsünü korur, CLI 0/1/2 döner.
6. Salt CLI seçenekleri TUI'de bulunmaz (negatif kontrol).

Bir dilim, bu kontroller ve ilgili kabul kriterleri geçmeden "tamamlandı" sayılmaz.

## Öncelik 1 - Çekirdek Kazanımlar

### 1.1 `--json`

* Amaç: `--durum`, `--listele` ve `--cek` çıktısını makine-okunur tek JSON nesnesine çevirmek; zamanlanmış koşu sonrası izleme ve harici araç entegrasyonu.
* Davranış: `--json` verildiğinde stdout'ta yalnızca tek JSON nesnesi bulunur; insan-okur tablo/özet üretilmez, tüm metin stderr'e gider. Kanal ve hata politikası ile kanonik alan şeması "Netleştirilen Mimari Kararlar > JSON çıktı sözleşmesi" bölümündedir; bu bölümdeki eski alan örneği geçersizdir.
* Alanlar: `durum` için `{surum, dersler:[{kimlik, ad, secili, otomasyon:{aktif, gunler, saat, gorevDurumu, sonSonuc}}]}`; `cek` için mevcut rapor sözlüğü (`yeni, guncellenen, atlanan, baglam, dogrulama_hatasi, donusum_hatasi, hatalar`).
* Kabul kriteri: `python dersmerkezi.py --durum --json` geçerli JSON döner; exit kodları değişmez (0/1/2); JSON dışı satır yazılmaz.
* Doğrulama: `json.loads` ile ayrıştırma, `--sessiz --json` kombinasyonu, alan şeması kontrolü.
* Risk: Düşük. Mevcut `print` çağrılarının JSON dalına ayrılması gerekir.

### 1.2 `--cek --kuru`

* Amaç: İndirme yapmadan planlanan işi göstermek (hangi dosya yeni/güncellenecek/atlanacak, boyutlar).
* Davranış: Depo listelenir, yerel durum ve SHA karşılaştırılır; hiçbir dosya yazılmaz, durum dosyası güncellenmez, günlük yalnızca özet satırı alır.
* Kabul kriteri: Kuru koşu sonrası `dersler/` altında değişiklik olmaz (`mtime` sabit); çıktı kategori sayılarını içerir; exit 0.
* Doğrulama: Kuru + gerçek koşu karşılaştırması; `.part` ve durum dosyası değişmezliği.
* Risk: Düşük; `--tasima --kuru` ile aynı desen.

### 1.3 `--sil --onayla`

* Amaç: CLI'da geri dönüşsüz ders silmeyi açık onaya bağlamak (TUI'de zaten `Confirm` var).
* Davranış: `--sil` yalnızca `--onayla` ile çalışır; onay yoksa anlaşılır hata + exit 2. Görev kaldırma ve kayıt silme sırası değişmez (önce görev, kaldırılamazsa silme yok).
* Kabul kriteri: `--sil --ders X` → exit 2 ve kayıt/görev değişmez; `--sil --ders X --onayla` → mevcut davranış.
* Doğrulama: Görev varken/yokken iki senaryo; fail-closed davranışın korunması.
* Risk: Düşük; mevcut kullanıcı alışkanlığını değiştirir, README/`kurulum.md` güncellenmeli.

### 1.4 Kombinasyon doğrulaması

* Amaç: Anlamsız veya çakışan bayrak kombinasyonlarını sessizce yok saymak yerine kullanım hatası vermek; her bayrağın yalnızca geçerli olduğu modda kullanılmasını garanti etmek.
* Temel kural: Aynı anda en fazla bir komut/mod bayrağı verilebilir (`--listele`, `--ekle`, `--sil`, `--cek`, `--durum`, `--saglik`, `--otomasyon-kur`, `--otomasyon-kaldir`, `--tasima`, `--surum`, `--oto-tamamlama`) ve `--otomatik` bağımsız zamanlanmış koşu modudur. Birden fazla mod verilirse stderr'e Türkçe mesaj + exit 2. Mod yoksa mevcut davranış korunur (TTY'de TUI, TTY değilse yardım + exit 2).
* Moda özgü seçenekler (`--dal`, `--desen`, `--gunler`, `--saat`) argparse'ta varsayılansız (`None`) tanımlanır; gerçek varsayılanlar ancak mod doğrulaması geçtikten sonra ilgili işleyicide uygulanır. Böylece `--durum` gibi yalın çağrılar matris tarafından yanlışlıkla geçersiz sayılmaz.
* `--otomatik` zamanlanmış görev sözleşmesidir; görev eylemi `"<betik>" --otomatik --ders <slug> --sessiz` biçiminde dondurulmuştur (`zamanlayici.beklenen_arguman`). Bu dize değiştirilemez; değişiklik gerekiyorsa eski/yeni eylemi tanıyan, sahiplik doğrulamalı ve geri alınabilir bir görev geçiş planı ayrıca yazılmalıdır.
* Bayrak-matris (önerilen kesin davranış):

| Bayrak | Geçerli mod | Gereklilik | Birlikte yasak / not |
|---|---|---|---|
| `--ad`, `--depo` | `--ekle` | `--ekle` ile zorunlu | Başka modda exit 2 |
| `--dal`, `--desen`, `--slug` | `--ekle` | Opsiyonel | Başka modda exit 2 |
| `--ders` | `--cek`, `--sil`, `--saglik`, `--otomasyon-kur`, `--otomasyon-kaldir`, `--otomatik`, `--ayarlar` | `--sil`, `--otomasyon-*` ve `--secili` ile zorunlu; `--cek`, `--saglik`, `--ayarlar` ve `--otomatik` ile opsiyonel | `--tasima`, `--ekle`, `--durum`, `--listele` ile exit 2 |
| `--gunler`, `--saat` | `--otomasyon-kur` | Opsiyonel (varsayılan `PZT` / `09:00`) | Başka modda exit 2 |
| `--kuru` | `--tasima`, `--cek` | Opsiyonel | Bu modlar dışında exit 2 |
| `--onayla` | `--tasima`, `--sil` | `--sil` ile zorunlu | `--kuru` ile birlikte exit 2 (kuru çalışmada onayın etkisi yok) |
| `--otomatik` | Bağımsız mod (zamanlanmış koşu) veya `--cek` | `--cek` ile birlikte anlamsız değil, uyumlu | Diğer modlarda exit 2; görev eylemi dizesi dondurulmuştur |
| `--sessiz` | Tüm modlar (`--surum` hariç) | Opsiyonel | `--surum` ile exit 2; `--json` ile birlikte JSON stdout'ta kalır |
| `--json` (1.1) | `--durum`, `--listele`, `--cek`, `--saglik`, `--surum`, `--oto-tamamlama`, `--ayarlar` | Opsiyonel | `--ayrintili` ile birlikte exit 2 (JSON şeması ayrıntı alanlarını taşır) |
| `--ayrintili` (2.4) | `--durum`, `--saglik` | Opsiyonel | Başka modda exit 2 |
| `--ag` (2.2) | `--saglik` | Opsiyonel | Başka modda exit 2; `--ders` ile birlikte exit 2 |
| `--zorla`, `--zorla-md` (2.1) | `--cek`, `--otomatik` | Opsiyonel | Başka modda exit 2; `--zorla` verildiğinde md de yeniden üretilir |
| `--kilit-bekle` (2.3) | `--cek`, `--otomatik` | Opsiyonel | Başka modda exit 2 |
| `--sinir` (3.1) | `--cek`, `--otomatik` | Opsiyonel | Başka modda exit 2 |
| `--her-gun`, `--hafta-ici` (3.3) | `--otomasyon-kur` | Opsiyonel | `--gunler` ile birlikte exit 2; başka modda exit 2 |
| `--tetikle` (3.2) | `--otomasyon-kur` | Opsiyonel | Başka modda exit 2 |
| `--log` (3.4) | Tüm modlar (`--surum` hariç) | Opsiyonel | `--surum` ile exit 2 |
| `--surum` | Mod gerektirmez | Tek başına veya yalnız `--json` ile | Diğer bayraklarla birlikte exit 2 |
| `--oto-tamamlama` (3.5) | Bağımsız mod | — | `--json` desteklenir; diğer modlarla exit 2 |
| `--ayarlar` (4.1) | Bağımsız mod | — | `--ders` opsiyonel; `--secili` ve `--json` desteklenir; diğer modlarla exit 2 |
| `--secili` (4.1) | `--ayarlar` | `--ders` zorunlu | Başka modda exit 2; değer kümesi `evet|hayir` |

* Uygulama yaklaşımı: `add_mutually_exclusive_group` kullanılmaz (hata metinleri İngilizce kalır); `parse_args` sonrası, her türlü yan etkiden önce çalışan saf `_dogrula(secenekler)` işlevi mod dışlamasını ve bayrak-mod matrisini tablo üzerinden denetler (Türkçe mesaj + exit 2). `ArgumentParser.error` yalnızca desteklenen ayrıştırma hata sınıflarını (bilinmeyen bayrak, eksik değer, geçersiz tamsayı/seçenek) belirlenmiş Türkçe şablonlara çevirir; eşlenemeyen mesajda jenerik Türkçe metin + ayrıntı yazılır ve özgün İngilizce metin kullanıcıya gösterilmez.
* Kabul kriteri: Tablodaki her satır için en az bir geçerli ve bir geçersiz kombinasyon kontrol edilir; geçersizlerde exit 2 + stderr mesajı, hiçbir yan etki yok; `--sessiz` verilse bile kullanım hatası stderr'e yazılır.
* Doğrulama: Birim/CLI matris kontrolü (kombinasyon listesi tablodan üretilir); mevcut README ve `belgeler/kurulum.md` komutlarının tamamının tabloya uyduğu doğrulanır.
* Risk: Düşük; mevcut meşru kullanımlar tabloyla uyumludur, yalnızca hatalı kombinasyonlar reddedilir.

### 1.5 `--surum`

* Amaç: Sürüm bilgisini tek kaynaktan yazdırmak; `UA` sabitini (`DersMerkezi/0.1`) sürümle eşlemek.
* Davranış: `--surum` → `DersMerkezi <sürüm>` + exit 0. Sürüm, `merkez/__init__.py` içindeki tek sabitten okunur; `CHANGELOG.md` ile uyumlu tutulur.
* Kabul kriteri: `--surum` çıktısı `CHANGELOG.md`'deki en güncel sürümle aynı; `--json --surum` geçerli JSON.
* Doğrulama: Çıktı karşılaştırması + `compileall`.
* Risk: Düşük.

## Öncelik 2 - Kullanışlılık ve Dayanıklılık

### 2.1 `--zorla` ve `--zorla-md`

* Amaç: SHA eşleşse veya md geçerli görünse de yeniden üretmek (şablon değişikliği, şüpheli yerel kopya).
* Davranış: `--zorla` indirmeyi, `--zorla-md` yalnız Markdown üretimini tetikler; doğrulama zinciri (blob SHA, md_sha/md_boyut) aynen uygulanır.
* Kabul kriteri: Zorla koşuda `guncellenen=1`; dosya içeriği kaynakla birebir doğrulanır; normal koşu davranışı değişmez.
* Doğrulama: Akış paketinde zorla/ikinci koşu karşılaştırması.
* Risk: Düşük.

### 2.2 `--saglik`

* Amaç: Tek komutla ortam ve erişim ön kontrolü: Python/paket sürümleri, depo erişimi, API kotası, görev durumu, kilit durumu.
* Davranış: Salt okunur; ağ çağrısı yalnızca API kotası ve depo erişimi için; sonuç kategori başlıklarıyla yazılır.
* Kabul kriteri: Sorunlu her bileşen için anlaşılır Türkçe satır; sorun varsa exit 1, yoksa 0.
* Doğrulama: Kota dolu/boş, 404 depo, paket eksik simülasyonları (birim + gerçek).
* Risk: Orta; ağ çağrı sayısı artar, `--json` ile birleştirilmeli.

### 2.3 `--kilit-bekle <sn>`

* Amaç: Kilit doluyken hemen atlamak yerine sınırlı süre beklemek (zamanlanmış koşuların çakışmasında telafi).
* Davranış: Varsayılan 0 (mevcut davranış); verilen süre boyunca kilit beklenir, alınamazsa mevcut "atlandı" davranışı.
* Kabul kriteri: Kilit doluyken `--kilit-bekle 5` çalışma başlar; süre aşımında exit 0 + uyarı.
* Doğrulama: Kilit tutan ikinci süreç senaryosu.
* Risk: Düşük; `Local\DersMerkezi` semantiği değişmez.

### 2.4 `--durum --ayrintili`

* Amaç: Görev `sonCalisma`/`sonSonuc`/`eylem` ve durum dosyası özetini göstermek.
* Kabul kriteri: `--durum` çıktısı geriye dönük uyumlu; `--ayrintili` ek satırlar ekler.
* Doğrulama: Mevcut `--durum` çıktısının korunması + yeni alanların varlığı.
* Risk: Düşük.

## Öncelik 3 - İsteğe Bağlı Genişletmeler

### 3.1 `--sinir <MB>`

* Dosya boyutu üst sınırını çağrı bazında değiştirir; varsayılan 200 MB. Üst sınır yine liste aşamasında uygulanır.

### 3.2 `--otomasyon-kur --tetikle`

* Kurulumdan sonra görevi bir kez `Start-ScheduledTask` ile çalıştırır; `LastTaskResult` ve son günlük satırını raporlar. Pil politikası nedeniyle oluşan "Queued" durumunu kullanıcıya görünür kılar.

### 3.3 Gün kısayolları

* `--her-gun` ve `--hafta-ici`; kapalı gün kümesi ve `.NET` eşlemesi korunur.

### 3.4 `--log <yol>`

* Alternatif günlük dosyası (test/çoklu kurulum); varsayılan `gunluk.log` değişmez, rotasyon aynı kuralla uygulanır.

### 3.5 Kabuk tamamlama

* `--oto-tamamlama` ile PowerShell/bash tamamlama betiği üretimi.

## Öncelik 4 - CLI Ayar Görünümü ve Seçim (0.1.3)

Sol danışma kararı (2026-09-22) doğrultusunda tek dilimde uygulanır.

### 4.1 `--ayarlar` ve `--secili`

* Amaç: Ders ayarlarını (ad, depo, dal, desen, seçili durumu, otomasyon özeti) CLI'dan salt-okunur görüntülemek ve çekilme işaretini güvenli biçimde değiştirmek; TUI "Ayarlar" ekranıyla aynı ortak işlevi paylaşmak.
* Davranış:
  * `--ayarlar`: tüm dersleri gösterir; `--ders <kimlik>` yalnız o dersi gösterir; ağ çağrısı, PowerShell görevi, indirme ve yazım yapmaz.
  * `--ayarlar --ders <kimlik> --secili evet|hayir`: seçim işaretini değiştirir (mutex, atomik yazım, tek nesil yedek zinciri); `--ders` yoksa exit 2; bilinmeyen ders exit 2; bozuk `ayarlar.json` karantinaya alınmaz, exit 1.
  * `--json` desteklenir: `{json_surum, komut:"ayarlar", uygulama_surum, dersler:[{kimlik, ad, depo, dal, desen, secili, otomasyon:{aktif, gunler, saat}}]}`. Mutasyon sonrası yeni durum döner.
  * `--sessiz` insan-okur çıktıyı bastırır; JSON stdout'ta kalır. `--ayrintili` ile birlikte exit 2; `--otomatik`, `--sil` ve diğer modlarla birlikte exit 2.
* Güvenli ortak işlev: `ayarlar.secili_ayarla(slug, secili)` fail-closed çalışır (`yukle_salt` + kilit + `kaydet`); mevcut `ayarlar.isaretle` bunu çağırır, TUI aynı yolu kullanır.
* Kabul kriteri: `--ayarlar` sonrası dosya/görev/ağ izi yok; `--secili hayir` sonrası `--cek --ders X` dersin seçili olmadığını raporlar (exit 0, atlanan=1); `--secili evet` ile geri alınır; bozuk ayarda görünüm ve mutasyon dosyayı değiştirmez.
* Doğrulama: matris çiftleri, JSON şeması, yan etkisizlik anlık görüntüsü, bozuk ayar, kilit senaryosu, TUI ortak işlev kontrolü.
* Risk: Düşük; yalnızca `secili` alanı değişir, görev eylemi ve otomasyon ayarları değişmez.
* Sol denetimi (0.1.3): `belgeler/gecmis/sol-denetim-2026-09-22-0.1.3.md`; tur 1'de 3 orta + 2 düşük bulgu açıldı ve kapatıldı, tur 3'te `SONUC: ONAY` alındı.

### Gerçek Konsol ve Takvim Teyitleri (0.1.4)

* Gerçek konsol (yeni pencere, `chcp 65001`) TUI turunda üç kusur saptandı ve düzeltildi: (1) ana menü sürüm paneli `_secim` ekran temizliği nedeniyle görünmüyordu — sürüm satırı menü açıklamasına taşındı; (2) Durum listesi, Dersler tablosu ve Otomasyon başlığı aynı nedenle kayboluyordu — `_secim`'e `ust` parametresi eklendi ve içerik kalıcı hale getirildi; (3) sağlık satırlarında stil etiketi metne karışıyordu (`[green]green ...`) — biçim düzeltildi. Sürüm 0.1.4.
* Gerçek konsol kanıtı: menü/Durum/Sağlık/çıkış akışı ve karakter kod noktaları (ü=U+00FC, ş=U+015F, ─=U+2500) konsol tamponundan birebir doğrulandı; tampon okuma bu ortamda ekranın bir bölümünü yakalayabildiği için satır satır görsel inceleme yerine kod noktası + akış kanıtı kullanıldı.
* Takvim teyidi: üretim görevi XML/ayar/eylem/`NextRunTime` doğrulandı; test göreviyle gerçek takvim tetiklemesi ateşlendi (`LastTaskResult=0`, günlük satırı) ve test görevi temizlendi. Üretim görevinin 28.09.2026 koşusu tarihte `gunluk.log` üzerinden görülecek; yapılandırma ve aynı mekanizmanın fiili ateşlemesi kanıtlandı.

* Kanıt (2026-09-22): geçici kopyada 418/418 kontrol (204 birim/akış + 153 fonksiyon kapsamı + 47 uçtan uca + 14 tetikleme/sahiplik); `trace` koşusunda 133/133 fonksiyon çağrıldı, ifade satırı kapsamı %81. Gerçek proje kapısı (0.1.4 son kod, 2026-09-22): `compileall` exit 0; `--cek --ders dosya-organizasyonu --sessiz` exit 0 (`atlanan=2`, üst depo iki dosya); `--surum` → `DersMerkezi 0.1.4`; `--ayarlar --json` exit 0; `--durum` → `dosya-organizasyonu: gorev=kayitli (Ready)`; `--saglik --ders dosya-organizasyonu --json` exit 0; üretim seçimi ve görevi değişmedi.

## Uygulama Sırası (revize)

0. Altyapı dilimi: parser kurulumunun `arguman_ayristirici()` işlevine taşınması; `merkez.__version__` tek kaynak ve `UA` türetimi; çıktı/kanal politikası ve JSON serileştirme noktası; Türkçe ayrıştırma hata eşleme katmanı; `_dogrula` iskeleti ve tablo tabanlı test altyapısı.
1. Mevcut mod matrisi dilimi: yalın mod çağrıları için regresyon, `--surum` (`--json` dahil), `--sil --onayla`, `--otomatik` bağımsız mod koruması ve dondurulmuş görev eylemi testi.
2. JSON dilimi: mevcut modlarda (`--durum`, `--listele`, `--cek`) kanonik şemaya geçiş.
3. Çekme genişletme dilimi: `--kuru`, `--zorla`/`--zorla-md`, `--kilit-bekle`, `--sinir` (matris, şema, test ve doküman aynı dilimde).
4. Sağlık dilimi: `--saglik`, `--ag`, `--durum --ayrintili` (ağ gating ve salt-okunurluk kanıtlarıyla).
5. Otomasyon dilimi: `--tetikle`, gün kısayolları, `--log`.
6. Tamamlama dilimi: parser kaynaklı `--oto-tamamlama`, `.gitignore` girdisi.
7. Ayar dilimi (0.1.3): `--ayarlar` görünümü ve `--secili` ile seçim değişikliği (matris, eşlik, test ve doküman aynı dilimde).

Her dilim bağımsız doğrulanabilir ve geri alınabilir; matris, JSON şeması, dokümantasyon ve "Eşlik Listesi" gereği CLI yüzeyi ile TUI bağlantıları ve arayüz eşliği kabul kontrolleri ilgili dilimle aynı değişiklikte tamamlanır. Her dilimde `AGENTS.md` "Doğrulama Kapısı" uygulanır; girdi doğrulaması ve çıkış kodu davranışı değişen dilimlerde birim/akış kontrolleri yeniden koşulur ve Sol denetimine sunulur.

## Kapsam Dışı

* Grafik arayüz (GUI).
* Belirli tarih listesiyle zamanlama (v1 haftalık gün + saat).
* `--kok <dizin>` ile proje kökünü değiştirme (mutex ve gerçek yol denetimi değişmezleriyle çelişir; istenirse yalnızca ortam değişkeni + kök içi sınırla değerlendirilir).
* Ingilizce bayrak adları; mevcut Türkçe adlandırma korunur.
* `--sinir` ile 200 MB üstüne çıkarma ve ilgili AGENTS.md değişmezinin revizyonu.
* bash/zsh kabuk tamamlama ve dinamik (slug/depo) tamamlama değerleri (v1 yalnız PowerShell ve bayrak tamamlama).
* `--ayrintili` seçeneğinin `--listele` ile kullanımı.
* argparse karşılıklı dışlama grubuyla İngilizce hata metni üretimi (Türkçe kural gereği kullanılmaz).
* `--ders-guncelle` (ad/depo/dal/desen güncelleme): durum dosyaları, slug kimliği ve geri alma politikası ayrı tasarım gerektirir; v1 kapsam dışıdır.

## Riskler

| Risk | Etki | Olasılık | Azaltım | Geri alma | Kanıt sahibi |
|---|---|---|---|---|---|
| Görev eylemi dizesi değişikliği | Kurulu görevler yabancı sayılır; güncelleme/kaldırma kilitlenir | Düşük (dize donduruldu) | Dilim 1 regresyon testi; değişiklik gerekiyorsa ayrı geçiş planı | XML yedeğinden geri yükleme (`gorev_yukle`) | Otomasyon dilimi |
| `--sil --onayla` davranış değişikliği | Onaysız komut exit 2 döner; kullanıcı şaşkınlığı | Orta | README ve `belgeler/kurulum.md` aynı dilimde güncellenir; Türkçe mesaj yol gösterir | Kapı kaldırılır (tek satır) | CLI dilimi |
| Kuru çalışmanın mutasyonsuzluğu | "Yazmaz" vaadi çürür; klasör/durum değişir | Orta | Kuru yolu ön hazırlıklardan önce ayır; ortak mutex altında salt-okunur; negatif FS kanıtı | Geri alınacak mutasyon yok | Çekme dilimi |
| Tetikleme yan etkisi | Gerçek koşu ağ/kota tüketir; kısmi koşu | Orta | Ön sahiplik doğrulaması; 60 sn zaman aşımı; hata kurulumu geri almaz, raporlar | Görev kurulu kalır; `--otomasyon-kaldir` | Otomasyon dilimi |
| Global çıktı durumu (`SESSIZ`) | JSON kirlenir veya tanılama kaybolur | Orta | Çağrı kapsamlı politika veya `try/finally` geri yükleme; ardışık çağrı testleri | Global durum her çağrıda eski değerine döner | JSON dilimi |
| Sağlık sorgularının API maliyeti | Kimliksiz kota (60/saat) tükenir; testler 403 alır | Orta | Varsayılan ağsız; `--ag` ilk 10 ders; atlananlar raporlanır | Ağsız moda dönülür; çağrı sayısı sıfırdır | Sağlık dilimi |
| Alternatif günlük yolu güvenliği | Kök dışı/junction/kilitli yol; yanlış rotasyon | Orta | `realpath` + reparse kontrolü, yazım anında yeniden doğrulama, fail-closed | Varsayılan `gunluk.log`'a dönülür | Otomasyon dilimi |
| Tamamlama dosyası yaşam döngüsü | Bayat/yanlış dosya; depo kirliliği | Düşük | `tamamlama/` altında üretim, `.gitignore`, parser eşitlik testi | Dosya silinir; kaynak parser'dır | Tamamlama dilimi |
| Argv varsayılanları | Yalın mod çağrıları yanlış reddedilir | Orta | `None` + doğrulama sonrası varsayılan; yalın çağrı regresyonları | Varsayılanlar argparse'a geri taşınır | Matris dilimi |
| Türkçe hata eşleme kırılganlığı | CPython sürüm değişiminde eşleme bozulur | Orta | Sınıflandırma + jenerik Türkçe geri dönüş; sürümden bağımsız testler; `exit_on_error=False` kullanılmaz | Eşleme katmanı kaldırılır; jenerik mesaj kalır | Altyapı dilimi |
| `--sinir` yükseltme beklentisi | Kullanıcı 200 MB üstü ister; değişmez ihlal edilir | Düşük | Yalnız düşürme (1-200); yükseltme ayrı değişmez revizyonu gerektirir | Değer 200'e döner | Çekme dilimi |

## Doğrulama Yaklaşımı

* Her madde için birim kontrolü + CLI akış kontrolü; geçici klasördeki proje kopyasında koşulur, repoya test dosyası eklenmez.
* Kombinasyon matrisi (1.4) testleri tablodaki her satırdan en az bir geçerli ve bir geçersiz çift üretir; doğrulama yan etkiden önce çalıştığı için hatalı kombinasyonlarda dosya, görev veya ağ izi oluşmadığı da kontrol edilir.
* Zamanlayıcıyı etkileyen maddeler (`--otomasyon-kur --tetikle`) test göreviyle kurulup kaldırılır; üretim görevi değiştirilmez.
* Kanıtlar bu belgeye ve `belgeler/plan/2026-09-21-dersmerkezi-cli.md` "Uygulama ve Doğrulama Kanıtları" bölümüne işlenir.

## Netleştirilen Mimari Kararlar (2026-09-21 araştırma turu)

Bu bölüm, Gemini 3.7/3.8 Flash ve DeepSeek Flash/Pro araştırmaları ile yerel kod kanıtları birleştirilerek belirsizliklerin kapatıldığı kararları içerir. Gemini bulguları hipotez kabul edilip yerel gözlemle çaprazlandı; doğrulanamayan noktalar işaretlendi.

### JSON çıktı sözleşmesi (1.1)

* Kök her zaman JSON nesnesidir; kök dizi yasaktır. Kökte `json_surum` (tamsayı, v1) ve `uygulama_surum` alanları bulunur; `surum` adı `ayarlar.json` şemasıyla karışmaması için kullanılmaz.
* Çoklu sonuçlar `dersler` dizisi altında modellenir; tek ders de dizi içinde tek öğedir.
* Tipler kararlıdır: liste alanları boşken `[]`, sayısal alanlar sayı; `null` yalnızca "bilinmiyor" anlamında (ör. görev sorgulanamadı).
* `--json` verildiğinde stdout yalnızca tek JSON nesnesi içerir; tüm insan-okur metin ve uyarılar stderr'e gider. `gunluk.kayit` bu modda stdout'a yazmaz (SESSIZ'den bağımsız); dosya günlüğü devam eder.
* Hata durumunda stderr'e `{json_surum, komut, hata:{sinif, mesaj}}` yazılır; çıkış kodu değişmez (0/1/2). Başarılı koşunun stdout'unda hata nesnesi bulunmaz.
* Şemalar: `durum`/`listele` ders kaydı `{kimlik, ad, depo, secili, otomasyon:{aktif, gunler, saat, gorev:{durum, sonCalisma, sonSonuc}}}`; `cek` için `{dersler:[{anahtar, hedef, yeni, guncellenen, atlanan, baglam, dogrulama_hatasi, donusum_hatasi, hatalar[]}], toplamlar}`.
* `--json --ayrintili` birlikte verilemez (exit 2); JSON şeması ayrıntı alanlarını zaten taşır.

### Doğrulama mimarisi (1.4)

* İki katman: (1) mod bayrakları için argparse'ta `add_mutually_exclusive_group` kullanılmaz; argparse'ın karşılıklı dışlama hata metinleri İngilizce olduğundan "kullanıcıya dönük tüm metinler Türkçe" kuralı ihlal edilir. (2) `parse_args` sonrası, hiçbir yan etkiden önce çalışan saf `_dogrula(secenekler)` işlevi mod dışlamasını ve bayrak-mod matrisini tablo üzerinden denetler; hata durumunda stderr'e Türkçe mesaj + exit 2.
* `ArgumentParser.error` yalnızca biçim hatalarını Türkçe önekle sarmak için ezilir; CPython'un İngilizce metinleri eşlenmeye çalışılmaz (sürüm kırılganlığı).
* Test: tablo tabanlı (argv, beklenen kod, beklenen mesaj parçası); geçerli/geçersiz çiftler matristen üretilir.

### Sürüm kaynağı (1.5)

* Tek kaynak `merkez/__init__.py` içindeki `__version__`; bu plan uygulandığında hedef sürüm 0.1.2. `indirici.UA` bu değerden türetilir. `--surum` bu sabiti yazar; birim kontrolü `CHANGELOG.md` en güncel başlığıyla eşitliği doğrular.

### Kuru çekme (1.2)

* `indir_ders(..., kuru=True)` yalnızca listeleme + yerel boyut/SHA karşılaştırması yapar; dosya, `.part` ve durum dosyası yazılmaz; `indirildi`/`md_uretildi` değişmez. Rapor sayıları korunur; ek olarak indirilecek toplam bayt raporlanır. `--json` desteklenir.

### Silme onayı (1.3)

* CLI'da `--sil` yalnızca `--onayla` ile çalışır; TUI'de mevcut `Confirm` akışı korunur. Onaysız çağrı exit 2 döner ve hiçbir değişiklik yapmaz; fail-closed sıra (önce sahiplik ve görev kaldırma) aynen korunur.

### Zorlama bayrakları (2.1)

* `--zorla`: indirmeyi ve md üretimini zorlar; `indirildi` ve `md_uretildi` yeni damga alır. `--zorla-md`: indirme kararı normal kurallarla verilir, md üretimi zorlanır; `indirildi` değişmez. Her iki durumda blob SHA ile `md_sha`/`md_boyut` doğrulaması atlanmaz.

### Sağlık kontrolü (2.2)

* Varsayılan `--saglik` ağ çağrısı yapmaz: Python/paket sürümleri (`importlib.metadata`), `ayarlar.json` şema geçerliliği, ders kayıtlarının doğrulaması, kilit durumu (`kilit_dolu()` yardımcı işlevi, `al(0)` + `finally` bırakma), günlük/durum dosyası erişilebilirliği.
* Ağ yalnızca açıkça istenirse: `--ders <kimlik>` o ders için tek depo listeleme çağrısı (kota başlıkları bu yanıttan okunur, ek `/rate_limit` çağrısı yapılmaz); `--ag` tüm dersleri listeler. Görev sorgusu yalnızca `--ders` veya `--ayrintili` ile yapılır (her sorgu ayrı PowerShell süreci; ders sayısına üst sınır uygulanır).
* Çıkış: sorun yok → 0 (uyarılar 0'ı değiştirmez), en az bir sorun → 1, kullanım hatası → 2. `--json` şeması: `{json_surum, komut:"saglik", uygulama_surum, genel, kontroller[], sorunlar[], uyarilar[], kota}`.

### Kilit bekleme (2.3)

* Birim saniye; `type=int`, varsayılan 0, aralık 0-3600; aralık dışı exit 2. Değer `Kilit.al(bekle_ms=sn*1000)` çağrısına geçirilir; süre aşımında mevcut "atlandı" davranışı (uyarı + exit 0) korunur.

### Ayrıntılı durum (2.4)

* `--durum --ayrintili`: ders başına `gorev:{durum, sonCalisma, sonSonuc, eylem}` ve durum dosyası özeti (dosya sayısı, toplam bayt, son güncelleme); sorgu hatası `sorgulanamadi` olarak raporlanır. Mevcut `--durum` çıktısı birebir korunur.

### Boyut sınırı (3.1)

* `--sinir <MB>` yalnızca düşürmeye izin verir: 1-200 aralığı, varsayılan 200; 0, negatif veya 200 üstü exit 2. Böylece AGENTS.md'deki "liste aşamasında 200 MB üstü reddi" değişmezi korunur. Liste aşaması ve akış kontrolü aynı değeri kullanır.

### Görev tetikleme (3.2)

* `--tetikle` yalnızca `--otomasyon-kur` ile: kurulum ve ayar yazımı başarılı olduktan sonra `Start-ScheduledTask` çağrılır; başlangıçta `LastRunTime` referansı saklanır.
* Tamamlanma ölçütü: durum `Running`/`Queued` dışına çıkar ve `LastRunTime` referanstan yenidir. Yoklama 1 sn aralık, 60 sn zaman aşımı.
* Sonuç raporu: `0` başarı; `267009` çalışıyor; `267011` hiç çalışmadı; `267014` sonlandırıldı; diğerleri hex ile. Zaman aşımında veya görev `Queued` kalırsa koşul teşhisi yapılır (`DisallowStartIfOnBatteries`, `RunOnlyIfIdle`, `RunOnlyIfNetworkAvailable`, `LogonType`, `Win32_Battery.PowerOnline`) ve Türkçe neden önerisi yazılır; exit 1.
* `schtasks /Run /I` koşulları yok sayar (yerel `schtasks /Run /?` çıktısıyla doğrulandı); bilinçli olarak kullanılmaz, yalnızca elle çalıştırma notu olarak belgelenir.
* Görev sahipliği ve geri alma kuralları değişmez; tetikleme yalnızca kurulum başarısından sonra yapılır.

### Gün kısayolları ve günlük yolu (3.3, 3.4)

* `--her-gun` (yedi gün) ve `--hafta-ici` (PZT-CUM) yalnızca `--otomasyon-kur` ile; `--gunler` ile birlikte verilirse exit 2. Kısayollar kapalı küme üzerinden mevcut `gun_listesi_coz` doğrulamasına girer.
* `--log <yol>` yolu `os.path.realpath` ile proje kökü içinde olmak zorundadır; üst dizin yoksa oluşturulur; rotasyon aynı kuralla (1 MB, `.old`) uygulanır ve mutex adı `Local\DersMerkezi` olarak kalır. Kök dışı veya yazılamayan yol exit 2/1 ile reddedilir; OSError sessizce yutulmaz, kullanıcıya bildirilir.

### Kabuk tamamlama (3.5)

* Parser kurulumu `arguman_ayristirici()` modül işlevine taşınır; tamamlama bayrak listesi parser'dan türetilir (tek kaynak).
* `--oto-tamamlama` ek bağımlılık olmadan PowerShell 5.1 için `Register-ArgumentCompleter` içeren statik betiği `tamamlama/dersmerkezi-tamamlama.ps1` yoluna yazar; dosya `.gitignore` dışındadır (deterministik üretim, sürüm kontrolüne alınmaz). Yazım `gunluk.kilitle()` altında `.tmp` + `flush` + `os.fsync` + `os.replace` ile atomiktir.
* v1 yalnızca bayrak tamamlar (dinamik slug/depo tamamlama kapsam dışı). `--json` ile `{json_surum, komut:"oto-tamamlama", hedef, bayrak_sayisi, bayraklar[]}` döner.

## Kaynaklar

Doğrulanan (yerel):

* CLI ve modül gerçekleri: DeepSeek Flash yerel analizi, `dersmerkezi.py` ve `merkez/*` dosya:satır kanıtları.
* Görev Zamanlayıcı yerel gözlemleri: `LastTaskResult=0` (başarılı koşular), `267011` (hiç çalışmadı), pil politikası nedeniyle `Queued` ve düzeltme sonrası fiili koşu; `schtasks /Run /?` ile `/I` anahtarının koşulları yok saydığı.
* `gh repo create` söz dizimi: `gh repo create --help`; kimlik doğrulama: `gh auth status` (hesap `mecik-arda`, `repo` kapsamı).

Danışmanlık (doğrulanmadı, hipotez):

* Gemini 3.7 Flash: JSON şema tasarımı önerileri (kök nesne, sürüm alanı, `--sessiz` önceliği, hata nesnesi).
* Gemini 3.8 Flash: doğrulama katmanı deseni (karşılıklı dışlama + merkezi saf doğrulama, `ArgumentParser.error` tuzakları, tablo tabanlı test) ve Görev Zamanlayıcı `LastTaskResult`/`Queued`/yoklama önerileri.
* DeepSeek Pro: `--saglik` ve `--oto-tamamlama` mimari önerileri.

Doğrulanamayan:

* Gemini Pro rotası bu turda `web_evidence_invalid` verdi; Görev Zamanlayıcı soruları Gemini 3.8 Flash ile yanıtlandı.
* Gemini bulgularındaki olay kimlikleri (`Microsoft-Windows-TaskScheduler/Operational` 322/327 vb.) ve `RunOnlyIfIdle` etkileşimleri yerel olarak test edilmedi.

## Sol Denetim Özeti ve Kapatılan Bulgular

Bağımsız denetimde 2 kritik, 14 orta ve 2 düşük bulgu saptandı. Bu tur yalnızca denetim sonucunu eklediği ve mevcut kararları değiştirmediği için kapatılan bulgu yoktur.

1. Kombinasyon doğrulaması / `--otomatik` — kritik — Matris `--otomatik` seçeneğini yalnızca `--cek` ile geçerli sayıyor; mevcut zamanlanmış görev eylemi ise `zamanlayici.beklenen_arguman` tarafından `--otomatik --ders <slug> --sessiz` olarak üretilip birebir sahiplik kanıtı kabul ediliyor. Bu karar mevcut görevleri kullanım hatasına düşürür; beklenen argüman değiştirilirse de kurulu görevler yabancı sayılarak güncelleme ve kaldırma zinciri kilitlenir. — Beklenen düzeltme: `--otomatik` mevcut bağımsız çekme tetikleyicisi olarak korunmalı ya da eski ve yeni eylemi güvenle tanıyan, görevleri sahiplik doğrulamasıyla taşıyan, geri alınabilir ve doğrulama kanıtlı bir geçiş planı tanımlanmalıdır.

2. Doğrulama mimarisi / argparse varsayılanları — kritik — `_dogrula(secenekler)` tasarımı açıkça verilen bayrağı Namespace varsayılanından ayırmıyor; mevcut parser `--dal`, `--desen`, `--gunler` ve `--saat` için dolu varsayılanlar üretiyor. Matris doğrudan uygulanırsa `--durum`, `--listele`, `--cek` gibi çağrılar kullanıcı bu bayrakları vermemişken de geçersiz görünebilir. — Beklenen düzeltme: Moda özgü seçenekler doğrulama öncesinde `None` veya `argparse.SUPPRESS` ile ayrıştırılmalı, varsayılanlar ancak matris doğrulamasından sonra uygulanmalı ve her modun yalın çağrısı regresyon testine eklenmelidir.

3. `--json` / JSON çıktı sözleşmesi — orta — 1.1 bölümü `surum`, düz `gorevDurumu` ve mevcut çekme raporunu tarif ederken netleştirilen kararlar `json_surum`, `uygulama_surum`, iç içe `gorev`, ders dizisi ve `toplamlar` tarif ediyor. Ayrıca “stdout yalnızca tek JSON nesnesi” kuralı ile hata nesnesinin yalnız stderr'e yazılması aynı sözleşmede hata anındaki stdout durumunu belirsiz bırakıyor. — Beklenen düzeltme: Tek kanonik şema seçilmeli; başarı, kullanım hatası ve çalışma hatası için stdout/stderr içeriği, boş akışlar ve çıkış kodları ayrı kabul örnekleriyle sabitlenmelidir.

4. `--surum` — orta — Kombinasyon matrisi `--surum` seçeneğinin tek başına olmasını ve başka her bayrakla exit 2 vermesini isterken 1.5 kabul kriteri `--json --surum` çağrısının geçerli JSON üretmesini istiyor. — Beklenen düzeltme: İki davranıştan biri seçilmeli; JSON desteklenecekse matris ve sürüm JSON şeması, desteklenmeyecekse 1.5 kabul kriteri buna göre uyumlu hale getirilmelidir.

5. `--saglik` / mod ve ağ sözleşmesi — orta — `--saglik` temel mod listesinde yer almıyor; netleştirilen karar `--ders`, `--ag` ve `--ayrintili` ile sağlık varyantları tanımlarken matris `--ders` ve `--ayrintili` seçeneklerini sağlık modunda yasaklıyor, `--ag` seçeneğini hiç tanımlamıyor. İlk 2.2 davranışı depo ve kota ağına işaret ederken son karar varsayılanı ağsız yapıyor; Riskler bölümü de hâlâ varsayılan kota tüketimi varsayımına dayanıyor. — Beklenen düzeltme: `--saglik` mod listesine ve matrise eklenmeli; `--ders`, `--ag`, `--ayrintili`, `--json` birleşimleri ile varsayılan ağ politikası tek sözleşmede tanımlanmalı ve ağ çağrısı sayısı sınırları kabul kriterine bağlanmalıdır.

6. `--saglik` / mevcut API ve salt-okunurluk — orta — Plan kota başlıklarının depo listeleme yanıtından okunmasını istiyor; mevcut `indirici.depo_listele` yalnız ayrıştırılmış listeyi döndürüyor ve başlıkları dışarı taşımıyor. “Günlük/durum dosyası erişilebilirliği” kontrolünün yazma denemesi yapıp yapmayacağı da salt-okunur sağlık vaadi açısından tanımlı değil. — Beklenen düzeltme: Yanıt meta verisinin token ve hata metni redaksiyonunu koruyan dönüş sözleşmesi belirlenmeli; sağlık kontrollerinin hiçbir dosya, yedek, klasör veya günlük oluşturmadığı negatif dosya sistemi kanıtıyla doğrulanmalıdır.

7. `--ayrintili` — orta — Matris `--ayrintili` seçeneğini hem `--durum` hem `--listele` için geçerli sayıyor; 2.4 ve netleştirilen karar yalnız `--durum --ayrintili` davranışını ve kabul kriterini tanımlıyor. Sağlık bölümünde üçüncü bir kullanım daha ortaya çıkıyor. — Beklenen düzeltme: Desteklenen modlar kesinleştirilmeli; her desteklenen mod için alanlar, hata davranışı, sorgu sayısı üst sınırı ve doğrulama yöntemi yazılmalı, desteklenmeyen birleşimler exit 2 olmalıdır.

8. Kombinasyon doğrulaması / eksik bayraklar — orta — `--ag`, `--her-gun`, `--hafta-ici` ve `--oto-tamamlama` matriste bulunmuyor; buna karşın sonraki kararlar bu bayraklara mod ve birleşim kuralları veriyor. `--log` için “tüm modlar” ifadesi de `--surum` seçeneğinin tek başına olma kuralıyla çatışıyor. — Beklenen düzeltme: Planlanan bütün bayraklar tek kanonik matrise alınmalı; mod sayılan komutlar, yardımcı bayraklar ve mod gerektirmeyen komutlar ayrılmalı, her satır için geçerli ve geçersiz örnekler üretilmelidir.

9. Kuru çekme — orta — Mevcut `indir_ders` hedef klasörü oluşturuyor, kalıntı `.part` ve `.tmp` dosyalarını siliyor ve bozuk durum dosyasını `_durum_yukle` üzerinden yeniden adlandırabiliyor. Yalnız `kuru=True` eklemek “hiçbir dosya yazılmaz” vaadini sağlamaz; aynı kilit alınmadan yapılan yerel SHA karşılaştırması gerçek çekmeyle yarışabilir. Başarısız ağ, bozuk durum ve doğrulama hatalarının çıkış kodu da kabul kriterinde yoktur. — Beklenen düzeltme: Kuru yol mutasyon yapan hazırlık yardımcılarından önce ayrılmalı, ortak mutex altında salt okunur inceleme yapmalı; olmayan hedef klasör, bozuk durum, kalıntı dosyalar, kilit doluluğu, ağ hatası ve doğrulama hatası senaryolarında sıfır mutasyon ile 0/1/2 davranışı doğrulanmalıdır.

10. JSON çıktı / `gunluk.SESSIZ` — orta — Mevcut `gunluk.kayit`, `SESSIZ` false iken stdout'a insan-okur satır basıyor; `main` ise bu modül globalini yalnız true yapıyor ve aynı süreçte sonraki çağrılar için geri almıyor. “SESSIZ'den bağımsız” ifadesi tek başına JSON çıktısının kirlenmesini ve testler arası global durum sızıntısını önleyecek tasarımı ya da kabul kriterini vermiyor. — Beklenen düzeltme: Konsol çıktı hedefi çağrı kapsamlı bir politika olarak ayrılmalı veya global durum `try/finally` ile geri yüklenmeli; art arda sessiz, JSON ve normal `main(argv)` çağrılarında stdout, stderr ve dosya günlüğü ayrı ayrı doğrulanmalıdır.

11. `--kilit-bekle` — orta — 0-3600 aralığı netleşmiş olsa da “kilit doluyken 5 saniyede çalışma başlar” kabulü kilidin ne zaman bırakıldığını söylemiyor. Dış çekme kilidi süre aşımına uğradıktan sonra mevcut `gunluk.kayit` aynı mutex için ayrıca 10 saniye beklediğinden toplam komut süresi istenen sınırı aşabilir. — Beklenen düzeltme: Kilidin süre dolmadan bırakıldığı başarı senaryosu ile hiç bırakılmadığı zaman aşımı senaryosu ayrılmalı; toplam duvar saati toleransı ve süre aşımı günlüğünün ek bloklama yapmadan fail-closed atlanması doğrulanmalıdır.

12. Görev tetikleme / sahiplik ve işlem sınırı — orta — Karar tetiklemeyi ayar yazımından sonra başlatıyor ancak başlatmadan hemen önce tek eylemli görev sahipliğinin yeniden doğrulanmasını, sorgu hatasının fail-closed davranışını ve tetikleme ya da yoklama başarısızlığında yeni kurulumun korunup korunmayacağını belirtmiyor. Böylece görev kurma işleminin geri alma sınırı belirsiz kalıyor. — Beklenen düzeltme: Tetikleme öncesi execute ve tam argüman eşitliği yeniden doğrulanmalı; yabancı görev ve sorgu hatası için görevin asla başlatılmadığı test edilmeli; kurulumun hangi noktada kesinleştiği ve tetikleme sonrası hatada geri alma yapılmayacağı ya da nasıl yapılacağı açıkça kararlaştırılmalıdır.

13. Görev tetikleme / doğrulanmamış işletim sistemi iddiaları — orta — Kaynaklar yalnız `0` ve `267011` değerlerini yerel gözlem olarak gösterirken karar `267009` ve `267014` anlamlarını, `LastRunTime` yoklama yeterliliğini ve çeşitli koşul teşhislerini kesin davranış olarak yazıyor. `schtasks /Run /I` iddiası yardım metnine dayanıyor; planlanan PowerShell yolunun eşdeğer davranışı için kanıt sunulmuyor. — Beklenen düzeltme: Kod eşlemeleri yetkili Microsoft belgeleriyle kaynaklandırılmalı veya doğrulanmamış olarak işaretlenmeli; çalışan, hiç çalışmamış, sonlandırılmış, hızlı tamamlanan, kuyrukta kalan ve sorgu hatalı görevler kontrollü test göreviyle kanıtlanmalıdır.

14. Doğrulama mimarisi / Türkçe hata metni — orta — Plan `ArgumentParser.error` içinde CPython'un İngilizce hata metinlerinin eşlenmeyeceğini açıkça söylüyor; yalnız Türkçe önek eklemek “kullanıcıya dönük tüm metinler Türkçe” kuralını karşılamıyor. Özellikle bilinmeyen bayrak, eksik değer ve geçersiz `int` hataları İngilizce kalabilir. — Beklenen düzeltme: Desteklenen ayrıştırma hata sınıfları Türkçe ve kararlı mesajlara dönüştürülmeli ya da tüm girdi biçimi denetimi kontrollü Türkçe doğrulama katmanına taşınmalı; temsilî parse hataları stderr ve exit 2 ile test edilmelidir.

15. Uygulama Sırası — orta — Öncelik 1'de kapatılması istenen matris Öncelik 2 ve 3'te eklenecek bayrakları şimdiden içeriyor; `--json` kabulü de henüz eklenmemiş `--saglik` ve `--oto-tamamlama` çıktısına bağlanıyor. “Aynı sürümde küçük ve bağımsız” yaklaşımı bu bağımlılıkları ve geri alma noktalarını göstermiyor. — Beklenen düzeltme: Önce parser, sürüm ve çıktı yönlendirme altyapısı; sonra mevcut mod matrisi; ardından her özellik ile aynı değişiklikte matris, şema ve dokümantasyon genişletmesi sıralanmalı, her dilim bağımsız doğrulanabilir ve geri alınabilir olmalıdır.

16. `--log` — orta — Alternatif günlük yolu için davranış kararı bulunmasına rağmen ayrı kabul kriteri ve doğrulama yöntemi yoktur. Mevcut `gunluk.LOG_YOLU` modül globalidir; ardışık çağrılarda yol sızıntısı, kök sınırı, bağlantı veya yeniden ayrıştırma yarışı, üst dizin oluşturma, rotasyon, kilitli hedef ve geçici dosya temizliği sınanmamıştır. — Beklenen düzeltme: Yolun çağrı kapsamı, kök içi son hedef doğrulaması ve hata sınıfları tanımlanmalı; normal ve JSON modları, ardışık farklı yollar, kök kaçışı, mevcut dizin hedefi, kilitli hedef ve rotasyon senaryoları kabul testine eklenmelidir.

17. Riskler ve Kapsam Dışı — düşük — Risk listesi yalnız üç konuyu kapsıyor; zamanlanmış görev kimliği geçişi, kuru çalışmanın gerçek mutasyonsuzluğu, tetikleme yan etkisi ve zaman aşımı, global çıktı ve günlük durumu, sağlık sorgularının maliyeti, alternatif yol güvenliği ve üretilen tamamlama dosyasının yaşam döngüsü yer almıyor. — Beklenen düzeltme: Bu başlıklar etki, olasılık, azaltım, geri alma ve kanıt sahibiyle risk listesine eklenmeli; kabul edilmeyen riskler kapsam dışı olarak açıkça belirtilmelidir.

18. Kabuk tamamlama ve boyut sınırı kararlarının dili — düşük — 3.5 ilk tanımı PowerShell ve bash üretimi söylerken net karar v1'i yalnız PowerShell ile sınırlandırıyor; “dosya `.gitignore` dışındadır” ile “sürüm kontrolüne alınmaz” ifadeleri de birbirini karşılamıyor. Benzer biçimde 3.1 sınırı “değiştirir” derken son karar yalnız düşürmeye izin veriyor. — Beklenen düzeltme: Son kararların önceki özetleri geçersiz kıldığı açıkça belirtilmeli; desteklenen kabuk, üretilen dosyanın izlenme veya yoksayılma politikası ve `--sinir` için 1, 200 ve 201 sınır örnekleri tek anlamlı hale getirilmelidir.

SONUC: BULGULAR

## Plan Revizyonu — Sol Tur 1 Bulgularının Kapatılması (2026-09-21)

Aşağıdaki kararlar Sol'un tur 1 bulgularını kapatır ve önceki bölümlerdeki çelişen ifadeleri geçersiz kılar (matris, uygulama sırası ve risk listesi ilgili bölümlerde ayrıca revize edilmiştir).

* F1 (kritik, `--otomatik`): Kapatıldı. `--otomatik` bağımsız zamanlanmış koşu modudur ve `--cek` ile birlikte de geçerlidir; görev eylemi dizesi `zamanlayici.beklenen_arguman` olarak dondurulmuştur ve değiştirilmez.
* F2 (kritik, argparse varsayılanları): Kapatıldı. Moda özgü seçenekler `None` ile tanımlanır; gerçek varsayılanlar doğrulama sonrası ilgili işleyicide uygulanır; her yalın mod çağrısı regresyon testine eklenir.
* F3 (orta, JSON şeması): Kapatıldı. Kanonik şema "Netleştirilen Mimari Kararlar > JSON çıktı sözleşmesi" bölümündedir; 1.1'deki eski alan örneği geçersizdir. Kanallar: başarı (0) → stdout'ta tek JSON, stderr yalnız uyarı; çalışma hatası (1) → stdout boş, stderr'de JSON hata nesnesi ve insan satırı; kullanım hatası (2) → stderr'de düz Türkçe metin, JSON yok. Başarısız koşuda stdout'a yarım JSON yazılmaz.
* F4 (orta, `--surum`): Kapatıldı. `--surum` tek başına veya yalnız `--json` ile geçerlidir (matris güncellendi); 1.5 kabul kriteriyle uyumludur.
* F5 (orta, `--saglik`): Kapatıldı. Mod listesine ve matrise eklendi. Ağ politikası: varsayılan ağsız; `--ders` → tek depo listeleme (1 API çağrısı) ve o dersin görev sorgusu; `--ag` → en fazla ilk 10 ders listelenir, atlananlar raporlanır; `--ag` ile `--ders` birlikte exit 2; `--ayrintili` → görev sorgusu (ağsız, en fazla 20 ders).
* F6 (orta, sağlık salt-okunurluğu ve meta): Kapatıldı. `depo_listele` yeni opsiyonel parametreyle kota meta verisini döndürür (`limit/kalan/sifirla`); mevcut çağrı imzaları değişmez; sağlık hiçbir dosya, dizin, yedek veya günlük oluşturmaz; bozuk ayarı karantinaya almaz, yalnız sorun olarak raporlar; negatif dosya sistemi kanıtı kabul kriteridir.
* F7 (orta, `--ayrintili`): Kapatıldı. Yalnız `--durum` ve `--saglik` ile geçerlidir; `--listele --ayrintili` kapsam dışıdır (exit 2).
* F8 (orta, matris bütünlüğü): Kapatıldı. `--ag`, `--her-gun`, `--hafta-ici` ve `--oto-tamamlama` matrise eklendi; `--log` yalnız `--surum` ile yasaktır.
* F9 (orta, kuru çekme mutasyonsuzluğu): Kapatıldı. Kuru yolu hedef klasör oluşturma, kalıntı silme ve karantinadan önce ayrılır; ortak mutex altında salt-okunur inceleme yapılır; hedef yok, bozuk durum, kalıntı, kilit dolu, ağ hatası ve doğrulama hatası senaryoları sıfır mutasyon ve 0/1 davranışıyla test edilir.
* F10 (orta, global çıktı): Kapatıldı. Konsol çıktı politikası çağrı kapsamlıdır (`main` içinde `try/finally` geri yükleme veya `kayit(konsol=...)`); ardışık sessiz/JSON/normal çağrı testleri zorunludur.
* F11 (orta, `--kilit-bekle`): Kapatıldı. Testler "süre dolmadan bırakıldı" ve "hiç bırakılmadı" senaryolarını ayırır; toplam duvar saati toleransı tanımlanır ve süre aşımı günlüğü ek bloklama yapmadan fail-closed atlanır.
* F12 (orta, tetikleme sınırı): Kapatıldı. Tetikleme öncesi tek-eylem sahipliği yeniden doğrulanır (sorgu hatası fail-closed, yabancı görev tetiklenmez); kurulum kesinleşme noktası ayar yazımının başarısıdır; tetikleme veya yoklama hatası kurulumu geri almaz, hata raporlanır.
* F13 (orta, doğrulanmamış işletim sistemi iddiaları): Kapatıldı. `267009`, `267014`, olay kimlikleri ve `/I` davranışı "danışmanlık/doğrulanmadı" olarak işaretlendi; kabul, kontrollü test göreviyle başarı, hiç çalışmadı, kuyrukta ve sorgu hatası senaryolarının kanıtlanmasını gerektirir; kod eşlemeleri yalnız kanıtlanan değerlerle kesinleştirilir (`0` ve `267011` yerel olarak doğrulandı).
* F14 (orta, Türkçe ayrıştırma hataları): Kapatıldı. Ayrıştırma hata sınıfları Türkçe şablonlara çevrilir; eşlenemeyen durumda jenerik Türkçe metin ve ayrıntı yazılır; `exit_on_error=False` kullanılmaz; temsilî hatalar stderr + exit 2 ile test edilir.
* F15 (orta, uygulama sırası): Kapatıldı. "Uygulama Sırası (revize)" altyapı → matris → JSON → çekme → sağlık → otomasyon → tamamlama dilimlerine ayrıldı.
* F16 (orta, `--log` kabul kriterleri): Kapatıldı. Kabul: çağrı kapsamlı yol, `realpath` kök kontrolü, dizin oluşturma, rotasyon, kilitli hedef, `.tmp` temizliği, normal/JSON modları ve ardışık farklı yol senaryoları.
* F17 (düşük, risk listesi): Kapatıldı. Risk listesi görev dizesi geçişi, kuru mutasyonsuzluk, tetikleme yan etkisi, global çıktı, sağlık maliyeti, günlük yolu güvenliği, tamamlama dosyası yaşam döngüsü, argv varsayılanları, Türkçe hata kırılganlığı ve `--sinir` beklentisiyle genişletildi.
* F18 (düşük, ifade tutarlılığı): Kapatıldı. v1 yalnız PowerShell tamamlama üretir; dosya `tamamlama/` altında üretilir ve `.gitignore` ile yok sayılır (sürüm kontrolüne alınmaz); `--sinir` yalnız düşürmeye izin verir (1-200; 0/1/200/201 sınır örnekleri kabul testindedir).

Tur 1'deki 2 kritik, 14 orta ve 2 düşük bulgu revize edildi; Tur 2 denetiminde 12'si kapandı, kalan 6 bulgu aşağıdaki ek kararlarla kapatıldı:

* F1 (kritik): `--ders` matris satırına `--otomatik` eklendi; dondurulmuş görev argv'si (`--otomatik --ders <slug> --sessiz`) geçerli kombinasyon testine alınır. `--ders` verilmezse `--otomatik` yalnız işaretli dersleri çeker (mevcut davranış korunur) ve bu kabul kriteridir.
* F4 (orta): `--sessiz` satırı `--surum` istisnasını taşır; `--surum --sessiz` exit 2, `--surum --json` geçerlidir.
* F11 (orta): İzin verilen toplam duvar saati = `--kilit-bekle` süresi + 15 sn sabit pay (kilit alma gecikmesi + olası 10 sn günlük kilidi beklemesi + işlem payı). İki senaryo (süre dolmadan bırakılma, hiç bırakılmama) bu sayısal sınırla test edilir; süre aşımı günlüğü ek bloklama yapmadan fail-closed atlanır.
* F13 (orta): Kontrollü test görevi senaryoları genişletildi: başarı (0), hiç çalışmadı (267011), kuyrukta kalma (koşul/pil), sonlandırılmış (ExecutionTimeLimit veya Stop-ScheduledTask), hızlı tamamlanan (Running hiç görülmeden Ready) ve sorgu hatası (fail-closed). Kanıtlanmayan sonuç kodları yalnız ham/hex olarak raporlanır; anlam eşlemesi yalnız kanıtlanan değerlerle yapılır.
* F16 (orta): `--log` için yazım öncesi ikinci doğrulama zorunludur: hedefin gerçek yolu kök içindedir ve hedef mevcut bir dizin değildir; junction/reparse noktası `os.lstat` reparse bayrağı ve `os.path.realpath` ile denetlenir; denetim-yazım arası yarışa karşı yazım anında yeniden doğrulama ve atomik yazım uygulanır. Negatif testler: mevcut dizin hedefi, junction/reparse değişimi, kök dışı hedef.
* F17 (düşük): Risk listesi tabloya çevrildi; her satırda Etki, Olasılık, Azaltım, Geri alma ve Kanıt sahibi alanları bulunur. Kabul edilmeyen riskler "Kapsam Dışı" bölümüne taşındı.

Tur 3 denetimi bekleniyor.

## Sol Denetim Turu 2 Sonucu

Tur 1 bulguları; revize kombinasyon matrisi, "Plan Revizyonu — Sol Tur 1 Bulgularının Kapatılması", "Uygulama Sırası (revize)", "Riskler" ve salt-okunur kod bağlamı birlikte değerlendirilerek yeniden denetlendi. Son revizyonun önceki çelişen ifadeleri geçersiz kıldığı kuralı dikkate alındı.

* F1 — açık (kritik): `--otomatik` satırı bağımsız zamanlanmış koşuyu ve dondurulmuş görev dizesini koruyor; ancak `--ders` satırı geçerli modlar arasında `--otomatik` seçeneğini saymıyor. Bu nedenle gerçek görev dizesi `--otomatik --ders <slug> --sessiz`, matrisin `--ders` kuralına göre hâlâ exit 2 üretebilir.
* F2 — kapatıldı: "Kombinasyon doğrulaması" moda özgü `--dal`, `--desen`, `--gunler` ve `--saat` değerlerini `None` yapıyor; gerçek varsayılanları doğrulama sonrasına taşıyor ve yalın mod regresyonlarını zorunlu kılıyor.
* F3 — kapatıldı: Son revizyon başarıyı stdout'ta tek JSON nesnesi, çalışma hatasını stdout boş ve stderr'de JSON hata nesnesi ile insan satırı, kullanım hatasını stderr'de düz Türkçe metin ve JSON'suz olarak ayrı ayrı tanımlıyor; 0/1/2 kanal politikası ve yarım JSON yasağı nettir.
* F4 — açık (orta): `--surum` satırı yalnız tek başına veya `--json` ile kullanıma izin verirken `--sessiz` satırı seçeneği "Tüm modlar" için geçerli sayıyor. `--surum --sessiz` birleşimi için hangi satırın üstün olduğu belirtilmediğinden matris ile F4 kapatma kararı tam uyumlu değildir.
* F5 — kapatıldı: `--saglik` mod listesi ve matriste yer alıyor; varsayılan ağsız davranış, `--ders` için tek depo çağrısı, `--ag` için ilk 10 ders sınırı, atlananların raporu, `--ag`/`--ders` dışlaması ve görev sorgusu sınırları son revizyonda bağlayıcı biçimde tanımlanıyor.
* F6 — kapatıldı: Kota meta verisinin opsiyonel dönüşü tanımlanıyor; sağlık kontrolünün dosya, dizin, yedek veya günlük oluşturması ve bozuk ayarı karantinaya alması yasaklanıyor. Negatif dosya sistemi kanıtı açık kabul ölçütüdür.
* F7 — kapatıldı: `--ayrintili` yalnız `--durum` ve `--saglik` ile geçerlidir; `--listele --ayrintili` için exit 2 kararı ve sağlık görev sorgusu üst sınırı belirtilmiştir.
* F8 — kapatıldı: `--ag`, `--her-gun`, `--hafta-ici` ve `--oto-tamamlama` matrise eklenmiş; `--log` ile `--surum` açıkça yasaklanmıştır. F4'teki `--sessiz` çelişkisi ayrıca izlenmektedir.
* F9 — kapatıldı: Kuru yolun hedef klasör oluşturma, kalıntı temizleme ve karantinadan önce ayrılması; ortak mutex altında salt-okunur çalışması; hedef yokluğu, bozuk durum, kalıntı, kilit, ağ ve doğrulama senaryolarında sıfır mutasyon kanıtı istenmiştir. Çalışma sonuçları için 0/1, kullanım hataları için genel matris üzerinden 2 davranışı test edilebilir durumdadır.
* F10 — kapatıldı: Çıktı politikası çağrı kapsamına alınmış, global durumun `try/finally` ile geri yüklenmesi veya konsol hedefinin parametreleştirilmesi kararlaştırılmış; ardışık sessiz, JSON ve normal çağrı testleri zorunludur.
* F11 — açık (orta): Süre dolmadan bırakılan ve hiç bırakılmayan kilit senaryoları ile ek günlük bloklamasının yasaklanması tanımlanmış; fakat "toplam duvar saati toleransı tanımlanır" denmesine rağmen sayısal tolerans veya hesaplama kuralı verilmemiştir. Kabul ölçütü hâlâ kesin ve tekrarlanabilir değildir.
* F12 — kapatıldı: Tetiklemeden hemen önce tek eylemli sahiplik yeniden doğrulaması, sorgu hatasında fail-closed davranış, yabancı görevin başlatılmaması, ayar yazımındaki kesinleşme noktası ve tetikleme/yoklama hatasında geri almama kararı açık ve test edilebilirdir.
* F13 — açık (orta): Son revizyon doğrulanmamış sonuç kodlarını ve `/I` davranışını danışmanlık olarak sınıflandırıyor; ancak Tur 1'in beklediği kontrollü senaryolardan sonlandırılmış ve hızlı tamamlanan görevler kabul listesine alınmamış. Yoklama yarışlarının ve `267014` yorumunun kanıt kapsamı eksik kalmıştır.
* F14 — kapatıldı: Bilinmeyen bayrak, eksik değer ve geçersiz tamsayı/seçenek sınıfları kararlı Türkçe şablonlara bağlanmış; eşlenemeyen hata için özgün İngilizceyi göstermeyen Türkçe geri dönüş ve stderr/exit 2 testleri tanımlanmıştır.
* F15 — kapatıldı: Revize sıra altyapı, mevcut matris, JSON, çekme, sağlık, otomasyon ve tamamlama dilimlerine ayrılmış; her dilimde matris, şema, test ve dokümantasyonun birlikte güncellenmesi ile bağımsız doğrulama ve geri alma şartı konmuştur.
* F16 — açık (orta): Çağrı kapsamı, kök denetimi, dizin oluşturma, rotasyon, kilitli hedef, geçici dosya temizliği ve ardışık yol testleri eklenmiştir; ancak mevcut bir dizinin dosya hedefi verilmesi ile junction/reparse noktasının denetim-yazım arasındaki yarışına ilişkin somut kabul testi ve fail-closed uygulama sınırı hâlâ yoktur.
* F17 — açık (düşük): Risk listesi önceki eksik konu başlıklarını kapsıyor; buna karşılık Tur 1'de istenen etki, olasılık, geri alma ve kanıt sahibi alanları riskler bazında belirtilmemiş, kabul edilmeyen riskler de "Kapsam Dışı" altında ayrıştırılmamıştır.
* F18 — kapatıldı: Son revizyon önceki çelişen özetleri geçersiz kılıyor; v1'i PowerShell ile sınırlıyor, üretilen dosyayı `tamamlama/` altında `.gitignore` ile yoksayıyor ve `--sinir` için yalnız 1-200 aralığını, 0/1/200/201 sınır örnekleriyle sabitliyor.

Kalan bulgular ve beklenen düzeltmeler:

* Kritik — F1: `--ders` matris satırına `--otomatik` modu eklenmeli; bağımsız dondurulmuş görev argv'si geçerli kombinasyon testine, `--otomatik` için derssiz çağrının davranışı da açık kabul ölçütüne alınmalıdır.
* Orta — F4: `--sessiz` satırı `--surum` istisnasını açıkça taşımalı veya `--surum --sessiz` desteklenecekse F4 kararı ve sürüm satırı buna göre değiştirilmelidir.
* Orta — F11: Kilit bekleme süresi için işletim sistemi zamanlama payını içeren sayısal üst sınır ya da hesaplama formülü yazılmalı ve iki duvar saati testi bu değere bağlanmalıdır.
* Orta — F13: Sonlandırılmış ve hızlı tamamlanan görev senaryoları kontrollü test listesine eklenmeli; kanıtlanmayan sonuç kodları yalnız ham/hex değer olarak raporlanmalıdır.
* Orta — F16: Mevcut dizin hedefi ve junction/reparse değiştirme yarışı için fail-closed davranış ile negatif testler tanımlanmalı; yalnız ilk `realpath` kontrolüne güvenilmemelidir.
* Düşük — F17: Her risk için etki, olasılık, azaltım, geri alma ve kanıt sahibi belirtilmeli; kabul edilmeyen riskler kapsam dışına açıkça taşınmalıdır.

Toplam: 12 bulgu kapatıldı; 1 kritik, 4 orta ve 1 düşük bulgu açık kaldı.

SONUC: BULGULAR

## Sol Denetim Turu 3 Sonucu

Tur 2'de açık kalan altı bulgu; son ek kararlar, revize bayrak matrisi, risk ve kapsam dışı bölümleri ile salt-okunur kod bağlamı birlikte değerlendirilerek yeniden denetlendi. "Plan Revizyonu — Sol Tur 1 Bulgularının Kapatılması" bölümünün önceki çelişen ifadeleri geçersiz kılan öncelik kuralı dikkate alındı.

* F1 — kapatıldı (kritik): `--ders` satırı artık `--otomatik` modunu açıkça geçerli sayıyor; dondurulmuş `--otomatik --ders <slug> --sessiz` görev argv'si geçerli kombinasyon testine bağlanmış ve derssiz `--otomatik` çağrısının yalnız işaretli dersleri çekmesi açık kabul kriteri yapılmıştır. Bu karar, `zamanlayici.beklenen_arguman` ve mevcut dersli/derssiz otomatik çekme davranışıyla uyumludur.
* F4 — kapatıldı (orta): `--sessiz` satırı `--surum` istisnasını açıkça taşıyor; `--surum --sessiz` exit 2 ve `--surum --json` geçerli kabul edilerek matris önceliği tek anlamlı hale getirilmiştir.
* F11 — kapatıldı (orta): Toplam duvar saati üst sınırı `--kilit-bekle` süresi + 15 saniye olarak sayısallaştırılmış, süre dolmadan bırakılma ve hiç bırakılmama senaryolarının ikisi de bu sınıra bağlanmış, süre aşımı günlüğünün ek bloklama yapmadan fail-closed atlanması zorunlu tutulmuştur.
* F13 — kapatıldı (orta): Kontrollü test listesi başarı, `267011`, kuyrukta kalma, sonlandırılma, hızlı tamamlanma ve sorgu hatasını kapsıyor; kanıtlanmayan sonuç kodlarının yalnız ham/hex raporlanması ve anlam eşlemesinin kanıtlanan değerlerle sınırlanması önceki kesin kod yorumlarını geçersiz kılan revizyon kuralıyla uyumludur.
* F16 — kapatıldı (orta): `--log` hedefi için yazım öncesi ikinci kök, dizin ve junction/reparse doğrulaması ile yazım anında yeniden doğrulama zorunlu kılınmış; mevcut dizin hedefi, junction/reparse değişimi ve kök dışı hedef negatif testleri fail-closed sınırı somutlaştırmıştır.
* F17 — kapatıldı (düşük): Riskler tablosu her risk için Etki, Olasılık, Azaltım, Geri alma ve Kanıt sahibi alanlarını içeriyor; kabul edilmeyen seçenekler Kapsam Dışı bölümünde ayrıştırılmıştır.

Toplam: 6 bulgu kapatıldı; açık bulgu ve kalan çelişki yoktur.

SONUC: ONAY

## Sol Denetim Turu 4 Sonucu

* Değişmezlerle uyum — kapatıldı: İlke mutex, atomik yazım ve görev sahipliği denetimini gevşetmiyor; Türkçe sunum ile dinamik Rich metinlerinde `rich.markup.escape` kullanımını TUI için açıkça koruyor.
* TUI kapsamının uygulanabilirliği — kapatıldı: Mevcut `merkez/arayuz.py` ders ekleme/çıkarma, çekme ve otomasyon menülerini barındırıyor; durum, sağlık ve kuru çalışma akışlarının aynı menü düzenine eklenmesi gerçekçi. CLI ve TUI'deki yinelenen silme, çekme ve otomasyon orkestrasyonunun ortak uygulama işlevlerine çıkarılması ilkeyle uyumludur.
* Yardım yüzeyi — açık (orta): İlke her özellik için `--yardim` açıklaması istiyor, ancak mevcut argparse yalnız yerleşik `-h/--help` yüzeyini sağlıyor; planda `--yardim` seçeneği, matris kuralı veya kabul testi yok. Beklenen düzeltme: İfade mevcut `-h/--help` çıktısı olarak düzeltilmeli ya da `--yardim` Türkçe takma adı matrise, uygulama sırasına ve yardım testine açıkça eklenmelidir.
* TUI eşliği sınırı — açık (orta): “TUI'de karşılığı olan” ve kapanıştaki “varsa TUI bağlantısı” ölçülebilir bir karar kuralı vermiyor; `--zorla`, `--zorla-md`, `--kilit-bekle`, `--sinir`, `--tetikle` ve `--ayrintili` seçeneklerinin hangilerinin mevcut çekme, otomasyon veya durum akışlarına taşınacağı belirsiz. Beklenen düzeltme: Her plan maddesini CLI seçeneği, TUI karşılığı veya gerekçeli CLI-özel sınıfı ve çağrılacak ortak işlevle eşleyen bağlayıcı bir eşlik listesi eklenmelidir.
* Salt CLI sınıflandırması — açık (düşük): `--json`, `--oto-tamamlama`, `--log` ve `--sessiz` topluca “çıktılar” diye adlandırılmıştır; `--log` bir çıktı biçimi değil günlük hedefi seçeneğidir ve bu ifade yeni CLI-özel seçeneklerin hangi ölçütle dışlanacağını açıklamaz. Beklenen düzeltme: Başlık “salt CLI seçenekleri ve çıktı kipleri” olarak netleştirilmeli, dışlama ölçütü etkileşimsiz/makine tüketimli yüzey olarak tanımlanmalıdır.
* Çıkış kodu sözleşmesi — açık (orta): TUI'nin “aynı çıkış kodu kurallarına” uyması mevcut sürekli menü modeliyle test edilebilir değildir; TUI işlem hatalarını ekranda gösterip menüye dönerken süreç genellikle 0 ile kapanır. Beklenen düzeltme: 0/1/2'nin yalnız CLI süreç sonucu olduğu, ortak işlevlerin başarı/çalışma hatası/kullanım hatası sınıfı döndürdüğü ve TUI'nin bu sınıfları Türkçe, kaçışlı iletiye dönüştürüp menü yaşam döngüsünü koruduğu yazılmalıdır.
* Kabul kriterlerinin somutluğu — açık (yüksek): Genel “arayüz eşliği kontrolü eklenir” cümlesi, özellik bazlı kabul ölçütlerini değiştirmiyor ve dilimin eşlik tamamlanmadan kapanmasını nesnel olarak kanıtlamıyor. Beklenen düzeltme: Her dilimde argparse seçeneği ve yardım görünürlüğü, README ile `belgeler/kurulum.md` güncelliği, eşlik listesindeki TUI menü erişimi, CLI ve TUI adaptörlerinin aynı ortak işlevi eşdeğer girdilerle çağırması, eşdeğer sonuç/hata sınıfları ve salt CLI seçeneklerinin TUI'de bulunmaması için çalıştırılabilir kontroller zorunlu kılınmalıdır.

SONUC: BULGULAR

## Sol Denetim Turu 5 Sonucu

* Yardım yüzeyi — kapatıldı: Kapsam ilkesi artık mevcut `-h/--help` çıktısını bağlayıcı yardım yüzeyi olarak tanımlıyor, Türkçe açıklamayı kabul kontrolüne bağlıyor ve ayrı bir `--yardim` bayrağı eklenmeyeceğini açıkça belirtiyor.
* TUI eşliği sınırı — açık (orta): Bağlayıcı "Eşlik Listesi" seçenek taşıyan özelliklerin CLI, TUI, sınıf ve ortak işlev karşılıklarını büyük ölçüde somutlaştırıyor; ancak bağımsız plan maddesi 1.4 "Kombinasyon doğrulaması" listede yer almıyor. Bu nedenle "her plan maddesi" kapsamı eksiksiz sağlanmış değildir. Beklenen düzeltme: 1.4 için CLI seçeneği veya uygulanabilir yüzey, TUI karşılığı ya da gerekçeli salt CLI sınıfı ve kullanılacak ortak doğrulama/sonuç sınırı eşlik listesine eklenmelidir.
* Salt CLI sınıflandırması — kapatıldı: Başlık "Salt CLI seçenekleri ve çıktı kipleri" olarak netleştirilmiş, dışlama ölçütü makine tüketimli veya etkileşimsiz yüzey olarak tanımlanmış ve `--log` açıkça günlük hedefi seçeneği olarak ayrıştırılmıştır.
* TUI çıkış kodu sözleşmesi — kapatıldı: 0/1/2 yalnız CLI süreç sonucu olarak sınırlandırılmış; ortak işlevlerin sonuç/hata sınıfı döndürmesi ve TUI'nin bunları Türkçe, kaçışlı iletilere çevirerek menü döngüsünü koruması açıkça yazılmıştır.
* Kabul kriterlerinin somutluğu — kapatıldı: Altı çalıştırılabilir kontrol yardım görünürlüğünü, README ve `belgeler/kurulum.md` güncelliğini, TUI menü erişimini, eşdeğer girdilerle aynı ortak işlev çağrısını, eşdeğer hata sınıflarını ve salt CLI seçeneklerinin TUI'de bulunmamasını kapsıyor; dilimin bu kontroller geçmeden tamamlanamayacağı belirtiliyor.

Toplam: 4 bulgu kapatıldı; 1 orta bulgu açık kaldı.

SONUC: BULGULAR

## Sol Denetim Turu 6 Sonucu

* TUI eşliği sınırı — kapatıldı: Bağlayıcı "Eşlik Listesi" artık 1.4 "Kombinasyon doğrulaması" maddesini içeriyor. Satır, CLI karşılığını tüm seçenekler için `_dogrula`, TUI karşılığını menülerin geçersiz kombinasyon üretmemesi ve ilkenin TUI akışlarında da geçerli olması, sınıfı "TUI eşli (dolaylı)", ortak işlevi ise ortak `_dogrula(secenekler)` sonuç/hata sınıfı olarak tanımlıyor. Böylece Tur 5'te beklenen CLI yüzeyi, TUI karşılığı, sınıflandırma ve ortak doğrulama/sonuç sınırı eksiksiz karşılanmıştır.

Kalan çelişki yoktur.

SONUC: ONAY


## Uygulama ve Doğrulama Kanıtları (0.1.2)

* Sürüm 0.1.2 uygulandı: `merkez/komut.py` (parser + `dogrula` matrisi + JSON/kanal sözleşmesi + Türkçe ayrıştırma hataları), `merkez/durum.py`, `merkez/saglik.py`, `merkez/tamamlama.py`, `merkez/ps/gorev_tetikle.ps1`; `indirici`, `zamanlayici`, `gunluk`, `ayarlar`, `arayuz` ve `dersmerkezi.py` güncellendi; `merkez/__init__.py` sürümü 0.1.2; `UA` sürümden türetilir.
* Eşlik Listesi uygulandı: TUI kuru önizleme + zorlama onayı, kilit "Bekle/Atla", Durum/Sağlık ekranı, "Kur ve hemen dene", gün kısayolları, menüde sürüm; CLI ve TUI aynı ortak işlevleri çağırır (`indir_ders`, `gorev_kur_guvenli`, `gorev_tetikle`, `ders_sil_guvenli`, `durum.kayitlar`, `saglik.denetle`).
* Kabul kontrolleri: `-h` tüm yeni seçenekleri listeler; README ve `belgeler/kurulum.md` güncellendi; salt CLI seçenekleri (`--json`, `--oto-tamamlama`, `--log`, `--sessiz`) TUI'de yok; eşdeğer hatalar aynı sınıflara düşer (kullanım 2 / çalışma 1).
* Test kanıtları: 164 birim/akış + 14 tetikleme/sahiplik kontrolü geçti (Tur 1 kapanışlarıyla genişletildi) (geçici kopyada; repoya test dosyası eklenmedi); ayrıntılar `belgeler/plan/2026-09-21-dersmerkezi-cli.md` "CLI Genişletmesi 0.1.2 Kanıtları" bölümünde.
* Doğrulama kapısı ve kontrollü test görevi senaryoları (başarı 0, süre aşımı/çalışıyor ham hex, temizlik) aynı bölümde kayıtlıdır.
* Uçtan uca ve kapsam testi (2026-09-22): dört paket (164 birim/akış + 150 fonksiyon kapsamı + 46 uçtan uca + 14 tetikleme/sahiplik) 374/374 geçti; `trace` koşusunda 131/131 fonksiyon çağrıldı, ifade satırı kapsamı %81. Gerçek ağ ve Görev Zamanlayıcı ile tam yaşam döngüsü (ekle/listele/çek/kuru/log/kilit/görev kur-güncelle-tetikle-kaldır/sil, `--her-gun` 127 ve `--hafta-ici` 62 maskeleri, tamamlama PS sözdizimi) doğrulandı; üretim görevi Ready|0 korundu. 0.1.4 son kod kapısı: `--cek --sessiz` exit 0 (`atlanan=2`), `--surum` 0.1.4, `--ayarlar --json`, `--durum` (Ready) ve `--saglik --ders` exit 0.
* Sol kod denetimi: tur 1'de 6 orta + 2 düşük, tur 2'de 1 orta bulgu (rotasyon) açıldı ve kapatıldı; tur 3'te `SONUC: ONAY` alındı. Bulguların kapatma kararları yukarıdaki "Uygulama Revizyonu" bölümündedir.


## Uygulama Revizyonu — Sol Uygulama Turu 1 Bulgularının Kapatılması (2026-09-22)

Aşağıdaki kararlar uygulama sonrası Sol denetiminin (0.1.2) tur 1 bulgularını kapatır ve önceki çelişen ifadeleri geçersiz kılar.

* U1 (orta, kanal politikası): Kapatıldı. Hata sayacı taşıyan mod sonuçları (çekme `dogrulama_hatasi`/`donusum_hatasi`, sağlık `sorunlar`) çalışma istisnası değildir; kanonik şemaları gereği JSON stdout'ta kalır ve exit 1 döner. Kanal politikasındaki "exit 1 → stdout boş" kuralı yalnızca istisna yolları (RuntimeError/IndirmeHatasi/OSError) içindir; bu durumda stdout boş, stderr'de JSON hata nesnesi + insan satırı yazılır. `--sessiz` yalnızca insan satırını bastırabilir; JSON hata nesnesi her durumda stderr'e yazılır.
* U2 (orta, kuru mutasyonsuzluk): Kapatıldı. `ayarlar.yukle_salt`/`ayarlar.secili_dersler_salt` eklendi; `--cek --kuru` bozuk ayarda karantina yapmaz, exit 1 döner ve ayar dosyası değişmez (test kanıtı).
* U3 (orta, 200 MB değişmezi): Kapatıldı. `indirici.indir_ders` girişinde `1 <= ust_boyut <= UST_BOYUT` fail-closed doğrulaması yapılır; CLI dışı çağrı yolları da 200 MB üstünü açamaz (test kanıtı).
* U4 (orta, `--log` yazılabilirliği): Kapatıldı. `gunluk.log_yolu_ayarla` hedefi append modunda açıp yazılabilirliği kanıtlar (OSError → exit 1); özel günlükte yazım/rotasyon hatası OSError olarak yükseltilir (varsayılan günlükte fail-closed atlama korunur). Kök dışı/dizin/reparse doğrulama hataları exit 2 kalır. Tur 2 bulgusu: `_rotasyon` hatası da özel günlük hedefinde `OSError` olarak yükseltilir; varsayılan günlükte fail-closed atlama korunur (test: kilitli `.old` → exit 1, hedef dosyalar değişmeden korunur).
* U5 (orta, TUI sağlık salt-okunurluğu): Kapatıldı. TUI durum ekranı `durum.kayitlar_salt` kullanır; bozuk ayarda karantina yapılmaz ve "Sağlık kontrolü" erişilebilir kalır (test kanıtı).
* U6 (orta, eşlik listesi): Kapatıldı. TUI çekme akışına "Zorla yeniden indir" ve "Yalnız bağlamı yenile" seçenekleri, sağlık ekranına "Tek ders için ağ kontrolü" eklendi; CLI ve TUI aynı ortak işlevleri eşdeğer girdilerle çağırır (test kanıtı).
* U7 (düşük, Rich kaçışı): Kapatıldı. Otomasyon detayındaki gün/saat/görev durumu ve görev kurulum satırları `rich.markup.escape` ile kaçışlanır; enjeksiyon testi eklendi.
* U8 (düşük, üretilen betik): Kapatıldı. Tamamlama betiğindeki yorum satırı kaldırıldı; üretim parser kaynaklı ve atomik kalır (test kanıtı).
