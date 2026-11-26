# 1989 agent law

This file is the agent form of `docs/STYLE.md`. It applies to every file in this project.

Before changing color, type, panel, frame, wallpaper, splash, greeter, terminal, or icons, read `docs/1989-studies.html` and `docs/STYLE.md`. The HTML is the picture. `docs/STYLE.md` is the written law. This file restates that law so an agent can follow it. If a result and the study disagree, change the result.

The desktop chrome is Mocha color on a Bauhaus poster: Blade’s thin bar, frosted windows, a square hairline, and Hack. Catppuccin Mocha stays Mocha. Do not recolor that scheme into a new palette. The desktop wallpaper is a separate picture, described under Desktop wallpapers.

## Palette

Default is the desktop drawn in the study. Use these values.

| Role | Value | Use |
| --- | --- | --- |
| field | `#181821` | Desktop, splash, greeter, window fill |
| surface | `rgba(24, 24, 33, 0.82)` | Frosted window and menu |
| panel | `rgba(24, 24, 33, 0.78)` | Top bar |
| title | `#cdd6f4` | Active titles, clock, folder labels, wordmark |
| text | `#bdc5e3` | Body, idle menu rows |
| dim | `#8d939f` | Idle titles, idle menu words, minimize hairline |
| mauve | `#d1b7f1` | Poster disc stroke, app-view selection fill, prompt host |
| peach | `#dd9d89` | Default accent: focus, panel hairline, close button |
| green | `#a6e3a1` | Positive: battery, prompt user, maximize hairline |
| sand | `#f9e2af` | Poster, splash, folder tiles, prompt mark, Default mark |
| teal | `#94e2d5` | Poster, splash, folder tiles, Default mark head |
| blue | `#89b4fa` | Study blue |
| pink | `#be86c6` | Study pink |
| disc | `#222233` | Poster circle fill |
| idle hairline | `rgba(189, 197, 227, 0.18)` | Unfocused frame, menu edge |
| panel hairline | `rgba(221, 157, 137, 0.45)` | Bottom edge of the top bar |
| offset | `10px solid rgba(8, 8, 14, 0.35)` | Flat stand-in for shadow in study drawings |

Sand and teal belong to the poster, the splash stripe, and the Default CachyOS mark. Do not use them for focus, body text, or the panel.

Frost is a flat translucency of field. The installed frame keeps its soft shadow outside the hairline. The study draws that shadow as the flat offset above. Chrome has no gradient, gloss, or inner highlight.

## Variations

Keep one geometry. There are five color rows only. The desktop in the study is Default. A variant swaps the accent and the CachyOS mark. Field, title, text, dim, Hack, the square hairline, and the layout stay.

| Variant | Accent | Head | Facet | Squares |
| --- | --- | --- | --- | --- |
| Default | `#dd9d89` | `#94e2d5` | `#a6e3a1` | `#dd9d89` `#d1b7f1` `#f9e2af` |
| Mocha | `#d1b7f1` | `#d1b7f1` | `#cba6f7` | `#f38ba8` `#fab387` `#f9e2af` |
| Blue | `#7ba5e3` | `#7ba5e3` | `#74b8c6` | `#7ba5e3` `#9ca6df` `#65a9c6` |
| Green | `#6f9a72` | `#6f9a72` | `#5e968e` | `#6f9a72` `#5e968e` `#7a6c48` |
| Red | `#b46176` | `#b46176` | `#9e6570` | `#b46176` `#9e6570` `#ab7662` |

The mark is one icon file. Head, facet, and the three squares take Highlight, Positive, Neutral, and Negative from the active scheme.

## Type

Hack is the only face: panel, menus, titles, terminal, splash, and greeter. The fallback stack is `Hack, ui-monospace, monospace`.

| Surface | Size |
| --- | --- |
| Panel and title bar | 12px, panel tracking `0.04em` |
| Terminal and menu rows | 13px, terminal line-height 1.55 |
| Folder labels | 11px |
| Study splash wordmark | 28px, tracking `0.18em` |

The wordmark is `1989` in the title color. Use no second face, no bold chrome, and no serif.

## Panel

Height 32. Padding `0 14px`. Gap 8. Field at 78% opacity. A 1px peach hairline at 45% opacity sits on the bottom edge.

Left to right: the CachyOS mark at 16px, then File in the title color, then Edit and View in dim. The right cluster is network, volume, battery, bell, then the clock in the title color. The clock is hours and minutes.

## Frames

Square. No corner radius on windows, panels, buttons, menus, or folders.

Title bar is 28px tall, padding `0 10px`, gap 8. The active title is the title color. The idle title is dim. The title is centered.

Buttons sit on the left, in this order:

- close: 11×11 filled square in the accent
- maximize: 9×9 hairline square in green
- minimize: 9×9 hairline square in dim

A focused frame uses a 1px accent border. An idle frame uses the idle hairline. Window fill is the frosted surface.

## Launcher

Width 220. Frosted surface, 1px idle hairline, Hack at 13px. Row padding `7px 12px`. Other rows are body text on a clear background.

## List highlight

Plasma lists (the launcher, the clipboard, applet lists) keep body text on a highlighted row. The highlight must stay dark enough for that text. The highlighted row is an accent wash with a 1px accent hairline, square, in `widgets/viewitem.svgz`:

- hover: accent at 28%
- selected: accent at 20%
- selected and hovered: accent at 35%

The accent comes from `ColorScheme-ButtonFocus`, so each variant uses its own accent. Do not fill a Plasma row with a solid or light color.

Qt app views (Dolphin, settings lists, menus) switch to the selection text color. There the selection is solid mauve, or the variant's Selection color, with field-colored text.

## Terminal

The prompt is user in green, `at` in dim, host in mauve, `in` in dim, path in peach. The prompt mark is sand. Command text is the body color. The selection wash is peach at 28% opacity.

## Desktop wallpapers

A desktop wallpaper is a color photograph with a late-1970s to late-1980s California feeling. It stays a photograph: real light, real depth, film color. A drawing, a flat poster, or a sky painted over a picture is the wrong result.

The subject is a 1980s scene, seen as a photograph: a classic car at sunset, a palm boulevard, a beach wagon, a neon roadside, an amusement park at dusk, or a warm city. A visible sun is in the frame. When there is no sun, neon is. Palms, chrome, and long shadows belong here. A cyberpunk street can use the same light.

The grade is split. Open sky and shadows lean teal. Sun, clouds, and highlights lean peach, sand, and mauve. Darks may sit near field `#181821`. The grade tints the photograph. It does not replace it.

The wallpaper carries no added type and no added logo.

A variant keeps a photograph in this family. It shifts the teal and the warm light toward that variant’s accent and squares. Wallpaper color stays on the wallpaper. Panel, frames, type, and icons keep the study palette.

## Poster

Peach, sand, teal and orientative colors.

The study drawing and the splash use this poster: a disc on the left, three bands on the right. That drawing is not the desktop wallpaper.

## Splash and greeter

The splash is the poster, centered.

The SDDM greeter uses the same image and Hack. Inputs are square and use the body color.

## CachyOS mark

Keep the geometry, on the 64×64 icon canvas. The study's 16-unit coordinates are:

- head `1,8 5.5,3 8,8 5.5,13`
- upper facet `5.5,3 10,5.2 8,8`
- lower facet `5.5,13 10,10.8 8,8`
- squares at `(11,2)`, `(12.2,5)`, and `(11,8)`, each 2×2

Default colors are teal, green, peach, mauve, sand. The mark stays recognizable as the CachyOS logo.

## Icons

A hand-drawn icon and a scalable app icon use a 64×64 canvas: `width="64"`, `height="64"`, `viewBox="0 0 64 64"`. A sized theme file uses that directory's canvas, and its `@2x` file uses twice that canvas.

Every icon we draw is an arcade console mark, in the language of a late-1980s.

When creating an icon: use the current icon and make it look as if it was being rendered in an arcade machine.

All system icons follow the same rules.

## Check before a visual change

A change lands only when it matches the study on all of these:

- square hairline, Hack, field `#181821`, flat color
- accent and mark colors from the variant row, not a new palette
- a Plasma list highlight is an accent wash with a 1px accent hairline, never a solid fill under body text
- buttons on the left; the study and the splash keep the poster disc on the left and three bands on the right
- a desktop wallpaper is a 1980s photograph with a visible sun, or with neon when there is no sun, in the teal and peach film grade
- a hand-drawn or scalable app icon is on a 64×64 canvas, in late-80s Atari arcade form; a sized file uses its directory canvas and `@2x` uses twice that canvas
- a recreated app icon takes its symbol from the brand, then the purpose, then the name
