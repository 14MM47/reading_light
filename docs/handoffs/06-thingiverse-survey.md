# Handoff 06 — Thingiverse moon-model survey (needs a real browser)

**For:** Claude Code in VS Code on Matt's laptop (with the built-in browser or Claude in Chrome), ~15 min.
**Why this exists:** Matt asked us to visit Thingiverse for moon models. From the cloud session Thingiverse (and
Printables/MakerWorld) return a Cloudflare challenge to scripts, and the session's web-search budget ran out, so the
survey could not be done there. The design decision did not depend on it: the moon is generated from NASA data at
the real 50 mm size (`cad/parts/moon_shell.py`) because scaling a 10–20 cm moon lamp to 5 cm shrinks its lithophane
walls to ~0.3–1 mm (unprintable / uneven). This survey is for credit, comparison and ideas only.

## Steps
1. Open https://www.thingiverse.com/search?q=moon+lamp&type=things&sort=popular in the browser (Matt signs in if
   needed). Also search "lithophane moon", "moon lamp 50mm", "small moon lamp".
2. For the 6–8 most popular/relevant results record in `docs/research/thingiverse-moons.md`: thing ID + URL, title,
   author, licence (CC-BY / CC-BY-NC / ...), designed diameter, wall/relief approach (displacement map? albedo?),
   min/max thickness if stated, opening/hole diameter, recommended print settings, number of makes.
3. Note any model designed at 40–60 mm. If one exists with a permissive licence, compare its thickness range to ours
   (0.9–2.6 mm) and its look (outer relief vs our smooth outside with inside relief).
4. Do **not** download/redistribute models into this repo unless the licence allows it; link only.
5. If a surveyed design suggests an improvement (e.g. outer relief looks better unlit), raise it with Matt as a
   multiple-choice question; `moon_shell.py` already has the relief side as one switch to flip (B11).

## Done when
`docs/research/thingiverse-moons.md` exists with the table above and a one-paragraph conclusion, committed.
