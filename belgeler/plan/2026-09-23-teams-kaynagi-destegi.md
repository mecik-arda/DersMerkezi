# DersMerkezi Teams Kaynağı Desteği - Keşif ve Plan

Tarih: 2026-09-23
Durum: T0-T4 kodu ve sahte Graph doğrulamaları tamamlandı; Sol T4 denetimi ONAY; `v0.2.0` etiketi Sol onayına dayanarak yayımlandı; canlı Graph kabulü ortam kimlik bilgilerine bağlı olarak beklemede
Kapsam: Mevcut GitHub akışına ek olarak Microsoft Teams kanal dosyalarını (SharePoint belge kitaplığı) ikinci kaynak türü olarak eklemek; mevcut yapıyı bozmadan.

## Amaç ve Özet

DersMerkezi bugün yalnız GitHub depolarından içerik çeker. Bu plan, ders kaydına isteğe bağlı `kaynak` alanı ekleyerek `teams` kaynağını tanımlar; dosyalar Microsoft Graph üzerinden listelenir ve indirilir, Markdown bağlamı ve Görev Zamanlayıcı akışı değişmeden çalışır. Şema sürümü artırılmaz; alanlar isteğe bağlıdır ve varsayılan `github`'dır. Böylece mevcut dersler ve üretim görevi etkilenmez.

## Hedef ve Kapsam

* `--ekle --kaynak teams` ile Teams/SharePoint kaynaklı ders kaydı (tenant, drive, klasör item kimliği; desen dosya adına uygulanır).
* `indirci` içinde kaynak adaptörü: Graph listeleme + indirme + bütünlük doğrulaması; ortak akış (200 MB, dosya adı kapıları, atomik yazım, Markdown üretimi, durum kaydı) aynen korunur.
* `--ayarlar`, `--listele`, `--durum`, `--saglik` çıktılarına `kaynak` alanı ve redakte edilmiş Teams özeti.
* TUI eşliği: ders ekleme ekranında kaynak seçimi ve koşullu alanlar; ders tablosuna Kaynak kolonu.
* Kimlik doğrulama: yalnız uygulama (app-only) client credentials; sırlar yalnız ortam değişkeninde.

## Hedef Dışı Bırakılanlar

* Delegated/cihaz kodu akışı ve MSAL bağımlılığı (v1 dışı; ileride ayrı dilim).
* Paylaşım bağlantısından (`/shares/...`) otomatik kaynak çözümleme ve alt klasör özyinelemesi (v1 yalnız tek klasör).
* Delta/change tracking ile artımlı senkronizasyon (v1 her koşuda listeleme; ileride iyileştirme).
* Kişisel Microsoft hesapları (app-only akış desteklemez).
* Teams mesaj/sohbet içeriği; yalnız kanal dosyaları.

## Mevcut Yapı (Kanıtlı)

* `merkez/ayarlar.py:14` SURUM=1; `yukle()` satır 222-225 farklı sürümde karantinaya alıp boş veri döner; bu nedenle şema sürümü artırılmamalıdır.
* `merkez/ayarlar.py:180-208` ders_dogrula yalnız GitHub `depo` alanına göre doğrular; kaynak ayrımı yok.
* `merkez/indirici.py:284-431` indir_ders: kaynak-bağımsız çekirdek (seçim, 200 MB kontrolü 345-348, dosya adı kapıları 338-342, atomik indirme 370-373, Markdown 392-428, durum 417-428) ve GitHub'a özgü kısımlar (`depo_listele` 324, `_raw_url` 361, blob SHA 29-36 ve 355) ayrıştırılabilir.
* `merkez/indirici.py:176-203` durum şeması sürüm 2; bilinmeyen alanlara toleranslı.
* `merkez/komut.py:10-24, 28-52, 54-78, 186-189` mod/bayrak matrisi ve `--ekle` zorunlulukları; tamamlama bayrakları parser'dan türetilir (`bayrak_listesi`).
* `merkez/zamanlayici.py:48-49, 52-57` görev eylemi dondurulmuş: `"<dersmerkezi.py>" --otomatik --ders {slug} --sessiz`; bu dize değişmemelidir.
* `merkez/saglik.py:114-133` ağ kontrolü GitHub `depo` alanına ve GITHUB_TOKEN mesajına bağlı.
* `merkez/arayuz.py:199-210, 181-196, 232-243` TUI ders ekleme ve tablo yalnız GitHub alanları.

## Mimari ve Teknoloji Kararları

* K1 Kimlik doğrulama: OAuth2 client credentials; token uç noktası `https://login.microsoftonline.com/{tenant}/oauth2/v2.0/token`, `grant_type=client_credentials`, `scope=https://graph.microsoft.com/.default`. Refresh token yoktur. Kaynak: Entra dokümanı (aşağıda). Gerekçe: otomasyon kullanıcısız çalışır; ek bağımlılık (MSAL) gerekmez, `requests` yeterlidir.
* K2 Sırlar ve kimlikler: Yalnız `TEAMS_CLIENT_SECRET` sırdır ve sadece ortam değişkeninde tutulur; `ayarlar.json`, durum dosyası ve günlüğe yazılmaz, hata mesajlarında redakte edilir. `tenantId` gizli değildir; ortam değişkeni (`TEAMS_TENANT_ID`) veya kayıt sırasında `--teams-tenant` ile verilir; `--teams-tenant` değeri ders kaydına yazılır ve çalışma zamanında kayıt > `TEAMS_TENANT_ID` önceliği uygulanır. `TEAMS_CLIENT_ID` yalnız ortam değişkeniyle verilir (ders kaydında tutulmaz). Token yalnız bellekte tutulur.
* K3 İzinler: Uygulama izni en az ayrıcalık: `Files.Read.All`. Kurumsal politika gerektirirse `Sites.Selected` + site bazlı yetkilendirme alternatif olarak belgelenir; yönetici onayı kullanıcı adımıdır.
* K4 Uç noktalar: liste `GET /drives/{driveId}/items/{itemId}/children` (sayfalama `@odata.nextLink`, varsayılan 200); indirme `GET /drives/{driveId}/items/{itemId}/content` (302 → ön kimlikli URL; yönlendirme takip edilir); dosya adı, boyut, `id` ve `file.hashes` alanları çocuk öğelerden okunur (indirme, listeden gelen ÇOCUK `id` değeriyle `GET /drives/{driveId}/items/{childId}/content` üzerinden yapılır; klasör `itemId` yalnız liste için kullanılır). Sayfalama kuralı: `@odata.nextLink` varsa liste tamamlanana kadar izlenir; en fazla 50 sayfa (10.000 öğe) sınırı uygulanır. Her `nextLink` isteği gönderilmeden önce doğrulanır: mutlak HTTPS, köken `graph.microsoft.com`, yol beklenen `/v1.0/drives/{driveId}/` önekiyle başlar; sayfalama ve Graph meta veri isteklerinin yönlendirmelerinde de aynı köken/yol denetimi uygulanır. Bu kural `/content` isteğinin ön kimlikli indirme yönlendirmesi için geçerli DEĞİLDİR; o yol K13'teki ayrı izinli hedef listesine tabidir. Uymayan istek gönderilmez; geçersiz, tekrarlanan veya döngüsel bağlantıda liste başarısız sayılır ve indirmeye başlanmaz (fail-closed). Kaynak: Graph referansları (aşağıda).
* K5 Bütünlük (fail-closed): `sha256Hash` Graph'te desteklenmez. Sağlayıcı `quickXorHash` sunuyorsa yerel QuickXorHash ile (`quickxor` yolu), ayrıca `sha1Hash` sunuyorsa yerel SHA1 ile (`sha1` yolu) karşılaştırılır; mevcut olan katmanların TÜMÜ eşleşmek zorundadır, herhangi bir uyuşmazlık `dogrulama_hatasi`'dır ve dosya nihai adına taşınmaz. Sağlayıcı hash'i yoksa içerik varsayılan olarak REDDEDİLİR (`dogrulama_hatasi`); dosya taşınmaz. Doğrulama güvence adları: Git blob SHA-1 ve SHA1 "kriptografik içerik özeti"; quickXorHash "kriptografik olmayan sağlayıcı değişim özeti"dir; ikisi eşdeğer sayılmaz ve rapor/JSON bu adları taşır. QuickXorHash yerel uygulaması bağımsız vektörlerle doğrulanmadan `quickxor` yolu etkinleştirilmez; bu yol devre dışıyken ve sağlayıcı yalnız quickXorHash sunuyorsa içerik reddedilir (otomatik zayıf kabul yolu açılmaz). Zayıf kabul yalnız ders kaydında açık `"zayif_dogrulama": true` ile ve kullanıcı risk kararıyla etkinleşir; bu durumda boyut + liste ile indirme öncesi/sonrası çocuk meta verisi arasında `eTag` karşılaştırması + yerel SHA-256 kaydı uygulanır, rapor/JSON `zayif_dogrulama` sayacı ve uyarı üretir, çıkış kodu hata sayılmaz; Zayıf kabul bağlama kuralları: (a) listeleme sırasında her çocuk için `eTag` ve `size` kaydedilir; `eTag` yoksa zayıf kabul de reddeder (fail-closed); (b) indirme öncesinde çocuk meta verisi tek istekle tazelenir (`$select=id,eTag,size,file`) ve listeyle karşılaştırılır; uyuşmazlıkta indirme yapılmaz; (c) kalıcı alanlar: `dogrulama` ("quickxor"|"sha1"|"quickxor+sha1"|"zayif") ve `saglayici_hashler` nesnesi (`{"quickxor": "...", "sha1": "..."}`; yalnız doğrulanan anahtarlar) ile `teams_etag`, `yerel_sha256`; sonraki koşuda kayıtlı her hash anahtarı yeniden hesaplanıp karşılaştırılır; (d) indirme tamamlandıktan hemen sonra çocuk meta verisi yeniden çekilir (`$select=id,eTag,size`) ve listeleme kaydıyla karşılaştırılır; indirilen bayt sayısı beklenen `size` ile eşit olmak zorundadır; herhangi bir uyuşmazlıkta geçici dosya silinir ve içerik reddedilir; (e) ikinci koşuda liste `eTag`/`size` değerleri kayıtlıyla karşılaştırılır; değişmişse içerik yeniden indirilir, aynıysa yerel SHA-256 yeniden hesaplanıp kayıtla karşılaştırılır; uyuşmazlık `dogrulama_hatasi`'dır ve nihai dosya korunmaz. (f) İki sağlayıcı hash'i de mevcutsa ikisi de doğrulanır ve `dogrulama` değeri `quickxor+sha1` olur; Markdown ve rapor/JSON bu adı taşır. (g) Zayıf kabul, listelemede `size` bulunmasını zorunlu kılar; `size` yoksa dosya zayıf kabulde de reddedilir. K10'daki `Content-Length`/akış bayt sayımı yedek yolu yalnız hash doğrulamalı yollar ve 200 MB koruması içindir, zayıf kabulü kurtarmaz.
* K6 Şema: `ayarlar.json` SURUM=1 kalır; ders kaydına isteğe bağlı `kaynak` (`github` varsayılan) ve `teams: {tenantId, driveId, itemId}` eklenir. `durum` şeması sürüm 2 kalır; ders kaydına isteğe bağlı `zayif_dogrulama` (yalnız `kaynak: teams` için, varsayılan false) eklenir; durum dosyasına isteğe bağlı `dogrulama` (`quickxor`|`sha1`|`quickxor+sha1`|`zayif`), `saglayici_hashler` (`{"quickxor": ..., "sha1": ...}`), `teams_etag`, `yerel_sha256` alanları eklenir; bilinmeyen alan toleransı korunur.
* K7 Adaptör: `indirci` içinde kaynak seçimi yalın `if kaynak == "teams"` dallarıyla yapılır; listeleme ve indirme kaynağa göre değişir, ortak akış fonksiyonları yeniden yazılmaz. Gerekçe: en küçük değişiklik, mevcut testlerin çoğu korunur.
* K8 Görev eylemi: değişmez; `--otomatik` yolu kaynağı ayarlardan okur. Üretim görevi eylem dizesi regresyon testiyle korunur.
* K9 Hız sınırlama: 429 + `Retry-After` ile sınırlı tekrar (mevcut GitHub deseniyle aynı üst sınır); başlık yoksa artan bekleme.
* K10 200 MB: liste aşamasında `size` ile ön kontrol; akış sırasında ikinci kontrol; sağlayıcı boyut vermezse indirme sırasında `Content-Length` varsa onunla doğrulanır; başlık yoksa akış sırasında 200 MB sınırı bayt sayılarak uygulanır ve sınır aşılırsa indirme kesilir.
* K11 Sağlık: kaynağa göre dallanır; Teams için hafif yetki yoklaması (token + klasör çocukları, tek çağrı); token eksikse anlaşılır Türkçe mesaj.
* K12 Sürüm: dilim tamamlanınca 0.2.0; CHANGELOG, README, kurulum, AGENTS ve mimari güncellenir.
* K13 Ön kimlikli indirme URL güvenliği: Graph `/content` yanıtındaki `Location` ön kimlikli ve kısa ömürlüdür. Yönlendirme yalnız HTTPS ve `1drv.com`, `sharepoint.com`, `sharepointonline.com`, `blob.core.windows.net` son eklerinden birine sahip Microsoft barındırma alan adlarına izinli listeyle takip edilir; `Authorization` başlığı yönlendirilen isteğe TAŞINMAZ; ön kimlikli URL günlüğe, hata mesajına, `kaynak_url` durum alanına ve Markdown'a yazılmaz; kalıcı kayıtta yalnız kimlik bilgisi içermeyen kısaltılmış `teams://<driveId-kisa>/<itemId-kisa>/<dosya>` gösterimi kullanılır (JSON ve Markdown ile aynı kısaltma kuralı). URL ve sorgu dizisi tüm hata yollarında redakte edilir.
* K14 Görev hesabı ve işletim: Zamanlanmış görev eylemi değişmez; Teams sırları kullanıcı düzeyi ortam değişkenleriyle (`setx`) tanımlanır ve Task Scheduler bu ortamı miras alır. Gerçek kimlik doğrulama, test dersi + test göreviyle (üretim görevi değiştirilmeden) kabul testine bağlanır. Sır rotasyonu ve sona erme adımları belgelenir; üretimde istemci sırrı yerine sertifika/federatif kimlik bilgisi önerilir (Microsoft önerisi, kaynak aşağıda) ve istemci sırrı kullanımı açık risk kararı olarak kaydedilir. `Sites.Selected` seçilirse kaynak başına site ataması gerekir.

## Veri Modeli Örnekleri

```json
"ornek-ders": {
  "ad": "Ornek Ders", "kaynak": "teams", "secili": true,
  "teams": {"tenantId": "<guid>", "driveId": "b!...", "itemId": "01ABC..."},
  "desen": "Hafta*.pdf",
  "otomasyon": {"aktif": true, "gunler": ["Monday"], "saat": "09:00", "gorevAdi": "DersMerkezi_ornek-ders"}
}
```

`kaynak` yoksa `github` kabul edilir; mevcut kayıtlar değişmeden çalışır.

## Arayüz Değişiklikleri

* CLI: `--ekle --kaynak github|teams`; `teams` seçilirse `--teams-drive <driveId>` ve `--teams-item <itemId>` zorunlu, `--depo` yasak; `github`/varsayılanda `--depo` zorunlu, Teams bayrakları yasak; `--zayif-dogrulama` `--ekle --kaynak teams` ile opsiyonel (varsayılan kapalı; açıldığında risk uyarısı yazılır ve TUI'de onay sorulur); `--teams-tenant` opsiyonel (yoksa ortam değişkeni). Matrise satırlar eklenir; geçersiz kombinasyon exit 2 ve iz bırakmaz.
* JSON: `--ayarlar` ve `--durum` ders kaydına `kaynak` ekler; Teams alanları redakte edilmiş özet olarak gösterilir (tam kimlik değerleri yalnız `ayarlar.json`'da).
* TUI: kaynak seçimi, koşullu alanlar (teams seçilirse zayıf doğrulama onayı risk uyarısıyla), tabloda Kaynak kolonu; iş mantığı `ayarlar.ders_ekle` üzerinden ortak.

### JSON ve Markdown Sözleşmeleri

* `--listele --json` / `--durum --json` ders kaydı: mevcut alanlar korunur; `kaynak` eklenir; Teams için `teams` alanı yalnız redakte edilmiş özet taşır (`{"tenantId": "<gizli>", "driveId": "<gizli>", "itemId": "<gizli>"}` yerine `{"ozet": "teams:b!2SIn…/01H7C…"}` gibi kısaltılmış, kimlik bilgisi içermeyen gösterim; tam kimlikler yalnız `ayarlar.json`'da); GitHub kaydının mevcut alanları ad/tip/değer olarak birebir korunur; yalnız ek alan olarak `kaynak: "github"` eklenir (additive; geriye uyum testi mevcut alanları doğrular).
* `--cek --json` toplamlar: mevcut sayaçlar korunur; `zayif_dogrulama` sayacı eklenir; çıkış kodu: doğrulama hatası varsa 1, yalnız zayıf kabul varsa 0 (uyarı olarak raporlanır).
* Sağlık JSON: `kota` alanı yalnız GitHub içindir; Teams kontrolü `kontroller[]` içinde `kaynak:teams` girdisiyle raporlanır; istek sayısı en çok iki (token + tek Graph çağrısı).
* Markdown şablonu: GitHub satırları aynen korunur (`> Git blob SHA: ...`); Teams'te bu satırın yerine `> Sağlayıcı: Microsoft Teams` ve doğrulama yoluna göre tek satır yazılır: `quickxor` → `> Doğrulama: quickXorHash=<değer>`, `sha1` → `> Doğrulama: sha1=<değer>`, `quickxor+sha1` → `> Doğrulama: quickXorHash=<değer>; sha1=<değer>`, `zayif` → `> Doğrulama: zayif (yerel sha256) <ilk 12 hane>`. "Kaynak" satırı kimlik bilgisi içermeyen kısaltılmış gösterimdir (`teams://<driveId-kisa>/<itemId-kisa>/<dosya>`). Şablon değişmezleri (başlık, sayfa numaraları, OCR uyarısı) korunur.

## Kabul Kriterleri ve Doğrulama

* Mevcut GitHub akışı regresyonsuz: genişletilmiş 423/423 regresyon paketi ve gerçek kapı yeniden koşar; üretim görevi eylem dizesi değişmez.
* Teams mutlu yol: sahte Graph yanıtlarıyla listeleme → indirme → doğrulama yolları (`quickxor`, `sha1`, `quickxor+sha1`, açık `zayif`) → Markdown → durum kaydı; ikinci koşuda `atlanan=1`.
* Hata yolları: 401/403 yetki, 429 `Retry-After`, boyut uyuşmazlığı, hash uyuşmazlığı (dosya taşınmaz, `dogrulama_hatasi`), 200 MB üstü, token yok.
* Şema uyumu: kaynak alanı olmayan mevcut `ayarlar.json` karantinaya alınmaz; görünüm ve çekme çalışır.
* Sağlık/TUI: `--saglik --ders <teams>` en çok iki istek (token + tek Graph çağrısı); TUI scriptli testleri geçer.
* Fail-closed doğrulama: sağlayıcı hash'i olmayan dosya varsayılan reddedilir; `zayif_dogrulama` yalnız açık işaretle etkinleşir ve sayaç/uyarı üretir; hash uyuşmazlığında nihai dosya oluşmaz.
* Zayıf doğrulama ikinci koşusu: kayıtlı `teams_etag`/boyut aynıyken yerel `yerel_sha256` uyuşmazsa `dogrulama_hatasi` verilir; zayıf doğrulamaya güvenilerek sessiz atlama veya otomatik yenileme yapılmaz, normal modda güvenilmez PDF/Markdown ve durum kaydı temizlenir. Kuru mod hatayı raporlar ve hiçbir dosyayı değiştirmez.
* Kuru çekmede zayıf doğrulama yalnız planlanan işlem uyarısıdır; gerçek kabul/sayaç sayılmaz. `zayif_dogrulama` sayacı ancak canlı indirme doğrulandıktan veya sağlam weak yerel dosya atlandıktan sonra artar.
* İndirme güvenliği: ön kimlikli URL günlük/durum/Markdown'da yok; yönlendirmede Authorization taşınmaz; indirme isteği çocuk `id` ile kurulur (klasör `itemId` ile içerik istenmez).
* Sayfalama: `nextLink` köken/yol/HTTPS denetiminden geçmeli; eksik/döngüsel/uyumsuz bağlantı fail-closed; liste tamamlanmadan indirme başlamaz.
* İşletim: gerçek Teams kimlik doğrulaması test dersi/test göreviyle doğrulanır; bu ortamda Entra kimlik bilgileri olmadığından bu kullanıcı kabul adımı beklemede, üretim görevi değişmemiştir.
* Şema giriş kuralları: `zayif_dogrulama` yalnız `kaynak: teams` kayıtlarında kabul edilir; GitHub kaydında veya CLI'de `--kaynak` olmadan verilirse exit 2.
* Dilim sınırı güvenliği: T0'da Teams kaydıyla `--cek`/`--otomatik` (kuru dâhil) geçici korumayla reddedilmişti; T2'de guard kaldırıldı ve sahte Graph adaptör testleri gerçek Teams indirme dalını doğruluyor.
* Doğrulama yöntemi: geçici kopyada birim/akış paketleri + `trace` kapsamı + gerçek proje kapısı (`--cek --sessiz`, `--durum`, `--surum`); test dosyaları repoya eklenmez, kanıtlar plan eki ve CHANGELOG'a işlenir.

## İş Kırılımı ve Kilometre Taşları

* T0 (ayar dilimi): tamamlandı; şema, CLI, redaksiyon, sağlık için kontrollü T3 yanıtı ve T2'ye kadar geçici indirme koruması uygulandı. Ayrıntılı kanıtlar aşağıdadır.
* T1 (Graph istemcisi): tamamlandı; client-credentials token, 50 sayfa/10.000 öğe sınırlı listeleme, Graph yönlendirme denetimi, ön kimlikli indirme ve QuickXorHash/SHA1 hesaplaması uygulandı. Microsoft Graph örnek yanıtındaki `12319191!11919` item kimliğinin mevcut karakter/uzunluk deseninden geçtiği doğrulandı. Gerçek kiracı/drive örneği canlı ortam değişkenleri olmadığından doğrulanamadı. Graph güvenlik/QuickXor paketi 220/220 geçti.
* T2 (indirici adaptörü + rapor/durum): tamamlandı; kaynak dalları, dosya/doğrulama sayaçları, `atlanan` idempotansı, Markdown/durum alanları ve T0 geçici guard'ının kaldırılması test edildi. Sahte Graph akış/idempotans paketi 57/57 geçti.
* T3 (sağlık + TUI + JSON): tamamlandı; kaynak türüne göre sağlık, Teams için token + tek Graph yoklaması, TUI kaynak/kimlik alanları ve JSON sayaç/uyarı eşliği uygulandı.
* T4 (kapanış): uygulama sürümü 0.2.0 ve CHANGELOG/README/kurulum/AGENTS/mimari belgeleri güncellendi; regresyon ve gerçek proje kapısı geçti; Sol T4 kod denetimi ONAY verdi ve kullanıcı kararıyla `v0.2.0` etiketi oluşturuldu. Canlı Graph tokenı ve test görevi kabulü bu geliştirme ortamında kimlik bilgileri tanımlı olmadığından doğrulanmadı; bu işletim kabulü beklemededir.

## Riskler ve Azaltma

* Şema karantinası: SURUM artırılmaz; isteğe bağlı alan; karantina regresyon testi.
* Sır sızıntısı: yalnız ortam değişkeni, redaksiyon, token bellekte; testlerde sahte değer.
* QuickXorHash doğruluğu: Microsoft algoritma açıklamasından türetilmiş ayrı bit düzeyi referansla çoklu uzunluk/parça sınırlarında doğrulanır; QuickXorHash kriptografik içerik özeti olarak sunulmaz.
* Yönetici onayı/izin: kullanıcı adımı; `Files.Read.All` reddedilirse `Sites.Selected` alternatifi belgelenir.
* Hız sınırlama: `Retry-After`; artan bekleme; sayfalama, indirme öncesi/sonrası meta veri ve indirme çağrıları dışında ek çağrı yapılmaz.
* 200 MB/boyut eksikliği: `Content-Length` varsa doğrulama, yoksa akışta bayt sayımı; aşımda kesme (K10 ile uyumlu).

## Doğrulanamayan veya Açık Noktalar

* Microsoft tarafından yayımlanmış QuickXorHash expected-output vektörü bulunamadı. T1 uygulaması Microsoft'un algoritma açıklamasından ayrı bit düzeyi referansla 16 veri uzunluğu ve beş akış parça boyutunda çapraz doğrulandı.
* Kiracı tarafında uygulama kaydı ve yönetici onayı kullanıcı adımıdır; geliştirme ortamında Teams kimlik bilgileri tanımlı değil, canlı Graph tokenı ve test görevi kabulü yapılmadı.
* Zayıf kabul varsayılan kapalıdır; yalnız ders bazında açık `"zayif_dogrulama": true` işaretiyle çalışır ve uyarı/sayaç üretir.

## Sınırlamalar ve Atlanan Adımlar

* Gemini 3.8 Flash web rotası bu oturumda `web_evidence_invalid` verdi; dış doğrulama resmi Microsoft dokümanlarından doğrudan yapıldı.
* Luna edit rotası yeni dosya için onay kanalı kapalı olduğundan plan dosyası orkestratör tarafından yazıldı (yalnız bu dosya).
* Delegated akış, paylaşım bağlantısı çözümleme, özyineleme ve delta v1 kapsamı dışıdır.

## Kaynaklar

Doğrulanan (resmi doküman):

* filesFolder: https://learn.microsoft.com/en-us/graph/api/channel-get-filesfolder
* Çocuk listeleme ve izinler: https://learn.microsoft.com/en-us/graph/api/driveitem-list-children
* İçerik indirme (302): https://learn.microsoft.com/en-us/graph/api/driveitem-get-content
* DriveItem örnek kimliği (`12319191!11919`): https://learn.microsoft.com/en-us/graph/api/resources/driveitem
* Hash türleri (quickXorHash; sha256Hash desteklenmiyor): https://learn.microsoft.com/en-us/graph/api/resources/hashes
* QuickXorHash algoritması: https://learn.microsoft.com/en-us/onedrive/developer/code-snippets/quickxorhash
* Hız sınırlama: https://learn.microsoft.com/en-us/graph/throttling
* Client credentials: https://learn.microsoft.com/en-us/entra/identity-platform/v2-oauth2-client-credentials-grant-flow
* Sertifika/federatif kimlik önerisi: https://learn.microsoft.com/en-us/entra/identity-platform/how-to-add-credentials?tabs=certificate

Danışmanlık (doğrulanmadı): Gemini 3.8 Flash oturumu başarısız; kullanılmadı. DeepSeek Flash yerel analizi kanıt satırlarıyla doğrulandı.

## Sol Denetim Özeti ve Kapatılan Bulgular

Sol Tur 1 (gpt-6-sol, salt-okunur): 2 kritik + 4 orta bulgu. Kapatma kararları:

* Kritik 1 (sağlayıcı hash'i olmadan kabul): Kapatıldı. Varsayılan fail-closed; yalnız açık `zayif_dogrulama` işaretiyle sınırlı kabul; sayaç/uyarı/çıkış kodu ve ikinci koşu kuralları eklendi.
* Kritik 2 (ön kimlikli URL ve sır sınırı): Kapatıldı. K13 ile başlık ayrımı, izinli HTTPS hedef listesi, Authorization taşımama ve URL redaksiyonu kabul kriterlerine bağlandı.
* Orta 3 (T1/T2 sırası ve güvence adları): Kapatıldı. Mevcut tüm hash katmanlarının eşleşmesi zorunlu; güvence adları rapor/JSON'da ayrıştırıldı; doğrulanmamış QuickXorHash otomatik zayıf kabul açmıyor.
* Orta 4 (görev hesabı/işletim): Kapatıldı. K14 ile ortam değişkeni kurulumu, test görevi kabul testi, rotasyon ve sertifika alternatifi kayda geçti.
* Orta 5 (sayfalama/kısmi başarı): Kapatıldı. Liste tamamlanmadan indirme yok; sayfa/öğe üst sınırı ve döngü fail-closed; eksik boyut başlığında akış sınırı.
* Orta 6 (JSON/Markdown sözleşmeleri): Kapatıldı. JSON örnekleri, sağlık istek sayısı ve Teams Markdown satır kuralları eklendi; GitHub geriye uyum testi korundu.

Sol Tur 2 (gpt-6-sol, salt-okunur): 3 bulgu kapatıldı; 2 açık + 2 yeni nokta. Kapatma kararları:

* Açık 1 (zayıf kabulün eTag bağlanması): Kapatıldı. Anahtar (a)-(d) kuralları: eTag zorunlu, indirme öncesi meta veri tazeleme, kalıcı alanlar (`dogrulama`, `teams_etag`, `yerel_sha256`), ikinci koşu karşılaştırma ve fail-closed davranışı tanımlandı.
* Açık 2 (`nextLink` ve yönlendirme doğrulaması): Kapatıldı. Mutlak HTTPS + `graph.microsoft.com` kökeni + beklenen `/v1.0/drives/{driveId}/` yolu denetimi, yönlendirmelerde aynı denetim ve göndermeden reddetme kuralı eklendi.
* Yeni kritik (indirme çocuk `id` ile): Kapatıldı. İndirme yolu çocuk `id` ile tanımlandı; klasör `itemId`'nin içerik isteğinde kullanılmayacağı kabul kriterine ve K4'e yazıldı.
* Yeni orta (risk metni ile K10 çelişkisi): Kapatıldı. Risk satırı K10 ile uyumlu hale getirildi.
* Yeni orta (Teams Markdown satırı): Kapatıldı. Markdown kuralı doğrulama yoluna göre ayrıştırıldı; JSON "redakte özet" ifadesi netleştirildi.

Sol Tur 3 (gpt-6-sol, salt-okunur): 2 kapandı; 3 açık kaldı. Kapatma kararları:

* Açık 1 (indirilen baytların eTag sürümüne bağlanması): Kapatıldı. İndirme sonrası çocuk meta verisi yeniden çekilip listeleme kaydıyla karşılaştırılır; indirilen bayt sayısı beklenen `size` ile eşit olmak zorundadır; uyuşmazlıkta geçici dosya silinir ve içerik reddedilir; `teams_etag` ve `yerel_sha256` K6 durum alanlarına eklendi.
* Açık 2 (K4–K13 yönlendirme çelişkisi): Kapatıldı. Graph köken/yol kuralı sayfalama ve meta veri istekleriyle sınırlandı; `/content` ön kimlikli indirme yönlendirmesi açıkça K13'ün izinli hedef listesine bağlandı.
* Açık 3 (JSON özeti ve birleşik doğrulama gösterimi): Kapatıldı. JSON özeti kısaltılmış kimlik gösterimine çevrildi; iki hash birlikte doğrulandığında `dogrulama: quickxor+sha1` değeri ve Markdown `quickXorHash=...; sha1=...` satırı tanımlandı.


Sol Tur 4-10 (gpt-6-sol, salt-okunur) özeti: dokuz turda toplam 2 kritik + 7 orta + 3 düşük bulgu kapatıldı. Öne çıkan kapanışlar:

* İndirme, listeden gelen ÇOCUK `id` ile yapılır; klasör `itemId` içerik isteğinde kullanılmaz.
* İndirilen baytlar, indirme sonrası çekilen çocuk meta verisi (`id/eTag/size`) ile sürüme bağlanır; bayt sayısı beklenen `size` ile eşit olmak zorundadır; uyuşmazlıkta geçici dosya silinir.
* K4 (Graph köken/yol) ile K13 (`/content` ön kimlikli indirme hedefleri) kuralları ayrıştırıldı.
* Birleşik hash saklama: `saglayici_hashler` nesnesi; sonraki koşuda kayıtlı her hash anahtarı yeniden doğrulanır.
* Doğrulama yolu adları kilometre taşlarından ayrıldı (`quickxor`, `sha1`, `quickxor+sha1`, açık `zayif`).
* Tenant kimliği gizli değildir; `--teams-tenant` değeri kayıt sırasında ders kaydına yazılır. Çalışma zamanı önceliği ders kaydı > `TEAMS_TENANT_ID`; `TEAMS_CLIENT_ID` yalnız ortam değişkeni; yalnız `TEAMS_CLIENT_SECRET` sırdır.
* `zayif_dogrulama` şema/CLI/TUI kuralları tanımlandı (yalnız teams, varsayılan false, risk onayı, geçersiz birleşimde exit 2).
* Zayıf kabulde `size` zorunludur; K10 yedek ölçüm yolu zayıf kabulü kurtarmaz.
* GitHub JSON çıktısında mevcut alanlar birebir korunur; yalnız `kaynak` alanı eklenir.

Tur 10 sonucu: kalan çelişki yok; plan uygulamaya hazır. Kullanıcı adımı: Microsoft Entra uygulama kaydı, `Files.Read.All` uygulama izni + yönetici onayı ve `TEAMS_TENANT_ID`/`TEAMS_CLIENT_ID`/`TEAMS_CLIENT_SECRET` ortam değişkenlerinin tanımlanması.

## T0 Uygulama ve Doğrulama Kanıtları (2026-09-23)

* Kapsam T0 ile sınırlı tutuldu: `ayarlar.json` sürüm 1; GitHub varsayılanı ve eski kayıtlara uyum; Teams kimlik/şema doğrulaması; CLI bayrak matrisi; redakte ayarlar/durum/liste görünümleri; T0 geçici indirme koruması; doküman iskeleti. Graph istemcisi ve T1+ akışları bu dilimde uygulanmadı.
* Teams `driveId`/`itemId` için 8-200, `tenantId` için 2-128 karakter sınırı ve güvenli karakter kümeleri uygulanır; hata mesajları tam kimlikleri içermez. Redakte özet en fazla ilk 6 karakteri gösterir ve doğrulanmış kimliğin son karakterini hiçbir durumda göstermez.
* T0 geçici `indirici.indir_ders` koruması seçili kontrolünden önce çalışır; `--cek`, `--otomatik`, kuru ve seçili olmayan Teams derslerinde hata + exit 1 sağlar. Koruma T2'de kaldırılıp gerçek adaptöre bağlanacak; T2 testi guard'ın kaldırıldığını doğrulayacak. T1 başlangıcında gerçek Graph ID örneğiyle desen uygunluğu teyit edilecek.
* Sağlık uyumu T0'da yalnız çökme önleme düzeyindedir: Teams için Graph/depo çağrısı yapılmadan T3 uyarısı verilir; gerçek Graph sağlık yoklaması T3 kapsamındadır.
* Geçici kopyada T0 paketi 198/198 geçti. Regresyon paketleri: birim/akış 206/206 (önceki 204 kontrole kaynak alanı için iki ek uyum kontrolü eklendi), kapsam 153/153, uçtan uca 47/47, tetikleme/sahiplik 14/14; toplam 420/420. `trace_runner.py` exit 0; Python `trace --count --summary` özeti `dersmerkezi.py` ve raporlanan `merkez` modüllerini %100 gösterdi. Test dosyaları depoya eklenmedi.
* Gerçek proje kapısı: `python -m compileall merkez dersmerkezi.py` exit 0; `--cek --ders dosya-organizasyonu --sessiz` exit 0, günlükte `yeni=0 guncellenen=0 atlanan=2 baglam=2`; `--durum` exit 0 ve görev `Ready`; `--surum` `DersMerkezi 0.1.5`; `--ayarlar --json` exit 0, mevcut GitHub alanları korunup `kaynak:"github"` eklendi. Üretim görevinin eylem koduna dokunulmadı; E2E üretim görevi kontrolü geçti.
* GitHub anonim API kotasının dolduğu bir ara denemede ağ testleri geçici olarak başarısız oldu; kota yenilendikten sonra gerçek çekme kapısı ve E2E paketi başarıyla yeniden koştu. Son sonuçlar yukarıdaki sayılardır.
* Sol salt-okunur kod denetimi: ilk turda Teams guard sırası ve insan-okur redaksiyon bulguları, ikinci turda T0 sağlık çökme riski, üçüncü turda `null` alan doğrulaması ve `--ekle` yardım metni bulguları düzeltildi. Son tur `SONUC: ONAY` verdi; rapor `belgeler/gecmis/sol-denetim-2026-09-23-0.2.0-t0.md`.

## T4 Uygulama ve Doğrulama Kanıtları (2026-09-24)

* Uygulama sürümü `0.2.0`; ayar şeması sürüm 1 ve indirme durumu sürüm 2 kaldı. `merkez/teams.py` app-only Graph istemcisi, güvenli sayfalama/yönlendirme, ön kimlikli indirme ve QuickXorHash/SHA-1 hesabını sağlar. `indirici` Teams akışı strong hash veya açık weak/eTag yoluyla son dosyayı atomik taşıma öncesi doğrular.
* Graph ID desen kontrolünde Microsoft Graph `driveItem` dokümanındaki örnek item ID `12319191!11919` kabul edildi. QuickXorHash uygulaması resmi algoritma açıklamasından türetilmiş ayrı bit düzeyi referansla 16 veri uzunluğu × 5 parça boyutunda eşleştirildi; test koşuları geçiş kanıtı verir.
* Geçici kopya son testleri: regresyon 423/423 (206 birim/akış + 156 kapsam + 47 uçtan uca + 14 tetikleme/sahiplik); T0 199/199; T1 Graph güvenlik/QuickXor 220/220; T2 sahte Graph adaptör/idempotans 57/57. Test dosyaları depoya eklenmedi.
* Gerçek proje kapısı (`chcp 65001`): `python -m compileall merkez dersmerkezi.py` exit 0; `--cek --ders dosya-organizasyonu --sessiz` exit 0 (`atlanan=2`); `--durum` exit 0 ve görev `Ready`; `--surum` `DersMerkezi 0.2.0`; `--ayarlar --json` geçerli, GitHub kaydı additive ve bozulmamış. `--saglik --ders dosya-organizasyonu --json` ağlı kontrolü exit 0 ve son ölçümde kota `limit=60 kalan=43` raporladı. GitHub API kotası yenilendikten sonra çekme/E2E testleri başarıyla tekrarlandı.
* `TEAMS_TENANT_ID`, `TEAMS_CLIENT_ID` ve `TEAMS_CLIENT_SECRET` bu geliştirme ortamında tanımlı değil. Bu nedenle gerçek Entra tokenı, canlı Teams erişimi ve ayrı test göreviyle işletim kabulü yapılmadı; Graph akışları sahte yanıtlarla doğrulandı. Canlı kabul kullanıcı ortam değişkenleri ve Entra uygulama izni/yönetici onayı gerektirir.
* T4 Sol kod denetiminin tüm kod/belge bulguları kapatıldı; son tur `SONUC: ONAY` verdi. Rapor: `belgeler/gecmis/sol-denetim-2026-09-23-0.2.0-t4.md`. Kullanıcı kararıyla `v0.2.0` etiketi bu onaya dayanarak oluşturuldu. Canlı Entra/Teams kabul testi ortam kimlik bilgileri beklendiğinden açık işletim adımıdır.
