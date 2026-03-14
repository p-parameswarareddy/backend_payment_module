
# Payment Module API

A production-ready Django + PostgreSQL payments API microservice.

## Features

- Idempotency: Duplicate requests (same `idempotency_key`) return existing payment
- One successful payment per order: Unique constraint prevents double payment
- State machine: Valid status transitions only (PENDING → SUCCESS/FAILED, SUCCESS → REFUNDED)
- Refunds: Partial refunds tracked separately, payment marked REFUNDED
- Row-level locking: Prevents race conditions during updates
- Dict-based results: Easy JSON serialization
- Custom management command: `python manage.py apply_schema`

## Database Schema

### payments table
```
id                  UUID PK (uuid_generate_v4)
order_id            VARCHAR(255) NOT NULL
idempotency_key     VARCHAR(255) NOT NULL UNIQUE
amount_in_subunits  BIGINT NOT NULL (>0)
currency            VARCHAR(3) DEFAULT 'INR'
status              VARCHAR(20) DEFAULT 'PENDING' (PENDING|SUCCESS|FAILED|REFUNDED)
failure_reason      TEXT
created_at          TIMESTAMPTZ DEFAULT NOW()
updated_at          TIMESTAMPTZ DEFAULT NOW()
```
**Unique index**: One SUCCESS payment per `order_id`

### refunds table
```
id                  UUID PK
payment_id          UUID FK → payments
amount_in_subunits  BIGINT NOT NULL (>0)
reason              TEXT
status              VARCHAR(20) DEFAULT 'SUCCESS'
created_at/updated_at TIMESTAMPTZ
```

## API Endpoints

All endpoints under `/api/`

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `payments/` | Record payment `{order_id, idempotency_key, amount_in_subunits, currency}` |
| `GET` | `payments/{payment_id}/` | Fetch payment |
| `PATCH` | `payments/{payment_id}/` | Update status `{status: 'SUCCESS'|'FAILED', failure_reason?}` |
| `POST` | `payments/{payment_id}/refund/` | Refund `{amount_in_subunits, reason?}` |
| `GET` | `orders/{order_id}/payments/` | List payments for order |

### API Examples (cURL)

**1. Create Payment** (POST /api/payments/)
```bash
curl -X POST http://localhost:8000/api/payments/ \\
  -H 'Content-Type: application/json' \\
  -d '{
    \"order_id\": \"ORD-123\",
    \"idempotency_key\": \"idemp-abc123\",
    \"amount_in_subunits\": 49900,
    \"currency\": \"INR\"
  }'
```
Response: `{success: true, data: {id: '...', status: 'PENDING'}}`

**2. Get Payment** (GET /api/payments/{id}/)
```bash
curl http://localhost:8000/api/payments/a1b2c3d4-e5f6-7890-abcd-ef1234567890/
```

**3. Update Status** (PATCH /api/payments/{id}/)
```bash
curl -X PATCH http://localhost:8000/api/payments/{payment_id}/ \\
  -H 'Content-Type: application/json' \\
  -d '{\"status\": \"SUCCESS\"}'
```

**4. List Order Payments** (GET /api/orders/{order_id}/payments/)
```bash
curl http://localhost:8000/api/orders/ORD-123/payments/
```

**5. Refund Payment** (POST /api/payments/{id}/refund/)
```bash
curl -X POST http://localhost:8000/api/payments/{payment_id}/refund/ \\
  -H 'Content-Type: application/json' \\
  -d '{\"amount_in_subunits\": 20000, \"reason\": \"Customer request\"}'
```


## Architecture

```
Django REST API → Services (Validation/Business Logic) 
               → Repository (Transactions/SQL) 
               → db.py (psycopg2 cursor wrapper)
               → PostgreSQL
```

## Quick Start

1. **Setup Virtual Environment**
   ```bash
   python -m venv venv
   venv\\Scripts\\activate  # Windows
   # source venv/bin/activate  # Linux/Mac
   ```

2. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **PostgreSQL Setup**
   ```bash
   # Create DB if not exists (psql as postgres user)
   createdb payments_db
   
   # Or via pgAdmin/psql:
   CREATE DATABASE payments_db;
   ```
   - Name: `payments_db`
   - User: `postgres`
   - Pass: `paramesh` (settings.py)
   - Port: `5432`
   - Host: `localhost`

4. **Apply Schema** (creates tables, indexes, triggers)
   ```bash
   python manage.py apply_schema
   ```
5. **Verify DB** (optional)
   ```bash
   psql payments_db -c "\dt"
   ```

6. **Run Server**
   ```bash
   python manage.py runserver
   ```

5. **Verify DB** (optional)
   ```bash
   psql payments_db -c "\dt"
   ```

5. **Run Server**
   ```bash
   python manage.py runserver
   ```

6. **Test APIs** (examples above)

## Run Server Command
```bash
python manage.py runserver
```
**Base URL**: `http://localhost:8000/api/`

## Development

- Empty `models.py` (raw SQL approach)
- Raw PostgreSQL queries (no Django ORM)
- DRF APIViews (no ViewSets/Serializers - lightweight)
- Comprehensive validation in `services.py`
- ACID transactions with row locks

## Production Notes

- Change `SECRET_KEY`, `DEBUG=False`, `ALLOWED_HOSTS`
- Use environment variables for DB credentials
- Add logging, rate limiting, auth (DRF TokenAuth ready)
- Consider connection pooling (pgbouncer)

## Tech Stack

- **Backend**: Django 5.1.3 + Django REST Framework 3.14+
- **Database**: PostgreSQL (psycopg2-binary)
- **UUID Extension**: `uuid-ossp`

---
Built for production payments infrastructure
