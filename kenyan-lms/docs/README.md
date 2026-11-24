# Documentation index

This folder is the operating manual for the project. Every guide reflects
the code that actually exists; unimplemented ideas are labelled as such.

## Two sides of the application

- Staff (platform admins, school admins, teachers, content managers) work in
  `/admin/...` using `DashboardLayout`.
- Learners and guardians work in `/portal/...` using `PortalLayout`.
- `/` is the public homepage. It introduces the platform and the supported
  user categories; administrator access is intentionally not advertised there.
- Sign-in and registration route each role to `/admin` or `/portal`. Old root
  URLs such as `/learners`, `/courses` and `/reports` redirect by role.

See `docs/USER_GUIDE.md` for the day-to-day view and `docs/ADMIN_ACCESS.md`
for safe access and permissions.

## Documents

| Document | Purpose | Status |
|---|---|---|
| `README.md` | This index | Written |
| `SYSTEM_OVERVIEW.md` | Architecture and request flow | Written |
| `DESIGN_SYSTEM.md` | Colour palette, contrast ratios and UI conventions | Written |
| `REFERENCE_MODELS.md` | Five reference systems, borrowed ideas, original design, accessibility and low-bandwidth guidance | Written |
| `ASSET_CREDITS.md` | Locally hosted photographs, original SVG and reference-use statement | New |
| `PUBLIC_SITE_CONTENT.md` | Editable footer text, role access previews and runtime override | New |
| `REFERENCE_NUMBERING.md` | Automatic admission, staff and other business codes | Written |
| `INSTALLATION_GUIDE.md` | Step-by-step setup on Windows | Written |
| `COMMANDS.md` | Complete PowerShell command list with working directories | Written |
| `PRODUCTION_CONFIGURATION.md` | Production settings, TLS, CORS and mail | Written |
| `DATABASE_GUIDE.md` | Tables, relationships, migrations, backups | Written |
| `FILE_STRUCTURE_GUIDE.md` | Folder structure and important files | Written |
| `USER_GUIDE.md` | How each role uses the system | Updated for `/admin` and `/portal` |
| `ADMIN_GUIDE.md` | Roles, permissions, institutions and school profile | Updated |
| `ADMIN_ACCESS.md` | Safe admin access, roles, invitation-only admin signup, isolation, locked-out help | Updated |
| `SAMPLE_DATA.md` | Labelled sample records, counts, idempotent seeder and caveats | New |
| `TROUBLESHOOTING.md` | Common errors and fixes | Written |
| `BACKUP_AND_RESTORE.md` | Safe backup and recovery | Written |
| `API_DOCUMENTATION.md` | Endpoints, school profile and frontend usage | Updated |
| `TESTING_CHECKLIST.md` | Tests actually run and pending tests | Updated |
| `HANDOVER_REPORT.md` | Status, verification and known limitations | Updated |
| `MILESTONES_AJ.md` | A–J records: earlier UI/profile work and the latest RBAC, CRUD, UI-template and verification milestone | Updated |

## How to use these documents

- New to the project? Read `SYSTEM_OVERVIEW.md`, then `INSTALLATION_GUIDE.md`.
- Need to run a command? Use `COMMANDS.md`.
- Need admin access or a password reset? Use `ADMIN_ACCESS.md`.
- Something broken? Start with `TROUBLESHOOTING.md`.
- Need to understand a table? Use `DATABASE_GUIDE.md`.
- Need an endpoint? Use `API_DOCUMENTATION.md`.
- Want the honest completion status? Use `HANDOVER_REPORT.md` and
  `TESTING_CHECKLIST.md`. Phase 0–6 are mostly implemented, Phase 7 is a
  foundation, Phase 8 is partial and Phase 9 is not complete.

No password belongs in any of these files. Use
`python manage.py changepassword <username>` or `createsuperuser` locally.
