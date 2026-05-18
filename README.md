# MARS — Mac Address Registration System

MARS is a full-stack platform designed to automate classroom and departmental attendance tracking using passive local network telemetry. By combining hardware-level radio wave analysis with a modern cloud-backed database architecture, MARS eliminates human error from tracking student presence.

---

#  System Architecture & Data Flow

MARS uses a distributed **Edge-to-Cloud** design:

1. **The Edge (Scanner)**  
   The teacher runs a portable standalone executable application (`scanner.py`) on their laptop. It dynamically tracks the active local WiFi subnet using Layer 2 ARP broadcasts.

2. **The Cloud (Backend API)**  
   A Flask RESTful service hosted in the cloud parses edge telemetry payloads, verifies unique physical identifiers against a Postgres pool, and commits instant records.

3. **The Data Layer (Supabase)**  
   Relational models capture point-in-time state tables for automated analytical reporting and historical evaluation.

4. **The Client (Web Frontend)**  
   An atomic desktop dashboard provides real-time data streams and interactive telemetry maps.

---

# Tech Stack

- **Backend Framework**: Flask (Python 3.x)
- **Database Layer**: PostgreSQL (Hosted via Supabase)
- **ORM / Migrations**: SQLAlchemy & Flask-Migrate (Alembic)
- **Security & Cryptography**: Flask-JWT-Extended & Flask-Bcrypt
- **Edge Hardware Interface**: Scapy (Layer 2 Packet Crafting Engine) & Requests
- **Environment & Dependency Management**: Pipenv

---

# Database Schema Blueprint

The system maps domain metrics uniformly across six highly decoupled metadata tables:

- **`teachers`**  
  Handles system access with strict email verification controls, password hashing parameters, and nullable department connections (`dept_id`).

- **`departments`**  
  Root organizational entity linking tracking data pools to academic categories.

- **`students`**  
  Atomic core of student data containing names, code profiles, and academic allocations.

- **`devices`**  
  Maps unique physical network identifiers (`mac_address`) directly to individual student profiles.

- **`attendance_logs`**  
  Tracks point-in-time network encounters with status definitions.

- **`reports`**  
  Historical analytical snapshots capturing department-wide performance variables.

---

#  Installation & Local Development Setup

## 1. Prerequisites

Ensure you have the following installed globally on your machine:

- Python 3.10+
- Pipenv

## 2. Environment Configuration

Create a `.env` file in the root directory of your project to inject configuration variables:

```ini
DATABASE_URL=postgresql://<user>:<password>@<host>:<port>/<db_name>
JWT_SECRET_KEY=your-secure-jwt-signature-key
```

---

## 3. Installation Steps

Clone the project structure, initialize the virtual environment, and install dependencies directly from the lock file:

```bash
# Clone and enter directory
git clone https://github.com/your-username/mars-backend.git

cd mars-backend

# Install dependencies from Pipfile.lock
pipenv install

# Activate virtual environment
pipenv shell

# Execute pending schema migrations
flask db upgrade

# Run the local micro-service container
python3 app.py
```

The core application service boots dynamically over:

```txt
http://0.0.0.0:5000
```

---

# Core API Route Documentation

All requests and responses use standard `application/json` structures.

Protected endpoints demand a:

```txt
Bearer <JWT_TOKEN>
```

string injected into the request's `Authorization` header.

---

# 🔐 Authentication Module (`/auth`)

| Endpoint | Method | Security | Payload Requirement | Description |
|---|---|---|---|---|
| `/auth/register` | POST | Public | `first_name`, `last_name`, `email`, `password`, `dept_id` *(optional)* | Enrolls a new administrative Teacher account. |
| `/auth/login` | POST | Public | `email`, `password` | Validates records and returns an `access_token` valid for 1 hour. |
| `/auth/me` | GET | JWT | None | Fetches fully serialized information of the active user session. |
| `/auth/me` | PATCH | JWT | `first_name` \| `last_name` \| `email` \| `password` | Safely updates active teacher states with duplicate checks. |

---

# 👥 Student Management Module (`/students`)

| Endpoint | Method | Security | URL Parameters / Payloads | Description |
|---|---|---|---|---|
| `/students` | GET | JWT | Query Param: `?search=<name_or_code>` | Returns a fuzzy-searched list of registered students. |
| `/students` | POST | JWT | `student_code`, `first_name`, `last_name`, `email`, `dept_id`, `mac_address` | Performs an atomic injection creating both student and device assets. |
| `/students/<id>` | GET | JWT | Path ID | Aggregates individual info alongside all matched physical devices. |
| `/students/<id>` | DELETE | JWT | Path ID | Cascades deletion through child hardware profiles. |
| `/students/<id>/activity` | GET | JWT | Path ID | Groups historical active counters into time-series data maps. |

---

# 📶 Attendance Logging Module (`/attendance`)

| Endpoint | Method | Security | Payload Requirement | Description |
|---|---|---|---|---|
| `/attendance/scan` | POST | Public | `mac_address` | Hardware Entry Hook: Appends instant records on matching targets. |
| `/attendance/stats` | GET | JWT | None | Returns distinct summaries (Present/Absent totals) for the day. |
| `/attendance/live` | GET | JWT | None | Yields a sliding window of the latest 10 localized network connections. |

---

# 📊 Reports & CSV Marshalling Engine (`/reports`)

| Endpoint | Method | Security | Payload Requirement | Description |
|---|---|---|---|---|
| `/reports` | GET | JWT | None | Fetches historical generated data streams across the deployment. |
| `/reports/generate` | POST | JWT | `dept_id`, `report_type` | Runs database aggregations to compute point-in-time metrics. |
| `/reports/<id>/export` | GET | JWT | Path ID | Generates an in-memory stream for browser-side CSV downloads. |
| `/reports/<id>` | DELETE | JWT | Path ID | Strict ownership rule: drops snapshots if user matches creator. |

---

# 💻 Edge Scanning Client Setup (Option 2 Deployment)

The `utils/scanner.py` script acts as a portable network sniffer.

To deploy this to end-users (Teachers) as a standalone consumer app, run `sudo python3 app/utils/scanner.py` from the root folder, outside the virtual environment.


# Known Operational Nuances

## MAC Randomization

Modern mobile operating systems utilize rotation protocols across generic access links.

Advise students to select:

```txt
Use Device MAC
```

for the campus WiFi link to protect record integrity.

---

## Network Isolation

The edge scanner must operate on subnets where internal client communication loops (Access Point Isolation) are systematically deactivated.
