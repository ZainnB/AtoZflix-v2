# AtoZflix-v2

# 🎬 AtoZflix v2 - Smart Movie Recommendation System

AtoZflix is an intelligent movie recommendation platform built with Flask (backend) and Svelte (frontend), using The Movie Database (TMDb) API for up-to-date movie data. It supports user authentication with JWT, ratings, watchlists, and admin features to manage movies dynamically.

---

## Features
- 🔐 JWT-based user authentication & authorization
- 🔒 Role-based access control (RBAC) for admin features
- ⭐ Rate & review movies
- 📜 Add to watchlist
- 🧠 Personalized movie recommendations
- 🎛️ Admin panel for batch movie import and user management
- 🌐 TMDb API integration for live metadata
- 🔐 Secure API endpoints with token-based authentication

---

## Tech Stack

- **Backend:** Flask, SQLAlchemy, PostgreSQL/SQLite, JWT, Flask-Limiter
- **Frontend:** SvelteKit, Svelte 5
- **API:** TMDb (The Movie Database)
- **Deployment:** Netlify (Frontend), Railway/Render/Heroku (Backend)

---

## Security Features

- ✅ JWT token-based authentication
- ✅ Automatic token refresh mechanism
- ✅ Role-based access control (Admin/User)
- ✅ Rate limiting on authentication endpoints
- ✅ CORS configuration
- ✅ Environment variable management
- ✅ Password hashing with Werkzeug
- ✅ User ownership verification for user-specific resources

---

## Environment Variables

### Backend Environment Variables

Create a `.env` file in the `backend/` directory (use `.env.example` as template):

```env
# Flask Configuration
SECRET_KEY=your-secret-key-here-change-in-production
FLASK_ENV=development

# JWT Configuration
JWT_SECRET_KEY=your-jwt-secret-key-here-change-in-production

# Database Configuration
# For SQLite (development):
DATABASE_URL=sqlite:///movies.db
# For PostgreSQL (production):
# DATABASE_URL=postgresql://username:password@localhost:5432/dbname

# CORS Configuration
# Comma-separated list of allowed origins
CORS_ORIGINS=http://localhost:5173,http://localhost:3000,http://127.0.0.1:5173

# TMDb API Configuration
TMDB_API_KEY=your-tmdb-api-key-here
```

### Frontend Environment Variables

Create a `.env` file in the `frontend_svelte/` directory:

```env
# Backend API Base URL
# For development (local):
VITE_API_BASE_URL=http://localhost:5000
# For production:
# VITE_API_BASE_URL=https://your-backend-url.com
```

---

## How to Run Locally

### ⚙️ Backend (Flask)

1. Navigate to backend directory:
```bash
cd backend
```

2. Create virtual environment:
```bash
python -m venv venv
venv\Scripts\activate  # On Windows
# or
source venv/bin/activate  # On Linux/Mac
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
```bash
# Copy .env.example to .env and fill in your values
cp .env.example .env
# Edit .env with your configuration
```

5. Initialize database (only once):
```bash
python setup_db.py
```

6. Run the server:
```bash
python run.py
```

The backend will run on `http://localhost:5000`

### 🎨 Frontend (Svelte)

1. Navigate to frontend directory:
```bash
cd frontend_svelte
```

2. Install dependencies:
```bash
npm install
```

3. Set up environment variables:
```bash
# Copy .env.example to .env
cp .env.example .env
# Edit .env with your backend URL
```

4. Run development server:
```bash
npm run dev
```

The frontend will run on `http://localhost:5173` (or your configured port)

---

## Deployment

### Backend Deployment

**Note:** Netlify only hosts static sites. You need to deploy the Flask backend separately.

#### Option 1: Railway (Recommended)
1. Push your code to GitHub
2. Create a new project on Railway
3. Connect your GitHub repository
4. Add a PostgreSQL database service
5. Set all environment variables in Railway dashboard
6. Deploy

#### Option 2: Render
1. Push your code to GitHub
2. Create a new Web Service on Render
3. Connect your GitHub repository
4. Add PostgreSQL database
5. Set build command: `pip install -r requirements.txt`
6. Set start command: `gunicorn run:app`
7. Add all environment variables
8. Deploy

#### Option 3: Heroku
1. Install Heroku CLI
2. Create Heroku app: `heroku create your-app-name`
3. Add PostgreSQL: `heroku addons:create heroku-postgresql:hobby-dev`
4. Set environment variables: `heroku config:set KEY=value`
5. Deploy: `git push heroku main`

### Frontend Deployment (Netlify)

1. Push your code to GitHub
2. Create a new site on Netlify
3. Connect your GitHub repository
4. Set build settings:
   - Base directory: `frontend_svelte`
   - Build command: `npm run build`
   - Publish directory: `.svelte-kit`
5. Set environment variable `VITE_API_BASE_URL` to your production backend URL
6. Deploy

**Important:** Make sure to update `CORS_ORIGINS` in your backend to include your Netlify domain.

---

## Database Migration

For production, migrate from SQLite to PostgreSQL. See `backend/migration_guide.md` for detailed instructions.

---

## API Authentication

All protected endpoints require a JWT token in the Authorization header:

```
Authorization: Bearer <access_token>
```

### Endpoints

#### Public Endpoints (No authentication required):
- `GET /api/latest` - Get latest movies
- `GET /api/trending` - Get trending movies
- `GET /api/top_rated` - Get top rated movies
- `GET /api/movie_details` - Get movie details
- `GET /api/search_movie` - Search movies
- `GET /api/get_genre_names` - Get genre names
- `GET /api/get_country_names` - Get country names
- `POST /api/register` - User registration
- `POST /api/signin` - User login

#### Protected Endpoints (Require authentication):
- All admin routes (require admin role)
- User-specific routes (ratings, watchlist, favourites)

#### Token Refresh:
- `POST /api/refresh` - Refresh access token using refresh token

---

## Security Best Practices

1. **Never commit `.env` files** - They are already in `.gitignore`
2. **Use strong secrets** - Generate random strings for `SECRET_KEY` and `JWT_SECRET_KEY`
3. **Rotate keys periodically** - Change JWT secret keys regularly in production
4. **Use HTTPS in production** - Always use HTTPS for API communication
5. **Keep dependencies updated** - Regularly update Python and Node packages
6. **Monitor rate limits** - Watch for abuse on authentication endpoints
7. **Database security** - Use strong database passwords and limit access
8. **CORS configuration** - Only allow trusted origins in production

---

## Troubleshooting

### Backend Issues
- **Import errors**: Ensure virtual environment is activated
- **Database errors**: Check DATABASE_URL in .env
- **CORS errors**: Verify CORS_ORIGINS includes your frontend URL
- **JWT errors**: Check JWT_SECRET_KEY is set correctly

### Frontend Issues
- **API connection errors**: Verify VITE_API_BASE_URL is correct
- **Token errors**: Clear localStorage and re-login
- **Build errors**: Ensure all dependencies are installed

---

## Project Structure

```
AtoZflix-v2/
├── backend/
│   ├── app/
│   │   ├── models/          # Database models
│   │   ├── routes/          # API route handlers
│   │   ├── utils/           # Utility functions (JWT, helpers, etc.)
│   │   └── __init__.py      # Flask app factory
│   ├── instance/            # SQLite database (dev)
│   ├── .env.example         # Environment variables template
│   ├── requirements.txt     # Python dependencies
│   ├── run.py              # Application entry point
│   ├── setup_db.py         # Database initialization
│   └── Procfile            # Deployment configuration
├── frontend_svelte/
│   ├── src/
│   │   ├── lib/            # Shared libraries (API client)
│   │   ├── routes/         # SvelteKit routes
│   │   └── utils/          # Utility functions (auth)
│   ├── .env.example        # Frontend environment template
│   ├── netlify.toml        # Netlify deployment config
│   └── package.json        # Node dependencies
└── README.md
```

---

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

---

## License

[Add your license here]

---

## Support

For issues and questions, please open an issue on GitHub.
