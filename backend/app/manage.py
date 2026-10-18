"""Local operator controls. No HTTP endpoint can grant itself repository access."""
import argparse
import getpass
import sys

from pwdlib import PasswordHash
from sqlalchemy import select
from sqlalchemy.orm import Session

from .database import make_engine
from .models import User
from .repositories import update_repository_grant
from .schemas import Registration
from .settings import get_settings


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["grant-repository", "revoke-repository", "create-user"])
    parser.add_argument("--workspace")
    parser.add_argument("--target")
    parser.add_argument("--profile")
    parser.add_argument("--email")
    parser.add_argument("--name")
    parser.add_argument("--password-stdin", action="store_true")
    args = parser.parse_args()
    if args.action != "create-user" and not all([args.workspace, args.target, args.profile]):
        parser.error("Repository actions require --workspace, --target and --profile")
    if args.action == "create-user" and not all([args.email, args.name]):
        parser.error("Account creation requires --email and --name")
    settings = get_settings()
    engine = make_engine(settings)
    try:
        with Session(engine) as db, db.begin():
            if args.action == "create-user":
                password = sys.stdin.readline().rstrip("\r\n") if args.password_stdin else getpass.getpass("Password: ")
                account = Registration(email=args.email, name=args.name, password=password)
                if db.scalar(select(User.id).where(User.email == str(account.email).lower())):
                    raise ValueError("Account already exists")
                db.add(User(email=str(account.email).lower(), name=account.name,
                            password_hash=PasswordHash.recommended().hash(account.password)))
            else:
                assert args.workspace and args.target and args.profile
                update_repository_grant(db, settings, args.workspace, args.target, args.profile,
                                        allowed=args.action == "grant-repository")
        print("Operator action completed")
    finally:
        engine.dispose()


if __name__ == "__main__":
    main()
