# Ubuntu Mono Nerd Font (updated)

An updated build of [Ubuntu Mono](https://fonts.google.com/specimen/Ubuntu+Mono)
with [Nerd Fonts](https://www.nerdfonts.com/) icons patched in.

The official [UbuntuMono Nerd Font](https://github.com/ryanoasis/nerd-fonts/tree/master/patched-fonts/UbuntuMono)
patches an older Ubuntu Mono release, so its normal characters render visibly
different from the current Google Fonts version (x-height 475 vs 530, cap
height 619 vs 693, letter widths 500 vs 560). This repo starts from the
current variable font and merges the icons in, keeping the modern look:

- full Nerd Font icon set (10,490 icon codepoints: 3,631 BMP PUA + 6,896
  supplementary-plane PUA — includes the Material Design set that lsd/eza use
  for .cs/.csproj at U+F031B, plus complete box drawing and braille)
- real Bold weight (instanced at 700, not synthesized)
- identical letterforms to plain Ubuntu Mono (0 ASCII outline differences)

## Files

| File | Family | Weight |
|---|---|---|
| `UbuntuMonoNF-Regular.ttf` | Ubuntu Mono NF | 400 |
| `UbuntuMonoNF-Bold.ttf` | Ubuntu Mono NF | 700 |

Use `font-family: "Ubuntu Mono NF"`. If the older look is fine for you, use
the official [Nerd Fonts release](https://github.com/ryanoasis/nerd-fonts/releases)
instead.

## Building

`merge_nerd_icons.py` copies the icon glyphs from a Nerd Font build into a
plain font, preserving its outlines, metrics, and family name. It strips
`gvar`/`fvar`/`STAT`/`avar` (adding glyphs to a variable font breaks gvar's
glyph-count invariant), so the output is a static font at the instanced
weight:

```bash
# instance the variable font at each weight (fontTools varLib.instancer,
# MUST use inplace=True or the wght deltas are not applied),
# then merge icons from the Nerd Fonts build
python3 merge_nerd_icons.py UbuntuMono-400.ttf UbuntuMonoNerdFontMono-Regular.ttf UbuntuMonoNF-Regular.ttf 400
python3 merge_nerd_icons.py UbuntuMono-700.ttf UbuntuMonoNerdFontMono-Bold.ttf UbuntuMonoNF-Bold.ttf 700
```

**Pitfall fixed 2026-08-18:** earlier builds only copied the BMP private-use
area (0xE000–0xF8FF). Nerd Fonts v3 keeps most icons in the supplementary
plane (0xF0000–0xF8FFF), including the Material Design set — so `.cs`/`.csproj`
icons from lsd/eza (U+F031B md-language_csharp) and many others rendered as
blank boxes. The current script copies the full supplementary plane, the
complete box-drawing/braille/IEC ranges, and emits a format-12 cmap subtable
(required for codepoints above 0xFFFF), seeded with the existing coverage.

## License

Ubuntu Mono: [Ubuntu Font Licence](https://ubuntu.com/legal/font-licence).
Nerd Fonts patches: MIT (see [LICENSE.md](https://github.com/ryanoasis/nerd-fonts/blob/master/LICENSE.md)).
