import { describe, expect, it } from "vitest";
import {
  DEFAULT_SITE_CONTENT, STYLE_SECTION_IDS, SITE_STYLE_GROUPS, mergeContent,
} from "./publicSite";

describe("editable site content", () => {
  it("keeps only the three supported role previews", () => {
    expect(DEFAULT_SITE_CONTENT.roles.cards.map((card) => card.key)).toEqual([
      "learners",
      "guardians",
      "teachers",
    ]);
  });

  it("cannot restore the retired content manager preview from cached overrides", () => {
    const cached = {
      roles: {
        cards: [
          ...DEFAULT_SITE_CONTENT.roles.cards,
          {
            key: "content",
            label: "Content managers",
            title: "Curate learning resources",
            rights: [],
            content: [],
          },
        ],
      },
    };

    const merged = mergeContent(DEFAULT_SITE_CONTENT, cached);
    expect(merged.roles.cards.map((card) => card.key)).toEqual([
      "learners",
      "guardians",
      "teachers",
    ]);
  });

  it("exposes the same allowlisted style sections in defaults and the editor", () => {
    expect(Object.keys(DEFAULT_SITE_CONTENT.styles)).toEqual(STYLE_SECTION_IDS);
    expect(SITE_STYLE_GROUPS.map((group) => group.id)).toEqual(STYLE_SECTION_IDS);
    expect(DEFAULT_SITE_CONTENT.styles.hero).toEqual({
      background: "",
      text: "",
      accent: "",
      border: "",
      radius: "",
      spacing: "",
    });
  });
});
