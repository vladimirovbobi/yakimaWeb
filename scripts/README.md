# Asset generation scripts

Pillow-based generators for brand placeholder assets. All output is git-ignored
where appropriate (or committed deliberately as launch-time placeholders).

## Run all

```bash
make assets
```

## Run individually

```bash
python scripts/generate_favicons.py
python scripts/generate_furniture_remover_samples.py
python scripts/generate_hero_placeholders.py
```

## Outputs

| Script | Outputs |
|---|---|
| `generate_favicons.py` | `frontend/public/favicon.ico`, `apple-touch-icon.png`, `icon-192.png`, `icon-512.png` |
| `generate_furniture_remover_samples.py` | `frontend/public/img/samples/furniture-remover/before-{1,2,3}.jpg`, `after-{1,2,3}.jpg` |
| `generate_hero_placeholders.py` | `frontend/public/img/hero/hero-{home,blog,services,community,tools}.jpg` |

## Demo OG samples

OG samples come from the Django management command (needs the DB stack):

```bash
docker compose exec api python manage.py regen_og_images --demo
```

Outputs to `frontend/public/og-samples/`.

## Deps

- `Pillow` — already in `pyproject.toml` dev group.
- `cairosvg` — NOT required. Mark glyphs are drawn directly via Pillow primitives
  so we never depend on a system SVG renderer.

## Replace before launch

Every asset produced by these scripts is a placeholder marked with `[demo]` or a
`DEMO` watermark. Replace with real photographer-supplied art before launch.
See `frontend/README.md` "Brand assets" for the full checklist.
