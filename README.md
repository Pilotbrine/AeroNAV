# ✈️ AeroNav System
**Competition Project — Smart Airline Route & Resource Optimization**

---

## 📌 About the Project
AeroNav System is a competition project aimed at reducing the **money wasted by airlines due to inefficient route planning, weather disruptions, and traffic mismanagement**.  

It intelligently integrates **route optimization, weather analysis, and air traffic prediction** to suggest the most cost-effective and safe flight paths.  

> **Main Development:** Stephen Mathew  
> A passionate programmer who loves solving problems and taking on challenges.  
> 📧 Email: flightpathoptimiser@gmai.com

---

## 👥 Developers
- **Stephen Mathew** — Lead Developer
- **Vinay Krishna** — Contributor

---

## 📁 Project Structure
```
AeroNav_System/
│
├── README.md
├── LICENSE.txt
├── requirements.txt
│
├── /docs
│   ├── Project_Report.pdf
│   ├── Architecture_Diagram.png
│   └── db_schema.png
│
├── /src
│   ├── main.py
│   ├── auth/               → User authentication & login
│   ├── admin/               → Admin panel actions
│   ├── optimiser/           → Route and traffic optimisation logic
│   ├── user/                 → User actions and dashboards
│   ├── database.py
│   └── utils/helpers.py
│
├── /config
│   └── config.json
│
├── /tests
│   ├── test_routes.py
│   ├── test_weather.py
│   └── test_db.py
│
├── /data
│   ├── sample_input.json
│   ├── sample_routes.csv
│   ├── weather_mock.json
│   └── output_logs.txt
│
├── /assets
│   ├── logo.png
│   └── screenshots/demo_ui.png
│
└── /setup
    ├── db_setup.sql
    ├── init_db.py
    └── sample_inserts.sql
```

---

## ⚙️ Setup & Installation

### 1. Install Python Dependencies
Make sure you have **Python 3.10+** installed.

Run:

```bash
pip install -r requirements.txt
```

**Requirements include:**
- mysql-connector-python  
- bcrypt  
- requests  
- matplotlib  
- cartopy  

---

## 🗄️ MySQL Database Setup

1. **Install MySQL Server**
   - Install and start MySQL on your system.

2. **Create the Database**
   ```sql
   CREATE DATABASE aeronav;
   ```

3. **Run Setup Scripts**
   - In the `/setup` folder:
     ```bash
     mysql -u <username> -p aeronav < db_setup.sql
     python setup/init_db.py
     mysql -u <username> -p aeronav < sample_inserts.sql
     ```

4. **Configure Credentials**
   - Open `config/config.json` and fill in your MySQL username, password, host, and database name.

---

## 📊 Entering Data
- Add new routes in `data/sample_routes.csv`
- Add mock weather data in `data/weather_mock.json`
- Logs will be stored in `data/output_logs.txt`

---

## ▶️ Running the Project
To start the system:

```bash
python src/main.py
```

This will launch the main application interface.  
Users can log in, plan routes, and view optimization reports.

---

## ✅ Testing
To run the automated tests:

```bash
pytest tests/
```

This will run unit and integration tests on routing, weather, and database modules.

---

## ⚠️ Known Issues
- Weather API mock data is static (no real-time API integrated yet)
- No role-based access restrictions fully implemented in the admin panel
- Limited visual UI — mostly CLI-based for now

---

## 💡 Future Improvements
- Integrate real-time weather and traffic APIs
- Add a full web-based front-end UI
- Implement advanced AI-based cost prediction models
- Role-based user permissions and audit logging

---

## 📩 Contact
For queries regarding this project:

- **Developer:** Stephen Mathew  
- **Email:** flightpathoptimiser@gmai.com

---

## ⚖️ License
This project is **proprietary software**.  
All rights reserved © 2025 — Stephen Mathew and Vinay Krishna.  
See [LICENSE.txt](./LICENSE.txt) for full details.
