# Payment Module API

A production-ready **Django + PostgreSQL payment microservice** that records payments, prevents duplicate transactions using idempotency, and supports partial refunds.

The service demonstrates real-world backend design concepts used in payment infrastructure such as transactional safety, state machines, and concurrency handling.

---

# Live Deployment

Base URL

https://backend-payment-module.onrender.com/api/

Example

GET https://backend-payment-module.onrender.com/api/payments/

Hosted on Render.

---

# Tech Stack

Backend
- Django 5.1.3
- Django REST Framework

Database
- PostgreSQL
- psycopg2-binary

Other
- Raw SQL queries
- UUID primary keys
- ACID transactions
- Row-level locking

---

# Features

## Idempotency Support
Duplicate payment requests with the same **idempotency_key** return the existing payment instead of creating a new one.

This prevents duplicate charges during network retries.

## One Successful Payment Per Order
Multiple payment attempts are allowed for an order, but only **one payment can reach SUCCESS state**.

A database constraint enforces this rule.

## Payment State Machine

Valid status transitions:

PENDING → SUCCESS  
PENDING → FAILED  
SUCCESS → REFUNDED

Invalid transitions are rejected.

## Refund Support
Supports **partial and full refunds**.  
Refund records are stored in a separate refunds table.

## Concurrency Safety
Uses **row-level locking and transactions** to prevent race conditions when multiple updates occur simultaneously.

## Clean API Response Structure
All APIs return a consistent JSON structure.

Success Response

{
  "success": true,
  "message": "Optional message",
  "data": {}
}

Error Response

{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "Description"
  }
}

---

# Database Schema

## Payments Table

| Column | Type | Description |
|------|------|-------------|
| id | UUID | Primary key |
| order_id | VARCHAR | Order identifier |
| idempotency_key | VARCHAR | Prevents duplicate requests |
| amount_in_subunits | BIGINT | Amount in paise |
| currency | VARCHAR | Currency code |
| status | VARCHAR | Payment status |
| failure_reason | TEXT | Failure reason |
| created_at | TIMESTAMPTZ | Created timestamp |
| updated_at | TIMESTAMPTZ | Updated timestamp |

Constraint

Only one **SUCCESS** payment allowed per order_id.

---

## Refunds Table

| Column | Type | Description |
|------|------|-------------|
| id | UUID | Refund identifier |
| payment_id | UUID | Reference to payment |
| amount_in_subunits | BIGINT | Refund amount |
| reason | TEXT | Refund reason |
| status | VARCHAR | Refund status |
| created_at | TIMESTAMPTZ | Creation time |

---

# API Endpoints

Base Path

/api/

| Method | Endpoint | Description |
|------|------|-------------|
| POST | payments/ | Record payment |
| GET | payments/{payment_id}/ | Fetch payment |
| PATCH | payments/{payment_id}/ | Update payment status |
| POST | payments/{payment_id}/refund/ | Refund payment |
| GET | orders/{order_id}/payments/ | List order payments |

---

# API Examples (cURL)

These examples can be imported into Postman.

## 1 Create Payment

POST /api/payments/

Use Cases

- initiate payment after order placement
- retry safely after network failure
- record payment before payment gateway processing

curl -X POST "http://localhost:8000/api/payments/" \
  -H "Content-Type: application/json" \
  -d '{
    "order_id": "ORD-123",
    "idempotency_key": "idemp-abc123",
    "amount_in_subunits": 49900,
    "currency": "INR"
  }'

{
  "success": true,
  "message": "Payment recorded.",
  "data": {
    "id": "uuid-here",
    "status": "PENDING",
    "order_id": "ORD-123"
  }
}
---

## 2 Get Payment
GET /api/payments/{payment_id}/

Use Cases

check payment status

frontend polling

admin lookup

curl "http://localhost:8000/api/payments/{payment_id}/"

---

## 3 Update Payment Status

PATCH /api/payments/{payment_id}/

Use Cases

- payment gateway confirms success
- payment gateway declines payment
curl -X PATCH "http://localhost:8000/api/payments/{payment_id}/" \
  -H "Content-Type: application/json" \
  -d '{
    "status": "SUCCESS"
  }'


---

## 4 List Payments for Order

GET /api/orders/{order_id}/payments/

Use Cases

- view order payment history
- detect duplicate payment attempts
curl "http://localhost:8000/api/orders/{order_id}/payments/"


---

## 5 Refund Payment

POST /api/payments/{payment_id}/refund/

Use Cases

- customer refund request
- order cancellation
- partial return
curl -X POST "http://localhost:8000/api/payments/{payment_id}/refund/" \
  -H "Content-Type: application/json" \
  -d '{
    "amount_in_subunits": 20000,
    "reason": "Customer request"
  }'


---

# Architecture

The service follows a layered architecture separating API, business logic, and database operations.

Django REST API  
↓  
Services (validation + business logic)  
↓  
Repository (transactions + SQL queries)  
↓  
db.py (psycopg2 database wrapper)  
↓  
PostgreSQL

This separation improves maintainability and scalability.

---

# Assumptions

1. Each order can have multiple payment attempts but only **one successful payment**.

2. Clients must provide a **unique idempotency_key** for safe retry behavior.

3. Payment amounts are stored in **subunits (paise)** to avoid floating point precision issues.

4. Refunds are allowed **only for successful payments**.

5. Refunds can be **partial or full**, and each refund is stored separately.

6. Payment status must follow valid state transitions.

7. Currency defaults to **INR**.

---

# Quick Start

## 1 Create Virtual Environment

python -m venv venv

Activate

Windows

venv\Scripts\activate

Linux / Mac

source venv/bin/activate

---

## 2 Install Dependencies

pip install -r requirements.txt

---

## 3 Setup PostgreSQL

Create database

CREATE DATABASE payments_db;

Database configuration

Name: payments_db  
User: postgres  
Password: postgres  
Host: localhost  
Port: 5432  

---

## 4 Apply Database Schema

python manage.py apply_schema

This creates

- tables
- indexes
- triggers
- constraints

---

## 5 Run Server

python manage.py runserver

Base API URL

http://localhost:8000/api/

---

# Project Structure

payment_module/

api/ – REST API views  
services/ – business logic  
repository/ – database queries  
db.py – PostgreSQL connection wrapper  
management/ – custom management commands  

---

# Development Notes

- models.py intentionally empty (raw SQL approach)
- Uses raw PostgreSQL queries
- Business logic inside services.py
- ACID transactions with row-level locks

---

# Production Notes

Before deploying:

- Set DEBUG = False
- Configure ALLOWED_HOSTS
- Use environment variables for database credentials

Recommended improvements

- authentication
- rate limiting
- logging
- monitoring
- connection pooling (PgBouncer)

---

