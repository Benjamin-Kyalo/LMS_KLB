import { useState } from "react";
import { Link } from "react-router-dom";
import { BarChart3, BookOpen, GraduationCap, Library, Users } from "lucide-react";
import { getFooterContent, getRolePreview } from "../config/publicSite";

const AUDIENCES = [
  {
    key: "learners",
    label: "Students & learners",
    icon: GraduationCap,
    title: "Learn at your own pace",
    copy: "Courses, assignments, quizzes and digital textbooks, with work that syncs when the network returns.",
    to: "/login?role=LEARNER",
    action: "Learner workspace",
  },
  {
    key: "guardians",
    label: "Parents & guardians",
    icon: Users,
    title: "Stay close to progress",
    copy: "Follow attendance, results and school messages for the learners you care about.",
    to: "/login?role=GUARDIAN",
    action: "Guardian workspace",
  },
  {
    key: "teachers",
    label: "Teachers",
    icon: BookOpen,
    title: "Plan, teach and assess",
    copy: "Lesson plans, class records, attendance, grading and curriculum tools in one working space.",
    to: "/login?role=TEACHER",
    action: "Teacher workspace",
  },
  {
    key: "content",
    label: "Content managers",
    icon: Library,
    title: "Curate learning resources",
    copy: "Maintain the textbook catalogue, learning outcomes and curriculum mappings used across the system.",
    to: "/login?role=CONTENT_MANAGER",
    action: "Content manager workspace",
  },
];

const WORKSPACES = [
  {
    key: "learning",
    index: "01",
    overline: "Learning workspace",
    title: "Lessons that continue offline",
    copy: "Courses, assignments, quizzes and a textbook library in one place, with changes queued when the connection drops.",
    image: "/images/family-progress.jpg",
    imageAlt: "A parent and learner working together at a desk",
    icon: GraduationCap,
  },
  {
    key: "school",
    index: "02",
    overline: "School day",
    title: "Records that stay connected",
    copy: "Attendance, timetables, assessments and class records share one school database with the learner portal.",
    image: "/images/teachers-lesson.jpg",
    imageAlt: "A teacher working with students in a classroom",
    icon: BarChart3,
  },
  {
    key: "publishing",
    index: "03",
    overline: "Digital publishing",
    title: "Curriculum tied to the classroom",
    copy: "Textbooks, chapters, resources and competency-based outcomes stay linked to the lessons teachers use.",
    image: "/images/digital-library.jpg",
    imageAlt: "Library shelves holding reference books",
    icon: Library,
  },
];

const INSIGHTS = [
  {
    title: "Attendance",
    copy: "Daily registers stay linked to the class and learner record.",
  },
  {
    title: "Assessments",
    copy: "Marks and feedback sit beside the courses they assess.",
  },
  {
    title: "Course activity",
    copy: "Lessons, resources and submissions share one academic timeline.",
  },
];

const FACTS = [
  { value: "14", label: "connected application modules" },
  { value: "10+", label: "labelled sample records per category" },
  { value: "Offline", label: "changes queued until reconnected" },
  { value: "1", label: "shared school database" },
];

export default function Home() {
  const [selectedRoleKey, setSelectedRoleKey] = useState(AUDIENCES[0].key);
  const selectedRole = AUDIENCES.find((item) => item.key === selectedRoleKey) || AUDIENCES[0];
  const selectedAccess = getRolePreview(selectedRole.key);
  const footer = getFooterContent();

  return (
    <div className="public-home">
      <header className="public-topbar">
        <Link to="/" className="public-brand">
          <span className="public-mark">KLB</span>
          <span><strong>Digital Learning Ecosystem</strong><small>Kenya Literature Bureau</small></span>
        </Link>
        <nav aria-label="Public navigation">
          <a href="#workspaces">Platform</a>
          <a href="#insights">Progress</a>
          <a href="#roles">Who it's for</a>
          <Link to="/login">Sign in</Link>
        </nav>
      </header>

      <main>
        <section className="public-hero">
          <div className="public-hero-copy">
            <div className="overline" style={{ color: "#b9d4c8" }}>One connected platform</div>
            <h1>Teaching and learning, connected for Kenyan schools.</h1>
            <p>
              A single KLB ecosystem for lessons, school records and digital textbooks —
              built for competency-based learning and usable when the network is not.
            </p>
            <div className="public-hero-actions">
              <Link to="/register" className="button-link light">Create an account</Link>
            </div>
          </div>
          <aside className="public-hero-panel" aria-label="Students using digital learning tools">
            <figure>
              <img
                src="/images/hero-students.jpg"
                alt="Students studying together with laptops and notebooks"
                className="hero-photo"
              />
              <figcaption>One school record, with the right view for every role.</figcaption>
            </figure>
          </aside>
        </section>

        <section className="public-workspaces" id="workspaces" aria-labelledby="workspaces-title">
          <div className="public-section-head">
            <div>
              <div className="overline">What the platform does</div>
              <h2 id="workspaces-title">Three connected ways to use KLB</h2>
            </div>
          </div>
          <div className="workspace-grid">
            {WORKSPACES.map((item) => {
              const Icon = item.icon;
              return (
                <article className={`workspace-card workspace-${item.key}`} key={item.key}>
                  <div className="workspace-media">
                    <img src={item.image} alt={item.imageAlt} loading="lazy" />
                    <span className="workspace-index" aria-hidden="true">{item.index}</span>
                  </div>
                  <div className="workspace-body">
                    <span className="workspace-icon" aria-hidden="true"><Icon size={20} strokeWidth={1.8} /></span>
                    <div className="overline">{item.overline}</div>
                    <h3>{item.title}</h3>
                    <p>{item.copy}</p>
                  </div>
                </article>
              );
            })}
          </div>
        </section>

        <section className="public-stats" aria-label="Platform at a glance">
          {FACTS.map((fact) => (
            <div className="public-stat" key={fact.label}>
              <strong>{fact.value}</strong>
              <span>{fact.label}</span>
            </div>
          ))}
        </section>

        <section className="public-insights" id="insights" aria-labelledby="insights-title">
          <div className="insight-copy">
            <div className="overline">Progress and insight</div>
            <h2 id="insights-title">A clearer picture of learning</h2>
            <p>
              School information is most useful when it is easy to read. The same
              records used for daily work also feed the dashboards and reports that
              teachers, managers and guardians rely on.
            </p>
            <ul className="insight-list">
              {INSIGHTS.map((item, index) => (
                <li key={item.title}>
                  <span className="insight-point-index" aria-hidden="true">0{index + 1}</span>
                  <div>
                    <strong>{item.title}</strong>
                    <p>{item.copy}</p>
                  </div>
                </li>
              ))}
            </ul>
          </div>
          <figure className="insight-visual">
            <img src="/hero-learning.svg" alt="" className="insight-illustration" />
            <span className="insight-chip">Attendance · Assessments · Courses</span>
            <figcaption>Illustrative view of records already captured by the school.</figcaption>
          </figure>
        </section>

        <section className="public-section" id="roles" aria-labelledby="audience-title">
          <div className="public-section-head">
            <div>
              <div className="overline">Choose your path</div>
              <h2 id="audience-title">Where do you fit?</h2>
            </div>
          </div>
          <div className="role-selector" role="group" aria-label="Choose a role to preview">
            {AUDIENCES.map((item) => {
              const Icon = item.icon;
              const selected = item.key === selectedRole.key;
              return (
                <button
                  type="button"
                  className={`role-choice${selected ? " is-selected" : ""}`}
                  aria-pressed={selected}
                  onClick={() => setSelectedRoleKey(item.key)}
                  key={item.key}
                >
                  <span className="audience-icon" aria-hidden="true"><Icon size={20} strokeWidth={1.8} /></span>
                  <span>{item.label}</span>
                </button>
              );
            })}
          </div>
          <div className="role-preview" aria-live="polite">
            <div className="role-preview-intro">
              <div className="overline">Access preview · {selectedRole.label}</div>
              <h3>{selectedRole.title}</h3>
              <p>{selectedRole.copy}</p>
              <Link to={selectedRole.to} className="button-link">{selectedRole.action}</Link>
            </div>
            <div className="role-preview-details">
              <div>
                <h4>Rights you receive</h4>
                <ul>
                  {selectedAccess.rights.map((right) => <li key={right}>{right}</li>)}
                </ul>
              </div>
              <div>
                <h4>Content you will see</h4>
                <ul>
                  {selectedAccess.content.map((item) => <li key={item}>{item}</li>)}
                </ul>
              </div>
            </div>
          </div>
        </section>
      </main>

      <footer className="public-footer">
        <div>
          <strong>{footer.name}</strong>
          {footer.lines.map((line) => <span key={line}>{line}</span>)}
        </div>
        <span className="public-footer-credit">
          {footer.credit.prefix}
          <a href={footer.credit.linkHref} target="_blank" rel="noreferrer">{footer.credit.linkLabel}</a>
          {footer.credit.suffix}
        </span>
      </footer>
    </div>
  );
}
