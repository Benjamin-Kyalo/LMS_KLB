import CONTENT_PACK from "./publicContentPack.json";

// Editable public-site content.
//
// Defaults live here so the public pages render before the first API response.
// Administrators change the same structure from the Appearance page, which
// saves to /api/theming/site-content/. Runtime overrides through
// window.__KLB_SITE_CONFIG__ remain supported for deployments.

// Section styles are allowlisted controls, not raw CSS. Empty values inherit
// the shipped design or active palette, so one section can change on its own.
export const STYLE_COLOUR_FIELDS = ["background", "text", "accent", "border"];
export const STYLE_CHOICES = {
  radius: [
    { value: "", label: "Inherit" },
    { value: "0px", label: "Square" },
    { value: "8px", label: "Small" },
    { value: "16px", label: "Medium" },
    { value: "24px", label: "Large" },
  ],
  spacing: [
    { value: "", label: "Inherit" },
    { value: "compact", label: "Compact" },
    { value: "comfortable", label: "Comfortable" },
    { value: "relaxed", label: "Relaxed" },
  ],
};
export const STYLE_FIELDS = [...STYLE_COLOUR_FIELDS, ...Object.keys(STYLE_CHOICES)];
export const STYLE_SECTION_IDS = [
  "header",
  "footer",
  "hero",
  "introduction",
  "capabilities",
  "library-feature",
  "teachers",
  "learners",
  "parents",
  "how-it-works",
  "closing-cta",
  "announcement",
  "quick-links",
  "trust",
  "workspaces",
  "routines",
  "access",
  "workspace-learning",
  "workspace-school",
  "workspace-publishing",
  "journey",
  "insights",
  "accessibility",
  "info",
  "spotlight",
  "roles",
  "support",
  "faq",
  "library",
  "login",
  "register",
  "invite",
  "tutor",
];

export const STYLE_FIELD_LABELS = {
  background: "Background colour",
  text: "Text colour",
  accent: "Accent colour",
  border: "Border colour",
  radius: "Corner style",
  spacing: "Section spacing",
};

function defaultSiteStyles() {
  return Object.fromEntries(STYLE_SECTION_IDS.map((section) => [
    section,
    Object.fromEntries(STYLE_FIELDS.map((field) => [field, ""])),
  ]));
}

export const DEFAULT_SITE_CONTENT = CONTENT_PACK;

export const DEFAULT_FOOTER = DEFAULT_SITE_CONTENT.footer;
export const DEFAULT_LIBRARY_CTA = {
  label: DEFAULT_SITE_CONTENT.hero.secondaryLabel,
  href: DEFAULT_SITE_CONTENT.hero.secondaryHref,
};

// Schema used by the admin editor. Every path maps to a value in the object
// above, so adding wording here does not require a new component.
export const SITE_CONTENT_GROUPS = [
  {
    id: "header",
    title: "Header and navigation",
    description: "The name, menu links and sign in label shown on public pages.",
    fields: [
      { path: "header.brand.mark", label: "Logo mark", type: "text" },
      { path: "header.brand.name", label: "Brand name", type: "text" },
      { path: "header.brand.subtitle", label: "Brand subtitle", type: "text" },
      { path: "header.links", label: "Main menu links", type: "objectList", itemFields: [
        { key: "label", label: "Link text", type: "text" },
        { key: "href", label: "Address", type: "text" },
      ] },
      { path: "header.signInLabel", label: "Sign in label", type: "text" },
      { path: "header.signInHref", label: "Sign in address", type: "text" },
      { path: "header.authLinks", label: "Registration page links", type: "objectList", itemFields: [
        { key: "label", label: "Link text", type: "text" },
        { key: "href", label: "Address", type: "text" },
      ] },
      { path: "header.adminLinks", label: "Invitation page links", type: "objectList", itemFields: [
        { key: "label", label: "Link text", type: "text" },
        { key: "href", label: "Address", type: "text" },
      ] },
    ],
  },
  {
    id: "footer",
    title: "Footer",
    description: "The wording and credits at the bottom of public pages.",
    fields: [
      { path: "footer.name", label: "Footer name", type: "text" },
      { path: "footer.tagline", label: "Footer introduction", type: "textarea" },
      { path: "footer.contactTitle", label: "Contact heading", type: "text" },
      { path: "footer.lines", label: "Footer lines", type: "lines", hint: "One line per row" },
      { path: "footer.exploreTitle", label: "Explore column heading", type: "text" },
      { path: "footer.exploreLinks", label: "Explore links", type: "objectList", itemFields: [
        { key: "label", label: "Link text", type: "text" },
        { key: "href", label: "Address", type: "text" },
      ] },
      { path: "footer.learnTitle", label: "Learn column heading", type: "text" },
      { path: "footer.learnLinks", label: "Learn links", type: "objectList", itemFields: [
        { key: "label", label: "Link text", type: "text" },
        { key: "href", label: "Address", type: "text" },
      ] },
      { path: "footer.credit.prefix", label: "Credit before link", type: "text" },
      { path: "footer.credit.linkLabel", label: "Credit link text", type: "text" },
      { path: "footer.credit.linkHref", label: "Credit link address", type: "text" },
      { path: "footer.credit.suffix", label: "Credit after link", type: "text" },
    ],
  },
  {
    id: "hero",
    title: "Homepage introduction",
    description: "The first message a visitor sees and the two buttons beneath it. Photos are managed in the Photos tab.",
    fields: [
      { path: "hero.overline", label: "Small heading", type: "text" },
      { path: "hero.eyebrow", label: "Hero badge", type: "text" },
      { path: "hero.title", label: "Main heading", type: "text" },
      { path: "hero.description", label: "Introduction", type: "textarea" },
      { path: "hero.highlights", label: "Hero highlights", type: "lines", hint: "One highlight per row" },
      { path: "hero.primaryLabel", label: "First button", type: "text" },
      { path: "hero.primaryHref", label: "First button address", type: "text" },
      { path: "hero.secondaryLabel", label: "Second button", type: "text" },
      { path: "hero.secondaryHref", label: "Second button address", type: "text" },
      { path: "hero.imageAlt", label: "Photo description", type: "text" },
      { path: "hero.imageCaption", label: "Photo caption", type: "text" },
    ],
  },
  {
    id: "home-sections",
    title: "Homepage sections",
    description: "The workspaces and progress panel on the homepage.",
    fields: [
      { path: "workspaces.overline", label: "Workspaces small heading", type: "text" },
      { path: "workspaces.title", label: "Workspaces heading", type: "text" },
      { path: "workspaces.cards", label: "Workspace cards", type: "objectList", itemFields: [
        { key: "key", label: "Style key", type: "text", readOnly: true },
        { key: "index", label: "Number", type: "text" },
        { key: "label", label: "Card label", type: "text" },
        { key: "title", label: "Card heading", type: "text" },
        { key: "copy", label: "Card text", type: "textarea" },
        { key: "imageAlt", label: "Photo description", type: "text" },
      ] },
      { path: "insights.overline", label: "Progress small heading", type: "text" },
      { path: "insights.title", label: "Progress heading", type: "text" },
      { path: "insights.description", label: "Progress introduction", type: "textarea" },
      { path: "insights.points", label: "Progress points", type: "objectList", itemFields: [
        { key: "title", label: "Point heading", type: "text" },
        { key: "copy", label: "Point text", type: "textarea" },
      ] },
      { path: "insights.chip", label: "Image label", type: "text" },
      { path: "insights.caption", label: "Image caption", type: "text" },
      { path: "insights.imageAlt", label: "Photo description", type: "text" },
    ],
  },
  {
    id: "home-journey",
    title: "Homepage journey and spotlight",
    description: "The trust strip, three-step guide, library spotlight and questions on the homepage.",
    fields: [
      { path: "trust.overline", label: "Trust small heading", type: "text" },
      { path: "trust.title", label: "Trust heading", type: "text" },
      { path: "trust.items", label: "Trust points", type: "objectList", itemFields: [
        { key: "key", label: "Style key", type: "text", readOnly: true },
        { key: "title", label: "Point heading", type: "text" },
        { key: "copy", label: "Point text", type: "textarea" },
      ] },
      { path: "journey.overline", label: "Steps small heading", type: "text" },
      { path: "journey.title", label: "Steps heading", type: "text" },
      { path: "journey.description", label: "Steps introduction", type: "textarea" },
      { path: "journey.steps", label: "Getting started steps", type: "objectList", itemFields: [
        { key: "index", label: "Number", type: "text" },
        { key: "title", label: "Step heading", type: "text" },
        { key: "copy", label: "Step text", type: "textarea" },
      ] },
      { path: "journey.checklistTitle", label: "Ready checklist heading", type: "text" },
      { path: "journey.checklist", label: "Ready checklist", type: "lines", hint: "One item per row" },
      { path: "spotlight.overline", label: "Spotlight small heading", type: "text" },
      { path: "spotlight.title", label: "Spotlight heading", type: "text" },
      { path: "spotlight.description", label: "Spotlight introduction", type: "textarea" },
      { path: "spotlight.actionLabel", label: "Spotlight button", type: "text" },
      { path: "spotlight.actionHref", label: "Spotlight button address", type: "text" },
      { path: "spotlight.imageAlt", label: "Spotlight photo description", type: "text" },
      { path: "spotlight.imageCaption", label: "Spotlight photo caption", type: "text" },
      { path: "faq.overline", label: "Questions small heading", type: "text" },
      { path: "faq.title", label: "Questions heading", type: "text" },
      { path: "faq.description", label: "Questions introduction", type: "textarea" },
      { path: "faq.items", label: "Questions", type: "objectList", itemFields: [
        { key: "question", label: "Question", type: "text" },
        { key: "answer", label: "Answer", type: "textarea" },
      ] },
    ],
  },
  {
    id: "home-extras",
    title: "Homepage extras",
    description: "The announcement, quick links, daily routines, access guide, usability notes and support callout.",
    fields: [
      { path: "announcement.text", label: "Announcement text", type: "textarea" },
      { path: "announcement.actionLabel", label: "Announcement button", type: "text" },
      { path: "announcement.actionHref", label: "Announcement button address", type: "text" },
      { path: "quickLinks.title", label: "Quick links label", type: "text" },
      { path: "quickLinks.links", label: "Quick links", type: "objectList", itemFields: [
        { key: "label", label: "Link text", type: "text" },
        { key: "href", label: "Address", type: "text" },
      ] },
      { path: "routines.overline", label: "Routines small heading", type: "text" },
      { path: "routines.title", label: "Routines heading", type: "text" },
      { path: "routines.description", label: "Routines introduction", type: "textarea" },
      { path: "routines.items", label: "Daily routines", type: "objectList", itemFields: [
        { key: "key", label: "Style key", type: "text", readOnly: true },
        { key: "title", label: "Routine heading", type: "text" },
        { key: "copy", label: "Routine text", type: "textarea" },
      ] },
      { path: "access.overline", label: "Access small heading", type: "text" },
      { path: "access.title", label: "Access heading", type: "text" },
      { path: "access.description", label: "Access introduction", type: "textarea" },
      { path: "access.columns", label: "Table headings", type: "lines", hint: "One heading per row" },
      { path: "access.rows", label: "Access rows", type: "objectList", itemFields: [
        { key: "role", label: "Role", type: "text" },
        { key: "sees", label: "What they see", type: "textarea" },
        { key: "actions", label: "What they can do", type: "textarea" },
      ] },
      { path: "accessibility.overline", label: "Usability small heading", type: "text" },
      { path: "accessibility.title", label: "Usability heading", type: "text" },
      { path: "accessibility.items", label: "Usability points", type: "objectList", itemFields: [
        { key: "key", label: "Style key", type: "text", readOnly: true },
        { key: "title", label: "Point heading", type: "text" },
        { key: "copy", label: "Point text", type: "textarea" },
      ] },
      { path: "support.overline", label: "Support small heading", type: "text" },
      { path: "support.title", label: "Support heading", type: "text" },
      { path: "support.description", label: "Support introduction", type: "textarea" },
      { path: "support.primaryLabel", label: "First button", type: "text" },
      { path: "support.primaryHref", label: "First button address", type: "text" },
      { path: "support.secondaryLabel", label: "Second button", type: "text" },
      { path: "support.secondaryHref", label: "Second button address", type: "text" },
    ],
  },
  {
    id: "roles",
    title: "Where do you fit?",
    description: "The role cards and the access preview shown under each role.",
    fields: [
      { path: "roles.overline", label: "Small heading", type: "text" },
      { path: "roles.title", label: "Section heading", type: "text" },
      { path: "roles.description", label: "Section introduction", type: "textarea" },
      { path: "roles.previewLabel", label: "Preview label", type: "text" },
      { path: "roles.rightsTitle", label: "First list heading", type: "text" },
      { path: "roles.contentTitle", label: "Second list heading", type: "text" },
      { path: "roles.cards", label: "Role cards", type: "objectList", itemFields: [
        { key: "key", label: "Role key", type: "text", readOnly: true },
        { key: "label", label: "Button label", type: "text" },
        { key: "title", label: "Card heading", type: "text" },
        { key: "copy", label: "Card text", type: "textarea" },
        { key: "to", label: "Card link", type: "text" },
        { key: "action", label: "Button text", type: "text" },
        { key: "rights", label: "What you can do", type: "lines" },
        { key: "content", label: "What you will see", type: "lines" },
      ] },
    ],
  },
  {
    id: "library",
    title: "Library",
    description: "The headings and introductions on the public book and resource library.",
    fields: [
      { path: "library.overline", label: "Small heading", type: "text" },
      { path: "library.title", label: "Page heading", type: "text" },
      { path: "library.description", label: "Introduction", type: "textarea" },
      { path: "library.booksOverline", label: "Books small heading", type: "text" },
      { path: "library.booksTitle", label: "Books heading", type: "text" },
      { path: "library.booksDescription", label: "Books introduction", type: "textarea" },
      { path: "library.resourcesOverline", label: "Resources small heading", type: "text" },
      { path: "library.resourcesTitle", label: "Resources heading", type: "text" },
      { path: "library.resourcesDescription", label: "Resources introduction", type: "textarea" },
    ],
  },
  {
    id: "auth",
    title: "Sign in and registration",
    description: "The words visitors see on the sign in, registration and invitation pages.",
    fields: [
      { path: "auth.login.publicHeading", label: "Sign in heading", type: "text" },
      { path: "auth.login.adminHeading", label: "Admin sign in heading", type: "text" },
      { path: "auth.login.storyCopy", label: "Sign in introduction", type: "textarea" },
      { path: "auth.login.footnote", label: "Sign in footnote", type: "text" },
      { path: "auth.login.publicIntro", label: "Sign in form note", type: "textarea" },
      { path: "auth.login.adminIntro", label: "Admin sign in form note", type: "textarea" },
      { path: "auth.register.overline", label: "Registration small heading", type: "text" },
      { path: "auth.register.heading", label: "Registration heading", type: "text" },
      { path: "auth.register.copy", label: "Registration introduction", type: "textarea" },
      { path: "auth.register.notice", label: "Registration note", type: "textarea" },
      { path: "auth.register.steps", label: "Registration steps", type: "lines" },
      { path: "auth.register.roleOptions", label: "Account types", type: "objectList", itemFields: [
        { key: "value", label: "Role value", type: "text", readOnly: true },
        { key: "label", label: "Role name", type: "text" },
        { key: "note", label: "Short note", type: "text" },
      ] },
      { path: "auth.admin.overline", label: "Invitation small heading", type: "text" },
      { path: "auth.admin.heading", label: "Invitation heading", type: "text" },
      { path: "auth.admin.copy", label: "Invitation introduction", type: "textarea" },
      { path: "auth.admin.warning", label: "Invitation warning", type: "textarea" },
    ],
  },
  {
    id: "photos",
    title: "Photos",
    description: "Replace, remove or restore the managed public and portal photographs. Uploads publish immediately.",
    fields: [
      { path: "hero.imageSrc", label: "Homepage hero photo", type: "image", slot: "hero", hint: "Shown on the homepage hero" },
      { path: "workspaces.cards.0.image", label: "Learning workspace photo", type: "image", slot: "workspace-learning", hint: "Shown on the first homepage workspace card" },
      { path: "workspaces.cards.1.image", label: "School day photo", type: "image", slot: "workspace-school", hint: "Shown on the second homepage workspace card" },
      { path: "workspaces.cards.2.image", label: "Digital publishing photo", type: "image", slot: "workspace-publishing", hint: "Shown on the third homepage workspace card" },
      { path: "insights.imageSrc", label: "Progress insight photo", type: "image", slot: "insights", hint: "Shown in the homepage progress panel" },
      { path: "spotlight.imageSrc", label: "Library spotlight photo", type: "image", slot: "spotlight", hint: "Shown in the homepage library spotlight" },
      { path: "auth.login.storyImageSrc", label: "Sign-in story photo", type: "image", slot: "login", hint: "Shown behind the sign-in story" },
      { path: "auth.register.storyImageSrc", label: "Registration story photo", type: "image", slot: "register", hint: "Shown on the registration page" },
      { path: "portal.tutorImageSrc", label: "Portal tutor photo", type: "image", slot: "tutor", hint: "Shown in the learner and guardian tutor workspace" },
    ],
  },
  {
    id: "app",
    title: "Signed in areas",
    description: "Brand labels for the staff and learner areas, plus portal menu names.",
    fields: [
      { path: "portal.tutorImageAlt", label: "Portal tutor photo description", type: "text" },
      { path: "app.adminBrand", label: "Staff area brand", type: "text" },
      { path: "app.portalBrand", label: "Learner area brand", type: "text" },
      { path: "app.portalNav", label: "Portal menu labels", type: "objectList", itemFields: [
        { key: "key", label: "Menu key", type: "text", readOnly: true },
        { key: "label", label: "Menu label", type: "text" },
      ] },
    ],
  },
  {
    id: "content-pack-home",
    title: "Homepage content pack",
    description: "The exact KLB Elimu homepage wording, cards, buttons and steps.",
    fields: [
      { path: "hero.title", label: "Hero heading", type: "text" },
      { path: "hero.description", label: "Hero introduction", type: "textarea" },
      { path: "hero.supportingStatement", label: "Hero supporting statement", type: "text" },
      { path: "introduction.title", label: "Introduction heading", type: "text" },
      { path: "introduction.paragraphs", label: "Introduction paragraphs", type: "lines" },
      { path: "capabilities.title", label: "What you can do heading", type: "text" },
      { path: "capabilities.cards", label: "What you can do cards", type: "objectList", itemFields: [
        { key: "title", label: "Card title", type: "text" },
        { key: "copy", label: "Card description", type: "textarea" },
        { key: "actionLabel", label: "Button label", type: "text" },
        { key: "actionHref", label: "Button address", type: "text" },
      ] },
      { path: "libraryFeature.title", label: "Digital library heading", type: "text" },
      { path: "libraryFeature.paragraphs", label: "Digital library paragraphs", type: "lines" },
      { path: "audiences.teachers.title", label: "Teacher section heading", type: "text" },
      { path: "audiences.teachers.paragraphs", label: "Teacher paragraphs", type: "lines" },
      { path: "audiences.learners.title", label: "Learner section heading", type: "text" },
      { path: "audiences.learners.paragraphs", label: "Learner paragraphs", type: "lines" },
      { path: "audiences.parents.title", label: "Parent section heading", type: "text" },
      { path: "audiences.parents.paragraphs", label: "Parent paragraphs", type: "lines" },
      { path: "steps.title", label: "How it works heading", type: "text" },
      { path: "steps.steps", label: "Getting started steps", type: "objectList", itemFields: [
        { key: "title", label: "Step title", type: "text" },
        { key: "copy", label: "Step description", type: "textarea" },
      ] },
      { path: "closingCta.title", label: "Closing call to action heading", type: "text" },
      { path: "closingCta.copy", label: "Closing call to action text", type: "textarea" },
    ],
  },
  {
    id: "content-pack-pages",
    title: "Public information pages",
    description: "About, role, library, help, contact, questions and policy pages.",
    fields: [
      { path: "publicPages.about.introduction", label: "About introduction", type: "lines" },
      { path: "publicPages.about.brandMessage", label: "Central brand message", type: "lines" },
      { path: "publicPages.about.approach", label: "Our approach", type: "objectList", itemFields: [
        { key: "title", label: "Heading", type: "text" },
        { key: "copy", label: "Description", type: "textarea" },
      ] },
      { path: "publicPages.schools.benefits", label: "School benefits", type: "objectList", itemFields: [
        { key: "title", label: "Benefit", type: "text" },
        { key: "copy", label: "Description", type: "textarea" },
      ] },
      { path: "publicPages.teachers.features", label: "Teacher features", type: "lines" },
      { path: "publicPages.learners.features", label: "Learner activities", type: "lines" },
      { path: "publicPages.parents.features", label: "Parent features", type: "lines" },
      { path: "publicPages.library.categories", label: "Library categories", type: "lines" },
      { path: "publicPages.library.searchPlaceholder", label: "Library search placeholder", type: "text" },
      { path: "publicPages.library.filters", label: "Library filters", type: "lines" },
      { path: "publicPages.library.accessLabels", label: "Access labels", type: "lines" },
      { path: "publicPages.help.categories", label: "Help categories", type: "objectList", itemFields: [
        { key: "title", label: "Category", type: "text" },
        { key: "items", label: "Articles", type: "lines" },
      ] },
      { path: "publicPages.faq.groups", label: "Questions and answers", type: "objectList", itemFields: [
        { key: "title", label: "Group", type: "text" },
        { key: "items", label: "Questions", type: "text" },
      ] },
      { path: "publicPages.contact.categories", label: "Enquiry categories", type: "lines" },
      { path: "publicPages.contact.confirmation", label: "Enquiry confirmation", type: "textarea" },
      { path: "publicPages.privacy.principles", label: "Privacy principles", type: "lines" },
    ],
  },
  {
    id: "shared-messages",
    title: "Shared application messages",
    description: "Empty states, loading notices, errors, confirmations and notification wording.",
    fields: [
      { path: "messages.pageIntroductions.overview", label: "Overview introduction", type: "text" },
      { path: "messages.pageIntroductions.records", label: "Records introduction", type: "text" },
      { path: "messages.pageIntroductions.reports", label: "Reports introduction", type: "text" },
      { path: "messages.pageIntroductions.settings", label: "Settings introduction", type: "text" },
      { path: "messages.pageIntroductions.notifications", label: "Notifications introduction", type: "text" },
      { path: "messages.searchPlaceholders.schools", label: "School search", type: "text" },
      { path: "messages.searchPlaceholders.learners", label: "Learner search", type: "text" },
      { path: "messages.searchPlaceholders.teachers", label: "Teacher search", type: "text" },
      { path: "messages.searchPlaceholders.resources", label: "Resource search", type: "text" },
      { path: "messages.searchPlaceholders.lessons", label: "Lesson search", type: "text" },
      { path: "messages.searchPlaceholders.announcements", label: "Announcement search", type: "text" },
      { path: "messages.searchPlaceholders.transactions", label: "Transaction search", type: "text" },
      { path: "messages.globalActions", label: "Global action labels", type: "lines" },
      { path: "messages.loading", label: "Loading messages", type: "lines" },
      { path: "messages.errors.somethingWrong", label: "General error", type: "textarea" },
      { path: "messages.errors.noPermission", label: "Permission error", type: "text" },
      { path: "messages.errors.sessionExpired", label: "Session error", type: "text" },
      { path: "messages.confirmations.deleteRecord", label: "Delete confirmation", type: "textarea" },
      { path: "messages.notifications.newLesson", label: "New lesson notification", type: "textarea" },
      { path: "messages.notifications.schoolAnnouncement", label: "School announcement notification", type: "textarea" },
      { path: "messages.notifications.securityNotice", label: "Security notification", type: "textarea" },
    ],
  },
];

const STYLE_SECTIONS = [
  { id: "header", title: "Public header", description: "The bar with the brand, menu and sign in link on public pages." },
  { id: "footer", title: "Public footer", description: "The closing strip on public pages." },
  { id: "hero", title: "Homepage hero", description: "The first panel and its two buttons." },
  { id: "introduction", title: "Homepage introduction", description: "The connected-learning explanation beneath the hero." },
  { id: "capabilities", title: "What you can do", description: "The four school, teacher, learner and parent cards." },
  { id: "library-feature", title: "Digital library feature", description: "The section introducing the KLB Digital Library." },
  { id: "teachers", title: "Teacher audience", description: "The teacher section on the homepage." },
  { id: "learners", title: "Learner audience", description: "The learner section on the homepage." },
  { id: "parents", title: "Parent audience", description: "The parent section on the homepage." },
  { id: "how-it-works", title: "Getting started steps", description: "The five-step setup guide on the homepage." },
  { id: "closing-cta", title: "Closing invitation", description: "The final invitation before the questions." },
  { id: "announcement", title: "Homepage announcement", description: "The short notice near the top of the homepage." },
  { id: "quick-links", title: "Quick links", description: "The on-page link ribbon under the header." },
  { id: "trust", title: "Homepage trust strip", description: "The three short value points under the hero." },
  { id: "workspaces", title: "Workspace introduction", description: "The heading above the three workspace cards." },
  { id: "routines", title: "Daily routines", description: "The three everyday routine cards." },
  { id: "access", title: "Access guide", description: "The who-sees-what table." },
  { id: "workspace-learning", title: "Learning workspace", description: "The first workspace card only." },
  { id: "workspace-school", title: "School day", description: "The second workspace card only." },
  { id: "workspace-publishing", title: "Digital publishing", description: "The third workspace card only." },
  { id: "journey", title: "Getting started", description: "The three-step guide on the homepage." },
  { id: "insights", title: "Progress insight", description: "The progress points and photograph on the homepage." },
  { id: "accessibility", title: "Usability commitment", description: "The keyboard, motion and connection notes." },
  { id: "info", title: "Public information pages", description: "The About, role, help, contact and policy pages." },
  { id: "spotlight", title: "Library spotlight", description: "The library invitation and photograph on the homepage." },
  { id: "roles", title: "Where do you fit?", description: "The role selector and access preview on the homepage." },
  { id: "support", title: "Support callout", description: "The help invitation before the questions." },
  { id: "faq", title: "Common questions", description: "The expandable questions near the end of the homepage." },
  { id: "library", title: "Library", description: "The public book and resource library page." },
  { id: "login", title: "Sign-in story", description: "The story panel beside the sign in form." },
  { id: "register", title: "Registration story", description: "The story panel on the registration page." },
  { id: "invite", title: "Invitation story", description: "The story panel on the administrator invitation page." },
  { id: "tutor", title: "Portal tutor", description: "The tutor introduction in the learner portal." },
];

export const SITE_STYLE_GROUPS = STYLE_SECTIONS.map((section) => ({
  id: section.id,
  title: section.title,
  description: `${section.description} Only this section changes.`,
  fields: STYLE_FIELDS.map((field) => ({
    path: `styles.${section.id}.${field}`,
    label: STYLE_FIELD_LABELS[field],
    type: STYLE_COLOUR_FIELDS.includes(field) ? "colour" : "choice",
    hint: STYLE_COLOUR_FIELDS.includes(field)
      ? "Leave empty to inherit the active palette"
      : undefined,
    choices: STYLE_CHOICES[field],
  })),
}));

const RETIRED_ROLE_KEYS = new Set(["content"]);

function withoutRetiredRoleCards(value) {
  if (!value || !Array.isArray(value.cards)) return value;
  const cards = value.cards.filter((card) => (
    !RETIRED_ROLE_KEYS.has(card?.key)
    && !/content\s+managers?/i.test(card?.label || "")
  ));
  return cards.length === value.cards.length ? value : { ...value, cards };
}

export function mergeContent(base, override) {
  if (Array.isArray(base)) {
    return Array.isArray(override) ? override : base.map((item) => mergeContent(item, null));
  }
  if (base && typeof base === "object") {
    const result = Object.fromEntries(
      Object.entries(base).map(([key, value]) => [key, mergeContent(value, null)]),
    );
    if (override && typeof override === "object" && !Array.isArray(override)) {
      Object.entries(override).forEach(([key, value]) => {
        if (key in base) result[key] = mergeContent(base[key], value);
      });
    }
    return withoutRetiredRoleCards(result);
  }
  return override !== null && override !== undefined && typeof override === typeof base
    ? override
    : base;
}

function clone(value) {
  if (Array.isArray(value)) return value.map(clone);
  if (value && typeof value === "object") {
    return Object.fromEntries(Object.entries(value).map(([key, item]) => [key, clone(item)]));
  }
  return value;
}

function runtimeOverrides() {
  if (typeof window === "undefined") return {};
  const config = window.__KLB_SITE_CONFIG__ || {};
  const overrides = clone(config.content || {});
  if (config.footer) {
    overrides.footer = { ...(overrides.footer || {}), ...clone(config.footer) };
  }
  if (config.libraryCta) {
    overrides.hero = {
      ...(overrides.hero || {}),
      secondaryLabel: config.libraryCta.label,
      secondaryHref: config.libraryCta.href,
    };
  }
  if (config.rolePreviews) {
    const cards = (overrides.roles?.cards || DEFAULT_SITE_CONTENT.roles.cards).map((card) => {
      const preview = config.rolePreviews[card.key];
      return preview ? { ...card, rights: preview.rights, content: preview.content } : card;
    });
    overrides.roles = { ...(overrides.roles || {}), cards };
  }
  return overrides;
}

export function getSiteContent() {
  return mergeContent(DEFAULT_SITE_CONTENT, runtimeOverrides());
}

// Legacy helpers keep older callers and tests working while all data now
// comes from the single editable document.
export function getFooterContent() {
  return getSiteContent().footer;
}

export function getLibraryCta() {
  const { secondaryLabel, secondaryHref } = getSiteContent().hero;
  return { label: secondaryLabel, href: secondaryHref };
}

export function getRolePreview(key) {
  const card = getSiteContent().roles.cards.find((item) => item.key === key);
  return card ? { rights: card.rights, content: card.content } : { rights: [], content: [] };
}

export function getIn(object, path) {
  return path.split(".").reduce((value, key) => value?.[key], object);
}

export function setIn(object, path, value) {
  const next = Array.isArray(object) ? [...object] : { ...object };
  const [key, ...rest] = path.split(".");
  if (!rest.length) {
    next[key] = value;
    return next;
  }
  next[key] = setIn(next[key] || {}, rest.join("."), value);
  return next;
}
