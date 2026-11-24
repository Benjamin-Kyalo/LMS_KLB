// Editable public-site content.
//
// Change the values below to customise the public footer and the access preview
// shown when a visitor selects a role on the homepage. No homepage component
// needs to change.
//
// A deployment can also override these values at runtime by setting
// window.__KLB_SITE_CONFIG__ before the React app mounts, for example in
// frontend/index.html. Shape:
// {
//   footer: { name, lines: [], credit: { prefix, linkLabel, linkHref, suffix } },
//   rolePreviews: { learners: { rights: [], content: [] }, ... }
// }
// Any omitted field keeps the default value below.

export const DEFAULT_FOOTER = {
  name: "KLB Digital Learning Ecosystem",
  lines: [
    "Kenya Literature Bureau · Nairobi, Kenya",
    "Access help: contact your school administrator",
    "Learning management · School information · Digital publishing",
  ],
  credit: {
    prefix: "Photography via ",
    linkLabel: "Unsplash",
    linkHref: "https://unsplash.com/license",
    suffix: " · Illustration by KLB",
  },
};

// Keys match the role buttons on the public homepage. The lists describe the
// permissions and record areas already enforced by the backend for each role.
export const DEFAULT_ROLE_PREVIEWS = {
  learners: {
    rights: [
      "Work only inside your own learner record",
      "Open your courses, assignments and quizzes",
      "Submit work while offline and sync on reconnect",
      "Read your results, progress report and messages",
    ],
    content: [
      "My courses and textbook library",
      "Assignments and quizzes",
      "Learning resources",
      "Progress report and school messages",
    ],
  },
  guardians: {
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
  teachers: {
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
  content: {
    rights: [
      "Maintain textbooks, chapters and learning resources",
      "Map material to competency-based outcomes",
      "Publish catalogue updates used across the platform",
      "No learner grading or user administration permissions",
    ],
    content: [
      "Textbook catalogue",
      "Chapters and digital resources",
      "Curriculum and competency mappings",
      "Catalogue status and publisher details",
    ],
  },
};

function runtimeConfig() {
  if (typeof window === "undefined") return {};
  return window.__KLB_SITE_CONFIG__ || {};
}

export function getFooterContent() {
  const override = runtimeConfig().footer || {};
  return {
    ...DEFAULT_FOOTER,
    ...override,
    credit: {
      ...DEFAULT_FOOTER.credit,
      ...(override.credit || {}),
    },
  };
}

export function getRolePreview(key) {
  const override = runtimeConfig().rolePreviews || {};
  return override[key] || DEFAULT_ROLE_PREVIEWS[key] || { rights: [], content: [] };
}
