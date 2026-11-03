# AtoZflix v2 - status and plan

Last updated: pipeline complete. Waiting on your local check.

## Where we are

| # | Step | Status |
|---|------|--------|
| 0 | Fix blockers (syntax error, MySQL bugs, secrets, config) | Done, verified |
| 1 | Create / migrate schema | Done (19 tables, zero drift) |
| 2 | Import catalog | Done: 4,986 movies (14 TMDb 404s, expected) |
| 3 | Import MovieLens ratings | Done: 15,633,893 rows, 40,000 users, 7.84% density |
| 4 | `build_similarity.py` | Done: 299,160 neighbour rows, all 4,986 films |
| 5 | Recent films (2020-2026) | Done: +1,500 -> **6,486 movies**, 0 failures |
| 6 | `backfill_people.py` | Done: 35,547 / 45,240 actors have a headshot (79%) |
| 7 | Admin user | Done: zainbaig.zb03@gmail.com / zain (user_id 2) |
| 8 | `eval_recommender.py` on real data | Done, results below |
| 9 | **You check everything locally** | **Current step** |

Start both servers from `frontend_svelte/`: `npm run dev:all` (API :5000, site :5173).

### Real-data evaluation (3,000 users, K=10, leave-one-out)

| Strategy | HitRate@10 | MRR | NDCG@10 | Coverage |
|---|---|---|---|---|
| popularity | 4.8% | 0.017 | 0.024 | 0.7% |
| content | 6.8% | 0.027 | 0.037 | 11.7% |
| collaborative | 24.8% | 0.137 | 0.163 | 4.5% |
| hybrid | 26.0% | 0.140 | 0.168 | 6.7% |

Hybrid beats either model alone and is +442% over popularity. These are higher than the README's table
(21.3% hybrid): this run sampled 3,000 users vs 2,000 there, and the catalog now has the 1,500 recent films.
The ordering is the same. Update the README table with these numbers (or re-run with the README's sample size) before quoting either.

## Done and confirmed

- `recommender.py` had an unterminated docstring (committed in 16f86c6), so the whole backend could not import. Fixed.
- MySQL 8 bugs: reserved word `rank` in `build_similarity.py`; double-quoted identifiers and a case-sensitivity no-op in `migrate_schema.py`; plain INSERT vs duplicate keys in `import_movielens.py` (now `INSERT IGNORE`).
- `setup_db.py` crashed on Windows (non-ASCII check marks). Now ASCII.
- Secrets: real `SECRET_KEY` / `JWT_SECRET_KEY` generated; app refuses to boot without them outside `FLASK_ENV=development`. `backend/.env.example` added.
- DB password no longer printed by any script (`safe_database_uri`).
- `seed_demo_data.py` can no longer `drop_all()` your real DB (needs a disposable target or `--force`).
- MySQL account quota (5000 queries/hour) lifted via `fix_mysql_limits.sql`.
- Stale `Actors.character_name NOT NULL` column dropped; `migrate_schema.py` now also reports stale columns.
- Importer fixes: character names clamped to 255 chars; duplicate keyword names reuse the existing id.
- Deploy config: `runtime.txt`, `.python-version` (3.11.9), Procfile (1 worker, 8 threads), README rewritten for MySQL and Netlify `build` dir.
- Frontend: library template removed from `package.json`, favicon fixed, root redirect uses `goto`, `npm audit fix` (12 -> 8 advisories, all Vite dev-server only), builds clean.
- `create_admin.py` written and tested on a throwaway DB (email login 200, admin routes 200, wrong password 401).
- Recommender verified on synthetic data: content 7.5%, collaborative 6.1%, hybrid 6.8% hit rate vs 0.5% popularity; API serves the precomputed model (`cf_source: precomputed`).

## Still open

- [ ] Rotate the MySQL password (it was printed into a session before masking existed).
- [ ] The TMDb API key appears in error URLs in the import logs / terminal output. Consider rotating it and redacting `api_key=` in `import_catalog.py` error printing.
- [ ] Update the README results table with the real-data numbers above.
- [ ] Commit the work (nothing is committed yet; ~19 modified, several new files).
- [ ] Not done on purpose: Vite 7 / SvelteKit 3 upgrade, Redis for multi-worker rate limiting, tests, CI, Dockerfile, LICENSE.
- [ ] `zain` is a weak password. Fine locally; change it before any deployment.

## Moving to another laptop after the pipeline finishes

**What a zip does NOT carry.** The data lives in MySQL on this machine, not in the repo. These are also gitignored or machine-specific, so a plain zip/clone will not give you a working app:

- the MySQL data (movies, ratings, similarity, your admin user)
- `backend/.env` (secrets, DB URL)
- `frontend_svelte/.env`
- `ml-25m/` (1.1 GB dataset)
- `backend/venv/` and `frontend_svelte/node_modules/` (not portable; delete them before zipping)

**Pick one way to get the data across:**

- Option A, dump (fast, recommended). On this laptop:
  `mysqldump -u atozflix_user -p --single-transaction --ignore-table=atozflix_db.movielens_ratings atozflix_db > atozflix.sql`
  Skipping `movielens_ratings` keeps it small; the running API reads `Item_Similarity`, not the raw ratings. You only need that table to rebuild similarity or run the eval. Include it if you want the full eval on the new laptop.
- Option B, rebuild (about 30 min). Needs the `ml-25m` zip and a TMDb key on the new machine, then rerun the pipeline from the README.

**On the new laptop:**

1. Install Python 3.11, Node 18+ (LTS), MySQL 8.
2. Unzip the repo. Delete `backend/venv` and `frontend_svelte/node_modules` if they came along.
3. In MySQL (as root): `CREATE DATABASE atozflix_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;` then create `atozflix_user` with privileges on it, and run `backend/fix_mysql_limits.sql` (removes the query quota). See `backend/migration_guide.md`.
4. Backend:
   ```
   cd backend
   python -m venv venv
   venv\Scripts\python.exe -m pip install -r requirements.txt
   venv\Scripts\python.exe -m pip install -r requirements-build.txt   (only if rebuilding / running eval)
   copy .env.example .env      (fill in: new SECRET_KEY and JWT_SECRET_KEY, DATABASE_URL, TMDB_API_KEY)
   ```
   Generate secrets with `python -c "import secrets; print(secrets.token_urlsafe(48))"`.
5. Data: Option A: `mysql -u atozflix_user -p atozflix_db < atozflix.sql`, then `python migrate_schema.py --dry-run` (should say nothing to do). Option B: `setup_db.py`, then the pipeline steps above.
6. Admin: included in a full dump. Otherwise run `create_admin.py` again.
7. Frontend:
   ```
   cd frontend_svelte
   npm ci
   copy .env.example .env      (VITE_API_BASE_URL=http://127.0.0.1:5000)
   npm run dev:all
   ```
   Open http://localhost:5173.

**Gotchas**

- Table names: Windows MySQL lower-cases them (`actors`), the models say `Actors`. A dump from Windows restored onto Linux/macOS (case-sensitive) will break queries. Restore onto Windows, or set `lower_case_table_names=1` on the new server before first start.
- Changing `JWT_SECRET_KEY` just logs everyone out; it does not break data.
- Never put `.env` in a zip you share: it holds the DB password and TMDb key.
