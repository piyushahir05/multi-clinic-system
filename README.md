# Multi-Clinic Doctor Appointment System

A full-stack web application to manage doctor appointments across multiple clinics with role-based access for Patients, Doctors, and Admins.

> **Status:** Production-ready. Core features implemented, tested, and documented.

---

## What’s New (Aug 15, 2025)

- ✅ End-to-end booking flow hardened (race-condition & double-booking protection)
- ✅ Role-based dashboards (Patient / Doctor / Admin)
- ✅ Admin CRUD for Clinics, Doctors, Time Slots, Appointments
- ✅ Doctor schedule management & day-wise availability
- ✅ UI refresh with Bootstrap 5 + accessible forms
- ✅ DB migrations via Flask-Migrate
- ✅ Postgres in production; SQLite for local dev
- ✅ Centralized config via `.env`
- ✅ Linting & basic tests (pytest)
- ✅ CSRF + strong password hashing (Werkzeug), sensible session settings

---

## Tech Stack

**Frontend**
- HTML, CSS, Vanilla JavaScript (no SPA framework)
- Bootstrap 5.3, Font Awesome 6

**Backend**
- Flask (Blueprint/MVC structure)
- Jinja2 templates
- Flask-SQLAlchemy, Flask-Migrate
- Werkzeug security
- Optional: Flask-Limiter (rate-limiting), ProxyFix (behind reverse proxy)

**Database**
- **Local Dev:** SQLite (zero-setup)
- **Production:** PostgreSQL
- Configurable via `DATABASE_URL`

---

## Architecture

### App Structure
- **Blueprints:** `auth`, `booking`, `admin`, `doctor`
- **Models:** `User`, `Clinic`, `Doctor`, `TimeSlot`, `Appointment`
- **Patterns:** MVC with services/helpers for reusable logic
- **Sessions:** Secure server-side sessions; role-based redirects

### Data Model (high-level)
```
User (id, email, password_hash, role)
Clinic (id, name, address, phone, email)
Doctor (id, user_id -> User, clinic_id -> Clinic, specialization, license_no, years_exp)
TimeSlot (id, doctor_id -> Doctor, start, end, is_available)
Appointment (id, patient_id -> User, doctor_id -> Doctor, timeslot_id -> TimeSlot, status)
```

**Double-Booking Prevention**
- Unique constraint on `(doctor_id, timeslot_id)` and status logic
- Transactional booking: check-then-book within a single DB transaction

---

## Features

- **Patient:** Register/login, browse clinics & doctors, book/reschedule/cancel, history
- **Doctor:** Manage availability & time slots, view day agenda, confirm/complete visits
- **Admin:** CRUD clinics/doctors/slots/appointments, assign doctors to clinics
- **UX:** Responsive, accessible forms, client+server validation

---

## API (Selected Endpoints)

> All endpoints assume authenticated sessions & role checks.

**Auth**
- `POST /auth/register` — {email, password, role}
- `POST /auth/login` — {email, password}
- `POST /auth/logout`

**Patient Booking**
- `GET /booking/clinics`
- `GET /booking/clinics/<clinic_id>/doctors`
- `GET /booking/doctors/<doctor_id>/timeslots?date=YYYY-MM-DD`
- `POST /booking/appointments` — {doctor_id, timeslot_id}
- `PATCH /booking/appointments/<id>` — reschedule/cancel

**Doctor**
- `GET /doctor/schedule?date=YYYY-MM-DD`
- `POST /doctor/timeslots` — bulk add/manage

**Admin**
- CRUD under `/admin/*` for clinics, doctors, timeslots, users, appointments

---

## Getting Started (Local Dev)

### Prerequisites
- Python 3.10+
- (Optional) PostgreSQL 14+

### Setup
```bash
git clone <your-repo>
cd multi-clinic-appointment-system

python -m venv venv
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate

pip install -r requirements.txt
```

Create `.env` (dev defaults shown):
```env
FLASK_ENV=development
FLASK_DEBUG=1
SESSION_SECRET=change-this-to-a-long-random-string
DATABASE_URL=sqlite:///clinic_appointments.db
# For Postgres in prod: postgresql+psycopg2://user:pass@host:5432/clinic_appointments
# Optional security hardening:
SESSION_COOKIE_SECURE=False
SESSION_COOKIE_HTTPONLY=True
SESSION_COOKIE_SAMESITE=Lax
```

Initialize DB & run:
```bash
# Create tables (migrations recommended)
flask db init
flask db migrate -m "init"
flask db upgrade

python main.py
# App available at http://localhost:5000
```

> **Seed Admin (recommended):** add a simple CLI or one-time script to create an admin user instead of shipping default credentials.

---

## Production Deployment

- **Server:** Gunicorn / uWSGI
- **Reverse Proxy:** Nginx (enable HTTPS, HSTS)
- **WSGI/Proxy:** Use `ProxyFix` if behind a proxy/load balancer
- **DB:** PostgreSQL; configure `DATABASE_URL`
- **Migrations:** `flask db upgrade` on deploy
- **Security:**
  - Strong `SESSION_SECRET`
  - `SESSION_COOKIE_SECURE=True`, `SAMESITE=Strict` (if feasible)
  - Disable debug, enable structured logging
  - Rate-limit auth & booking endpoints (Flask-Limiter)
  - Regular backups (DB + `.env` excluded from VCS)

Example (systemd + Gunicorn sketch):
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:8000 'app:create_app()'
```

---

## Project Structure
```
multi-clinic-appointment-system/
├── app.py                 # Flask app factory & extensions
├── main.py                # Dev entrypoint
├── models.py              # SQLAlchemy models
├── requirements.txt
├── .env                   # Local config (do NOT commit)
├── routes/
│   ├── auth.py
│   ├── booking.py
│   ├── admin.py
│   └── doctor.py
├── services/              # (Optional) business logic helpers
├── templates/
│   ├── base.html
│   ├── auth/
│   ├── booking/
│   ├── admin/
│   └── doctor/
└── static/
    ├── css/
    ├── js/
    └── images/
```

---

## Testing & Quality

Install dev tools:
```bash
pip install pytest pytest-flask flake8 black
```

Run:
```bash
pytest
flake8
black --check .
```

Suggested tests:
- Auth (register/login/logout, role redirects)
- Booking (race conditions, double-booking, reschedule)
- Doctor schedule CRUD
- Admin CRUD & permissions

---

## Accessibility & UX

- Form labels, ARIA for dynamic components
- Keyboard navigation focus states
- Sufficient color contrast
- Error summaries near form tops

---

## Troubleshooting

- **Port in use:** change port in `main.py` or run `python main.py --port 5050`
- **DB connection fails:** verify `DATABASE_URL` & service status
- **Migrations drift:** `flask db stamp head && flask db migrate && flask db upgrade`
- **Static not loading in prod:** ensure Nginx serves `/static` or let Flask serve with proper config

---

## Roadmap (Optional)

- Calendar view with drag-drop reschedule
- Email/SMS reminders
- Multi-clinic analytics dashboard
- i18n (English + regional languages)
- Audit logs for admin actions
- Patient-doctor chat (secure, ephemeral)

---

## License

MIT (or your preferred license)

---

## Acknowledgements

Built with Flask, Bootstrap, SQLAlchemy, and a lot of coffee ☕
