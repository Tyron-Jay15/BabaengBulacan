# PWA & Mobile QR Code — Beginner Setup Guide

This guide explains how the Progressive Web App (PWA) and dynamic QR code work in BabaengBulacan, and how to test them on your phone.

---

## Step 1 — Install required packages

Packages are already listed in `requirements.txt` at the project root:

```bash
cd projdjango
pip install -r ../requirements.txt
```

Key packages:

| Package | Purpose |
|---------|---------|
| `qrcode` | Generates QR code images |
| `Pillow` | PWA app icons |
| `python-dotenv` | Environment variables for production URL |

---

## Step 2 — Web manifest

The manifest tells Android/Chrome how to install the app.

**Dynamic (recommended):** `/manifest.webmanifest` or `/manifest.json`  
Built at runtime with the correct URL for dev or production.

**Static fallback:** `static/manifest.json` (development reference only)

Important fields:

- `display: standalone` — full-screen, no browser bar
- `theme_color: #7B2CBF` — status bar / splash accent
- `background_color: #ffffff` — splash screen background
- Icons in `static/icons/` (72px through 512px)

Linked in `templates/base.html`:

```html
<link rel="manifest" href="{% url 'web_manifest' %}">
```

---

## Step 3 — Service worker

File: `static/sw.js`  
Served at: `/sw.js`

- Caches CSS, JS, and icons for faster loads
- Does **not** cache login sessions, API, or admin pages
- Auto-updates when `CACHE_VERSION` in `sw.js` is bumped
- Users see an “Update Available” prompt when a new version is ready

Registered in `static/js/pwa-install.js` on every page.

---

## Step 4 — Detect local IP address

File: `projdjango/network_utils.py`

On each request in development, Django detects your computer’s LAN IPv4 (e.g. `192.168.1.15`) using a standard network trick — **not** `localhost` or `127.0.0.1`.

When the server starts, the console logs:

```
Mobile QR URL (scan from phone): http://192.168.1.15:8000/accounts/login/
```

---

## Step 5 — Generate QR code dynamically

File: `projdjango/mobile_access.py`

| Environment | QR contains |
|-------------|-------------|
| **Development** (`DEBUG=True`) | `http://<your-lan-ip>:8000/accounts/login/` |
| **Production** (`DEBUG=False`) | `https://yourdomain.com/accounts/login/` from `SITE_BASE_URL` |

No hardcoded IP. No code changes when deploying.

QR image endpoint: `/mobile-access/qr.png`  
Regenerates on every login page load in development.

---

## Step 6 — Display QR on login page

Open: `http://127.0.0.1:8000/accounts/login/`

The login form appears on the left; the QR panel on the right shows:

> Scan this QR Code to open BabaengBulacan on your mobile device.

The home page (`/home/`) also includes a compact QR section.

---

## Step 7 — Configure install prompt

When Chrome on Android supports installation, a bottom banner appears:

**Install BabaengBulacan**

Handled by `static/js/pwa-install.js`. After install:

- App opens in standalone (full-screen) mode
- Uses BabaengBulacan icon and name
- Login sessions are preserved (same cookies as browser)

---

## Step 8 — Test on Android

1. Connect your **phone and computer to the same Wi-Fi**.

2. Start Django bound to all interfaces:

```bash
python manage.py runserver 0.0.0.0:8000
```

> **Important:** `runserver` without `0.0.0.0` only listens on this computer. The login page will show a yellow warning if phones cannot connect.

3. On your computer, open the login page and check the QR URL shows your LAN IP (not localhost).

4. On your phone, open the **Camera** app and scan the QR code.

5. Tap the link — BabaengBulacan opens in Chrome.

6. Test login, register, incident report, and dashboard.

7. In Chrome menu → **Install app** or **Add to Home screen**.

---

## Step 9 — Test on desktop

1. Open Chrome DevTools → **Application** tab.
2. Check **Manifest** loads without errors.
3. Check **Service Workers** shows `/sw.js` activated.
4. Use **Lighthouse** → Progressive Web App audit (optional).

---

## Step 10 — Production deployment (PythonAnywhere)

Set in `.env`:

```env
DJANGO_ENV=production
DEBUG=False
SITE_BASE_URL=https://yourusername.pythonanywhere.com
ALLOWED_HOSTS=yourusername.pythonanywhere.com
```

The QR code **automatically** switches to your production HTTPS URL. No code changes.

Run:

```bash
python manage.py collectstatic --noinput
```

Reload the web app on PythonAnywhere.

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Phone cannot open scanned link | Run `python manage.py runserver 0.0.0.0:8000` |
| `DisallowedHost` on phone | Restart server — dev settings auto-add your LAN IP to `ALLOWED_HOSTS` |
| QR shows `127.0.0.1` | Connect to Wi-Fi; restart Django; check firewall |
| Install prompt missing | Use Chrome on Android over HTTPS (production) or localhost/LAN for dev |
| reCAPTCHA fails on phone | Register your LAN IP or production domain in Google reCAPTCHA admin |

---

## File reference

| File | Role |
|------|------|
| `projdjango/mobile_access.py` | QR URL logic (dev vs prod) |
| `projdjango/network_utils.py` | LAN IP detection & connectivity check |
| `projdjango/pwa_views.py` | Manifest + service worker views |
| `static/sw.js` | Service worker |
| `static/js/pwa-install.js` | Install prompt + updates |
| `static/icons/icon-*.png` | PWA icons |
| `templates/components/mobile_qr_panel.html` | QR UI component |

---

*Expected result:* On the same Wi-Fi, anyone scans the login QR, opens BabaengBulacan on their phone, logs in with full auth, and can install it as a PWA — with zero code changes when you deploy to production.
