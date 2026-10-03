"""Local APOS server and maintenance commands."""
import argparse
from getpass import getpass
from werkzeug.security import check_password_hash
import os
import sqlite3
from pathlib import Path

from app import create_app, save_settings, price_cents
from catalog_import import parse_catalog


def main():
    parser = argparse.ArgumentParser(description="APOS association point of sale")
    parser.add_argument("command", nargs="?", choices=("serve", "backup", "password", "setup", "demo-stock"), default="serve")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=5000)
    parser.add_argument("--output", help="New destination file for backup")
    args = parser.parse_args()
    os.umask(0o077)
    app = create_app()
    if args.command == "demo-stock":
        rows = parse_catalog((Path(__file__).parent / "data" / "demo_catalog.csv").read_bytes(), price_cents)
        with sqlite3.connect(app.config["DATABASE"]) as connection:
            connection.execute("BEGIN IMMEDIATE")
            names = {row[0].casefold() for row in connection.execute("SELECT name FROM products")}
            additions = [row for row in rows if row["name"].casefold() not in names]
            connection.executemany("INSERT INTO products(name,cents,usd_cents,in_stock,active) VALUES (:name,:cents,:usd_cents,:in_stock,:active)", additions)
        print(f"Added {len(additions)} demo products; existing products were preserved.")
    elif args.command == "setup":
        with sqlite3.connect(app.config["DATABASE"]) as connection:
            current_url = connection.execute("SELECT value FROM settings WHERE key='patron_base_url'").fetchone()[0]
            password = getpass("New recovery admin password (at least 12 characters): ")
            if password != getpass("Confirm staff password: "):
                parser.error("Passwords do not match")
            base_url = input(f"Guest-facing URL/FQDN [{current_url}]: ").strip() or current_url
            try:
                save_settings(connection, base_url, password)
            except ValueError as error:
                parser.error(str(error))
        print("Admin setup saved. Sign in as admin with your chosen password. Existing staff sessions have been signed out.")
    elif args.command == "password":
        with sqlite3.connect(app.config["DATABASE"]) as connection:
            password_hash = connection.execute("SELECT password_hash FROM accounts WHERE username='admin'").fetchone()[0]
        if check_password_hash(password_hash, app.config["STAFF_PASSWORD"]):
            print(app.config["STAFF_PASSWORD"])
        else:
            print("A custom password is configured and cannot be displayed. Run 'python main.py setup' locally to reset it.")
    elif args.command == "backup":
        if not args.output:
            parser.error("backup requires --output")
        destination = Path(args.output)
        if destination.resolve() == Path(app.config["DATABASE"]).resolve():
            parser.error("backup destination must differ from the live database")
        try:
            with destination.open("xb"):
                pass
        except FileExistsError:
            parser.error("backup destination already exists; choose a new filename")
        with sqlite3.connect(app.config["DATABASE"]) as source, sqlite3.connect(destination) as target:
            source.backup(target)
        print(f"Backup saved to {destination}")
    else:
        from waitress import serve
        print(f"APOS: http://{args.host}:{args.port}", flush=True)
        print("Admin username: admin. Password: run 'python main.py password' in another terminal.", flush=True)
        serve(app, host=args.host, port=args.port)


if __name__ == "__main__":
    main()
