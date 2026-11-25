/* Runtime palette helpers.
 *
 * The server is the catalogue owner. These helpers convert an API palette into
 * CSS custom properties and concrete colours for Recharts. Components read the
 * active palette from ThemeContext, so adding a palette never requires a code
 * change here.
 */

export const SHADE_STEPS = [900, 800, 700, 600, 500, 400, 300, 200, 100];

/* Matches the server's default active palette so the first paint is correct
   even before /api/theming/active/ responds. */
const FALLBACK_SHADES = Object.freeze({
  900: "#1A0F14",
  800: "#291720",
  700: "#820263",
  600: "#D90368",
  500: "#04A777",
  400: "#FB8B24",
  300: "#FFB067",
  200: "#FFD9B8",
  100: "#FFF3E8",
});

const CHART_STEPS = [800, 700, 500, 600, 400, 300];
export const HEX_COLOUR = /^#[0-9A-Fa-f]{6}$/;
export const MIN_TEXT_CONTRAST = 4.5;

function readShades(payload) {
  const raw = payload?.shades || {};
  return Object.freeze(Object.fromEntries(SHADE_STEPS.map((step) => [
    step,
    String(raw[step] || payload?.[`shade_${step}`] || FALLBACK_SHADES[step]).toUpperCase(),
  ])));
}

export function normalisePalette(payload) {
  const shades = readShades(payload);
  return {
    id: payload?.id ?? 0,
    name: payload?.name || "Plum Harvest",
    slug: payload?.slug || "plum-harvest",
    description: payload?.description || "",
    sourceLabel: payload?.source_label || payload?.sourceLabel || "",
    isActive: Boolean(payload?.is_active ?? payload?.isActive ?? false),
    shades,
    colors: {
      chart: CHART_STEPS.map((step) => shades[step]),
      attendance: Object.freeze({
        PRESENT: shades[800],
        ABSENT: shades[900],
        LATE: shades[600],
        EXCUSED: shades[700],
      }),
      score: shades[700],
      grid: shades[100],
    },
  };
}

export const DEFAULT_PALETTE = normalisePalette(null);

function hexToRgba(hex, alpha) {
  const value = String(hex).replace("#", "");
  const red = parseInt(value.slice(0, 2), 16);
  const green = parseInt(value.slice(2, 4), 16);
  const blue = parseInt(value.slice(4, 6), 16);
  return `rgba(${red}, ${green}, ${blue}, ${alpha})`;
}

function relativeLuminance(hex) {
  const value = String(hex).replace("#", "");
  const channels = [0, 2, 4].map((index) => parseInt(value.slice(index, index + 2), 16) / 255);
  const linear = channels.map((channel) =>
    channel <= 0.04045 ? channel / 12.92 : ((channel + 0.055) / 1.055) ** 2.4
  );
  return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2];
}

export function contrastRatio(first, second) {
  const firstLuminance = relativeLuminance(first);
  const secondLuminance = relativeLuminance(second);
  const lighter = Math.max(firstLuminance, secondLuminance);
  const darker = Math.min(firstLuminance, secondLuminance);
  return (lighter + 0.05) / (darker + 0.05);
}

export function paletteToCssVariables(palette) {
  const shades = palette.shades || DEFAULT_PALETTE.shades;
  const variables = {};
  SHADE_STEPS.forEach((step) => {
    variables[`--ramp-${step}`] = shades[step];
  });
  variables["--modal-scrim"] = hexToRgba(shades[900], 0.55);
  variables["--index-tag"] = hexToRgba(shades[800], 0.92);
  return variables;
}

export function applyPaletteToDocument(palette) {
  if (typeof document === "undefined") return;
  const normalised = normalisePalette(palette);
  const root = document.documentElement;
  Object.entries(paletteToCssVariables(normalised)).forEach(([name, value]) => {
    root.style.setProperty(name, value);
  });
  root.dataset.theme = normalised.slug;
  const themeMeta = document.querySelector('meta[name="theme-color"]');
  if (themeMeta) themeMeta.setAttribute("content", normalised.shades[800]);
}
