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

## Data Pipeline

The catalog is real TMDb metadata; the collaborative signal is real MovieLens
25M interaction data. The two are joined on TMDb id.

### Why MovieLens drives the selection

The obvious approach — import "popular movies" from TMDb and hope MovieLens has
ratings for them — gets the dependency backwards and leaves a catalog full of
films with no collaborative signal at all. So the order is inverted: MovieLens
is ranked by how many ratings each film actually has, the top N are taken,
`links.csv` maps MovieLens ids to TMDb ids, and only those films are fetched.
Every film in the catalog therefore arrives with real interaction data attached.

The long tail is cut deliberately. MovieLens has 62,423 films but the **median
film has only 6 ratings** — nowhere near enough to compute a similarity from.
The top 5,000 by rating volume cover **92.3% of all 25M ratings**, for a tenth
of the API calls and a fraction of the storage.

### What the dataset actually looks like

Worth knowing before quoting it: **MovieLens 25M is not an old dataset.** Its
ratings run to **21 November 2019**, and 2015–2019 contribute 1.2–1.7M ratings
per year. The gap needing content-based fallback is 2020 onward, not 2017.

| | |
|---|---|
| Ratings | 25,000,095 |
| Users | 162,541 (`userId` 1–162,541, contiguous) |
| Films rated | 59,047 of 62,423 |
| Rating scale | 0.5–5.0 in half-star steps (rescaled ×2 to this project's 0–10 integers) |
| Timestamps | UNIX epoch seconds, Jan 1995 → Nov 2019 |
| Full-matrix density | 0.26% |
| `movieId` | MovieLens-internal, **not** a TMDb id — `links.csv` maps it |

`links.csv` is missing `tmdbId` for 107 rows (0.17%) and contains 35 duplicate
`tmdbId` values (re-releases and duplicate entries). Since TMDb id is our
primary key, the most-rated row wins and the rest are dropped.

### Running the pipeline

```bash
cd backend
python setup_db.py                                    # create tables
python import_catalog.py --limit 5000 --workers 12    # ~3.5 min  (MovieLens-ranked)
python import_movielens.py --max-users 40000          # ~13 min
python build_similarity.py                            # ~2.5 min
python import_catalog.py --recent --limit 1500        # ~1 min    (post-2019 gap)
python eval_recommender.py                            # measure it
```

Requires `TMDB_ACCESS_TOKEN` (v4 read token) in `backend/.env` and the
[ml-25m](https://files.grouplens.org/datasets/movielens/ml-25m.zip) extract at
`MOVIELENS_DIR`. The dataset is ~1.1GB and is **not** committed.

`import_catalog.py` uses TMDb's `append_to_response=credits,keywords` to get
details, cast, crew and keywords in **one** request instead of three — 5,000
calls rather than 15,000. Cast is capped at the top 15 by billing order; past
that it is noise that dilutes the similarity vectors.

Resulting local dataset:

| | |
|---|---|
| Movies | 4,986 (14 TMDb ids in `links.csv` are stale → 404) |
| MovieLens ratings loaded | 15,633,893 |
| Users | 40,000 (those with ≥15 in-catalog ratings) |
| **Matrix density** | **7.8%** (MovieLens-100k, a standard benchmark, is ~6%) |

MovieLens ratings live in their own `MovieLens_Ratings` table, never in
`Ratings`. Their user ids are a dense 1–162,541 sequence that would collide
head-on with the app's autoincrementing `Users.user_id`, and they are not users
of this application — nobody can log in as them, and they must never appear in
an admin user list. The recommender unions both sources at read time under
namespaced keys.

### The post-2019 gap, and why the catalog has two halves

MovieLens ends in November 2019, so the selection above cannot yield a single
film newer than that — the catalog stopped at *Joker*, and the "Trending" shelf
was permanently empty.

`import_catalog.py --recent` covers the gap from the other direction: it asks
TMDb directly for well-rated films in a year range, with no MovieLens
involvement. Those films have **zero collaborative signal by construction**,
which is precisely the case content-based filtering exists to serve — a film is
recommendable from its metadata the moment it is imported, long before anyone
has interacted with it.

| Half | Films | Served by |
|---|---|---|
| pre-2020 | 4,986 | full hybrid (CF + content) |
| 2020–2026 | 1,500 | content + popularity prior only |

This is the clearest demonstration of why the system is a hybrid rather than
just the stronger model. Asking for films similar to **Dune: Part Two** (2024,
no ratings anywhere in the dataset) returns *Dune* (2021) at 0.500, then *Dune*
(1984) and the *Star Wars* films — recovered entirely from shared cast, crew and
keywords. A CF-only system, despite its far better headline number, would be
structurally incapable of ranking it at all.

---

## Recommendation Engine

Three rankers live in `backend/app/utils/recommender.py`, exposed through
`backend/app/routes/recommendation_routes.py`.

**1. Content-based filtering.** Every movie becomes a sparse TF-IDF weighted
vector over its metadata — genres, keywords, cast, crew, country, language and
decade. IDF is what makes it work: a shared director is rare and highly
informative, a shared "Drama" tag is not, and inverse document frequency weights
them accordingly. A user becomes a vector too, via the **Rocchio** method — the
centroid of what they liked, pushed away from the centroid of what they disliked,
so the profile doesn't collapse into "this user likes popular things." Ranking is
cosine similarity, computed through an inverted index so only movies sharing at
least one feature are ever scored.

**2. Collaborative filtering.** Item-item neighbourhood CF over the user-item
matrix, folding ratings, favourites and watch-later rows into one preference
score. Similarity is cosine with **significance shrinkage** — `n/(n+λ)` — so two
films sharing one lonely user don't look like perfect twins. Item-item rather
than user-user because the catalog changes far more slowly than the user base, so
similarities stay valid between rebuilds and can be precomputed.

Raw metadata cosine is popularity-blind, so a **Bayesian popularity prior** is
mixed into the content score. This is the single largest quality win on real
data — see the findings below.

**3. Hybrid.** Both score lists are min-max normalised onto a common scale and
blended, with the weight tuned against the offline harness. Users with no history
fall back to a Bayesian-weighted popularity ranking, which is the cold-start path.

### Where the models are built

The item-item matrix is **built offline** by `build_similarity.py` and stored in
the `Item_Similarity` table. The web process never builds it — it reads
precomputed neighbour lists.

This changed as the data grew, and the reasoning is worth stating. The first
version built the matrix in-process on a cache miss; at 1,500 movies and 28k
interactions that took 0.88s and was entirely reasonable. At 15.6M ratings the
co-occurrence accumulation is O(Σk²) in pure Python and runs for hours — and
would run once *per gunicorn worker*. Moving it offline and expressing it as
sparse matrix multiplication (`Xᵀ @ X`) brought the full build to **115 seconds**.

The payoff is an import boundary: **numpy and scipy are build dependencies, not
runtime ones.** The API still runs on the original `requirements.txt`, every
worker shares one consistent model, and a cold start is an indexed query instead
of a multi-hour computation. The content model is still built in-process (2s) and
cached behind a TTL plus a row-count fingerprint.

### Measured results

Offline evaluation is **leave-one-out with a temporal split**: each user's most
recent positive interaction is hidden, models are trained on the rest, and the
question is whether the held-out film lands in the top 10. A temporal split
matters — splitting randomly would let the model train on a user's future to
predict their past.

The collaborative model is **rebuilt from the training split** inside the
harness. It deliberately does *not* read `Item_Similarity`, because that matrix
is built over all data including the held-out interactions; using it would leak
the answers. This is why the scipy build lives in `app/utils/cf_builder.py` and
is shared by both the harness and the production build script.

**4,986 movies, 15.6M MovieLens ratings, 40,000 users, 2,000 sampled for
evaluation:**

| Strategy | HitRate@10 | MRR | NDCG@10 | Coverage |
|---|---|---|---|---|
| popularity (baseline) | 5.9% | 0.027 | 0.034 | 1.3% |
| content-based | 7.7% | 0.028 | 0.040 | 12.6% |
| collaborative | 19.2% | 0.087 | 0.112 | 5.3% |
| **hybrid** | **21.3%** | **0.107** | **0.132** | **7.6%** |

The hybrid is **106x random guessing**, **+259% over the popularity baseline**,
and beats *either* model alone (19.2% CF-only, 7.7% content-only) — the blend is
earning its complexity, not just averaging.

Coverage is reported deliberately: popularity posts a non-trivial 5.9% hit rate
while only ever surfacing **1.3%** of the catalog — the same handful of
blockbusters for everyone. That is precisely the failure a hit-rate-only
evaluation hides.

### Three findings that came from the harness, not intuition

**1. CF score normalisation was wrong for the task (1.5% → 5.8%).** Dividing the
CF score by summed similarity produces a *predicted rating*. Top-N ranking asks a
different question, and for it the number of a user's items vouching for a
candidate is real evidence, not a bias to divide away.

**2. A popularity prior on content-based (2.8% → 11.2%).** Pure metadata cosine
happily ranks an obscure film sharing three character actors above an obvious
classic. On the real catalog, content-only scored *worse than recommending by raw
popularity*. Mixing in a Bayesian prior at weight 0.4 quadrupled it. Measured:
0.0 → 2.8%, 0.2 → 9.5%, 0.4 → 11.2%, 0.6 → 8.4% — past ~0.4 the prior starts
drowning out the personalisation it exists to deliver.

**3. Synthetic data inverted the model ranking.** Tuned first on generated data,
this looked content-dominated (content 7.0%, CF 5.8%, hybrid at parity with
content alone). On real data the ordering flipped hard: **CF 19.2%, content 7.7%,
and the hybrid a clear winner.** The generator encoded its predictive structure
directly in metadata, which flattered the content model, and it gave every film
comparable exposure, which hid the popularity problem entirely. A relative
ranking measured on generated data should not be trusted.

### The synthetic fixture

`seed_demo_data.py` remains as a **development fixture**, not the evaluation
basis. It generates a latent-factor dataset so the pipeline can be exercised
without a TMDb key or a 1.1GB download, and the recommender falls back to an
in-process CF build when `Item_Similarity` is empty, so it still works end to
end. On that dataset the harness also reports an **oracle** row — a ranker that
cheats by reading the generator's hidden latent factors — as a ceiling, since
top-N hit rates are otherwise hard to interpret in absolute terms. Finding #3 is
the reason it is a fixture and not the headline.

```bash
DATABASE_URL=sqlite:///demo.db python seed_demo_data.py
DATABASE_URL=sqlite:///demo.db python eval_recommender.py
```

### Recommendation endpoints

| Endpoint | Auth | Purpose |
|---|---|---|
| `GET /api/recommendations?limit=&explain=` | user | Personalised hybrid feed. User comes from the JWT, never a query param. |
| `GET /api/similar_movies?movie_id=&strategy=` | public | "More like this". `strategy` = `content`, `collaborative` or `hybrid`. |
| `GET /api/recommender_stats` | admin | Index size, build time, cache state, CF source. |
| `POST /api/rebuild_recommender` | admin | Force a rebuild after a bulk import. |

`explain=true` returns `because_of_features` (the shared metadata that drove the
match) and `because_you_liked` (the user's own films whose CF neighbourhoods
pulled it in).

Real output for an account that favourited five Nolan films:

```
GET /api/recommendations?limit=5&explain=true
  The Dark Knight Rises   via ['Emma Thomas', 'Christopher Nolan', 'Jonathan Nolan', 'tragic hero']
  Memento                 via ['Christopher Nolan', 'memory', 'manipulation']
  Iron Man                via ['superhero', 'based on comic', 'Science Fiction']
  The Departed            via ['organized crime', 'undercover', 'Crime']
  V for Vendetta          via ['based on comic', 'Science Fiction', 'Action']

GET /api/similar_movies?movie_id=27205        (Inception, hybrid)
  0.926 The Dark Knight     0.882 The Dark Knight Rises   0.705 Interstellar
  0.676 Batman Begins       0.623 The Prestige            0.458 Iron Man
```

The collaborative half learns structure nobody encoded. Trained only on
behaviour, never on a director field, `Star Wars` returns *The Empire Strikes
Back* (0.907), *Return of the Jedi* (0.870), then *Raiders of the Lost Ark* —
and `Inception` returns Nolan's filmography.

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
