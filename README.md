# SmartPark — Smart Parking Management System (PBL-I)

> **Tagline:** “Smart Parking. Simple Campus.”  
> **Course:** Project-Based Learning (PBL-I)  
> **Tech Stack:** Python Flask, MySQL / SQLite, Bootstrap 5, Vanilla CSS & JavaScript

---

## 1. Project Overview & Objective

**SmartPark** is a complete, responsive, and production-grade web application engineered to solve vehicle congestion and parking mismanagement across educational and enterprise campuses.

The primary objective of **PBL-I** is to digitize campus parking through four core pillars:
1. **Real-time Parking Slot Availability:** Instant visual overview of campus bays with color-coded live statuses (Available 🟢, Occupied 🔴, Maintenance 🟡).
2. **Intelligent Slot Booking:** Conflict-free slot reservations preventing overlapping time-window bookings.
3. **Vehicle & User History:** Auditable digital trails of parking logs, check-ins, and receipts.
4. **Administrative Control Panel:** Role-based dashboard allowing campus administrators to manage parking bays, monitor occupancy, track users, and update reservation states.

---

## 2. PBL-I Scope vs. PBL-II Roadmap

### In-Scope for PBL-I (Implemented & Functional)
* Real-time slot availability visualizer with filters (Section, Floor, Vehicle Type, Status).
* User authentication (Registration, Login, Password Hashing, Session Security).
* Campus vehicle registration (Cars, Bikes, Scooters) with plate validation.
* Slot booking with strict backend overlap-prevention algorithms.
* Booking lifecycle management (Booked ➔ Active ➔ Completed / Cancelled).
* Digital booking confirmation slips/receipts.
* Dedicated Admin Portal (`/admin/login`, `/admin/dashboard`, `/admin/slots`, `/admin/users`, `/admin/bookings`, `/admin/history`).
* Live calculated dashboard analytics directly from database queries.
* Comprehensive vehicle entry/exit history logs.
* Responsive desktop, tablet, and mobile interface with Bootstrap 5.

### Future Scope (PBL-II Roadmap)
* **Automatic Number Plate Recognition (ANPR):** Computer vision camera feed integration using OpenCV and Deep Learning.
* **IoT Hardware Sensors:** Ultrasonic/IR sensors connected via ESP32 / Arduino and MQTT protocol.
* **Interactive Live Campus GIS Map:** Vector maps with turn-by-turn routing to bays.
* **Online Payment Gateways:** UPI / Card / Fastag digital fee collection via Razorpay / Stripe.
* **Automated Barrier Boom Gates:** Hardware relay triggers for automatic boom barrier lifting.

---

## 3. Technology Stack

| Layer | Technology | Details |
|---|---|---|
| **Backend** | Python 3.11+ / Flask | Modular Blueprints (`auth`, `user`, `booking`, `admin`), parameterized SQL queries |
| **Frontend** | HTML5, CSS3, JavaScript | Bootstrap 5, Bootstrap Icons, Custom sleek smart-campus theme |
| **Database** | MySQL (with SQLite automatic fallback) | PyMySQL driver with DictCursor, foreign key constraints |
| **Security** | Werkzeug Security | Password hashing (`scrypt` / `pbkdf2`), Flask sessions, Role-Based Access Control |

---

## 4. System Architecture & Folder Structure

```
smartpark/
├── app.py                     # Main Flask application initialization and error handlers
├── config.py                  # App configuration and environment variable loading
├── requirements.txt           # Python dependencies
├── .env.example               # Example environment variables
├── .env                       # Local environment configuration
├── init_db.py                 # Database setup and schema/seed executor utility
├── README.md                  # Complete documentation
│
├── database/
│   ├── db.py                  # Database connection abstraction layer (MySQL & SQLite)
│   ├── schema.sql             # MySQL schema definitions
│   ├── seed.sql               # Seed data for admin, sample users, slots, bookings
│   └── smart_parking.db       # Local database store
│
├── routes/
│   ├── __init__.py
│   ├── auth.py                # Registration, login, logout, password hashing, session guards
│   ├── user.py                # User dashboard, profile, vehicles CRUD, parking history
│   ├── booking.py             # Parking availability, slot booking logic, overlap validation
│   └── admin.py               # Admin auth, dashboard stats, slot/user/booking management
│
├── templates/
│   ├── base.html              # Base layout with navbar, footer, toast container
│   ├── index.html             # Landing page (Hero, How It Works, Features, Live preview)
│   ├── future_scope.html      # PBL-II Future Scope showcase
│   ├── login.html             # User login portal
│   ├── register.html          # User registration portal
│   ├── dashboard.html         # User dashboard with stats and active booking card
│   ├── parking.html           # Real-time visual slot grid with filters and booking modal
│   ├── booking.html           # Dedicated booking form
│   ├── booking_confirm.html   # Digital confirmation receipt
│   ├── my_bookings.html       # User bookings list with filter tabs
│   ├── vehicles.html          # Vehicle management (Add/Edit/Delete)
│   ├── history.html           # Vehicle parking history with date and status filters
│   ├── profile.html           # User profile and password security
│   ├── errors/
│   │   ├── 403.html           # Forbidden access error page
│   │   ├── 404.html           # Page not found error page
│   │   └── 500.html           # Server error page
│   └── admin/
│       ├── login.html         # Admin login portal
│       ├── dashboard.html     # Admin dashboard with 8 KPI metrics & slot bay overview
│       ├── slots.html         # Parking slot management (Add/Edit/Delete/Status)
│       ├── users.html         # Registered campus users directory
│       ├── bookings.html      # All campus bookings with status controls
│       └── history.html       # Full campus vehicle parking audit logs
│
└── static/
    ├── css/
    │   └── style.css          # Modern smart-campus typography, slot grid colors, responsive layouts
    └── js/
        └── app.js             # Toast alerts, modals, time conflict validation, interactive toggles
```

---

## 5. Database Design & Entity Relationships

The system operates on 5 relational tables:

1. **`users`**: User profiles with hashed passwords and role flags (`user`, `admin`).
2. **`vehicles`**: Campus vehicles registered by users (`user_id` foreign key).
3. **`parking_slots`**: Campus bays defined by slot number, section, floor, vehicle type, and status (`available`, `occupied`, `maintenance`).
4. **`bookings`**: Reservations with user, vehicle, slot, date, start time, end time, and status (`booked`, `active`, `completed`, `cancelled`).
5. **`parking_history`**: Audit trail recording actual entry timestamps, exit timestamps, vehicle number, and session states.

---

## 6. Installation & Setup Guide

### Step 1: Clone or Open Project
Open the project directory in VS Code or your terminal:
```bash
cd "c:\Users\Tanish Jain\Downloads\PBL - I"
```

### Step 2: Create and Activate Virtual Environment
```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# Linux / macOS
python3 -m venv .venv
source .venv/bin/activate
```

### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 4: Configure Environment Variables
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
Default `.env` values:
```ini
SECRET_KEY=smartpark-secret-key-super-secure-change-in-prod-2026
DB_TYPE=mysql
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=
MYSQL_DB=smart_parking
FLASK_ENV=development
FLASK_DEBUG=1
PORT=5000
```

> **Note on Zero-Config Fallback:** If your MySQL server is not running (or during instant evaluator testing), SmartPark will automatically fall back to its embedded SQLite database without crashing.

### Step 5: Initialize Database & Seed Data
Run the initialization script:
```bash
python init_db.py
```
This automatically sets up all tables and loads seed data for the admin, sample users, vehicles, and parking slots.

### Step 6: Start Flask Web Server
```bash
python app.py
```
Open your browser and navigate to:
```
http://127.0.0.1:5000
```

---

## 7. Default Seed Credentials

### 🛡️ Administrator Account
* **URL:** `http://127.0.0.1:5000/admin/login`
* **Email:** `admin@smartpark.com`
* **Password:** `Admin@123`

### 👤 Sample Student/User Accounts
* **Email:** `rahul.sharma@example.com`
* **Password:** `User@123`
* **Registered Vehicles:** `GJ01AB1234` (Car), `GJ01CD5678` (Bike)

* **Email:** `priya.patel@example.com`
* **Password:** `User@123`
* **Registered Vehicles:** `MH02EF9012` (Car), `MH02GH3456` (Scooter)

---

## 8. Complete Workflows

### 🚗 User Workflow
1. Navigate to `http://127.0.0.1:5000/register` and create an account.
2. Sign in at `/login`.
3. Go to **My Vehicles** (`/vehicles`) and register your car or two-wheeler.
4. Click **Parking Availability** (`/parking`) to view real-time slot colors.
5. Click **Book Now** on an available green slot.
6. Select your vehicle, date, and time interval.
7. Confirm booking and receive your digital booking confirmation slip.
8. View and manage your reservation in **My Bookings** (`/my-bookings`) or cancel if needed.
9. Review historical entry/exit timestamps in **Vehicle History** (`/history`).

### 🛡️ Admin Workflow
1. Log in at `http://127.0.0.1:5000/admin/login` with `admin@smartpark.com` / `Admin@123`.
2. Inspect the **Admin Dashboard** for live KPI cards (Total Slots, Available, Occupied, Maintenance, Users, Bookings).
3. Access **Manage Slots** (`/admin/slots`) to add new bays, edit sections, or toggle maintenance status.
4. Review **Campus Users** (`/admin/users`) to view registered students and vehicle counts.
5. Open **All Bookings** (`/admin/bookings`) to mark reservations as *Active (Parked)*, *Completed (Exited)*, or *Cancelled*.
6. Monitor the campus audit logs under **Campus History** (`/admin/history`).

---

## 9. Security & Validation Highlights

* **Password Protection:** Strong hashing via Werkzeug `scrypt` algorithms.
* **SQL Injection Prevention:** 100% parameterized database queries.
* **Role-Based Authorization:** Custom decorators `@login_required` and `@admin_required`.
* **Booking Conflict Engine:** Prevents double-booking slots for identical or overlapping time windows:
  $$\text{Overlap} \iff (\text{Existing Start} < \text{New End}) \land (\text{Existing End} > \text{New Start})$$
* **Data Ownership Safeguards:** Users cannot view, modify, or cancel other users' vehicles or reservations.

---

## 10. Authors & Acknowledgements

* **Project:** SmartPark – Smart Parking Management System
* **Submission Category:** PBL-I (Project-Based Learning)
* **Status:** Complete, Tested, and Production-Ready
