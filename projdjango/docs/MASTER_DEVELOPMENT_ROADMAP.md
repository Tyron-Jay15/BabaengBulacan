# BabaengBulacan — Master Development Roadmap

This document tracks implementation progress against the master specification.  
**Principle:** extend the existing Django project — never recreate from scratch.

---

## Phase 1 — Case Management & Audit Foundation ✅ (Complete)

| Feature | Status | Location |
|---------|--------|----------|
| CaseTimeline model | ✅ | `projdjango/models.py` |
| CaseAssignment model | ✅ | `projdjango/models.py` |
| Evidence model | ✅ | `projdjango/models.py` |
| AuditLog model | ✅ | `projdjango/models.py` |
| Archive flags (Incident, Announcement) | ✅ | `is_archived`, `archived_at` |
| case_management services | ✅ | `projdjango/case_management/services.py` |
| audit services | ✅ | `projdjango/audit/services.py` |
| Admin incident detail (timeline + evidence) | ✅ | `/admin-dashboard/incidents/<id>/` |
| Officer assignment & reassignment | ✅ | incident edit + services |
| Evidence upload (admin) | ✅ | `/admin-dashboard/incidents/<id>/evidence/` |
| Email on status change / assignment | ✅ | `projdjango/emails.py` |
| Chart.js analytics dashboard | ✅ | `/admin-dashboard/analytics/` |
| Activity logs page | ✅ | `/admin-dashboard/activity-logs/` |
| Officer workload page | ✅ | `/admin-dashboard/officer-workload/` |
| Django admin registrations | ✅ | `projdjango/admin.py` |
| Search excludes archived by default | ✅ | `search/services.py` |
| Migration 0013 | ✅ | applied |

---

## Phase 2 — Advanced Reports & Track Case

| Feature | Status | Notes |
|---------|--------|-------|
| PDF export (incidents, users, stats) | ⬜ | Use `reportlab` or `weasyprint` |
| Excel export | ⬜ | Use `openpyxl` |
| Monthly / annual report views | ⬜ | Admin dashboard sub-routes |
| Municipality / barangay statistics export | ⬜ | Reuse `get_analytics_data()` |
| Wire `/track-case/` to database | ⬜ | Replace mock JS with API lookup |
| User-facing case timeline view | ⬜ | Resident sees own report timeline |

---

## Phase 3 — Data Archive & Backups

| Feature | Status | Notes |
|---------|--------|-------|
| Archive UI (incidents, announcements, users) | ⬜ | Soft-delete via `is_archived` |
| Archived search toggle | ✅ partial | `include_archived=1` param |
| Manual database backup download | ⬜ | Management command + admin view |
| Scheduled backups | ⬜ | `django-crontab` or Celery beat |
| Backup restore | ⬜ | Admin-only, audit logged |
| BackupHistory tracking | ✅ model | UI pending |

---

## Phase 4 — Community Modules

| Feature | Status | Notes |
|---------|--------|-------|
| Feedback submission (residents) | ⬜ | Model exists |
| Feedback admin review / respond | ⬜ | Admin dashboard section |
| FAQ public page (dynamic) | ⬜ | Replace static FAQ template |
| FAQ admin CRUD | ⬜ | Admin dashboard or Django admin |
| Public Awareness articles | ⬜ | Model exists; need views + templates |
| Emergency contacts CMS | ⬜ | Category in AwarenessArticle |
| Downloadable resources | ⬜ | FileField on AwarenessArticle |

---

## Phase 5 — Search, Performance & Production

| Feature | Status | Notes |
|---------|--------|-------|
| Multi-keyword search | ⬜ | Split `q` on spaces |
| Saved filters (session/DB) | ⬜ | New SavedFilter model optional |
| Sort newest/oldest toggle | ⬜ | `order` GET param |
| Export search results | ⬜ | CSV/PDF from search views |
| Query optimisation audit | ⬜ partial | select_related in search services |
| Redis / file cache | ⬜ | `CACHES` in production settings |
| Settings split (base/dev/prod) | ✅ | `projdjango/settings/` |
| Environment variables (.env) | ✅ | `.env.example` provided |
| PythonAnywhere deployment guide | ✅ | `docs/PYTHONANYWHERE_DEPLOYMENT.md` |
| Security headers (CSP, HSTS) | ✅ partial | Cookies + XSS; HSTS optional |
| Rate limiting / login throttle | ⬜ partial | Existing lockout in UserProfile |
| Gunicorn + Nginx config docs | ⬜ | PA uses built-in WSGI |
| Logging configuration | ✅ | Rotating file log in production |
| Unit tests for new modules | ⬜ | `tests/test_case_management.py` |

---

## Phase 6 — UI/UX Polish

| Feature | Status | Notes |
|---------|--------|-------|
| Toast notifications | ⬜ | JS toast library or Bootstrap toasts |
| Skeleton loaders | ⬜ | Dashboard + search pages |
| WCAG accessibility pass | ⬜ | aria labels, focus states |
| Dark mode toggle | ⬜ | Currently forced light theme |
| Empty states | ✅ partial | Search module has `_empty_state.html` |
| Mobile responsiveness | ✅ partial | Bootstrap 5 base |

---

## Key URLs

| URL | Purpose |
|-----|---------|
| `/accounts/login/` | Login (reCAPTCHA, 2FA, face optional for staff) |
| `/admin-dashboard/` | Admin KPI dashboard |
| `/admin-dashboard/analytics/` | Chart.js analytics |
| `/admin-dashboard/activity-logs/` | Audit trail browser |
| `/admin-dashboard/officer-workload/` | Officer case counts |
| `/admin-dashboard/incidents/<report_id>/` | Incident detail + timeline |
| `/dashboard/` | Resident dashboard |
| `/search/` | Search hub |
| `/admin/security-dashboard/` | Auth security overview |

---

## Test Admin Account

| Field | Value |
|-------|-------|
| Email | `admin@babaengbulacan.local` |
| Password | `Admin@Bulacan2026!` |
| Username | `babaeng_admin` |

---

## Recommended Next Implementation Order

1. **Track Case backend** — highest user-facing value, low risk  
2. **Feedback module** — model ready, straightforward CRUD  
3. **FAQ dynamic page** — replace static content  
4. **Public Awareness module** — CMS-style article listing  
5. **PDF/Excel reports** — admin export buttons  
6. **Archive UI** — soft-archive actions in admin dashboard  
7. **Production settings split** — deployment readiness  
8. **UI polish** — toasts, skeletons, accessibility  

---

*Last updated: June 2026 — Phase 1 complete.*
