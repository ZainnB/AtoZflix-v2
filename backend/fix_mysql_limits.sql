-- Run ONCE as root (or any account with CREATE USER + RELOAD privileges) in
-- MySQL Workbench. This is the only step that needs an admin account.
--
-- WHY THIS IS NEEDED
-- ------------------
-- migration_guide.md creates atozflix_user through the Workbench "Users and
-- Privileges" dialog, whose "Account Limits" tab was used to set a ceiling of
-- 5000 queries per hour. That is far below what this project needs.
--
-- The data pipeline writes eight tables per film (movie, genres, countries,
-- actors, crew, keywords and their junction rows) and session.merge() issues a
-- SELECT before every INSERT, so a 5,000-film import runs to tens of thousands
-- of statements. It dies partway through with:
--
--   (1226, "User 'atozflix_user' has exceeded the 'max_questions' resource")
--
-- which reads like an application bug but is purely an account quota.
--
-- It throttles the running API too, not just the import: the home page alone
-- issues nine API calls, so a 5000/hour ceiling locks out a browsing user far
-- sooner than it looks. Leave these at 0 (unlimited) and rely on Flask-Limiter
-- for request throttling, which is the layer that can actually return a 429.

ALTER USER 'atozflix_user'@'localhost'
  WITH MAX_QUERIES_PER_HOUR 0
       MAX_UPDATES_PER_HOUR 0
       MAX_CONNECTIONS_PER_HOUR 0
       MAX_USER_CONNECTIONS 0;

-- migration_guide.md suggests '%' as the host pattern, so the account may exist
-- under either or both. If this one does not exist you will get error 1396,
-- which is safe to ignore.
ALTER USER 'atozflix_user'@'%'
  WITH MAX_QUERIES_PER_HOUR 0
       MAX_UPDATES_PER_HOUR 0
       MAX_CONNECTIONS_PER_HOUR 0
       MAX_USER_CONNECTIONS 0;

-- Resets the counters immediately so you do not have to wait out the hour.
FLUSH USER_RESOURCES;

-- Verify: all four columns should read 0.
SELECT User, Host, max_questions, max_updates, max_connections, max_user_connections
FROM mysql.user
WHERE User = 'atozflix_user';
