/* Helpers for administrator-managed, section-scoped appearance overrides.
 *
 * Values come from the same site-content document as the public wording. Only
 * allowlisted colours, radii and spacing scales become CSS custom properties,
 * and each property is set on one section element. No raw CSS is accepted.
 */
import { useSiteContent } from "../context/SiteContentContext";
import { HEX_COLOUR, MIN_TEXT_CONTRAST, contrastRatio } from "./palette";
import {
  STYLE_CHOICES, STYLE_COLOUR_FIELDS, STYLE_FIELD_LABELS, STYLE_FIELDS,
  STYLE_SECTION_IDS,
} from "../config/publicSite";

const SPACING_SCALE = {
  compact: "0.8",
  comfortable: "1",
  relaxed: "1.2",
};

function allowedChoice(field, value) {
  const choices = STYLE_CHOICES[field] || [];
  return choices.some((choice) => choice.value === value);
}

export function sectionStyleVars(styles, sectionId) {
  const section = styles?.[sectionId] || {};
  const vars = {};

  if (HEX_COLOUR.test(section.background || "")) vars["--section-bg"] = section.background;
  if (HEX_COLOUR.test(section.text || "")) vars["--section-ink"] = section.text;
  if (HEX_COLOUR.test(section.accent || "")) vars["--section-accent"] = section.accent;
  if (HEX_COLOUR.test(section.border || "")) vars["--section-border"] = section.border;
  if (allowedChoice("radius", section.radius)) vars["--section-radius"] = section.radius;
  if (allowedChoice("spacing", section.spacing)) {
    vars["--section-pad-scale"] = SPACING_SCALE[section.spacing] || "1";
  }
  return vars;
}

export function firstStyleError(styles) {
  for (const section of STYLE_SECTION_IDS) {
    const sectionStyles = styles?.[section] || {};
    for (const field of STYLE_FIELDS) {
      const value = sectionStyles[field] || "";
      const label = STYLE_FIELD_LABELS[field] || field;
      if (STYLE_COLOUR_FIELDS.includes(field)) {
        if (value && !HEX_COLOUR.test(value)) {
          return `${label}: enter a six-digit hex colour such as #FFFFFF.`;
        }
      } else if (!allowedChoice(field, value)) {
        return `${label}: choose one of the supplied options.`;
      }
    }
    const background = sectionStyles.background;
    const text = sectionStyles.text;
    if (HEX_COLOUR.test(background || "") && HEX_COLOUR.test(text || "")
      && contrastRatio(background, text) < MIN_TEXT_CONTRAST) {
      return "Text colour needs at least 4.5:1 contrast with the section background.";
    }
  }
  return "";
}

export function useSectionStyle(sectionId) {
  const { content } = useSiteContent();
  return sectionStyleVars(content.styles, sectionId);
}
