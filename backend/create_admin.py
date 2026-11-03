"""
Create an admin account, or promote an existing user to admin.

WHY THIS EXISTS
---------------
/api/register always assigns role="user" - deliberately, since an endpoint
that let a caller choose its own role would be the whole access-control model
undone. That leaves no way to create the first admin, so every deployment
needs one out-of-band step. This is it.

Passwords are hashed with the same helper the registration endpoint uses, so
an account made here is indistinguishable from a registered one apart from
its role.

Usage:
    python create_admin.py --email me@example.com --username me --password secret
    python create_admin.py --email me@example.com --promote
    python create_admin.py --list
"""

import argparse
import sys

from dotenv import load_dotenv

from app import create_app, db
from app.models.models import User
from app.utils.helpers import hash_password, safe_database_uri
from app.utils.validators import is_valid_email

load_dotenv()


def main():
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--email", help="account email (the login identifier)")
    parser.add_argument("--username", help="display name; defaults to the local part of the email")
    parser.add_argument("--password", help="plaintext password; it is hashed before storage")
    parser.add_argument("--promote", action="store_true",
                        help="promote the existing user with this email instead of creating one")
    parser.add_argument("--list", action="store_true", dest="list_users",
                        help="list every account and role, then exit")
    args = parser.parse_args()

    app = create_app()
    with app.app_context():
        print(f"Database: {safe_database_uri(app.config['SQLALCHEMY_DATABASE_URI'])}")

        if args.list_users:
            users = User.query.order_by(User.user_id).all()
            if not users:
                print("No accounts.")
                return
            print(f"{len(users)} account(s):")
            for user in users:
                print(f"  {user.user_id:>4}  {user.role:<6}  {user.email}  ({user.username})")
            return

        if not args.email:
            parser.error("--email is required")
        if not is_valid_email(args.email):
            parser.error(f"not a valid email address: {args.email}")

        existing = User.query.filter_by(email=args.email).first()

        if args.promote:
            if not existing:
                sys.exit(f"No account with email {args.email}. Drop --promote to create one.")
            if existing.role == "admin":
                print(f"{args.email} is already an admin (user_id {existing.user_id}).")
                return
            was = existing.role
            existing.role = "admin"
            db.session.commit()
            print(f"Promoted {args.email} from {was} to admin (user_id {existing.user_id}).")
            return

        if existing:
            sys.exit(
                f"An account with email {args.email} already exists "
                f"(user_id {existing.user_id}, role {existing.role}).",
            )

        if not args.password:
            parser.error("--password is required when creating an account")

        username = args.username or args.email.split("@")[0]
        user = User(
            email=args.email,
            username=username,
            password=hash_password(args.password),
            role="admin",
        )
        db.session.add(user)
        db.session.commit()
        print(f"Created admin {args.email} (username {username}, user_id {user.user_id}).")


if __name__ == "__main__":
    main()
