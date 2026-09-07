#!/usr/bin/env python3
"""Merge Nerd Font icon glyphs into a plain Ubuntu Mono font.

The plain variable font (UbuntuMono[wght].ttf, family "Ubuntu Mono") has the
modern look Christian wants. The Nerd Fonts build (UbuntuMonoNerdFontMono)
patches an OLDER release of Ubuntu Mono, so its normal letters/digits differ
visibly. Solution: copy ONLY the icon/symbol glyphs (plus their cmap entries)
from the Nerd build into the plain font, preserving the plain font's outlines
and metrics. Result: same plain look + full Nerd icons.

Usage: merge_nerd_icons.py <plain.ttf> <nerd.ttf> <output.ttf> [weight]
"""

import sys
from fontTools.ttLib import TTFont


def is_icon_codepoint(cp: int) -> bool:
    """Nerd Fonts v3 icon ranges (BMP PUA + supplementary-plane PUA).

    v3 keeps MOST icons in the supplementary plane (0xF0000-0xF8FFF),
    including the Material Design set (md-language_csharp at U+F031B etc.).
    Old scripts that only copied the BMP PUA (0xE000-0xF8FF) produced fonts
    where lsd/eza icons for .cs/.csproj and many others were missing.
    We also copy the Nerd build's non-PUA symbol ranges the plain variable
    font lacks (full box drawing, braille, IEC power symbols) — the terminal
    uses this font and those codepoints appear in tree views and status bars.
    """
    return (
        0xE000 <= cp <= 0xF8FF          # BMP private use (devicons, seti, FA, codicons)
        or 0xF0000 <= cp <= 0xF8FFF     # supplementary plane (Nerd v3 main set)
        or 0x2300 <= cp <= 0x23FF       # misc technical (IEC power symbols)
        or 0x2500 <= cp <= 0x257F       # box drawing (complete set)
        or 0x2580 <= cp <= 0x259F       # block elements
        or 0x2600 <= cp <= 0x27FF       # misc symbols / dingbats
        or 0x2800 <= cp <= 0x28FF       # braille patterns
        or 0x2B00 <= cp <= 0x2BFF       # misc symbols and arrows
    )


def _set_name_record(rec, value: str) -> None:
    """Write a name-table record using the record's own encoding."""
    encoding = rec.getEncoding()
    rec.string = value.encode(encoding) if encoding else value.encode()


def main():
    plain_path, nerd_path, out_path = sys.argv[1:4]
    weight = int(sys.argv[4]) if len(sys.argv) > 4 else 400
    style = "Bold" if weight >= 700 else "Regular"

    plain = TTFont(plain_path)
    nerd = TTFont(nerd_path)

    plain_glyphs = set(plain.getGlyphOrder())
    nerd_glyphs = set(nerd.getGlyphOrder())
    added_glyphs = nerd_glyphs - plain_glyphs
    print("glyphs to add (name-diff):", len(added_glyphs))

    # Only glyphs reachable via icon codepoints that plain lacks
    plain_cmap = plain.getBestCmap()
    nerd_cmap = nerd.getBestCmap()
    new_pua = {
        cp: gn
        for cp, gn in nerd_cmap.items()
        if is_icon_codepoint(cp) and cp not in plain_cmap
    }
    print("new icon codepoints:", len(new_pua))
    wanted = set(new_pua.values())
    print("distinct glyph names wanted:", len(wanted))

    # Also carry over glyph names the wanted glyphs depend on (composite
    # components, e.g. braille dots or accented PUA combos) even when the
    # component itself maps to a non-PUA codepoint.
    plain_glyf = plain["glyf"]
    nerd_glyf = nerd["glyf"]
    plain_hmtx = plain["hmtx"]
    nerd_hmtx = nerd["hmtx"]

    def copy_glyf(gname, seen):
        """Deep-copy gname (and its composite components) from nerd into plain."""
        if gname in seen or gname in plain_glyphs:
            return
        seen.add(gname)
        g = nerd_glyf[gname]
        if g.isComposite():
            for comp in g.components:
                copy_glyf(comp.glyphName, seen)
        plain_glyf[gname] = g
        try:
            aw, lsb = nerd_hmtx[gname]
        except KeyError:
            aw, lsb = nerd_hmtx[nerd.getGlyphID(gname)]
        plain_hmtx[gname] = (aw, lsb)
        plain_glyphs.add(gname)

    for name in sorted(wanted):
        if name in plain_glyphs:
            continue  # shouldn't happen for PUA-only, but guard
        copy_glyf(name, set())

    # Update glyf glyphOrder
    order = list(plain.getGlyphOrder())
    for name in sorted(wanted):
        if name not in order:
            order.append(name)
    plain.setGlyphOrder(order)

    # The variable font's gvar table holds per-glyph variation deltas for the
    # ORIGINAL glyph set only. Adding glyphs without gvar entries breaks
    # decompilation (gvar expects glyphCount entries). The input is already
    # instanced at the requested weight, so strip the remaining variation
    # tables and keep this output as a static face at that weight.
    for tag in ("gvar", "fvar", "STAT", "MVAR", "cvar", "avar"):
        if tag in plain:
            del plain[tag]
            print("stripped table:", tag)

    # Add icon codepoints to each Unicode cmap subtable, and ensure a
    # format-12 subtable exists (required for supplementary-plane > 0xFFFF).
    cmap_table = plain["cmap"]
    unicode_tables = [t for t in cmap_table.tables if t.isUnicode()]
    if not any(t.format == 12 for t in unicode_tables):
        from fontTools.ttLib.tables._c_m_a_p import cmap_classes
        sub12 = cmap_classes[12]()
        sub12.platformID = 3
        sub12.platEncID = 10
        sub12.format = 12
        sub12.language = 0
        # Seed with the FULL existing coverage (not just the new PUA entries):
        # the browser uses the format-12 subtable when present, so it must
        # carry every BMP codepoint the font already maps (åäö, box drawing,
        # etc.), not only the newly added icons.
        sub12.cmap = dict(plain_cmap)
        cmap_table.tables.append(sub12)
        unicode_tables.append(sub12)
        print("added format-12 cmap subtable (seeded from existing cmap)")
    for table in unicode_tables:
        # Format-4/6 subtables only address the BMP; only the format-12
        # subtable can carry supplementary-plane codepoints (0x10000+).
        for cp, gn in new_pua.items():
            if cp > 0xFFFF and table.format != 12:
                continue
            if cp not in table.cmap:
                table.cmap[cp] = gn

    # Rename and fully style-link the family. Windows Terminal/DirectWrite
    # uses several pieces of metadata when resolving ANSI bold. Setting only
    # usWeightClass/macStyle is not enough: name IDs 2/17, fsSelection and
    # unique/PostScript names must agree or Windows may synthesize/select the
    # wrong face even when a real 700-weight TTF is installed.
    base_family = None
    for rec in plain["name"].names:
        if rec.nameID == 1 and rec.toUnicode():
            base_family = rec.toUnicode()
            break

    if base_family:
        nf_family = base_family + " NF"
        nf_full = f"{nf_family} {style}"
        ps_family = "".join(ch for ch in nf_family if ch.isalnum())
        ps_name = f"{ps_family}-{style}"
        unique_id = f"{nf_family};{style};{weight}"

        for rec in plain["name"].names:
            if rec.nameID in (1, 16):          # family / typographic family
                _set_name_record(rec, nf_family)
            elif rec.nameID in (2, 17):        # subfamily / typographic subfamily
                _set_name_record(rec, style)
            elif rec.nameID == 3:              # unique font identifier
                _set_name_record(rec, unique_id)
            elif rec.nameID == 4:              # full font name
                _set_name_record(rec, nf_full)
            elif rec.nameID == 6:              # PostScript name
                _set_name_record(rec, ps_name)

        print("renamed family:", base_family, "->", nf_family)
        print("style:", style)
        print("PostScript name:", ps_name)

    # Set weight/style metadata consistently for Windows, macOS and other
    # font consumers.
    plain["OS/2"].usWeightClass = weight

    # OS/2.fsSelection: bit 5 = BOLD, bit 6 = REGULAR. These are mutually
    # exclusive for our two upright faces.
    fs_selection = plain["OS/2"].fsSelection
    if weight >= 700:
        fs_selection |= 0x20
        fs_selection &= ~0x40
        plain["head"].macStyle |= 0x01
    else:
        fs_selection &= ~0x20
        fs_selection |= 0x40
        plain["head"].macStyle &= ~0x01
    plain["OS/2"].fsSelection = fs_selection

    print("set usWeightClass:", weight)
    print("set fsSelection:", hex(fs_selection))

    plain.save(out_path)
    print("saved:", out_path)
    print("glyph count:", len(order))


if __name__ == "__main__":
    main()
