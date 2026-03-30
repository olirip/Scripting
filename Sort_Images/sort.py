#!/usr/bin/env python3
"""
Photo organizer

Structure :
  ROOT/Photos/          -> source principale (sous-dossiers arbitraires)
  ROOT/DuplicatedPhotos/ -> source secondaire (noms macOS à corriger)
  ROOT/Sorted/          -> destination finale, Année/MM_Mois/

Comportement :
  - Parcourt Photos/ et DuplicatedPhotos/ récursivement
  - Corrige les noms macOS type "photo.jpg - copie (6)" avant de déplacer
  - Déplace chaque fichier immédiatement dans Sorted/Année/MM_Mois/
  - Renomme uniquement en cas de doublon dans la destination (_dup_001, etc.)
  - Ne touche pas à Sorted/

Usage:
  python3 organize_photos.py --dry-run
  python3 organize_photos.py
"""

import os
import re
import sys
import shutil
import argparse
from pathlib import Path
from datetime import datetime

try:
    from PIL import Image
    HAS_PILLOW = True
except ImportError:
    HAS_PILLOW = False
    print("[WARN] Pillow non installé. Utilisation de la date de modification fichier.")
    print("       Pour les EXIF : pip install Pillow\n")

ROOT_DIR   = Path("/Volumes/HD1/Archives/MarieDeCasteja/All Photos")
PHOTOS_DIR = ROOT_DIR / "Photos"
DUPES_DIR  = ROOT_DIR / "DuplicatedPhotos"
SORTED_DIR = ROOT_DIR / "Sorted"

PHOTO_EXTENSIONS = {
    ".jpg", ".jpeg", ".png", ".heic", ".heif",
    ".tiff", ".tif", ".raw", ".cr2", ".cr3",
    ".nef", ".arw", ".dng", ".bmp", ".gif",
    ".webp", ".mov", ".mp4", ".avi", ".m4v",
}

MONTH_NAMES = {
    1: "01_Janvier",  2: "02_Fevrier",  3: "03_Mars",
    4: "04_Avril",    5: "05_Mai",      6: "06_Juin",
    7: "07_Juillet",  8: "08_Aout",     9: "09_Septembre",
    10: "10_Octobre", 11: "11_Novembre", 12: "12_Decembre",
}

# Patterns macOS : "photo.jpg - copie", "photo.jpg - copie (6)", "photo - copie.png"
# Cas 1 : "stem.ext - copie (N)"  ou  "stem.ext - copie"
RE_COPY_IN_STEM = re.compile(
    r'^(.+?)(\.[a-zA-Z0-9]+)\s+-\s+copie(?:\s+\((\d+)\))?$',
    re.IGNORECASE
)
# Cas 2 : "stem - copie (N).ext"  ou  "stem - copie.ext"
RE_COPY_BEFORE_EXT = re.compile(
    r'^(.+?)\s+-\s+copie(?:\s+\((\d+)\))?$',
    re.IGNORECASE
)


def fix_macos_copy_name(path: Path) -> str:
    """
    Corrige les noms macOS 'photo.jpg - copie (6)' en 'photo_copie_006.jpg'.
    Retourne le nom corrigé, ou le nom d'origine si aucune correction nécessaire.
    """
    name = path.name
    ext  = path.suffix.lower()
    stem = path.stem

    # Cas 1 : l'extension est dans le stem ("photo.jpg - copie (6)")
    m = RE_COPY_IN_STEM.match(name)
    if m:
        real_stem = m.group(1)
        real_ext  = m.group(2).lower()
        num       = int(m.group(3)) if m.group(3) else 1
        return f"{real_stem}_copie_{num:03d}{real_ext}"

    # Cas 2 : extension normale mais stem contient " - copie"
    m = RE_COPY_BEFORE_EXT.match(stem)
    if m:
        real_stem = m.group(1)
        num       = int(m.group(2)) if m.group(2) else 1
        return f"{real_stem}_copie_{num:03d}{ext}"

    return name


def get_exif_date(path: Path) -> datetime | None:
    if not HAS_PILLOW:
        return None
    try:
        img = Image.open(path)
        exif_data = img._getexif()
        if not exif_data:
            return None
        from PIL.ExifTags import TAGS
        for tag_id, value in exif_data.items():
            tag = TAGS.get(tag_id, tag_id)
            if tag in ("DateTimeOriginal", "DateTime", "DateTimeDigitized"):
                return datetime.strptime(value, "%Y:%m:%d %H:%M:%S")
    except Exception:
        pass
    return None


def get_file_date(path: Path) -> datetime:
    exif_date = get_exif_date(path)
    if exif_date:
        return exif_date
    return datetime.fromtimestamp(os.path.getmtime(path))


def get_dest_dir(date: datetime) -> Path:
    return SORTED_DIR / str(date.year) / MONTH_NAMES[date.month]


def resolve_dest_path(dest_dir: Path, filename: str) -> Path:
    """Retourne le chemin destination, avec suffixe _dup_001 si collision."""
    dst = dest_dir / filename
    if not dst.exists():
        return dst
    stem = Path(filename).stem
    ext  = Path(filename).suffix
    counter = 1
    while True:
        new_name = f"{stem}_dup_{counter:03d}{ext}"
        dst = dest_dir / new_name
        if not dst.exists():
            return dst
        counter += 1


def process_dir(source: Path, dry_run: bool, counters: dict):
    """Parcourt récursivement source et traite chaque fichier photo."""
    for root, dirs, files in os.walk(source, topdown=True):
        root_path = Path(root)

        for filename in sorted(files):
            src = root_path / filename

            if not src.is_file():
                continue

            # Détecter l'extension réelle (cas "photo.jpg - copie")
            # On vérifie d'abord si le nom corrigé révèle une extension valide
            fixed_name = fix_macos_copy_name(src)
            effective_ext = Path(fixed_name).suffix.lower()

            if effective_ext not in PHOTO_EXTENSIONS:
                # Dernier recours : extension du fichier original
                if src.suffix.lower() not in PHOTO_EXTENSIONS:
                    continue

            date     = get_file_date(src)
            dest_dir = get_dest_dir(date)

            # Nom final : corrigé si nécessaire
            was_renamed = fixed_name != filename
            dst = resolve_dest_path(dest_dir, fixed_name)
            is_dup = dst.name != fixed_name

            labels = []
            if was_renamed:
                labels.append(f"renommé → {fixed_name}")
            if is_dup:
                labels.append(f"doublon → {dst.name}")
            label_str = f"  [{', '.join(labels)}]" if labels else ""

            rel_src = src.relative_to(ROOT_DIR)
            rel_dst = dst.relative_to(ROOT_DIR)

            if dry_run:
                print(f"  {rel_src}")
                print(f"    → {rel_dst}{label_str}")
            else:
                try:
                    dest_dir.mkdir(parents=True, exist_ok=True)
                    shutil.move(str(src), str(dst))
                    counters["moved"] += 1
                    if was_renamed:
                        counters["renamed"] += 1
                    if is_dup:
                        counters["dupes"] += 1
                    print(f"  ✓ {rel_dst}{label_str}")
                except Exception as e:
                    counters["errors"].append((src, e))
                    print(f"  ✗ ERREUR {filename} : {e}")


def run(dry_run: bool):
    print(f"\n{'='*60}")
    print(f"  Photo Organizer {'[DRY RUN]' if dry_run else '[LIVE]'}")
    print(f"  Destination : {SORTED_DIR}")
    print(f"{'='*60}\n")

    for d in (ROOT_DIR, PHOTOS_DIR, DUPES_DIR):
        if not d.exists():
            print(f"[ERREUR] Dossier introuvable : {d}")
            sys.exit(1)

    SORTED_DIR.mkdir(parents=True, exist_ok=True)

    counters = {"moved": 0, "renamed": 0, "dupes": 0, "errors": []}

    print(f"--- Photos/ ---")
    process_dir(PHOTOS_DIR, dry_run, counters)

    print(f"\n--- DuplicatedPhotos/ ---")
    process_dir(DUPES_DIR, dry_run, counters)

    print(f"\n{'='*60}")
    if dry_run:
        print("  [DRY RUN] Aucune modification. Lancez sans --dry-run pour appliquer.")
    else:
        print(f"  Déplacés          : {counters['moved']}")
        print(f"  Noms corrigés     : {counters['renamed']}")
        print(f"  Doublons dest.    : {counters['dupes']}")
        print(f"  Erreurs           : {len(counters['errors'])}")
    print(f"{'='*60}\n")

    if counters["errors"]:
        print("Fichiers en erreur :")
        for src, e in counters["errors"]:
            print(f"  {src.name} : {e}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="Aperçu sans modification")
    args = parser.parse_args()
    run(dry_run=args.dry_run)
