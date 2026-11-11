# Hostel Management System (HMS)

A complete, beginner-friendly, full-stack Python web application for hostel management built with **Flask**, **MongoDB (PyMongo)**, **Flask-Login**, **Flask-WTF**, and **Bootstrap 5**.

---

## 🌟 Features & Roles

### 1. Role-Based Access Control (RBAC)
- **Admin**: Full control — manage wardens, residential blocks, rooms, fees, financial reports, occupancy analytics.
- **Warden**: Daily operations — manage student admissions, room allocation & checkout, complaint status, leave/outpass approvals, visitor registry, notices, mess menu & attendance.
- **Student**: Self-service portal — view allocated room & roommates, fee breakdown & payment history, submit complaints with live tracking, apply for leaves/outpasses, view weekly mess menu and hostel notices.

### 2. Modules
1. **Authentication**: Secure login/logout, password hashing with Werkzeug, role-based redirects, change password.
2. **Student Management**: Full profile (roll no, course, year, contact, guardian info, address, optional photo upload), search, filter, pagination, checkout status.
3. **Block & Room Management**: Blocks with floor breakdown, rooms by type (Single, Double, Triple), real-time capacity and bed vacancy tracking, maintenance status.
4. **Room Allocation**: Assign students without overbooking capacity, prevent duplicate allocations, room change, checkout to free beds, complete allocation history.
5. **Fee Management**: Flexible fee structures (Hostel, Mess, Maintenance), partial & full payment recording with date & mode (Cash, UPI, Online, Cheque), printable receipt page with auto-numbering, defaulters list.
6. **Mess Management**: 7-day weekly menu (breakfast, lunch, dinner) editable by Warden/Admin, daily meal attendance tracking, monthly student meal consumption summary.
7. **Complaints**: Student ticket submission across categories (Plumbing, Electrical, Internet, Cleanliness, Food, etc.), warden status workflow (Open → In Progress → Resolved) with administrative remarks.
8. **Leave & Outpass**: Student date-range leave application, warden review and approval/rejection with remarks.
9. **Visitor Log**: Record visitor identity, student visited, purpose, arrival time, and one-click exit time stamping.
10. **Notices & Announcements**: Warden/Admin broadcast notices with priority badges (Normal vs Urgent) prominently shown on dashboards.
11. **Dashboards & Visualizations**:
    - **Admin/Warden**: KPI stat cards, Interactive Chart.js charts for Block Occupancy (stacked bar) and 6-Month Fee Collection (line chart), latest notices.
    - **Student**: Room info card, fee summary alert, quick action shortcuts, recent complaints and notices.
12. **Reports & Exports**: Block occupancy report, fee collection report, fee defaulters list — with one-click **CSV download** for each.

---

## 🛠️ Tech Stack

- **Backend**: Python 3.11+, Flask (Modular Blueprints architecture)
- **Database**: MongoDB via PyMongo
- **Authentication**: Flask-Login + Werkzeug Security
- **Forms & CSRF**: Flask-WTF / WTForms
- **Frontend**: Jinja2 Templates, Bootstrap 5 (CDN), Bootstrap Icons, Chart.js (CDN), Vanilla JavaScript
- **Configuration**: python-dotenv

---

## 🚀 Quick Start Guide (Windows PowerShell)

Follow these exact commands step-by-step in Windows PowerShell:

### Step 1: Open Terminal in Project Directory
```powershell
cd "c:\Users\hp\Desktop\Hostel Management System\hostel-management-system"
```

### Step 2: Create Virtual Environment
```powershell
python -m venv venv
```

### Step 3: Activate Virtual Environment
```powershell
.\venv\Scripts\Activate.ps1
```
*(If PowerShell shows a script execution error, run: `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` then re-run the activate command)*

### Step 4: Install Dependencies
```powershell
pip install -r requirements.txt
```

### Step 5: Configure Environment (.env)
Copy the example file to `.env`:
```powershell
Copy-Item .env.example .env
```
Open `.env` in any text editor if you wish to adjust the MongoDB URI or Secret Key:
```env
MONGO_URI=mongodb://127.0.0.1:27017
DB_NAME=hostel_db
SECRET_KEY=hms-super-secret-key-production-2024
```

### Step 6: Start MongoDB
Choose either **Option A (Local)** or **Option B (Cloud / Free Atlas)**:

#### Option A: Local MongoDB
If MongoDB is installed locally on your machine, start the MongoDB service or daemon:
```powershell
# If installed as a Windows service:
net start MongoDB

# Or run mongod directly:
mongod --dbpath "C:\data\db"
```

#### Option B: Free MongoDB Atlas (Cloud - No Local Installation Required!)
1. Go to [https://www.mongodb.com/cloud/atlas](https://www.mongodb.com/cloud/atlas) and create a free account.
2. Create a free **M0 Shared Cluster**.
3. Under **Database Access**, create a user (e.g., `hms_user` / `YourPassword123`).
4. Under **Network Access**, click **Add IP Address** and choose **Allow Access from Anywhere (`0.0.0.0/0`)**.
5. Click **Connect** → **Drivers** (Python) and copy your connection string.
6. Paste it into your `.env` file:
   ```env
   MONGO_URI=mongodb+srv://hms_user:YourPassword123@cluster0.xxxxx.mongodb.net/?retryWrites=true&w=majority
   DB_NAME=hostel_db
   SECRET_KEY=your-custom-secret-key
   ```

### Step 7: Populate Initial Sample Data (Seed)
Run the automated seed script to populate admin, warden, blocks, rooms, students, allocations, fees, and notices:
```powershell
python seed.py
```

### Step 8: Start the Web Application
```powershell
python run.py
```
Open your web browser and navigate to:
👉 **[http://127.0.0.1:5000](http://127.0.0.1:5000)**

---

## 🔐 Default Login Credentials

After running `seed.py`, log in with any of these sample accounts:

| Role | Username | Password | Notes |
|------|----------|----------|-------|
| **Admin** | `admin` | `admin123` | Full access to blocks, rooms, fees, reports, all settings |
| **Warden** | `warden` | `warden123` | Manages students, allocations, complaints, leaves, visitors, notices |
| **Student (1)** | `student1` | `student123` | Aarav Sharma (Room A-101, paid fees, complaints) |
| **Student (2)** | `student2` | `student123` | Ananya Iyer (Room B-101, active leave/outpass) |
| **Student (3-15)**| `student3` to `student15` | `student123` | Various allocations, pending/partial fees, defaulters |

---

## 📁 Project Structure

```text
hostel-management-system/
├── app/
│   ├── blueprints/           # Modular Flask Blueprints
│   │   ├── __init__.py
│   │   ├── allocations.py    # Room allocation & checkout
│   │   ├── auth.py           # Login, logout, change password
│   │   ├── complaints.py     # Ticket filing & tracking
│   │   ├── dashboard.py      # Admin & Student dashboards
│   │   ├── fees.py           # Fee assignment, payments, receipts
│   │   ├── leaves.py         # Student leave / outpass workflow
│   │   ├── mess.py           # Weekly menu, attendance, meal summary
│   │   ├── notices.py        # Broadcast announcements
│   │   ├── reports.py        # Occupancy, fee & defaulters + CSV
│   │   ├── rooms.py          # Blocks & Rooms CRUD
│   │   ├── students.py       # Student profiles & search
│   │   └── visitors.py       # Visitor gate registry
│   ├── static/
│   │   ├── css/
│   │   │   └── style.css     # Teal & white UI theme
│   │   ├── js/
│   │   │   └── main.js       # Delete confirmation, auto alerts, search debounce
│   │   └── uploads/          # Student photos
│   ├── templates/
│   │   ├── auth/             # Login & password templates
│   │   ├── shared/           # All module views & printable receipts
│   │   └── base.html         # Master layout with role-based navigation
│   ├── __init__.py           # App factory & blueprint registration
│   ├── config.py             # Environment configurations
│   ├── db.py                 # PyMongo connection & index management
│   ├── models.py             # User class with Flask-Login integration
│   └── utils.py              # role_required decorator, ObjectId validation
├── .env.example              # Template environment configuration
├── .gitignore                # Git exclusions (venv, .env, uploads, cache)
├── requirements.txt          # Python dependencies
├── run.py                    # Application entry point
├── seed.py                   # Automated database seeder with realistic test data
└── README.md                 # Complete documentation & run guide
```

---

## 🛡️ Error Handling
- **Database Offline**: If MongoDB is unreachable, the system gracefully renders a friendly error page informing the user to check their connection string instead of crashing.
- **Safe ObjectIds**: All URL parameter conversions to MongoDB `ObjectId` are wrapped with safety guards against malformed IDs.
- **404 / 500 Pages**: Custom styled HTTP error pages matching the hostel teal theme.

