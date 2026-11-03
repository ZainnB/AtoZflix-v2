# setup_db.py
from app import create_app, db
from app.models import models
from app.utils.helpers import safe_database_uri
from dotenv import load_dotenv
import os
import sys

load_dotenv()

app = create_app()

with app.app_context():
    database_uri = app.config['SQLALCHEMY_DATABASE_URI']
    print("=" * 60)
    print("Database Setup Script")
    print("=" * 60)

    # The old inline masking replaced every occurrence of the password string
    # anywhere in the URI, which mangles the host or database name whenever the
    # password happens to be a substring of either. One shared helper now does
    # it properly for every script.
    safe_uri = safe_database_uri(database_uri)

    print(f"Database URI: {safe_uri}")
    print(f"Database Type: {'MySQL' if 'mysql' in database_uri.lower() else 'SQLite'}")
    print("=" * 60)
    
    try:
        # Test connection first
        print("Testing database connection...")
        db.engine.connect()
        print("[OK] Connection successful!")
        
        print("\nCreating tables...")
        db.create_all()
        print("[OK] All tables created successfully (or already exist).")
        
        # Verify tables
        print("\nVerifying tables...")
        inspector = db.inspect(db.engine)
        tables = inspector.get_table_names()
        print(f"[OK] Found {len(tables)} tables:")
        for table in sorted(tables):
            print(f"    - {table}")
            
        print("\n" + "=" * 60)
        print("[OK] Database setup completed successfully!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n[FAIL] Error during database setup:")
        print(f"  {type(e).__name__}: {e}")
        print("\n" + "=" * 60)
        print("TROUBLESHOOTING:")
        print("=" * 60)
        
        if "Access denied" in str(e) or "1045" in str(e):
            print("MySQL Access Denied Error Detected!")
            print("\nRun this diagnostic script first:")
            print("  python test_mysql_connection.py")
            print("\nCommon fixes:")
            print("1. Create user for 'localhost' in MySQL Workbench:")
            print("   See migration_guide.md section 1 for detailed steps")
            print("\n2. Quick SQL fix in MySQL Workbench:")
            print("   CREATE USER 'atozflix_user'@'localhost' IDENTIFIED BY 'your_password';")
            print("   GRANT ALL PRIVILEGES ON atozflix_db.* TO 'atozflix_user'@'localhost';")
            print("   FLUSH PRIVILEGES;")
            
        elif "Unknown database" in str(e) or "1049" in str(e):
            print("Database does not exist!")
            print("Create the database in MySQL Workbench first:")
            print("  CREATE DATABASE atozflix_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")
            
        else:
            print("Check your DATABASE_URL in .env file")
            print("Verify MySQL server is running")
            print("See migration_guide.md for detailed setup instructions")
        
        print("=" * 60)
        sys.exit(1)

