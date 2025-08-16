# 🏥 Multi-Clinic Doctor Appointment System

A full-stack Flask web app to manage doctor appointments across multiple clinics with role-based access for Patients, Doctors, and Admins.

**Status:** Production-ready · Secure booking flow · Role-based dashboards · Responsive UI

---

## 🚀 Features

* **Patient:** Browse clinics/doctors, book/reschedule/cancel appointments
* **Doctor:** Manage availability, view daily agenda
* **Admin:** CRUD for clinics, doctors, time slots, appointments
* **Security:** CSRF protection, hashed passwords, session hardening
* **UX:** Responsive (Bootstrap 5), accessible forms, client+server validation

---

## 🛠️ Tech Stack

<table>
  <tr>
    <th>Layer</th>
    <th>Tools & Libraries</th>
  </tr>
  <tr>
    <td><b>Frontend</b></td>
    <td>HTML, CSS, JavaScript, Bootstrap 5</td>
  </tr>
  <tr>
    <td><b>Backend</b></td>
    <td>Flask, Jinja2, Flask-SQLAlchemy, Flask-Migrate</td>
  </tr>
  <tr>
    <td><b>Database</b></td>
    <td>SQLite (dev), PostgreSQL (prod)</td>
  </tr>
  <tr>
    <td><b>Security</b></td>
    <td>Werkzeug, CSRF, secure sessions</td>
  </tr>
  <tr>
    <td><b>Testing</b></td>
    <td>Pytest, Flake8, Black</td>
  </tr>
  <tr>
    <td><b>Deployment</b></td>
    <td>Gunicorn, Docker, Nginx, Heroku / AWS</td>
  </tr>
</table>

---

## 📁 Project Structure

```
multi-clinic-appointment-system/
├── app.py / main.py
├── models.py / routes/ / services/
├── templates/ / static/
├── requirements.txt / .env
```

---

## ⚙️ Local Setup

### Prerequisites

* Python 3.10+
* (Optional) PostgreSQL 14+

### Steps

```bash
git clone <repo>
cd multi-clinic-appointment-system
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Create a `.env` file

```
FLASK_ENV=development
DATABASE_URL=sqlite:///clinic_appointments.db
SESSION_SECRET=your-secret-key
```

### Initialize DB

```bash
flask db init
flask db migrate -m "init"
flask db upgrade
python main.py
```

App runs at: **[http://localhost:5000](http://localhost:5000)**

---

## 📅 Roadmap

* Calendar view with drag-drop reschedule
* Email/SMS reminders
* Analytics dashboard
* Audit logs & secure chat

---

## 📄 License

MIT

---

## 🙏 Acknowledgements

Built with Flask, Bootstrap, SQLAlchemy, and a lot of ☕.
