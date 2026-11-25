"""Initial palettes shipped with the platform.

These values are seed data only. Administrators can add more palettes through
the API or the Theme manager page; no component code contains a palette name or
a hard-coded colour choice. The exact swatches from the supplied images are
kept in each ramp; darker steps are derived to meet the 4.5:1 text rule.
"""

OCEAN_BLUE = {
    "name": "Ocean Blue Serenity",
    "slug": "ocean-blue-serenity",
    "description": (
        "White-dominant blue ramp approved for the original KLB visual system."
    ),
    "source_label": "Ocean Blue Serenity.png",
    "shades": {
        900: "#03045E",
        800: "#023E8A",
        700: "#0077B6",
        600: "#0096C7",
        500: "#00B4D8",
        400: "#48CAE4",
        300: "#90E0EF",
        200: "#ADE8F4",
        100: "#CAF0F8",
    },
}

SAGE_GREEN = {
    "name": "Sage Green",
    "slug": "sage-green",
    "description": (
        "Calm green ramp based on the five exact swatches in colors.png. "
        "Darker text shades were derived for WCAG AA contrast on white."
    ),
    "source_label": "colors.png",
    "shades": {
        900: "#1E3B2F",
        800: "#244C3B",
        700: "#2F4A3D",
        600: "#3A5F50",
        500: "#6B9080",
        400: "#A4C3B2",
        300: "#CCE3DE",
        200: "#EAF4F4",
        100: "#F6FFF8",
    },
}

BLUE_CORAL = {
    "name": "Blue Coral Daylight",
    "slug": "blue-coral-daylight",
    "description": (
        "Five exact swatches from new color.png. Darker text shades were "
        "derived from the navy swatch for WCAG AA contrast on white."
    ),
    "source_label": "new color.png",
    "shades": {
        900: "#182039",
        800: "#232F54",
        700: "#304071",
        600: "#324376",
        500: "#586BA4",
        400: "#F76C5E",
        300: "#F68E5F",
        200: "#F5DD90",
        100: "#FAF0CD",
    },
}

FOREST_GREEN = {
    "name": "Forest Green",
    "slug": "forest-green",
    "description": (
        "Five exact greens from color 2.png. Darker text shades were derived "
        "from the deepest green for WCAG AA contrast on white."
    ),
    "source_label": "color 2.png",
    "shades": {
        900: "#022807",
        800: "#033A0A",
        700: "#03440C",
        600: "#036016",
        500: "#04773B",
        400: "#058E3F",
        300: "#069E2D",
        200: "#5DC076",
        100: "#B4E2C0",
    },
}

CITRUS_BLOOM = {
    "name": "Citrus Bloom",
    "slug": "citrus-bloom",
    "description": (
        "Five exact lime and pink swatches from color 3.png. Darker text "
        "shades were derived from the magenta for WCAG AA contrast on white."
    ),
    "source_label": "color 3.png",
    "shades": {
        900: "#3F0E29",
        800: "#5B143C",
        700: "#7A1A50",
        600: "#FF37A6",
        500: "#43B929",
        400: "#87E752",
        300: "#5CF64A",
        200: "#FFCAE9",
        100: "#FFE7F5",
    },
}

HERITAGE_SPICE = {
    "name": "Heritage Spice",
    "slug": "heritage-spice",
    "description": (
        "Five exact green, red, orange and gold swatches from color 4.png. "
        "Darker text shades were derived from the deepest green."
    ),
    "source_label": "color 4.png",
    "shades": {
        900: "#02271C",
        800: "#023828",
        700: "#034732",
        600: "#008148",
        500: "#EF2917",
        400: "#EF8A17",
        300: "#C6C013",
        200: "#DAD666",
        100: "#EEECB8",
    },
}

BRIGHT_HORIZON = {
    "name": "Bright Horizon",
    "slug": "bright-horizon",
    "description": (
        "Four exact yellow, coral, green and blue swatches from color 5.png. "
        "Darker text shades were derived from the coral swatch."
    ),
    "source_label": "color 5.png",
    "shades": {
        900: "#3C1517",
        800: "#571E22",
        700: "#74292E",
        600: "#FF5964",
        500: "#35A7FF",
        400: "#6BF178",
        300: "#FFE74C",
        200: "#FFEF8B",
        100: "#FFF8C9",
    },
}

PLUM_HARVEST = {
    "name": "Plum Harvest",
    "slug": "plum-harvest",
    "description": (
        "Five exact swatches from color 7.png. A deeper plum step was derived "
        "from the source image for WCAG AA contrast on white."
    ),
    "source_label": "color 7.png",
    "shades": {
        900: "#1A0F14",
        800: "#291720",
        700: "#820263",
        600: "#D90368",
        500: "#04A777",
        400: "#FB8B24",
        300: "#FFB067",
        200: "#FFD9B8",
        100: "#FFF3E8",
    },
}

SWATCH_PALETTES = (
    BLUE_CORAL,
    FOREST_GREEN,
    CITRUS_BLOOM,
    HERITAGE_SPICE,
    BRIGHT_HORIZON,
)

INITIAL_PALETTES = (OCEAN_BLUE, SAGE_GREEN, *SWATCH_PALETTES, PLUM_HARVEST)
DEFAULT_ACTIVE_SLUG = PLUM_HARVEST["slug"]
