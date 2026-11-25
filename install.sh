#!/bin/bash
# Install 1989 into new directories under ~/.local/share.
# Refuses to replace anything that is not already an 1989 package.
# Does not install the SDDM theme and does not reset the panel layout.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
OUT="$ROOT/out"
SHARE="${XDG_DATA_HOME:-$HOME/.local/share}"

if [[ ! -d "$OUT" ]]; then
  echo "missing $OUT — run scripts/build_theme.py first" >&2
  exit 1
fi

refuse() {
  local dest="$1"
  case "$dest" in
    *Catppuccin*|*ColorFlow*|*Apple-cursors*|*/cachyos.svg)
      echo "refusing to write $dest" >&2
      exit 1
      ;;
  esac
}

install_tree() {
  local src="$1"
  local dest="$2"
  refuse "$dest"
  if [[ -e "$dest" && ! -f "$dest/.1989" ]]; then
    echo "refusing to replace existing $dest" >&2
    exit 1
  fi
  rm -rf "$dest"
  mkdir -p "$(dirname "$dest")"
  cp -a "$src" "$dest"
  if [[ ! -f "$dest/.1989" ]]; then
    echo "1989" > "$dest/.1989"
  fi
}

install_file() {
  local src="$1"
  local dest="$2"
  refuse "$dest"
  if [[ -e "$dest" ]] && ! grep -q "1989" "$dest"; then
    echo "refusing to replace existing $dest" >&2
    exit 1
  fi
  mkdir -p "$(dirname "$dest")"
  cp -a "$src" "$dest"
}

shopt -s nullglob
for scheme in "$OUT"/color-schemes/*.colors; do
  install_file "$scheme" "$SHARE/color-schemes/$(basename "$scheme")"
done
for scheme in "$OUT"/konsole/*.colorscheme "$OUT"/konsole/*.profile; do
  install_file "$scheme" "$SHARE/konsole/$(basename "$scheme")"
done
for dir in "$OUT"/plasma/desktoptheme/*; do
  install_tree "$dir" "$SHARE/plasma/desktoptheme/$(basename "$dir")"
done
for dir in "$OUT"/plasma/look-and-feel/*; do
  install_tree "$dir" "$SHARE/plasma/look-and-feel/$(basename "$dir")"
done
if [[ -d "$OUT/wallpapers" ]]; then
  for dir in "$OUT"/wallpapers/*; do
    install_tree "$dir" "$SHARE/wallpapers/$(basename "$dir")"
  done
fi
for dir in "$OUT"/aurorae/themes/*; do
  install_tree "$dir" "$SHARE/aurorae/themes/$(basename "$dir")"
done
for dir in "$OUT"/icons/*; do
  install_tree "$dir" "$SHARE/icons/$(basename "$dir")"
done
# The cursor list in System Settings searches ~/.icons only. It does not
# search ~/.local/share/icons, which is where the packages above are copied.
mkdir -p "$HOME/.icons"
for dir in "$OUT"/icons/*; do
  [[ -d "$dir/cursors" ]] || continue
  name="$(basename "$dir")"
  link="$HOME/.icons/$name"
  if [[ -L "$link" ]]; then
    rm "$link"
  elif [[ -e "$link" ]]; then
    echo "refusing to replace existing $link" >&2
    exit 1
  fi
  ln -s "$SHARE/icons/$name" "$link"
done
for dir in "$OUT"/themes/*; do
  install_tree "$dir" "$SHARE/themes/$(basename "$dir")"
done

echo "installed 1989 packages under $SHARE"
echo "SDDM theme left in $ROOT/sddm/1989"
