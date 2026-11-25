"""Small WCAG helpers used to validate administrator-supplied palettes."""
import re

HEX_COLOUR = re.compile(r"^#[0-9A-Fa-f]{6}$")
MIN_TEXT_CONTRAST = 4.5


def relative_luminance(hex_colour):
    """Return WCAG relative luminance for a six-digit hex colour."""
    channels = [int(hex_colour[index:index + 2], 16) / 255 for index in (1, 3, 5)]
    linear = [
        channel / 12.92 if channel <= 0.04045 else ((channel + 0.055) / 1.055) ** 2.4
        for channel in channels
    ]
    return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2]


def contrast_ratio(first, second):
    """Return the WCAG contrast ratio between two six-digit hex colours."""
    first_luminance = relative_luminance(first)
    second_luminance = relative_luminance(second)
    lighter = max(first_luminance, second_luminance)
    darker = min(first_luminance, second_luminance)
    return (lighter + 0.05) / (darker + 0.05)
