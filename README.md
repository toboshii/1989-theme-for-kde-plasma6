# 1989

1989 is a global theme for KDE Plasma 6. The desktop is a dark field (`#181821`), a square hairline, and the Hack typeface. The default accent is peach (`#dd9d89`). Five variants share that layout and recolor the accent: Default, Mocha, Blue, Green, and Red.

The package contains the global theme, Plasma style, color scheme, Aurorae window decoration, icon theme, cursor theme, wallpaper, GTK theme, Konsole profile, splash screen, and SDDM greeter. Icons, cursors, and the wallpaper are shared. Each variant has its own global theme, Plasma style, color scheme, window decoration, GTK theme, and Konsole color scheme.

| Variant | Global theme | GTK theme |
| --- | --- | --- |
| Default | 1989 | 1989 |
| Mocha | 1989 Mocha | 1989-Mocha |
| Blue | 1989 Blue | 1989-Blue |
| Green | 1989 Green | 1989-Green |
| Red | 1989 Red | 1989-Red |

Source: https://github.com/cdtenzi/1989-theme-for-kde-plasma6

## Requirements

- KDE Plasma 6
- The Hack font. On Arch and CachyOS the package is `ttf-hack`. On Debian and Ubuntu it is `fonts-hack`.
- The Breeze widget style and the Breeze icon theme, which ship with Plasma. The 1989 icon theme inherits Breeze.
- Aurorae window decorations, which ship with KWin.

## Download

Download the full theme:

https://github.com/cdtenzi/1989-theme-for-kde-plasma6/releases/download/v1.0.0/1989-theme-for-kde-plasma6-1.0.0.tar.gz

Or clone the repository. `out/` is already built, so the clone can be installed without running the build scripts.

```bash
git clone https://github.com/cdtenzi/1989-theme-for-kde-plasma6.git
cd 1989-theme-for-kde-plasma6
```

The installable archives, one file per Plasma component, are packed separately for the KDE Store and for “Install from file”:

https://github.com/cdtenzi/1989-theme-for-kde-plasma6/releases/download/v1.0.0/1989-theme-for-kde-plasma6-1.0.0-installable.tar.gz

## Install the full theme

From the downloaded archive:

```bash
tar -xzf 1989-theme-for-kde-plasma6-1.0.0.tar.gz
cd 1989-theme-for-kde-plasma6
./install.sh
```

From a clone, run `./install.sh` in the repository root.

`install.sh` copies the theme into `~/.local/share` and links the cursor theme into `~/.icons`, which is the directory System Settings searches. An existing directory is left in place when it is not already an 1989 package. The script keeps the current panel layout. The SDDM greeter stays in `sddm/1989` until the login-screen steps below.

Then open **System Settings → Colors & Themes → Global Theme** and choose **1989**, or one of the other four variants.

Apply the theme with **Desktop layout** off to keep your current panels. **Desktop layout** on replaces the panels with this theme’s layout: a top bar and a bottom dock, with the 1989 wallpaper.

The global theme also selects the matching color scheme, Plasma style, window decoration, icons, cursors, wallpaper, GTK theme, and Hack font. In Konsole, choose the **1989** profile.

## Install the SDDM greeter

The login screen is installed for all users and needs root.

```bash
sudo cp -a sddm/1989 /usr/share/sddm/themes/1989
sudo mkdir -p /etc/sddm.conf.d
printf '[Theme]\nCurrent=1989\n' | sudo tee /etc/sddm.conf.d/1989.conf
```

The greeter is used at the next login.

## Install one component

Extract `1989-theme-for-kde-plasma6-1.0.0-installable.tar.gz`. These commands install the Default variant. Repeat them with `1989Mocha`, `1989Blue`, `1989Green`, or `1989Red` for the other variants. GTK archive names use hyphens: `1989-Mocha`, `1989-Blue`, `1989-Green`, `1989-Red`.

```bash
kpackagetool6 --type Plasma/LookAndFeel --install global-theme/1989.tar.gz
kpackagetool6 --type Plasma/Theme --install plasma-theme/1989.tar.gz

mkdir -p ~/.local/share/aurorae/themes ~/.local/share/wallpapers \
  ~/.local/share/color-schemes ~/.local/share/konsole ~/.local/share/icons \
  ~/.themes ~/.icons
tar -xzf aurorae/1989.tar.gz -C ~/.local/share/aurorae/themes
tar -xzf wallpaper/1989.tar.gz -C ~/.local/share/wallpapers
cp color-schemes/1989.colors ~/.local/share/color-schemes/
cp konsole/1989.colorscheme konsole/1989.profile ~/.local/share/konsole/
tar -xzf icons/1989.tar.gz -C ~/.local/share/icons
tar -xzf cursors/1989-cursors.tar.gz -C ~/.icons
tar -xzf gtk/1989.tar.gz -C ~/.themes
```

Icons, cursors, and the wallpaper are shared, so install those once. The SDDM archive extracts the same `1989` directory documented above; copy it to `/usr/share/sddm/themes/1989`.

These paths are the ones the KDE Store uses. Global Theme and Plasma Theme install through `kpackagetool6`. Aurorae, wallpaper, icons, cursors, GTK, and color schemes are archives extracted into their directories. On the store, each archive belongs to its own category. Installing the Global Theme there applies the look-and-feel, including the splash screen. The other pieces are installed from their own categories. The full archive does all of that with one `./install.sh` run. `./install.sh` places the GTK theme in `~/.local/share/themes` and the cursor theme in `~/.local/share/icons`, then links the cursors into `~/.icons`.

## Credits and licenses

The global theme, color schemes, window decorations, and SDDM greeter are released under GPLv3, as declared in their metadata. The wallpaper metadata declares CC-BY-SA-4.0.

The Plasma style metadata credits zayronxio and describes that style as an Amethyst Haze fork. The icon theme credits zayronxio and inherits Breeze.
