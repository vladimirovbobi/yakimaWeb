"""Flyer style presets — six design philosophies distilled into named recipes.

Each preset is a complete design contract: palette + fonts + layout brief +
the prompt-directive snippet handed to the active flyer-generator backend.
The directives lean on the same vocabulary the huashu-design skill uses
internally — Pentagram editorial architecture, Hara emptiness, Sagmeister
boldness, Field.io geometry, Müller-Brockmann grid, Vignelli rationalism.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class FlyerPreset:
    slug: str
    name: str
    blurb: str
    inspiration: str
    palette: dict[str, str]  # primary / secondary / accent / bg / fg as hex
    fonts: dict[str, str]  # heading / body / label as font-family stacks
    layout_brief: str  # one-paragraph layout philosophy
    prompt_directive: str  # snippet stitched into the LLM prompt
    preview_image: str = ""  # /static/... thumbnail path (filled in commit 5)
    palette_token_names: dict[str, str] = field(default_factory=dict)


_CORMORANT = "Cormorant Garamond, Georgia, serif"
_RALEWAY = "Raleway, Inter, system-ui, sans-serif"
_INTER = "Inter, system-ui, sans-serif"
_MONO = "JetBrains Mono, ui-monospace, Menlo, monospace"


PRESETS: tuple[FlyerPreset, ...] = (
    FlyerPreset(
        slug="editorial-architect",
        name="Editorial Architect",
        blurb="Pentagram editorial — bold hierarchy, structured columns, hairline rules.",
        inspiration="Pentagram editorial",
        palette={
            "primary": "#BFA06A",  # gold
            "secondary": "#F5EFE0",  # ivory
            "accent": "#DEC98A",  # gold-hi
            "bg": "#080604",  # black
            "fg": "#F5EFE0",  # ivory
        },
        palette_token_names={
            "primary": "gold",
            "secondary": "ivory",
            "accent": "gold-hi",
            "bg": "black",
            "fg": "ivory",
        },
        fonts={"heading": _CORMORANT, "body": _INTER, "label": _INTER},
        layout_brief=(
            "Editorial baseline grid with a dominant Cormorant headline as the visual anchor. "
            "Property facts set as a structured information grid; one large hero photo treated "
            "as a printed plate. Generous outer margins, hairline rules between blocks."
        ),
        prompt_directive=(
            "Apply Pentagram-style editorial architecture: bold typographic hierarchy with the "
            "headline set in Cormorant Garamond at heroic scale, structured fact-columns set in "
            "Inter, generous white space, single dominant photo treated as a printed plate, "
            "hairline gold rules between sections, no decorative ornament."
        ),
    ),
    FlyerPreset(
        slug="quiet-luxe",
        name="Quiet Luxe",
        blurb="Kenya Hara emptiness — restrained typography, abundant negative space.",
        inspiration="Kenya Hara",
        palette={
            "primary": "#706450",  # dim
            "secondary": "#CEC4A8",  # mist
            "accent": "#BFA06A",  # gold
            "bg": "#F5EFE0",  # ivory
            "fg": "#0D0904",  # deep
        },
        palette_token_names={
            "primary": "dim",
            "secondary": "mist",
            "accent": "gold",
            "bg": "ivory",
            "fg": "deep",
        },
        fonts={"heading": _CORMORANT, "body": _RALEWAY, "label": _RALEWAY},
        layout_brief=(
            "Extreme negative space with a single delicate focal photograph and a small, "
            "perfectly placed headline. Body text restrained to absolute essentials. One "
            "horizontal hairline as the only divider. Whitespace IS the design."
        ),
        prompt_directive=(
            "Apply Kenya Hara quiet-luxe philosophy: emptiness as content. Restrained Cormorant "
            "Light typography at modest scale. One small, delicate photograph as the focal point. "
            "Abundant negative space. A single hairline rule as the only divider. No decoration, "
            "no color blocks, no dramatic gestures. The whitespace IS the design."
        ),
    ),
    FlyerPreset(
        slug="bold-statement",
        name="Bold Statement",
        blurb="Sagmeister-style experimental — oversized typography, dramatic color blocks.",
        inspiration="Stefan Sagmeister",
        palette={
            "primary": "#DEC98A",  # gold-hi
            "secondary": "#080604",  # black
            "accent": "#F5EFE0",  # ivory
            "bg": "#080604",  # black
            "fg": "#F5EFE0",  # ivory
        },
        palette_token_names={
            "primary": "gold-hi",
            "secondary": "black",
            "accent": "ivory",
            "bg": "black",
            "fg": "ivory",
        },
        fonts={"heading": _CORMORANT, "body": _INTER, "label": _INTER},
        layout_brief=(
            "Oversized headline as the hero element, set at viewport-filling scale. Dramatic "
            "asymmetric color blocks. Property facts treated as deliberate typographic contrast — "
            "small, structured, almost shy against the headline. One large photograph as a held "
            "moment of stillness."
        ),
        prompt_directive=(
            "Apply Sagmeister-style bold experimental design: an oversized Cormorant Garamond "
            "headline as the hero element filling the upper third, dramatic asymmetric gold-hi "
            "color blocks, property facts set as deliberately small structured Inter type for "
            "contrast, one large photograph as a still counterweight, typographic personality "
            "through scale not decoration."
        ),
    ),
    FlyerPreset(
        slug="motion-geometry",
        name="Motion Geometry",
        blurb="Field.io kinetic geometry — structured grid with diagonal accents and mono labels.",
        inspiration="Field.io",
        palette={
            "primary": "#BFA06A",  # gold
            "secondary": "#1A1208",  # warm
            "accent": "#5A4A28",  # gold-dim
            "bg": "#0D0904",  # deep
            "fg": "#F5EFE0",  # ivory
        },
        palette_token_names={
            "primary": "gold",
            "secondary": "warm",
            "accent": "gold-dim",
            "bg": "deep",
            "fg": "ivory",
        },
        fonts={"heading": _INTER, "body": _INTER, "label": _MONO},
        layout_brief=(
            "Strict geometric grid with two or three fine diagonal accent lines that suggest "
            "frozen motion. Monospace data labels next to property facts. Geometric photo frames "
            "with thin gold borders. Sense of structure under tension, like architectural drawings."
        ),
        prompt_directive=(
            "Apply Field.io kinetic geometry: a strict 12-column grid with two or three thin "
            "diagonal accent lines suggesting frozen motion, monospace JetBrains-style labels for "
            "data points, geometric thin-bordered photo frames, structural elegance under tension. "
            "Read like an architectural drawing, not a brochure."
        ),
    ),
    FlyerPreset(
        slug="swiss-grid",
        name="Swiss Grid",
        blurb="Müller-Brockmann modernism — strict modular grid, ruthless hierarchy.",
        inspiration="Josef Müller-Brockmann",
        palette={
            "primary": "#080604",  # black
            "secondary": "#F5EFE0",  # ivory
            "accent": "#BFA06A",  # gold
            "bg": "#F5EFE0",  # ivory
            "fg": "#080604",  # black
        },
        palette_token_names={
            "primary": "black",
            "secondary": "ivory",
            "accent": "gold",
            "bg": "ivory",
            "fg": "black",
        },
        fonts={"heading": _INTER, "body": _INTER, "label": _INTER},
        layout_brief=(
            "Strict modular grid with ruthless typographic hierarchy expressed only through size "
            "and weight. Zero decoration. Information-dense fact panels aligned to the grid. "
            "Photographs cropped square or rectangular to grid cells. Black, ivory, one accent."
        ),
        prompt_directive=(
            "Apply Müller-Brockmann Swiss modernism: a strict 12-column modular grid, grotesque "
            "sans-serif typography (use Inter as proxy), ruthless hierarchy expressed only "
            "through size and weight, zero decoration, no rounded corners, photographs cropped "
            "to grid cells, palette of black + ivory + one gold accent. Factual, not poetic."
        ),
    ),
    FlyerPreset(
        slug="italian-editorial",
        name="Italian Editorial",
        blurb="Vignelli rationalism — classical publication grid with serif throughout.",
        inspiration="Massimo Vignelli",
        palette={
            "primary": "#0D0904",  # deep
            "secondary": "#5A4A28",  # gold-dim
            "accent": "#F5EFE0",  # ivory
            "bg": "#F5EFE0",  # ivory
            "fg": "#0D0904",  # deep
        },
        palette_token_names={
            "primary": "deep",
            "secondary": "gold-dim",
            "accent": "ivory",
            "bg": "ivory",
            "fg": "deep",
        },
        fonts={"heading": _CORMORANT, "body": _CORMORANT, "label": _CORMORANT},
        layout_brief=(
            "Classical Italian publication grid with serif throughout. Body text given equal "
            "visual weight to the headline. Three-color palette only. Simple horizontal rules "
            "as section breaks. The body copy is the star, not the headline."
        ),
        prompt_directive=(
            "Apply Vignelli rationalist editorial design: a classical Italian publication grid "
            "with Cormorant Garamond used throughout for headline AND body, body copy given "
            "equal weight to the headline, palette restricted to three colors only "
            "(deep + gold-dim + ivory), simple horizontal rules as section breaks, no sans-serif "
            "anywhere. Read like a 1970s editorial, not a flyer."
        ),
    ),
)

PRESETS_BY_SLUG: dict[str, FlyerPreset] = {p.slug: p for p in PRESETS}


def get_preset(slug: str) -> FlyerPreset | None:
    return PRESETS_BY_SLUG.get(slug)


def list_presets() -> list[FlyerPreset]:
    return list(PRESETS)
