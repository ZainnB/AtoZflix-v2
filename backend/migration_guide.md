# Database Migration Guide - MySQL

## Overview
This guide covers migrating from SQLite (development) to MySQL (production) for the AtoZflix-v2 application using MySQL Workbench 8.0.

## Prerequisites
- MySQL Server 8.0 or later installed (local or cloud-hosted)
- MySQL Workbench 8.0 installed
- Database credentials (host, port, database name, username, password)
- Access to your deployment platform's environment variables

## Migration Steps

### 1. Set Up MySQL Database Using MySQL Workbench 8.0

#### Option A: Using MySQL Workbench GUI

1. **Open MySQL Workbench 8.0**
   - Launch MySQL Workbench
   - Connect to your MySQL server (click on your server connection)

2. **Create Database**
   - Click on the "Schema" tab in the left sidebar
   - Right-click in the schemas panel → Select "Create Schema"
   - Enter database name: `atozflix_db`
   - Select charset: `utf8mb4`
   - Select collation: `utf8mb4_unicode_ci`
   - Click "Apply" → "Apply" → "Finish"

3. **Create User and Set Permissions**
   - Go to "Administration" tab → "Users and Privileges"
   - Click "Add Account"
   - Enter login name: `atozflix_user`
   - Click "Limit to Hosts Matching": `%` (or specific IP/hostname)
   - Enter password: `your_secure_password` (click "Generate" for random password if needed)
   - Select "Account Limits" tab and set resource limits if needed
   - Go to "Schema Privileges" tab → Click "Add Entry"
   - Select "Selected schema": `atozflix_db`
   - Click "Select All" for privileges, or at minimum:
     - SELECT, INSERT, UPDATE, DELETE
     - CREATE, DROP, ALTER, INDEX
     - CREATE TEMPORARY TABLES
     - LOCK TABLES
   - Click "Apply"

#### Option B: Using SQL Script in MySQL Workbench

1. **Open SQL Editor**
   - In MySQL Workbench, click "File" → "New Query Tab"
   - Or press `Ctrl+T` (Windows) / `Cmd+T` (Mac)

2. **Run SQL Script**
   ```sql
   -- Create database
   CREATE DATABASE IF NOT EXISTS atozflix_db 
   CHARACTER SET utf8mb4 
   COLLATE utf8mb4_unicode_ci;
   
   -- Create user for localhost (required for local connections)
   CREATE USER IF NOT EXISTS 'atozflix_user'@'localhost' IDENTIFIED BY 'your_secure_password';
   
   -- Grant privileges for localhost user
   GRANT ALL PRIVILEGES ON atozflix_db.* TO 'atozflix_user'@'localhost';
   
   -- Create user for remote connections (optional, if needed)
   CREATE USER IF NOT EXISTS 'atozflix_user'@'%' IDENTIFIED BY 'your_secure_password';
   
   -- Grant privileges for remote user
   GRANT ALL PRIVILEGES ON atozflix_db.* TO 'atozflix_user'@'%';
   
   -- Refresh privileges
   FLUSH PRIVILEGES;
   
   -- Verify users were created
   SELECT User, Host FROM mysql.user WHERE User='atozflix_user';
   ```

3. **Execute Script**
   - Click the "Execute" button (⚡) or press `Ctrl+Shift+Enter`
   - Verify success in "Output" panel

### 2. Update Environment Variables

In your `.env` file or deployment platform environment variables, update `DATABASE_URL`:

```env
# For MySQL (local)
DATABASE_URL=mysql+pymysql://atozflix_user:your_secure_password@localhost:3306/atozflix_db

# For MySQL (remote/cloud)
DATABASE_URL=mysql+pymysql://username:password@host:port/database_name

# Alternative format (if using mysql-connector-python)
DATABASE_URL=mysql+mysqlconnector://username:password@host:port/database_name
```

**Important Notes:**
- Default MySQL port is `3306`
- Use `pymysql` driver for better compatibility with SQLAlchemy
- Replace `localhost` with your MySQL server hostname/IP in production

### 3. Install MySQL Adapter

The SQLAlchemy library needs a MySQL driver. Install `PyMySQL` (recommended):

```bash
pip install PyMySQL
```

Add to `requirements.txt`:
```
PyMySQL==1.1.0
```

**Alternative:** If you prefer the official MySQL connector:
```bash
pip install mysql-connector-python
```

And update connection string to use `mysql+mysqlconnector://`

### 4. Export SQLite Data (Optional - if you have existing data)

If you need to migrate existing data:

```bash
# Export SQLite data to SQL
sqlite3 movies.db .dump > dump.sql
```

**Convert SQLite SQL to MySQL syntax in MySQL Workbench:**

1. Open `dump.sql` in a text editor
2. Make the following conversions:
   - Remove `BEGIN TRANSACTION;` and `COMMIT;`
   - Replace `INTEGER PRIMARY KEY AUTOINCREMENT` with `INT AUTO_INCREMENT PRIMARY KEY`
   - Replace `TEXT` with `TEXT` or `VARCHAR(255)` as appropriate
   - Replace `BLOB` with `BLOB` or appropriate type
   - Update date formats if needed
   - Remove SQLite-specific functions

3. Import converted SQL:
   - In MySQL Workbench, open SQL Editor
   - File → Open SQL Script → Select your converted dump.sql
   - Select target schema: `atozflix_db` (dropdown at top)
   - Execute script (⚡ button)

### 5. Test MySQL Connection (Recommended)

Before running setup_db.py, test your connection:

```bash
cd backend
python test_mysql_connection.py
```

This script will:
- Verify your DATABASE_URL format
- Test the connection
- Provide detailed error messages and troubleshooting tips

### 6. Run Database Setup

The application uses Flask-SQLAlchemy which will create tables automatically:

```bash
cd backend
python setup_db.py
```

**If you get "Access denied" error:**
1. Run `python test_mysql_connection.py` first for detailed diagnostics
2. Make sure you created the user for 'localhost' (not just '%')
3. Verify the password in your .env file matches the MySQL user password

**Verify in MySQL Workbench:**
1. Refresh the schema (`atozflix_db`) in the left sidebar
2. Expand `Tables` folder
3. You should see all tables:
   - Movies
   - Users
   - Genres
   - Ratings
   - Favorites
   - WatchLater
   - etc.

### 7. Verify Migration in MySQL Workbench

#### View All Tables:
1. In MySQL Workbench, select `atozflix_db` schema
2. Click on "Tables" in the left sidebar
3. Right-click any table → "Select Rows - Limit 1000" to view data

#### Run Verification Queries:
1. Open SQL Editor (Ctrl+T)
2. Select schema: `atozflix_db`
3. Run queries:
   ```sql
   -- List all tables
   SHOW TABLES;
   
   -- Check table structure
   DESCRIBE Movies;
   DESCRIBE Users;
   
   -- Verify data count (if migrated)
   SELECT COUNT(*) FROM Movies;
   SELECT COUNT(*) FROM Users;
   
   -- Check indexes
   SHOW INDEX FROM Movies;
   ```

## Deployment Platforms

### Railway
1. Add MySQL service in Railway dashboard
   - Go to your project → "New" → "Database" → "MySQL"
2. Copy the `MYSQL_URL` or `DATABASE_URL` from the service
3. Add it to your Flask app's environment variables
4. Format: `mysql+pymysql://user:password@host:port/database`

### Render
1. Create a MySQL database in Render dashboard
   - Dashboard → "New" → "PostgreSQL" (Render may offer MySQL, or use ClearDB)
   - Or use external MySQL service (AWS RDS, PlanetScale, etc.)
2. Copy the database connection string
3. Add to environment variables in your web service as `DATABASE_URL`

### Heroku with ClearDB or JawsDB
```bash
# ClearDB MySQL (free tier available)
heroku addons:create cleardb:ignite

# Get database URL
heroku config:get CLEARDB_DATABASE_URL

# Or use JawsDB MySQL
heroku addons:create jawsdb:kitefin
heroku config:get JAWSDB_URL
```

### AWS RDS (MySQL)
1. Create MySQL RDS instance in AWS Console
2. Note the endpoint, port (3306), database name
3. Get credentials from AWS Secrets Manager or set during creation
4. Format connection string: `mysql+pymysql://user:password@endpoint:3306/dbname`

### PlanetScale (MySQL-compatible)
1. Create database on PlanetScale
2. Get connection string from dashboard
3. Format: `mysql+pymysql://user:password@host:port/database?ssl_mode=REQUIRED`

## Troubleshooting

### Connection Issues

**Error: "Access denied for user" (Error 1045)**

This is the most common issue! MySQL treats `'user'@'localhost'` and `'user'@'%'` as different users.

**Solution Steps:**

1. **Check if user exists:**
   ```sql
   SELECT User, Host FROM mysql.user WHERE User='atozflix_user';
   ```
   
2. **If user doesn't exist for 'localhost', create it:**
   ```sql
   CREATE USER 'atozflix_user'@'localhost' IDENTIFIED BY 'your_secure_password';
   GRANT ALL PRIVILEGES ON atozflix_db.* TO 'atozflix_user'@'localhost';
   FLUSH PRIVILEGES;
   ```

3. **Verify password is correct:**
   - Check your `.env` file: `DATABASE_URL=mysql+pymysql://atozflix_user:password@localhost:3306/atozflix_db`
   - The password after the colon (`:`) must match what you set in MySQL

4. **Check user has correct privileges:**
   ```sql
   SHOW GRANTS FOR 'atozflix_user'@'localhost';
   ```

5. **If password is wrong, reset it:**
   ```sql
   ALTER USER 'atozflix_user'@'localhost' IDENTIFIED BY 'new_password';
   FLUSH PRIVILEGES;
   ```
   Then update your `.env` file with the new password.

**Quick Fix Script for MySQL Workbench:**
```sql
-- Drop existing user if needed (optional)
DROP USER IF EXISTS 'atozflix_user'@'localhost';
DROP USER IF EXISTS 'atozflix_user'@'%';

-- Recreate for localhost
CREATE USER 'atozflix_user'@'localhost' IDENTIFIED BY 'your_secure_password';
GRANT ALL PRIVILEGES ON atozflix_db.* TO 'atozflix_user'@'localhost';

-- Create for remote connections (optional)
CREATE USER 'atozflix_user'@'%' IDENTIFIED BY 'your_secure_password';
GRANT ALL PRIVILEGES ON atozflix_db.* TO 'atozflix_user'@'%';

FLUSH PRIVILEGES;
```

**Error: "Can't connect to MySQL server"**
- Check MySQL server is running
- Verify hostname/IP and port (default 3306)
- Check firewall rules allow connections
- For remote connections, ensure MySQL bind-address allows external connections

**Error: "Unknown database"**
- Verify database name is correct and exists
- Check user has access to the database
- In MySQL Workbench: Refresh schema list (right-click Schemas → Refresh All)

### Schema Differences (SQLite to MySQL)

| SQLite | MySQL |
|--------|-------|
| `INTEGER PRIMARY KEY AUTOINCREMENT` | `INT AUTO_INCREMENT PRIMARY KEY` |
| `TEXT` | `TEXT` or `VARCHAR(255)` |
| `REAL` | `DOUBLE` or `DECIMAL` |
| Case-insensitive by default | Case-sensitive for table/column names |
| No date/time types | `DATE`, `DATETIME`, `TIMESTAMP` |

**Common Issues:**
- Table/column names with mixed case: MySQL may lowercase them depending on system
- Auto-increment: MySQL uses `AUTO_INCREMENT` instead of `AUTOINCREMENT`
- String comparisons: Use `BINARY` for case-sensitive or `COLLATE` for case-insensitive

### Performance Optimization in MySQL Workbench

1. **Add Indexes:**
   ```sql
   -- Example: Add index on frequently queried columns
   CREATE INDEX idx_user_email ON Users(email);
   CREATE INDEX idx_movie_release_date ON Movies(release_date);
   CREATE INDEX idx_rating_user_movie ON Ratings(user_id, movie_id);
   ```

2. **Analyze Tables:**
   ```sql
   -- In MySQL Workbench SQL Editor
   ANALYZE TABLE Movies;
   ANALYZE TABLE Users;
   ```

3. **Optimize Tables:**
   ```sql
   OPTIMIZE TABLE Movies;
   OPTIMIZE TABLE Users;
   ```

4. **Check Table Status:**
   - Right-click table → "Table Inspector"
   - View indexes, constraints, and statistics

5. **Set Up Connection Pooling:**
   Add to your Flask app configuration:
   ```python
   # In app/__init__.py
   app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
       'pool_size': 10,
       'pool_recycle': 3600,
       'pool_pre_ping': True
   }
   ```

## Best Practices

1. **Backup First**: Always backup your SQLite database before migration
   ```bash
   # Backup SQLite
   cp instance/movies.db instance/movies.db.backup
   ```

2. **Test Locally**: Test migration in a local MySQL instance first using MySQL Workbench
   - Create a test database
   - Run your application against it
   - Verify all functionality works

3. **Use Migrations**: Consider using Flask-Migrate for schema versioning
   ```bash
   pip install Flask-Migrate
   flask db init
   flask db migrate -m "Initial migration"
   flask db upgrade
   ```

4. **Monitor Performance**: 
   - Use MySQL Workbench's Performance Dashboard
   - Monitor slow queries: `SHOW FULL PROCESSLIST;`
   - Check table sizes and indexes usage

5. **Connection Pooling**: Configure SQLAlchemy connection pooling for production (see Performance Optimization section)

6. **Security**: 
   - Use strong passwords
   - Limit user privileges to only what's needed
   - Use SSL/TLS for remote connections
   - Regularly update MySQL server

7. **Regular Backups**: Set up automated backups using MySQL Workbench or mysqldump
   ```bash
   mysqldump -u atozflix_user -p atozflix_db > backup_$(date +%Y%m%d).sql
   ```

## MySQL Workbench 8.0 Tips

### Connecting to Remote MySQL Server
1. File → Manage Connections
2. Click "+" to add new connection
3. Set:
   - Connection Name: Your choice
   - Hostname: Your MySQL server IP/hostname
   - Port: 3306 (default)
   - Username: Your MySQL username
   - Password: Click "Store in Keychain" for security
4. Test Connection → OK → Close

### Managing Tables Visually
- **Create Table**: Right-click Tables → "Create Table"
- **Edit Table**: Right-click table → "Alter Table"
- **View Data**: Right-click table → "Select Rows - Limit 1000"
- **Drop Table**: Right-click table → "Drop Table" (use with caution!)

### Running SQL Scripts
- File → Open SQL Script → Select .sql file
- Or paste SQL in query tab
- Select target schema from dropdown
- Execute with ⚡ button or Ctrl+Shift+Enter

### Exporting/Importing Data
- **Export**: Server → Data Export → Select schema/tables → Export
- **Import**: Server → Data Import → Select import file → Import

### Performance Monitoring
- Server Status → Performance Dashboard
- View active connections, queries, and resource usage


