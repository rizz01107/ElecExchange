# ElecExchange — Used Electronics Exchange Platform

A full-stack web application for buying and selling used electronics, built with Python (Flask) and SQLite. No database setup required — just install Flask and run.

---

## Tech Stack

- **Backend:** Python 3.11 + Flask
- **Database:** SQLite (auto-created on first run)
- **Frontend:** HTML5, Bootstrap 5, JavaScript
- **Auth:** Session-based with SHA-256 password hashing

---

## Getting Started

**1. Install dependency**
```bash
pip install flask
```
**2. Run the app**
```Bash
python app.py
```
**3. Open in browser**
```bash
[http://127.0.0.1:5000](http://127.0.0.1:5000)
```
**The database (database.db) is created automatically on first run with sample data.**

---
## Default Accounts

| Role  | Email             | Password |
|-------|-------------------|----------|
| Admin | admin@elec.com    | password |
| User  | ali@gmail.com     | password |
| User  | sara@gmail.com    | password |

---
## Features

- User registration with 6-digit verification code
- Login / Logout with session management
- List products with image upload, category & condition
- Filter by category, condition, sort by price
- Search products by keyword
- Place orders with payment method selection (COD, EasyPaisa, JazzCash, Bank Transfer)
- Refund request system
- Star ratings & reviews
- Admin dashboard — manage users, products, transactions

---
## Project Structure

```text
elec_exchange_v2/
├── app.py                  # All routes and logic
├── requirements.txt        # pip install flask
├── database.db             # Auto-created SQLite DB
├── static/
│   └── uploads/            # Product images
└── templates/
    ├── base.html
    ├── index.html
    ├── login.html
    ├── register.html
    ├── verify.html
    ├── product.html
    ├── add_product.html
    ├── search.html
    ├── user/
    │   ├── profile.html
    │   ├── my_listings.html
    │   └── my_orders.html
    └── admin/
        ├── dashboard.html
        ├── users.html
        ├── products.html
        └── transactions.html
```
---
## Reset Database

Delete `database.db` and restart — sample data will reload automatically.

---

## Developer

**Muhammad Rizwan**
