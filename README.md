# Payment Module API

A production-ready **Django + PostgreSQL payments API microservice**.

---

# Features

* **Idempotency**: Duplicate requests (same `idempotency_key`) return existing payment
* **One successful payment per order**: Unique constraint prevents double payment
* **State machine**: Valid status transitions only
  `PENDING → SUCCESS/FAILED`
  `SUCCESS → REFUNDED`
* **Refunds**: Partial refunds tracked separately, payment marked `REFUNDED`
* **Row-level locking**: Prevents race conditions during updates
* **Dict-based results**: Easy JSON serialization
* **Custom management command**:

  ```bash
  python manage.py apply_schema
  ```

---

# Database Schema

## payments table

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

**Unique index:** One `SUCCESS` payment per `order_id`

---

## refunds table

```
id                  UUID PK
payment_id          UUID FK → payments
amount_in_subunits  BIGINT NOT NULL (>0)
reason              TEXT
status              VARCHAR(20) DEFAULT 'SUCCESS'
created_at          TIMESTAMPTZ
updated_at          TIMESTAMPTZ
```

---

# API Endpoints

All endpoints are under:

```
/api/
```

| Method | Endpoint                        | Description                |
| ------ | ------------------------------- | -------------------------- |
| POST   | `payments/`                     | Record payment             |
| GET    | `payments/{payment_id}/`        | Fetch payment              |
| PATCH  | `payments/{payment_id}/`        | Update payment status      |
| POST   | `payments/{payment_id}/refund/` | Refund payment             |
| GET    | `orders/{order_id}/payments/`   | List payments for an order |

---

# API Examples (cURL)

These commands can be **directly imported into Postman**.

---

# 1. Create Payment

### Endpoint

```
POST /api/payments/
```

### Use Cases

* Initiate payment after order placement
* Retry safely if network fails
* Record payment before PSP processing

### Status Codes

| Code | Meaning                                               | Success |
| ---- | ----------------------------------------------------- | ------- |
| 201  | Payment created                                       | Yes     |
| 200  | Duplicate idempotency key (existing payment returned) | Yes     |
| 400  | Invalid JSON                                          | No      |
| 422  | Validation error                                      | No      |
| 409  | Order already paid                                    | No      |

### cURL

```bash
curl -X POST "http://localhost:8000/api/payments/" \
  -H "Content-Type: application/json" \
  -d '{
    "order_id": "ORD-123",
    "idempotency_key": "idemp-abc123",
    "amount_in_subunits": 49900,
    "currency": "INR"
  }'
```

### Success Response

```json
{
  "success": true,
  "message": "Payment recorded.",
  "data": {
    "id": "uuid-here",
    "status": "PENDING",
    "order_id": "ORD-123"
  }
}
```

---

# 2. Get Payment

### Endpoint

```
GET /api/payments/{payment_id}/
```

### Use Cases

* Check payment status after PSP webhook
* Frontend polling
* Admin lookup

### Status Codes

| Code | Meaning           |
| ---- | ----------------- |
| 200  | Payment found     |
| 404  | Payment not found |

### cURL

```bash
curl "http://localhost:8000/api/payments/a1b2c3d4-e5f6-7890-abcd-ef1234567890/"
```

### Success Response

```json
{
  "success": true,
  "data": {
    "id": "uuid-here",
    "status": "SUCCESS"
  }
}
```

---

# 3. Update Payment Status

### Endpoint

```
PATCH /api/payments/{payment_id}/
```

### Use Cases

* PSP confirms payment
* PSP declines payment
* Internal payment processing updates

### Status Codes

| Code | Meaning                  |
| ---- | ------------------------ |
| 200  | Status updated           |
| 400  | Invalid JSON             |
| 404  | Payment not found        |
| 422  | Invalid state transition |

### cURL

```bash
curl -X PATCH "http://localhost:8000/api/payments/{payment_id}/" \
  -H "Content-Type: application/json" \
  -d '{
    "status": "SUCCESS"
  }'
```

### Success Response

```json
{
  "success": true,
  "message": "Payment status updated.",
  "data": {
    "status": "SUCCESS"
  }
}
```

---

# 4. List Payments for Order

### Endpoint

```
GET /api/orders/{order_id}/payments/
```

### Use Cases

* Show order payment history
* Check payment status for order
* Prevent duplicate payments

### Status Codes

| Code | Meaning          |
| ---- | ---------------- |
| 200  | List returned    |
| 422  | Invalid order id |

### cURL

```bash
curl "http://localhost:8000/api/orders/ORD-123/payments/"
```

### Success Response

```json
{
  "success": true,
  "data": {
    "order_id": "ORD-123",
    "count": 1,
    "payments": []
  }
}
```

---

# 5. Refund Payment

### Endpoint

```
POST /api/payments/{payment_id}/refund/
```

### Use Cases

* Customer refund request
* Partial order return
* PSP refund record

### Status Codes

| Code | Meaning               |
| ---- | --------------------- |
| 201  | Refund created        |
| 400  | Invalid JSON          |
| 404  | Payment not found     |
| 422  | Invalid refund amount |

### cURL

```bash
curl -X POST "http://localhost:8000/api/payments/{payment_id}/refund/" \
  -H "Content-Type: application/json" \
  -d '{
    "amount_in_subunits": 20000,
    "reason": "Customer request"
  }'
```

### Success Response

```json
{
  "success": true,
  "message": "Refund successful.",
  "data": {
    "id": "refund-uuid"
  }
}
```

---

# Architecture

```
Django REST API
       ↓
Services (validation + business logic)
       ↓
Repository (transactions + SQL)
       ↓
db.py (psycopg2 cursor wrapper)
       ↓
PostgreSQL
```

---

# Quick Start

## 1. Setup Virtual Environment

```bash
python -m venv venv
```

Activate environment:

**Windows**

```bash
venv\Scripts\activate
```

**Linux / Mac**

```bash
source venv/bin/activate
```

---

## 2. Install Dependencies

```bash
pip install -r requirements.txt
```

---

## 3. PostgreSQL Setup

Create database:

```bash
createdb payments_db
```

Or inside PostgreSQL:

```sql
CREATE DATABASE payments_db;
```

Database config:

```
Name: payments_db
User: postgres
Password: paramesh
Port: 5432
Host: localhost
```

---

## 4. Apply Database Schema

```bash
python manage.py apply_schema
```

This creates:

* tables
* indexes
* triggers
* constraints

---

## 5. Verify Database (Optional)

```bash
psql payments_db -c "\dt"
```

---

## 6. Run Server

```bash
python manage.py runserver
```

Base API URL:

```
http://localhost:8000/api/
```

---

# Development Notes

* `models.py` intentionally empty (raw SQL approach)
* Uses **raw PostgreSQL queries**
* DRF **APIView** (no serializers or viewsets)
* Business logic inside `services.py`
* ACID transactions with **row-level locks**

---

# Production Notes

Before deployment:

* Set `DEBUG = False`
* Change `SECRET_KEY`
* Configure `ALLOWED_HOSTS`
* Use **environment variables** for DB credentials
* Add:

  * authentication
  * rate limiting
  * logging
  * monitoring
* Consider **pgbouncer** for connection pooling

---

# Tech Stack

**Backend**

* Django 5.1.3
* Django REST Framework 3.14+

**Database**

* PostgreSQL
* psycopg2-binary

**Extensions**

* `uuid-ossp` for UUID generation

---

Built for **production-grade payment infrastructure**.
