# Suhulat

A marketplace backend built with Django REST Framework, where sellers list goods by the kilogram, litre, piece, box or ton and buyers order them or ask for quotes. It includes a small JavaScript single-page frontend served by Django.

## Features

- **Accounts**: phone-number login with JWT (access and refresh tokens, logout via token blacklist). Users register as buyers or sellers; a user can be both.
- **Seller profiles**: seller types (surplus, maker, wholesale), verification by an admin, and public seller pages.
- **Listings**: fixed or negotiable prices, units, available quantity, minimum order quantity, images, Uzbekistan regions and categories (names in Uzbek and Russian), filtering and search, and automatic expiry.
- **Requests for quotation**: buyers post an RFQ; sellers answer with offers that can be countered, accepted or rejected.
- **Orders**: pickup or delivery, with a status flow from pending → confirmed → fulfilling → delivered → completed, and cancellation while still pending or confirmed.
- **Cart, wishlist and seller reviews.**
- **Admin API**: approve or reject sellers, moderate listings and reviews, marketplace statistics.
- Role-based permissions, pagination, request throttling and a consistent error format.
- OpenAPI docs with drf-spectacular (Swagger UI and ReDoc).

## Stack

Python · Django · Django REST Framework · SimpleJWT · django-filter · drf-spectacular · PostgreSQL (SQLite for local development) · Pillow

## Running locally

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env             # set USE_SQLITE=True to skip PostgreSQL
python manage.py migrate
python manage.py seed_catalog    # regions and categories
python manage.py seed_data       # optional: 20 demo listings (downloads images)
python manage.py createsuperuser
python manage.py runserver
```

| URL | What |
|---|---|
| http://localhost:8000/ | Web frontend |
| http://localhost:8000/api/docs/ | Swagger UI |
| http://localhost:8000/api/redoc/ | ReDoc |
| http://localhost:8000/admin/ | Django admin |

## Configuration

Settings are read from `.env` (see `.env.example`):

| Variable | Purpose |
|---|---|
| `SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS` | Django basics |
| `USE_SQLITE` | `True` for a local SQLite database, `False` for PostgreSQL |
| `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT` | PostgreSQL connection |

Listings with an expiry date are closed by a management command; in production, schedule it hourly:

```bash
python manage.py expire_listings
```

## Tests

```bash
python manage.py test
```

## API overview

| Prefix | Area |
|---|---|
| `/api/auth/` | register (buyer / seller), login, token refresh, me, change password, logout |
| `/api/profiles/` | buyer and seller profiles |
| `/api/regions/`, `/api/categories/` | catalogue |
| `/api/listings/` | listings |
| `/api/rfq/` | requests for quotation and offers |
| `/api/orders/` | orders and status changes |
| `/api/cart/`, `/api/wishlist/` | cart and wishlist |
| `/api/reviews/` | seller reviews |
| `/api/admin/` | seller approval, moderation, statistics |
