# Deploy BabaengBulacan on PythonAnywhere

This guide assumes your project folder is uploaded or cloned to PythonAnywhere at:

`/home/YOUR_USERNAME/ProjDjango/projdjango`

(Adjust paths if your repo layout differs.)

---

## Is the project ready?

**After following this guide: yes, for hosting the core app.**

The codebase now supports production via `DJANGO_ENV=production`. You still need to configure secrets, database, email, and reCAPTCHA on PythonAnywhere yourself — those cannot be baked into the repo.

### What was missing before (now fixed)

| Item | Status |
|------|--------|
| `DEBUG = False` in production | Fixed |
| `ALLOWED_HOSTS` from environment | Fixed |
| Strong `SECRET_KEY` required in production | Fixed |
| `STATIC_ROOT` + `collectstatic` | Fixed |
| `CSRF_TRUSTED_ORIGINS` for HTTPS | Fixed |
| Secure cookies (HTTPS) | Fixed |
| Production logging to file | Fixed |
| Settings split (dev / prod) | Fixed |
| `.env.example` template | Fixed |
| WSGI template for PythonAnywhere | Fixed |
| MySQL driver in requirements | Fixed |

### What you still configure on PythonAnywhere

| Item | Why |
|------|-----|
| `.env` with secrets | Security — never commit real keys |
| MySQL database | SQLite is not recommended for production on PA |
| SMTP email | Verification, password reset, notifications |
| reCAPTCHA keys for your domain | Login/register will fail CAPTCHA otherwise |
| Static + media URL mappings | PA serves files outside Django |
| `collectstatic` + `migrate` | One-time setup commands |

### Features not required for hosting but still incomplete in the app

These do not block deployment but are listed in `docs/MASTER_DEVELOPMENT_ROADMAP.md`:

- PDF/Excel report exports
- Dynamic FAQ / Feedback / Awareness CMS pages
- Scheduled database backups UI
- Track-case wired to real database (may still use mock JS)
- Advanced search (saved filters, export)

---

## Step 1 — Upload the project

1. Create a PythonAnywhere account: https://www.pythonanywhere.com
2. Open **Consoles → Bash**
3. Clone or upload the project:

```bash
cd ~
git clone YOUR_REPO_URL ProjDjango
# or upload a zip and unzip
```

Your `manage.py` should be at:

`/home/YOUR_USERNAME/ProjDjango/projdjango/manage.py`

---

## Step 2 — Virtual environment

```bash
cd ~/ProjDjango/projdjango
python3.10 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r ../requirements.txt
```

If `mysqlclient` fails to build, run:

```bash
sudo apt-get install python3-dev default-libmysqlclient-dev build-essential
pip install mysqlclient
```

(On PythonAnywhere, MySQL dev headers are usually available; contact support if the build fails.)

---

## Step 3 — Create MySQL database

1. PythonAnywhere **Dashboard → Databases**
2. Create a MySQL database (e.g. `babaengbulacan`)
3. Note: host, username, password, database name (`YOUR_USERNAME$babaengbulacan`)

---

## Step 4 — Environment file

```bash
cd ~/ProjDjango/projdjango
cp .env.example .env
nano .env
```

Example production `.env`:

```env
DJANGO_ENV=production
SECRET_KEY=paste-a-long-random-key-here
ALLOWED_HOSTS=yourusername.pythonanywhere.com
CSRF_TRUSTED_ORIGINS=https://yourusername.pythonanywhere.com
SITE_BASE_URL=https://yourusername.pythonanywhere.com

DB_ENGINE=django.db.backends.mysql
DB_NAME=yourusername$babaengbulacan
DB_USER=yourusername
DB_PASSWORD=your-mysql-password
DB_HOST=yourusername.mysql.pythonanywhere-services.com
DB_PORT=3306

EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=you@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=BabaengBulacan <you@gmail.com>

RECAPTCHA_SITE_KEY=your-production-site-key
RECAPTCHA_SECRET_KEY=your-production-secret-key
RECAPTCHA_REQUIRED=True

TIME_ZONE=Asia/Manila
```

Generate a secret key locally:

```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

Register reCAPTCHA at https://www.google.com/recaptcha/admin — add domain `yourusername.pythonanywhere.com`.

---

## Step 5 — Migrate and collect static files

```bash
cd ~/ProjDjango/projdjango
source venv/bin/activate
export DJANGO_ENV=production
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py createsuperuser
```

Optional — create the admin account used in docs:

```bash
python manage.py shell
```

```python
from django.contrib.auth.models import User
from projdjango.models import UserProfile
u, _ = User.objects.get_or_create(username='babaeng_admin', defaults={'email': 'admin@babaengbulacan.local', 'is_staff': True, 'is_superuser': True})
u.set_password('YourSecurePassword123!')
u.save()
UserProfile.objects.get_or_create(user=u, defaults={'email_verified': True})
```

---

## Step 6 — Configure the Web app

1. **Web → Add a new web app → Manual configuration → Python 3.10**
2. **Virtualenv:** `/home/YOUR_USERNAME/ProjDjango/projdjango/venv`
3. **WSGI configuration file** — replace contents with:

```python
import os
import sys

path = '/home/YOUR_USERNAME/ProjDjango/projdjango'
if path not in sys.path:
    sys.path.insert(0, path)

os.environ['DJANGO_ENV'] = 'production'
os.environ['DJANGO_SETTINGS_MODULE'] = 'projdjango.settings'

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
```

4. **Static files** (Web tab → Static files):

| URL | Directory |
|-----|-----------|
| `/static/` | `/home/YOUR_USERNAME/ProjDjango/projdjango/staticfiles` |
| `/media/` | `/home/YOUR_USERNAME/ProjDjango/projdjango/media` |

5. Click **Reload** on the Web tab.

---

## Step 7 — Verify

Visit:

- `https://yourusername.pythonanywhere.com/accounts/login/`
- `https://yourusername.pythonanywhere.com/admin-dashboard/` (staff only)
- `https://yourusername.pythonanywhere.com/api/` (JSON API)

Check logs if something fails:

```bash
tail -f ~/ProjDjango/projdjango/logs/django.log
```

Run deployment checks:

```bash
export DJANGO_ENV=production
python manage.py check --deploy
```

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| **DisallowedHost** | Add your PA domain to `ALLOWED_HOSTS` in `.env`, reload web app |
| **403 CSRF** | Set `CSRF_TRUSTED_ORIGINS=https://yourusername.pythonanywhere.com` |
| **Static files 404** | Run `collectstatic`, verify Static files mapping in Web tab |
| **Media uploads 404** | Add `/media/` mapping; ensure `media/` folder exists and is writable |
| **500 on startup** | Check error log in Web tab; usually missing `SECRET_KEY` or `ALLOWED_HOSTS` |
| **reCAPTCHA error** | Register production domain in Google reCAPTCHA admin |
| **Email not sending** | Configure SMTP in `.env`; free PA may block outbound SMTP on some plans |
| **mysqlclient install fail** | Install system MySQL dev packages or use PA support docs |

---

## Updating after code changes

```bash
cd ~/ProjDjango/projdjango
source venv/bin/activate
git pull   # if using git
pip install -r ../requirements.txt
export DJANGO_ENV=production
python manage.py migrate
python manage.py collectstatic --noinput
```

Then **Reload** the web app on PythonAnywhere.

---

## Local development (unchanged)

```powershell
cd projdjango
python manage.py runserver
```

Uses `DJANGO_ENV=development` by default (SQLite, `DEBUG=True`).
