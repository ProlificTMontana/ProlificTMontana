# profile/

The source for everything on the GitHub profile page. The root `README.md`
and every image in `assets/` are **generated**. Don't edit them by hand.

```
profile/
├── content.py      ← all words, links, projects, skills: edit this
├── build.py        → renders assets/*.svg (dark + light) and README.md
├── telemetry.py    → live stats card, run daily by GitHub Actions
├── design.py       theme tokens, font metrics/subsetting, SVG primitives
├── icons.json      brand icons vendored from simple-icons (CC0-1.0)
└── fonts/          Space Grotesk + JetBrains Mono (SIL OFL 1.1)
```

## Update the profile

```bash
pip install -r profile/requirements.txt
```

```bash
python profile/build.py
```

Commit `profile/`, `assets/` and `README.md` together. CI (`profile-ci.yml`)
rebuilds on every push and pull request and fails if the committed output is stale.

Preview the telemetry card offline with fake data:

```bash
python profile/telemetry.py --sample --out /tmp/telemetry
```

## How it works

- **Light and dark.** Every asset is rendered in both themes and swapped by
  `<picture>` + `prefers-color-scheme`. Each image is a self-contained card,
  so it reads correctly even if the OS and GitHub themes disagree.
- **Identical everywhere.** GitHub's image proxy blocks external fonts, so each
  SVG embeds WOFF2 fonts subset to only the glyphs it uses (a few KB each).
  Layout uses real font metrics, so text never overflows its card.
- **Robust motion.** Only decorative loops are animated (radar sweep, typing
  prompt, pulses), and content is never hidden behind an entrance animation.
  `prefers-reduced-motion` is respected.
- **Deterministic.** The same inputs always produce byte-identical files.
- **No third-party stat services.** `telemetry.yml` queries the GitHub GraphQL
  API with the workflow's own token and force-pushes the card to an orphan
  `output` branch, so daily refreshes never touch `main`'s history.

## Telemetry options

| Setting | Where | Effect |
| --- | --- | --- |
| `TELEMETRY_TOKEN` | repo secret | Fine-grained read-only PAT; adds private contribution counts |
| `TELEMETRY_INCLUDE_PRIVATE` | repo variable | `1` to include private repos in language stats (needs the PAT) |
| `TELEMETRY_EXCLUDE_LANGUAGES` | repo variable | e.g. `HTML,CSS` to leave markup out of the language bar |
