# setup_db.py
from app import create_app, db
from app.models import models
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
    
    # Hide password in output
    if '@' in database_uri:
        parts = database_uri.split('@')
        if ':' in parts[0]:
            user_pass = parts[0].split('://', 1)[1]
            if ':' in user_pass:
                user = user_pass.split(':')[0]
                safe_uri = database_uri.replace(user_pass.split(':')[1], '***')
            else:
                safe_uri = database_uri
        else:
            safe_uri = database_uri
    else:
        safe_uri = database_uri
        
    print(f"Database URI: {safe_uri}")
    print(f"Database Type: {'MySQL' if 'mysql' in database_uri.lower() else 'SQLite'}")
    print("=" * 60)
    
    try:
        # Test connection first
        print("Testing database connection...")
        db.engine.connect()
        print("✓ Connection successful!")
        
        print("\nCreating tables...")
        db.create_all()
        print("✓ All tables created successfully (or already exist).")
        
        # Verify tables
        print("\nVerifying tables...")
        inspector = db.inspect(db.engine)
        tables = inspector.get_table_names()
        print(f"✓ Found {len(tables)} tables:")
        for table in sorted(tables):
            print(f"    - {table}")
            
        print("\n" + "=" * 60)
        print("✓ Database setup completed successfully!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n✗ Error during database setup:")
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

