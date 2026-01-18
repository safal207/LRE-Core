"""
User management CLI
Commands for creating and managing users
"""
import sys
import argparse
import getpass
from datetime import datetime, timezone
from src.auth.models import User, Role
from src.storage.user_store import user_store


def create_user_cmd(args):
    """Create a new user"""
    username = args.username
    password = args.password
    role = args.role

    if not password:
        password = getpass.getpass(f"Enter password for {username}: ")
        confirm = getpass.getpass("Confirm password: ")
        if password != confirm:
            print("Error: Passwords do not match")
            sys.exit(1)

    try:
        user = User.create(username, password, role)
        user_store.create_user(user)
        print(f"Successfully created user: {username} (Role: {role})")
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)


def list_users_cmd(args):
    """List all users"""
    users = user_store.list_users(include_inactive=args.all)

    if not users:
        print("No users found")
        return

    print(f"{'Username':<20} {'Role':<15} {'Status':<10} {'Created At'}")
    print("-" * 65)
    for user in users:
        status = "Active" if user.is_active else "Inactive"
        created_at = user.created_at.strftime("%Y-%m-%d %H:%M:%S")
        print(f"{user.username:<20} {user.role:<15} {status:<10} {created_at}")


def deactivate_user_cmd(args):
    """Deactivate a user"""
    user = user_store.get_user_by_username(args.username)
    if not user:
        print(f"Error: User '{args.username}' not found")
        sys.exit(1)

    user_store.deactivate_user(user.user_id)
    print(f"Successfully deactivated user: {args.username}")


def change_password_cmd(args):
    """Change user's password"""
    user = user_store.get_user_by_username(args.username)
    if not user:
        print(f"Error: User '{args.username}' not found")
        sys.exit(1)

    password = args.password
    if not password:
        password = getpass.getpass(f"Enter new password for {args.username}: ")
        confirm = getpass.getpass("Confirm password: ")
        if password != confirm:
            print("Error: Passwords do not match")
            sys.exit(1)

    try:
        new_hash = User.hash_password(password)
        user_store.update_password(user.user_id, new_hash)
        print(f"Successfully updated password for user: {args.username}")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="LRE-Core User Management CLI")
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # Create user
    create_parser = subparsers.add_parser("create", help="Create a new user")
    create_parser.add_argument("username", help="Unique username")
    create_parser.add_argument("--role", choices=["admin", "developer", "viewer"], default="viewer", help="User role")
    create_parser.add_argument("--password", help="User password (will prompt if not provided)")

    # List users
    list_parser = subparsers.add_parser("list", help="List all users")
    list_parser.add_argument("--all", action="store_true", help="Include inactive users")

    # Deactivate user
    deactivate_parser = subparsers.add_parser("deactivate", help="Deactivate a user")
    deactivate_parser.add_argument("username", help="Username to deactivate")

    # Change password
    password_parser = subparsers.add_parser("change-password", help="Change a user's password")
    password_parser.add_argument("username", help="Username to change password for")
    password_parser.add_argument("--password", help="New password (will prompt if not provided)")

    args = parser.parse_args()

    if args.command == "create":
        create_user_cmd(args)
    elif args.command == "list":
        list_users_cmd(args)
    elif args.command == "deactivate":
        deactivate_user_cmd(args)
    elif args.command == "change-password":
        change_password_cmd(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
