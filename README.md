# AtoZflix-v2

# 🎬 AtoZflix v2 - Smart Movie Recommendation System

AtoZflix is an intelligent movie recommendation platform built with Flask (backend) and Svelte (frontend), using The Movie Database (TMDb) API for up-to-date movie data. It supports user authentication, ratings, watchlists, and admin features to manage movies dynamically.

---

## Features
- 🔐 User registration & login
- ⭐ Rate & review movies
- 📜 Add to watchlist
- 🧠 Personalized movie recommendations
- 🎛️ Admin panel for batch movie import and user management
- 🌐 TMDb API integration for live metadata

---

## Tech Stack

- **Backend:** Flask, SQLAlchemy, SQLite/MySQL
- **Frontend:** Svelte
- **API:** TMDb (The Movie Database)

---

##  How to Run

### ⚙️ Backend (Flask)

run on bash or terminal after cloning:
-backend
cd backend
python -m venv venv
venv\Scripts\activate  # On Windows
pip install -r requirements.txt

# Initialize DB (only once)
python setup_db.py

# Run the server
python run.py

-frontend
cd frontend
npm install
npm run dev

