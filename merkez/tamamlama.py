import os
from pathlib import Path

from . import ayarlar, gunluk, komut

KLASOR = ayarlar.KOK / "tamamlama"
DOSYA = KLASOR / "dersmerkezi-tamamlama.ps1"


def _betik(bayraklar):
    satirlar = [
        "$DersMerkeziBayraklar = @(",
    ]
    for bayrak in bayraklar:
        satirlar.append("    '{}'".format(bayrak))
    satirlar.extend([
        ")",
        "",
        "Register-ArgumentCompleter -Native -CommandName python -ScriptBlock {",
        "    param($kelime, $satir, $imlec)",
        "    if ($kelime -like '-*') {",
        "        $DersMerkeziBayraklar | Where-Object { $_ -like \"$kelime*\" } | ForEach-Object {",
        "            [System.Management.Automation.CompletionResult]::new($_, $_, 'ParameterName', $_)",
        "        }",
        "    }",
        "}",
        "",
    ])
    return "\n".join(satirlar)


def uret(hedef=None):
    bayraklar = komut.bayrak_listesi()
    hedef_yolu = Path(hedef) if hedef else DOSYA
    hedef_yolu.parent.mkdir(parents=True, exist_ok=True)
    gecici = hedef_yolu.with_name(hedef_yolu.name + ".tmp")
    with gunluk.kilitle():
        try:
            with open(gecici, "w", encoding="utf-8", newline="\n") as dosya:
                dosya.write(_betik(bayraklar))
                dosya.flush()
                os.fsync(dosya.fileno())
            ayarlar._replace_tekrar(gecici, hedef_yolu)
        except OSError:
            try:
                gecici.unlink()
            except OSError:
                pass
            raise
    return hedef_yolu, bayraklar
