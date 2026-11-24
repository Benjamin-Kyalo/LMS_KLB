# User guide

## Where to go after sign in

Open <http://127.0.0.1:5173> for the public homepage, choose your role's sign-in
link, enter your username and password, then press **Sign in**. You do not need
to choose a side after that: the app sends staff to `/admin` and learners or
guardians to `/portal`. Old bookmarks are handled by `RoleHome`.

| Side | Address | Who uses it |
|---|---|---|
| Staff admin panel | `/admin/...` | Platform admins, school admins, teachers, content managers |
| Learner / guardian portal | `/portal/...` | Learners and guardians |

Old bookmarks such as `/learners`, `/courses` and `/reports` still work. They
redirect to the right page for your role, so keep using them if you already
have them saved. New links should use `/admin/...` or `/portal/...`.

Accounts created by an administrator have no usable password until the owner
uses the password-reset flow; no password is generated or shown. Accounts
created through public registration use the password chosen on the form.
Change your password under **Profile → Change password**. Never share a
password in a message; a local administrator can reset it with
`python manage.py changepassword <username>` — see `docs/ADMIN_ACCESS.md`.

## Learner and guardian portal (`/portal/...`)

- **Home** (`/portal`) shows your own record or the linked learner, attendance
  and assessment charts, and quick links. A guardian sees only learners linked
  to the account; a school administrator must create that link.
- **My courses** (`/portal/courses`) shows your courses.
- **Textbook library** (`/portal/textbooks`) shows titles your institution is
  licensed to use. Open one to see its chapters, exercises and resources.
- **Resources** (`/portal/resources`) lists audio, video, PDF and links.
- **Assignments** (`/portal/assignments`) and **Quizzes** (`/portal/quizzes`)
  show work set by teachers.
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
  `/admin/questions`: create work and questions, mark submissions.
- **Attendance** — `/admin/attendance`: record daily attendance.
- **Messages** — `/admin/communications`: announcements and direct messages.
- **Reports** — `/admin/reports`: attendance and performance charts.

### Administrator

- **Institutions** — `/admin/institutions` (platform admins only): register
  schools. School codes are generated from the name unless an official code is
  supplied.
- **School profile** — `/admin/school`: update your own school's name, phone,
  email, website, motto, address and logo. Only school and platform admins can
  save this page. The logo must be JPG, PNG or WebP and at most 2 MB; upload it
  while online. The same logo then appears in the learner/guardian portal.
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

## Offline behaviour

If the network drops, a banner explains that you are offline. Previously
cached pages stay readable. When you create or edit something while offline,
a notice says "1 change waiting to sync" — the change is saved on the device,
not lost. It is sent automatically when the connection returns. You can also
press **Sync now**. If the server says the record changed while you were
offline, the app tries your change once against the newer server version. If it
still conflicts, the change stays in the queue with a **Use current version**
option and manual retry/discard controls — it is never silently overwritten.

School logo uploads are the exception: they need an internet connection and
are not queued, because a file cannot be replayed from saved JSON.

## Getting help

Check `TROUBLESHOOTING.md` first. If you need help from a developer, send the
exact error text, the URL you were on (for example `/portal/reports`), and
your role. Never include a password.
