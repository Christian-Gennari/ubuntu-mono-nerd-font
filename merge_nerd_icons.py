#!/usr/bin/env python3
"""Merge Nerd Font icon glyphs into a plain font.

Copies ONLY the PUA icon glyphs (plus cmap entries) from a Nerd Font build
into a plain font, preserving the plain font's outlines, metrics, and family
name. Strips gvar/fvar/STAT/avar on output (adding glyphs to a variable font
breaks gvar's glyph-count invariant), so the result is a static font at the
instanced weight.

Usage: merge_nerd_icons.py <plain.ttf> <nerd.ttf> <output.ttf>
"""
import sys
from fontTools.ttLib import TTFont


def main():
    plain_path, nerd_path, out_path = sys.argv[1:4]
    plain = TTFont(plain_path)
    nerd = TTFont(nerd_path)

    plain_glyphs = set(plain.getGlyphOrder())
    nerd_glyphs = set(nerd.getGlyphOrder())
    added_glyphs = nerd_glyphs - plain_glyphs
    print("glyphs to add (name-diff):", len(added_glyphs))

    # Only glyphs reachable via PUA codepoints that plain lacks
    plain_cmap = plain.getBestCmap()
    nerd_cmap = nerd.getBestCmap()
    new_pua = {
        cp: gn
        for cp, gn in nerd_cmap.items()
        if (0xE000 <= cp <= 0xF8FF or 0xF5000 <= cp <= 0xF8FFE)
        and cp not in plain_cmap
    }
    print("new PUA codepoints:", len(new_pua))
    wanted = set(new_pua.values())
    print("distinct glyph names wanted:", len(wanted))

    # Copy the glyph data (glyf, hmtx, cmap subset of names)
    plain_glyf = plain["glyf"]
    plain_hmtx = plain["hmtx"]
    nerd_glyf = nerd["glyf"]
    nerd_hmtx = nerd["hmtx"]

    for name in sorted(wanted):
        if name in plain_glyphs:
            continue  # shouldn't happen for PUA-only, but guard
        # Copy glyf entry (deep-copy composite glyphs recursively)
        def copy_glyf(gname, seen):
            if gname in seen or gname in plain_glyphs:
                return
            seen.add(gname)
            g = nerd_glyf[gname]
            if g.isComposite():
                for comp in g.components:
                    copy_glyf(comp.glyphName, seen)
            plain_glyf[name] = g
            # hmtx metrics (lsb, advance)
            try:
                aw, lsb = nerd_hmtx[gname]
            except KeyError:
                aw, lsb = nerd_hmtx[nerd.getGlyphID(gname)]
            plain_hmtx[name] = (aw, lsb)
            plain_glyphs.add(gname)

        copy_glyf(name, set())

    # Update glyf glyphOrder + cmap
    order = list(plain.getGlyphOrder())
    for name in sorted(wanted):
        if name not in order:
            order.append(name)
    plain.setGlyphOrder(order)

    # The variable font's gvar table holds per-glyph variation deltas for the
    # ORIGINAL glyph set only. Adding glyphs without gvar entries breaks
    # decompilation (gvar expects glyphCount entries). Simplest correct fix:
    # strip gvar + fvar, making this a static 400-weight font. CSS serves it
    # at any weight via the @font-face range, but rendering is always the
    # default instance (400). The plain variable font's default IS 400, so
    # the look is unchanged.
    for tag in ("gvar", "fvar", "STAT", "MVAR", "cvar", "avar"):
        if tag in plain:
            del plain[tag]
            print("stripped table:", tag)

    # Add PUA entries to each cmap subtable
    for table in plain["cmap"].tables:
        if table.isUnicode():
            for cp, gn in new_pua.items():
                if cp not in table.cmap:
                    table.cmap[cp] = gn

    plain.save(out_path)
    print("saved:", out_path)
    print("glyph count:", len(order))


if __name__ == "__main__":
    main()
