# 🧰 Santexnika — Django Web Application

## 📖 Project Overview
**Santexnika** is a Django-based web application designed to manage plumbing product sales, clients, and transactions.  
It provides a clean admin interface and modular apps for handling accounts, clients, products, and sales management.

---

## 🚀 Features
- User authentication and account management  
- Client registration and tracking  
- Product catalog management  
- Sales tracking and invoice management  
- Admin dashboard for managing all modules  
- Built-in SQLite database for local development  

---

## ⚙️ Installation & Setup

### 1. Clone the repository
```bash
git clone https://github.com/<your-username>/santexnika.git
cd santexnika
```

### 2. Create a virtual environment
```bash
python -m venv venv
source venv/bin/activate  # On macOS/Linux
venv\Scripts\activate     # On Windows
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Apply migrations
```bash
python manage.py migrate
```

### 5. Create a superuser (admin)
```bash
python manage.py createsuperuser
```

### 6. Run the development server
```bash
python manage.py runserver
```

Open your browser at **http://127.0.0.1:8000/** to view the app.

---

## 🗂️ Folder Structure
```
santexnika/
│
├── accounts/        # User management (login, register, etc.)
├── clients/         # Client data management
├── products/        # Product catalog and categories
├── sell/            # Sales and transactions
├── templates/       # HTML templates
├── manage.py        # Django project entry point
└── db.sqlite3       # Local database
```

---

## 🧩 Technologies Used
- **Python 3**
- **Django Framework**
- **SQLite3** (default database)
- **HTML / CSS / Bootstrap** (for frontend templates)

---

## 🧪 Example Commands
Initialize database and run server locally:
```bash
python manage.py makemigrations
python manage.py migrate
python manage.py runserver
```

Create a new app:
```bash
python manage.py startapp <app_name>
```

Access Django admin panel:
```
http://127.0.0.1:8000/admin/
```

---

## 🧰 Development Notes
- Default database is SQLite, stored in `db.sqlite3`
- Static files and templates can be customized under `templates/`
- You can add `.env` file for environment variables (optional)

---

## 📜 License
This project is open source and available under the [MIT License](LICENSE).

---

## ✨ Author
Developed by [Your Name]  
📧 Contact: [your.email@example.com]  
🌐 GitHub: [https://github.com/<your-username>]

Feel free to contribute or open issues on GitHub!
