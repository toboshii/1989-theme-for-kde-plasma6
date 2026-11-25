#!/bin/bash
# Pack the built theme into a downloadable archive and store-installable archives.
# Run from anywhere. Requires the tree already built in ../out.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DIST="$ROOT/dist"
VERSION="1.0.0"
NAME="1989-theme-for-kde-plasma6"
INSTALLABLE="$DIST/installable"

if [[ ! -d "$ROOT/out/plasma/look-and-feel/1989" ]]; then
  echo "missing $ROOT/out — run scripts/build_theme.py first" >&2
  exit 1
fi

rm -rf "$INSTALLABLE"
mkdir -p "$INSTALLABLE"/{global-theme,plasma-theme,aurorae,gtk,color-schemes,konsole,icons,cursors,wallpaper,sddm}

variants=(1989 1989Mocha 1989Blue 1989Green 1989Red)
gtk=(1989 1989-Mocha 1989-Blue 1989-Green 1989-Red)

for variant in "${variants[@]}"; do
  tar -C "$ROOT/out/plasma/look-and-feel" -czf "$INSTALLABLE/global-theme/${variant}.tar.gz" "$variant"
  tar -C "$ROOT/out/plasma/desktoptheme" -czf "$INSTALLABLE/plasma-theme/${variant}.tar.gz" "$variant"
  tar -C "$ROOT/out/aurorae/themes" -czf "$INSTALLABLE/aurorae/${variant}.tar.gz" "$variant"
  cp -a "$ROOT/out/color-schemes/${variant}.colors" "$INSTALLABLE/color-schemes/"
  cp -a "$ROOT/out/konsole/${variant}.colorscheme" "$INSTALLABLE/konsole/"
done
cp -a "$ROOT/out/konsole/1989.profile" "$INSTALLABLE/konsole/"

for variant in "${gtk[@]}"; do
  tar -C "$ROOT/out/themes" -czf "$INSTALLABLE/gtk/${variant}.tar.gz" "$variant"
done

tar -C "$ROOT/out/icons" -czf "$INSTALLABLE/icons/1989.tar.gz" 1989
tar -C "$ROOT/out/icons" -czf "$INSTALLABLE/cursors/1989-cursors.tar.gz" 1989-cursors
tar -C "$ROOT/out/wallpapers" -czf "$INSTALLABLE/wallpaper/1989.tar.gz" 1989
tar -C "$ROOT/sddm" -czf "$INSTALLABLE/sddm/1989.tar.gz" 1989

tar -C "$ROOT" -czf "$DIST/${NAME}-${VERSION}.tar.gz" \
  --transform "s,^,${NAME}/," \
  README.md install.sh out sddm

tar -C "$DIST" -czf "$DIST/${NAME}-${VERSION}-installable.tar.gz" installable

echo "wrote $DIST/${NAME}-${VERSION}.tar.gz"
echo "wrote $DIST/${NAME}-${VERSION}-installable.tar.gz"
