"""Download and instantiate the four OFL font families used by pdf-production.

Google Fonts distributes Noto SC and Source families as variable TTFs (a single
file with a wght axis). ReportLab cannot reliably use variable fonts, so this
script downloads each variable TTF and uses fontTools to produce static Regular
(400) and Bold (700) instances in the local cache.

Idempotent: existing files in the cache are reused. Prints the cache directory
on stdout so callers can capture it.
"""
from __future__ import annotations

import os
import sys
import urllib.request
from pathlib import Path


def _cache_dir() -> Path:
    if os.name == "nt":
        base = os.environ.get("LOCALAPPDATA")
        root = Path(base) if base else Path.home() / "AppData" / "Local"
        return root / "pdf-production" / "fonts"
    return Path.home() / ".cache" / "pdf-production" / "fonts"


FAMILIES = [
    {
        "name": "NotoSerifSC",
        "url": "https://raw.githubusercontent.com/google/fonts/main/ofl/notoserifsc/NotoSerifSC%5Bwght%5D.ttf",
        "var_file": "NotoSerifSC-var.ttf",
        "outputs": {"Regular": "NotoSerifSC-Regular.ttf", "Bold": "NotoSerifSC-Bold.ttf"},
    },
    {
        "name": "NotoSansSC",
        "url": "https://raw.githubusercontent.com/google/fonts/main/ofl/notosanssc/NotoSansSC%5Bwght%5D.ttf",
        "var_file": "NotoSansSC-var.ttf",
        "outputs": {"Regular": "NotoSansSC-Regular.ttf", "Bold": "NotoSansSC-Bold.ttf"},
    },
    {
        "name": "SourceSerif4",
        "url": "https://raw.githubusercontent.com/google/fonts/main/ofl/sourceserif4/SourceSerif4%5Bopsz%2Cwght%5D.ttf",
        "var_file": "SourceSerif4-var.ttf",
        "outputs": {"Regular": "SourceSerif4-Regular.ttf", "Bold": "SourceSerif4-Bold.ttf"},
    },
    {
        "name": "SourceSans3",
        "url": "https://raw.githubusercontent.com/google/fonts/main/ofl/sourcesans3/SourceSans3%5Bwght%5D.ttf",
        "var_file": "SourceSans3-var.ttf",
        "outputs": {"Regular": "SourceSans3-Regular.ttf", "Bold": "SourceSans3-Bold.ttf"},
    },
]


def _download(url: str, dest: Path) -> None:
    print(f"Downloading {url}", file=sys.stderr)
    req = urllib.request.Request(url, headers={"User-Agent": "pdf-production/1.0"})
    tmp = dest.with_suffix(dest.suffix + ".part")
    try:
        with urllib.request.urlopen(req, timeout=60) as resp, open(tmp, "wb") as out:
            out.write(resp.read())
        tmp.replace(dest)
    except Exception:
        tmp.unlink(missing_ok=True)
        raise


def _instantiate(src: Path, dst: Path, weight: int) -> None:
    from fontTools.varLib.instancer import instantiateVariableFont
    from fontTools.ttLib import TTFont

    font = TTFont(str(src))
    instantiateVariableFont(font, {"wght": weight})
    font.save(str(dst))
    font.close()


def main() -> int:
    cache = _cache_dir()
    cache.mkdir(parents=True, exist_ok=True)

    for fam in FAMILIES:
        var_path = cache / fam["var_file"]
        outputs = {w: cache / name for w, name in fam["outputs"].items()}

        if all(p.exists() for p in outputs.values()):
            var_path.unlink(missing_ok=True)  # clean leftover intermediate
            continue

        if not var_path.exists():
            _download(fam["url"], var_path)

        try:
            _instantiate(var_path, outputs["Regular"], 400)
            _instantiate(var_path, outputs["Bold"], 700)
            var_path.unlink()  # remove the large intermediate file
        except ModuleNotFoundError:
            print(
                "fonttools is required to instantiate static weights. "
                "Install it with: pip install fonttools",
                file=sys.stderr,
            )
            return 1

    print(cache)
    return 0


if __name__ == "__main__":
    sys.exit(main())
