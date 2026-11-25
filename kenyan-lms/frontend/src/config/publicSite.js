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
  "workspaces",
  "workspace-learning",
  "workspace-school",
  "workspace-publishing",
  "insights",
  "roles",
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

export const DEFAULT_SITE_CONTENT = {
  header: {
    brand: {
      mark: "KLB",
      name: "Digital Learning Ecosystem",
      subtitle: "Kenya Literature Bureau",
    },
    links: [
      { label: "Platform", href: "/#workspaces" },
      { label: "Library", href: "/library" },
      { label: "Who it's for", href: "/#roles" },
    ],
    signInLabel: "Sign in",
    signInHref: "/login",
    authLinks: [{ label: "Sign in", href: "/login" }],
    adminLinks: [
      { label: "Admin sign in", href: "/admin/login" },
      { label: "User registration", href: "/register" },
    ],
  },
  footer: {
    name: "KLB Digital Learning Ecosystem",
    lines: [
      "Kenya Literature Bureau, Nairobi, Kenya",
      "Access help: contact your school administrator",
      "Learning management, school information and digital publishing",
    ],
    credit: {
      prefix: "Photography via ",
      linkLabel: "Unsplash",
      linkHref: "https://unsplash.com/license",
      suffix: " and illustration by KLB",
    },
  },
  hero: {
    overline: "One connected platform",
    title: "Teaching and learning, connected for Kenyan schools.",
    description:
      "A single KLB ecosystem for lessons, school records and digital textbooks, built for competency based learning.",
    primaryLabel: "Create an account",
    primaryHref: "/register",
    secondaryLabel: "Browse the library",
    secondaryHref: "/library",
    imageSrc: "/images/hero-community.png",
    imageAlt: "Students and teachers in a school learning space",
    imageCaption: "One school record, with the right view for every role.",
  },
  workspaces: {
    overline: "What the platform does",
    title: "Three connected ways to use KLB",
    cards: [
      {
        key: "learning",
        label: "Learning workspace",
        index: "01",
        title: "Learning in one place",
        copy: "Courses, assignments, quizzes and a textbook library share the same school records.",
        image: "/images/workspace-skill.jpg",
        imageAlt: "Learner practising a school skill",
      },
      {
        key: "school",
        label: "School day",
        index: "02",
        title: "Records that stay connected",
        copy: "Attendance, timetables, assessments and class records share one school database with the learner portal.",
        image: "/images/workspace-education.jpg",
        imageAlt: "Education and school records in use",
      },
      {
        key: "publishing",
        label: "Digital publishing",
        index: "03",
        title: "Curriculum tied to the classroom",
        copy: "Textbooks, chapters, resources and competency based outcomes stay linked to the lessons teachers use.",
        image: "/images/digital-library.jpg",
        imageAlt: "Library shelves holding reference books",
      },
    ],
  },
  insights: {
    overline: "Progress and insight",
    title: "A clearer picture of learning",
    description:
      "School information is most useful when it is easy to read. The same records used for daily work also feed the dashboards and reports that teachers, managers and guardians rely on.",
    points: [
      { title: "Attendance", copy: "Daily registers stay linked to the class and learner record." },
      { title: "Assessments", copy: "Marks and feedback sit beside the courses they assess." },
      { title: "Course activity", copy: "Lessons, resources and submissions share one academic timeline." },
    ],
    chip: "Attendance, assessments and courses",
    caption: "Illustrative view of records already captured by the school.",
    imageSrc: "/images/insight-success.jpg",
    imageAlt: "A learner celebrating academic progress",
  },
  roles: {
    overline: "Choose your path",
    title: "Where do you fit?",
    description:
      "Pick the area that sounds like you. We will show what you can open, what you can do and where to start.",
    previewLabel: "Access preview",
    rightsTitle: "What you can do",
    contentTitle: "What you will see",
    cards: [
      {
        key: "learners",
        label: "Students & learners",
        title: "Learn at your own pace",
        copy: "Open your courses, assignments, quizzes and digital books, all linked to your school record.",
        to: "/login?role=LEARNER",
        action: "Learner workspace",
        rights: [
          "Work only inside your own learner record",
          "Open your courses, assignments and quizzes",
          "Track feedback and results in one place",
          "Read your results, progress report and messages",
        ],
        content: [
          "My courses and textbook library",
          "Assignments and quizzes",
          "Learning resources",
          "Progress report and school messages",
        ],
      },
      {
        key: "guardians",
        label: "Parents & guardians",
        title: "Stay close to progress",
        copy: "See attendance, results and school messages for the learners linked to you, with clear updates that are easy to follow.",
        to: "/login?role=GUARDIAN",
        action: "Guardian workspace",
        rights: [
          "View progress for the learners linked to you",
          "Read attendance, results and school messages",
          "Update your own guardian profile",
          "No staff or administration permissions",
        ],
        content: [
          "Linked learner progress",
          "Attendance and assessment results",
          "School messages",
          "Guardian profile",
        ],
      },
      {
        key: "teachers",
        label: "Teachers",
        title: "Plan, teach and assess",
        copy: "Plan lessons, keep class records, mark work and use curriculum tools in one calm workspace.",
        to: "/login?role=TEACHER",
        action: "Teacher workspace",
        rights: [
          "Prepare courses, lessons, assignments and quizzes",
          "Record attendance and manage class results",
          "View learner records for your classes",
          "No user administration or staff appointment permissions",
        ],
        content: [
          "Courses, modules and lessons",
          "Assignments, submissions and question bank",
          "Timetable, attendance and exams",
          "Learners and curriculum tools",
        ],
      },
    ],
  },
  library: {
    overline: "Public library",
    title: "Find books and learning resources",
    description:
      "Browse the KLB catalogue for published titles and learning resources. Open a book preview or filter resources by level, learning area, collection and keyword.",
    booksOverline: "Textbook catalogue",
    booksTitle: "Books to explore",
    booksDescription:
      "See published titles from the catalogue. Full book access depends on your school licence and is managed by your administrator.",
    resourcesOverline: "Learning resources",
    resourcesTitle: "Find learning resources",
    resourcesDescription:
      "Browse published resources by level, learning area, collection and keyword. Start with a textbook topic, a document or a curated collection.",
  },
  auth: {
    login: {
      publicHeading: "One platform for teaching, records and textbooks.",
      adminHeading: "One administration portal for the whole school.",
      storyCopy:
        "Built for Kenyan schools with competency based learning, school administration and a digital publishing library. It works well on modest connections.",
      storyImageSrc: "/images/signin-time.jpg",
      footnote: "Kenya Literature Bureau, Digital Education",
      publicIntro: "Use the account your school administrator created, or register below.",
      adminIntro: "Use an administrator account issued by your institution or platform administrator.",
    },
    register: {
      overline: "Create your account",
      heading: "Choose your role, then fill in only what applies.",
      copy: "Learner and guardian accounts are ready to use straight away. Teacher accounts wait for approval by the school. Administrator accounts need a secure invitation and are never created through this form.",
      notice: "The school database is shared, so accounts created here appear in the administration portal for the same institution.",
      storyImageSrc: "/images/register-learn.jpg",
      steps: ["Choose account type", "Add your details", "Complete your role setup"],
      roleOptions: [
        { value: "LEARNER", label: "Learner", note: "Courses, assignments and results" },
        { value: "GUARDIAN", label: "Parent / Guardian", note: "Follow a learner's progress" },
        { value: "TEACHER", label: "Teacher", note: "Created pending school approval" },
      ],
    },
    admin: {
      overline: "Administration portal",
      heading: "Administrator accounts use invitations only.",
      copy: "A platform or school administrator must issue a secure, single use invitation token. The token fixes the role and school. This form cannot grant administrator privileges by itself. Each token works once and expires after seven days.",
      warning: "Do not share invitation tokens or passwords over unsecured channels. If you do not have a token, contact your platform administrator.",
    },
  },
  portal: {
    tutorImageSrc: "/images/tutor-brain.jpg",
    tutorImageAlt: "A learner thinking through a problem",
  },
  app: {
    adminBrand: "KLB Learning",
    portalBrand: "KLB Learning",
    portalNav: [
      { key: "home", label: "Home" },
      { key: "courses", label: "My courses" },
      { key: "textbooks", label: "Textbook library" },
      { key: "resources", label: "Resources" },
      { key: "documents", label: "Documents" },
      { key: "assignments", label: "Assignments" },
      { key: "quizzes", label: "Quizzes" },
      { key: "reports", label: "Progress report" },
      { key: "remediation", label: "My support tasks" },
      { key: "fees", label: "Fees" },
      { key: "tutor", label: "Ask the tutor" },
      { key: "communications", label: "Messages" },
      { key: "profile", label: "My profile" },
    ],
  },
  styles: defaultSiteStyles(),
};

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
      { path: "footer.lines", label: "Footer lines", type: "lines", hint: "One line per row" },
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
      { path: "hero.title", label: "Main heading", type: "text" },
      { path: "hero.description", label: "Introduction", type: "textarea" },
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
];

const STYLE_SECTIONS = [
  { id: "header", title: "Public header", description: "The bar with the brand, menu and sign in link on public pages." },
  { id: "footer", title: "Public footer", description: "The closing strip on public pages." },
  { id: "hero", title: "Homepage hero", description: "The first panel and its two buttons." },
  { id: "workspaces", title: "Workspace introduction", description: "The heading above the three workspace cards." },
  { id: "workspace-learning", title: "Learning workspace", description: "The first workspace card only." },
  { id: "workspace-school", title: "School day", description: "The second workspace card only." },
  { id: "workspace-publishing", title: "Digital publishing", description: "The third workspace card only." },
  { id: "insights", title: "Progress insight", description: "The progress points and photograph on the homepage." },
  { id: "roles", title: "Where do you fit?", description: "The role selector and access preview on the homepage." },
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
