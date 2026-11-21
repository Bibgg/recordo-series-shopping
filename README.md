# BIGICO — Baglung Local Products Marketplace

BIGICO is a Nepal-first Android marketplace concept starting with verified local products from Baglung. The app uses Nepalese Rupees (NPR / रु). This repository contains the Android app and the FastAPI backend.

## Android app

- Native Android app built with Kotlin and Jetpack Compose.
- Local marketplace home screen, search, product categories and NPR prices.
- Product catalogue is loaded from the backend API; no invented products are seeded.
- Empty/error state is shown until the API is configured and real products are published.
- Customer order, account and seller workflows are planned for later MVP iterations.

### Build an APK with GitHub Actions

1. Open the **Actions** tab in this repository.
2. Select **Build BIGICO Android APK** and run it, or push to the `bigico-android-mvp` branch.
3. Open the successful workflow run and download the `BIGICO-debug-apk` artifact.

To connect the app to a deployed backend, provide the HTTPS API root as the Gradle property or environment variable `BIGICO_API_BASE_URL` during the build. The app appends `/api/v1/products`. Do not put admin tokens or private credentials in the Android app.

## Backend setup

Python 3.11+ recommended.

```bash
cd backend
python -m venv .venv
# activate it, then:
pip install -r requirements.txt
export ADMIN_API_TOKEN='use-a-long-random-secret'
uvicorn app.main:app --reload
```

The local default database is SQLite (`backend/recordo.db` when launched from this folder). For production, set `DATABASE_URL` to a managed PostgreSQL connection string and set a strong `ADMIN_API_TOKEN`. Never expose the admin token in the Android app.

API docs: `http://127.0.0.1:8000/docs`

## Current API

- `GET /health`, `GET /api/v1/config`
- `GET /api/v1/products`
- `POST /api/v1/admin/products` — requires `X-Admin-Token`
- `PATCH /api/v1/admin/products/{id}` — requires `X-Admin-Token`
- `POST /api/v1/orders` — server calculates totals from current product prices and checks stock
- `GET /api/v1/orders/{order_code}?phone=...` — customer order tracking
- `GET /api/v1/admin/orders` and `PATCH /api/v1/admin/orders/{code}` — requires admin token

## Important before public launch

This is an early MVP foundation, not ready for public payments or full logistics operations. Before accepting real customer orders: deploy over HTTPS, use managed persistent PostgreSQL, configure backups, add secure seller/customer authentication, rate limiting, audit logs, privacy/terms/refund policy, delivery fees/zones and rider assignment, and integrate a Nepal payment provider only after merchant onboarding (eSewa/Khalti/Fonepay). Start with a small, legally compliant pilot and manually confirmed payment or cash on delivery. Do not store card or wallet credentials.
