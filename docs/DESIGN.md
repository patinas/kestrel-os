# Design system and polish rules

Polish is a release requirement. A feature that doesn't meet these rules
doesn't ship.

## Look and feel

- Minimal. Content first; the shell stays out of the way.
- One typeface (Inter, open source), one icon set, one set of design tokens
  (color, spacing, radius, motion) shared by shell, settings and setup.
- Light and dark theme, following the time of day by default. No other themes.
- Motion: 150-250 ms, ease-out, never blocks input. Reduced-motion setting honoured.

## Rules

1. One shell. No desktop icons, no panel plugins, no widget zoo.
2. Every screen works with keyboard, mouse, touch and screen reader.
3. No terminal, config file or error dialog in the normal user path.
4. Every setting has a visible home in Settings; nothing is hidden in files.
5. Boot to login in under 10 s on a 2015-era SSD laptop; no text on screen
   during boot (quiet boot + splash).
6. Every string is translated before release (Danish and English first).
7. Frame budget: shell animations hold 60 fps on the lowest supported GPU.

## Review

Every UI change needs a screenshot or screen recording on both light and dark
theme, reviewed against this page before merge.
