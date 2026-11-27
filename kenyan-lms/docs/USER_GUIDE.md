# User guide

**This is a normal web app.** There is no offline mode, service worker, PWA
install or mobile/native app. Work that cannot be saved shows an error and is
not kept on your device. Uploads need a live connection.

## Where to go after sign in

Open <http://127.0.0.1:5173> for the public homepage, choose your role's sign-in
link, enter your username and password, then press **Sign in**. You do not need
to choose a side after that: the app sends staff to `/admin` and learners or
guardians to `/portal`. Old bookmarks are handled by `RoleHome`.

| Side | Address | Who uses it |
|---|---|---|
| Staff admin panel | `/admin/...` | `SUPER_ADMIN`, `ADMIN`, custom roles with `admin.access`, teachers |
| Learner / guardian portal | `/portal/...` | Learners and guardians |

The old platform/school/content-manager role names are retired; those accounts
are now `ADMIN`. `SUPER_ADMIN` is unchanged. A custom role is a named set of
picked capabilities and only appears in the admin panel when `admin.access` was
selected.

Old bookmarks such as `/learners`, `/courses` and `/reports` still work. They
redirect to the right page for your role, so keep using them if you already
have them saved. New links should use `/admin/...` or `/portal/...`.

Accounts created by an administrator have no usable password until the owner
uses the password-reset flow; no password is generated or shown. Accounts
created through public registration use the password chosen on the form.
Change your password under **Profile → Change password**. Sign-in uses a
secure session cookie; the app re-reads your identity and role from
`/api/auth/me/` on each visit, so sign out and sign in again if your role
changes. Password edits end other active sessions. Reset links expire after
one hour and can be used once. Never share a password in a message; a local
administrator can reset it with `python manage.py changepassword <username>`
— see `docs/ADMIN_ACCESS.md`.

## Learner and guardian portal (`/portal/...`)

- **Home** (`/portal`) shows your own record or the linked learner, attendance
  and assessment charts, and quick links. A guardian sees only learners linked
  to the account; an institution administrator (`ADMIN`) must create that link.
- **My courses** (`/portal/courses`) shows your courses.
- **Textbook library** (`/portal/textbooks`) shows titles your institution is
  licensed to use. Open one to see its chapters, exercises and resources.
- **Resources** (`/portal/resources`) lists audio, video, PDF and links.
- **Assignments** (`/portal/assignments`) and **Quizzes** (`/portal/quizzes`)
  show work set by teachers. **My submissions** (`/portal/submissions`) shows
  published feedback and, where allowed, a resubmit action.
- **Progress report** (`/portal/reports`) shows attendance and exam results.
- **Messages** (`/portal/communications`) shows announcements and direct
  messages from the school.
- **My profile** (`/portal/profile`) lets you update your own details and
  change your password.

The portal header shows the school name and logo. If a school has not uploaded
a logo yet, the default KLB mark is shown.

## Staff admin panel (`/admin/...`)

### Teacher

- **Learners** — `/admin/learners`: view class lists and register learners.
  Leave the admission number blank to generate one such as `ADM-KSCH-003`.
- **Courses** — `/admin/courses`: create courses, then add modules and lessons
  from `/admin/modules` and `/admin/lessons`.
- **Assignments / Quizzes** — `/admin/assignments`, `/admin/quizzes` and
  `/admin/questions`: create work and questions.
- **Rubrics & feedback** — `/admin/rubrics`: build bands, scored criteria and a
  reusable comment bank. **Submissions** — `/admin/submissions`: mark work with
  a rubric or direct score, then publish feedback.
- **Attendance** — `/admin/attendance`: record daily attendance.
- **Messages** — `/admin/communications`: announcements and direct messages.
- **Reports** — `/admin/reports`: attendance and performance charts.

### Administrator

- **Institutions** — `/admin/institutions` (`SUPER_ADMIN` only): register
  schools. `ADMIN` cannot create global institutions. School codes are generated
  from the name unless an official code is supplied.
- **School profile** — `/admin/school`: update your own school's name, phone,
  email, website, motto, address and logo. `ADMIN` and `SUPER_ADMIN` can save
  this page; a custom role is limited to its picked capabilities. The logo must
  be JPG, PNG or WebP and at most 2 MB; the upload needs a live connection and
  must be retried if it fails. The same logo then appears in the learner/guardian
  portal.
- **Custom roles** — named reusable roles with picked capabilities are managed
  through `/api/auth/roles/`. An `ADMIN` can create and assign them but cannot
  grant `SUPER_ADMIN`; `SUPER_ADMIN` can grant any role. `/api/auth/users/roles/`
  lists the built-ins plus custom options. A custom role only enters `/admin`
  when `admin.access` is selected, and the backend enforces the other
  capabilities.
- **Learners / Teachers / Guardians** — `/admin/learners`,
  `/admin/teachers`, `/admin/guardians`: manage people and accounts.
  Admission, assessment and staff numbers are generated when left blank.
- **Classes & subjects** — `/admin/classes`: set up the academic structure;
  subject codes are generated per school.
- **Dashboard** — `/admin`: clickable statistics and quick links that open
  the matching records.
- **Reports** — `/admin/reports`: school dashboard and learner reports.
- **Messages** — `/admin/communications`: publish announcements.
- **Profile** — `/admin/profile`: your own details and password.

## When the connection fails

If the network drops while you are saving, the page shows an error. The change
is **not saved** and is not queued on your device: there is no “waiting to
sync” notice, **Sync now** button or conflict screen. Reconnect and submit the
form again. School logo uploads and other file uploads also need a live
connection; a failed upload must be retried.

The public homepage headline is drawn with a small canvas effect. It keeps the
real heading text available to screen readers, and the animation is disabled
when your system requests reduced motion.

## Getting help

Check `TROUBLESHOOTING.md` first. If you need help from a developer, send the
exact error text, the URL you were on (for example `/portal/reports`), and
your role. Never include a password.
