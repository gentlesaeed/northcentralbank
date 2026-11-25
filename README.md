# North Central Bank — Django demo

A Django conversion of the original Tkinter banking simulation. It includes customer registration and sign-in, persistent demo accounts, internal transfers, a transaction ledger, checking/savings summaries, sample loan and tier requests, reports, and security preferences.

> **Educational simulation only.** This project does not hold or move real money, provide financial services, assess credit, or send two-factor verification codes. Do not enter real financial or sensitive personal information. It is not production-ready banking software.

## Run locally

Requires Python 3.10 or newer.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

Open <http://127.0.0.1:8000/> and create a demo customer account. Use `python manage.py createsuperuser` to create an administrator for `/admin/`.

The local SQLite database is stored in `db.sqlite3`. For development, Django uses a fallback secret key and debug mode. Before any deployment, set a private `DJANGO_SECRET_KEY`, `DJANGO_DEBUG=0`, and `DJANGO_ALLOWED_HOSTS`; serve behind HTTPS and set `DJANGO_SECURE_SSL_REDIRECT=1`, `DJANGO_SECURE_COOKIES=1`, and an appropriate `DJANGO_HSTS_SECONDS` value. Complete a security review before deployment. A real financial service would require a separately designed, independently reviewed security, regulatory, and payment-provider architecture.

## Deploying on Vercel

Vercel detects this Django project from `manage.py` and uses the configured ASGI application. Configure these project environment variables in Vercel for Production (and Preview if used):

- `DJANGO_SECRET_KEY` (or `SECRET_KEY`): a newly generated, private Django secret key.
- `DJANGO_DEBUG`: `0`.
- `DJANGO_ALLOWED_HOSTS`: comma-separated custom hostnames, if using a custom domain. Vercel deployment hostnames are read from Vercel's system environment variables.

The app enables HTTPS-aware secure cookies and redirects on Vercel, and Vercel collects the configured static files during build. SQLite is suitable for local development only; its filesystem is not persistent across Vercel function instances. Configure a persistent external database before relying on registration or saved banking demo data.

## Tests

```powershell
python manage.py test
```
