# Recordo Series Shopping — Nepal

Nepal-focused shopping and grocery marketplace starter.

## Nepal-first defaults
- Country: Nepal (NP)
- Currency: Nepalese Rupee (NPR / रु)
- Prices are numeric NPR amounts; never INR.
- Initial categories: vegetables, fruits, groceries, daily essentials.
- Languages planned: Nepali and English.

## Layout
- `android/`: native Android app using Kotlin + Jetpack Compose
- `backend/`: Python FastAPI service
- `.github/workflows/`: APK build workflow

## Run backend
```bash
cd backend
python -m venv .venv
pip install -r requirements.txt
uvicorn app.main:app --reload
```
API docs: http://127.0.0.1:8000/docs

## Build APK
Run **Build Android APK** from GitHub Actions. Download the generated debug APK from the workflow artifact.

## Important
This is a starter, not a production marketplace. The Android app and API currently use sample catalogue data. Seller accounts, MongoDB persistence, cart/checkout, order tracking, delivery operations, and Nepal payment integrations (eSewa/Khalti/Fonepay) are not enabled yet. Configure secrets securely and complete security, legal, payment-provider, and delivery testing before launch. Never commit passwords, API keys, or signing keys.
