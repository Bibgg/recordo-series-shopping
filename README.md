# Recordo Series Shopping — Nepal

Nepal-first shopping, grocery and local-delivery marketplace. Currency is Nepalese Rupees (NPR / रु), not INR.

## First working slice
- Product catalogue backed by a database (no fake catalogue seeded).
- Admin-only product creation and stock management.
- Customer order placement with server-side price calculation and stock checks.
- Order tracking protected by order code + buyer phone.
- Admin order list and status updates.
- Nepal address fields: district, municipality, ward and delivery address.
- Android APK workflow.

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

## API outline
- `GET /health`, `GET /api/v1/config`
- `GET /api/v1/products`, optional `?category=Vegetables`
- `POST /api/v1/admin/products` — requires `X-Admin-Token`
- `PATCH /api/v1/admin/products/{id}` — requires `X-Admin-Token`
- `POST /api/v1/orders` — server calculates total from current product prices
- `GET /api/v1/orders/{order_code}?phone=...` — customer tracking
- `GET /api/v1/admin/orders` and `PATCH /api/v1/admin/orders/{code}` — requires admin token

## Operational reality
This is an MVP foundation, not ready to take public payments or run a logistics fleet yet. Before real customers: deploy over HTTPS, use managed persistent PostgreSQL, configure backups, add OTP authentication, rate limiting, audit logs, privacy/terms/refund policy, delivery fees/zones and rider assignment, and integrate a Nepal payment provider only after merchant onboarding (eSewa/Khalti/Fonepay). Start with cash on delivery or manually confirmed payment during a small village pilot. Do not store card or wallet credentials.
