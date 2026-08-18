# Ubuntu Mono Nerd Font (updated)

An updated build of [Ubuntu Mono](https://fonts.google.com/specimen/Ubuntu+Mono)
with [Nerd Fonts](https://www.nerdfonts.com/) icons patched in.

The official [UbuntuMono Nerd Font](https://github.com/ryanoasis/nerd-fonts/tree/master/patched-fonts/UbuntuMono)
patches an older Ubuntu Mono release, so its normal characters render visibly
different from the current Google Fonts version (x-height 475 vs 530, cap
height 619 vs 693, letter widths 500 vs 560). This repo starts from the
current variable font and merges the icons in, keeping the modern look:

- full Nerd Font icon set (3,631 PUA codepoints)
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

`merge_nerd_icons.py` copies the PUA icon glyphs from a Nerd Font build into a
plain font, preserving its outlines, metrics, and family name. It strips
`gvar`/`fvar`/`STAT`/`avar` (adding glyphs to a variable font breaks gvar's
glyph-count invariant), so the output is a static font at the instanced
weight:

```bash
# instance the variable font at each weight (fontTools varLib.instancer),
# then merge icons from the Nerd Fonts build
python3 merge_nerd_icons.py UbuntuMono-400.ttf UbuntuMonoNerdFontMono-Regular.ttf UbuntuMonoNF-Regular.ttf
```

## License

Ubuntu Mono: [Ubuntu Font Licence](https://ubuntu.com/legal/font-licence).
Nerd Fonts patches: MIT (see [LICENSE.md](https://github.com/ryanoasis/nerd-fonts/blob/master/LICENSE.md)).
