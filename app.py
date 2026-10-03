"""APOS v1: a local, persistent association point of sale."""
import os
from member_import import parse_members
from notices import sanitize_notice, display_notice, example_notice
import base64
import segno
import secrets
import csv
import io
import json
from catalog_import import parse_catalog, MAX_CSV_BYTES
from member_photos import read_photo
from mail_delivery import configure_mail, ready as mail_ready, email_address, send_bon
import smtplib
from cryptography.fernet import InvalidToken
import sqlite3
import re
from urllib.parse import urlsplit
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timezone, timedelta
from decimal import Decimal, InvalidOperation
from pathlib import Path

from flask import Flask, abort, flash, g, redirect, render_template, request, session, url_for, Response


def price_cents(value, maximum=999999):
    try:
        amount = Decimal(str(value))
        if not amount.is_finite() or amount <= 0 or amount > maximum:
            raise ValueError("Price must be between 0.01 and 999999.00.")
        if amount != amount.quantize(Decimal("0.01")):
            raise ValueError("Use at most two decimal places.")
        return int(amount * 100)
    except (InvalidOperation, TypeError):
        raise ValueError("Enter a valid price.") from None


DICEWARE_WORDS = tuple(line.split()[1] for line in (Path(__file__).parent / "data" / "eff_large_wordlist.txt").read_text().splitlines())
DICEWARE_WORD_SET = frozenset(DICEWARE_WORDS)

GUEST_CODE_ALPHABET = "23456789ABCDEFGHJKLMNPQRSTUVWXYZ"


def generate_guest_code():
    # Uniform independent choices are equivalent to five fair dice per word.
    return "-".join(secrets.choice(DICEWARE_WORDS) for _ in range(4))


def normalize_guest_code(value):
    words = re.split(r"[\s-]+", value.strip().lower())
    if len(words) == 4 and all(word in DICEWARE_WORD_SET for word in words):
        return "-".join(words)
    compact = re.sub(r"[\s-]", "", value).upper()
    if len(compact) == 20 and all(char in GUEST_CODE_ALPHABET for char in compact):
        return "-".join(compact[index:index + 4] for index in range(0, 20, 4))
    return value


def normalize_base_url(value):
    value = value.strip()
    if not value:
        return ""
    if "://" not in value:
        value = "https://" + value
    try:
        parsed = urlsplit(value)
        port = parsed.port
        if (parsed.scheme not in ("http", "https") or not parsed.hostname
                or parsed.username is not None or parsed.password is not None
                or parsed.path not in ("", "/") or parsed.query or parsed.fragment
                or not re.fullmatch(r"[A-Za-z0-9.-]+", parsed.hostname)
                or any(char.isspace() for char in value)):
            raise ValueError
    except ValueError:
        raise ValueError("Enter a hostname or an HTTP/HTTPS URL without a path.") from None
    return f"{parsed.scheme}://{parsed.netloc}".rstrip("/")


def save_settings(connection, base_url, password=None, guest_ordering=None, account_id=None, currency=None):
    base_url = normalize_base_url(base_url)
    if currency is not None and currency not in ("EUR", "USD"):
        raise ValueError("Select EUR or USD.")
    if password is not None and not 12 <= len(password) <= 256:
        raise ValueError("Staff password must contain 12–256 characters.")
    with connection:
        connection.execute("INSERT OR REPLACE INTO settings(key,value) VALUES ('patron_base_url',?)", (base_url,))
        if currency is not None:
            connection.execute("INSERT OR REPLACE INTO settings VALUES ('currency',?)", (currency,))
        if guest_ordering is not None:
            connection.execute("INSERT OR REPLACE INTO settings VALUES ('guest_ordering',?)", ("1" if guest_ordering else "0",))
        if password is not None:
            recovery_change = account_id is None or connection.execute("SELECT username FROM accounts WHERE id=?", (account_id,)).fetchone()[0] == "admin"
            if recovery_change:
                connection.execute("UPDATE settings SET value=? WHERE key='staff_password_hash'", (generate_password_hash(password),))
            connection.execute("UPDATE settings SET value=CAST(value AS INTEGER)+1 WHERE key='credential_version'")
            if connection.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='accounts'").fetchone():
                if account_id is None:
                    connection.execute("UPDATE accounts SET password_hash=?,version=version+1,active=1,role='Admin' WHERE username='admin'", (generate_password_hash(password),))
                else:
                    connection.execute("UPDATE accounts SET password_hash=?,version=version+1 WHERE id=?", (generate_password_hash(password),account_id))


def create_app(config=None):
    app = Flask(__name__)
    app.config.from_mapping(DATABASE=os.environ.get("APOS_DATABASE", str(Path(app.instance_path) / "apos.sqlite3")),
                            SECRET_KEY=os.environ.get("APOS_SECRET_KEY"), STAFF_PASSWORD=os.environ.get("APOS_STAFF_PASSWORD"),
                            SESSION_COOKIE_HTTPONLY=True,
                            SESSION_COOKIE_SECURE=os.environ.get("APOS_SECURE_COOKIES", "0") == "1",
                            SESSION_COOKIE_SAMESITE="Strict", MAX_CONTENT_LENGTH=4 * 1024 * 1024, PATRON_BASE_URL=os.environ.get("APOS_PATRON_BASE_URL", ""))
    if config:
        app.config.update(config)
    Path(app.instance_path).mkdir(parents=True, exist_ok=True)
    if not app.config["SECRET_KEY"]:
        key_file = Path(app.instance_path) / "secret.key"
        try:
            with open(key_file, "x", opener=lambda path, flags: os.open(path, flags, 0o600)) as handle:
                handle.write(secrets.token_hex(32))
        except FileExistsError:
            pass
        app.config["SECRET_KEY"] = key_file.read_text().strip()

    if not app.config["STAFF_PASSWORD"]:
        password_file = Path(app.instance_path) / "staff.key"
        try:
            with open(password_file, "x", opener=lambda path, flags: os.open(path, flags, 0o600)) as handle:
                handle.write(secrets.token_urlsafe(18))
        except FileExistsError:
            pass
        app.config["STAFF_PASSWORD"] = password_file.read_text().strip()

    def db():
        if "db" not in g:
            g.db = sqlite3.connect(app.config["DATABASE"], timeout=10)
            g.db.row_factory = sqlite3.Row
            g.db.execute("PRAGMA foreign_keys = ON")
        return g.db

    @app.teardown_appcontext
    def close_db(_error):
        connection = g.pop("db", None)
        if connection:
            connection.close()

    with app.app_context():
        db().executescript("""
        CREATE TABLE IF NOT EXISTS accounts (
          id INTEGER PRIMARY KEY, username TEXT NOT NULL COLLATE NOCASE UNIQUE,
          password_hash TEXT NOT NULL, role TEXT NOT NULL CHECK(role IN ('Member','Guest','Staff','Admin')),
          member_id INTEGER REFERENCES members(id), active INTEGER NOT NULL DEFAULT 1 CHECK(active IN (0,1)),
          version INTEGER NOT NULL DEFAULT 1);
        CREATE TABLE IF NOT EXISTS account_events (
          id INTEGER PRIMARY KEY, actor TEXT NOT NULL, subject_id INTEGER, action TEXT NOT NULL, occurred TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS member_imports (token TEXT PRIMARY KEY, payload TEXT NOT NULL, created TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS catalog_imports (token TEXT PRIMARY KEY, payload TEXT NOT NULL, created TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS members (
          id INTEGER PRIMARY KEY, name TEXT NOT NULL, code TEXT NOT NULL UNIQUE,
          active INTEGER NOT NULL DEFAULT 1 CHECK(active IN (0,1)), photo BLOB);
        CREATE TABLE IF NOT EXISTS products (
          id INTEGER PRIMARY KEY, name TEXT NOT NULL, cents INTEGER NOT NULL CHECK(cents > 0),
          usd_cents INTEGER NOT NULL CHECK(usd_cents > 0),
          active INTEGER NOT NULL DEFAULT 1 CHECK(active IN (0,1)),
          in_stock INTEGER NOT NULL DEFAULT 1 CHECK(in_stock IN (0,1)));
        CREATE TABLE IF NOT EXISTS tabs (
          id INTEGER PRIMARY KEY, member_id INTEGER NOT NULL REFERENCES members(id),
          opened TEXT NOT NULL, closed TEXT, currency TEXT NOT NULL CHECK(currency IN ('EUR','USD')),
          code TEXT NOT NULL UNIQUE, expires TEXT, guest_email_state TEXT);
        CREATE UNIQUE INDEX IF NOT EXISTS one_open_tab ON tabs(member_id) WHERE closed IS NULL;
        CREATE TABLE IF NOT EXISTS lines (
          id INTEGER PRIMARY KEY, tab_id INTEGER NOT NULL REFERENCES tabs(id),
          name TEXT NOT NULL, cents INTEGER NOT NULL CHECK(cents > 0),
          quantity INTEGER NOT NULL CHECK(quantity BETWEEN 1 AND 999),
          ordered TEXT NOT NULL, product_id INTEGER NOT NULL REFERENCES products(id));
        CREATE TABLE IF NOT EXISTS cancellations (
          line_id INTEGER PRIMARY KEY REFERENCES lines(id), cancelled TEXT NOT NULL, reason TEXT NOT NULL,
          actor TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS receipts (
          id INTEGER PRIMARY KEY, tab_id INTEGER NOT NULL REFERENCES tabs(id),
          paid TEXT NOT NULL, method TEXT NOT NULL CHECK(method IN ('cash','card')),
          total_cents INTEGER NOT NULL CHECK(total_cents > 0), payment_token TEXT NOT NULL UNIQUE,
          paid_after INTEGER NOT NULL, due_after INTEGER NOT NULL);
        CREATE TABLE IF NOT EXISTS receipt_lines (
          receipt_id INTEGER NOT NULL REFERENCES receipts(id), name TEXT NOT NULL,
          cents INTEGER NOT NULL, quantity INTEGER NOT NULL, ordered TEXT NOT NULL);
        CREATE INDEX IF NOT EXISTS lines_tab ON lines(tab_id);
        CREATE INDEX IF NOT EXISTS lines_ordered ON lines(ordered);
        CREATE INDEX IF NOT EXISTS receipts_tab ON receipts(tab_id);
        CREATE INDEX IF NOT EXISTS receipts_paid ON receipts(paid);
        """)

        with db():
            if "guest_email_state" not in {row["name"] for row in db().execute("PRAGMA table_info(tabs)")}:
                db().execute("ALTER TABLE tabs ADD COLUMN guest_email_state TEXT")
            db().execute("INSERT OR IGNORE INTO settings VALUES ('smtp_config',?)", (json.dumps({"enabled":False,"host":"","port":587,"sender":"","username":"","security":"starttls","password":""}),))
            db().execute("INSERT OR IGNORE INTO settings VALUES ('guest_ordering','0')")
            db().execute("INSERT OR IGNORE INTO settings VALUES ('currency','EUR')")
            for key in ("legal_notice", "privacy_notice"):
                db().execute("INSERT OR IGNORE INTO settings VALUES (?,'')", (key,))
                db().execute("INSERT OR IGNORE INTO settings VALUES (?,'plain')", (key + "_format",))
            if "alcohol" not in {row["name"] for row in db().execute("PRAGMA table_info(products)")}:
                db().execute("ALTER TABLE products ADD COLUMN alcohol INTEGER NOT NULL DEFAULT 0 CHECK(alcohol IN (0,1))")
            member_columns = {row["name"] for row in db().execute("PRAGMA table_info(members)")}
            if "active" not in member_columns:
                db().execute("ALTER TABLE members ADD COLUMN active INTEGER NOT NULL DEFAULT 1 CHECK(active IN (0,1))")
            if "is_guest" not in member_columns:
                db().execute("ALTER TABLE members ADD COLUMN is_guest INTEGER NOT NULL DEFAULT 0 CHECK(is_guest IN (0,1))")
            if "guest_number" not in member_columns:
                db().execute("ALTER TABLE members ADD COLUMN guest_number INTEGER")
            db().execute("CREATE UNIQUE INDEX IF NOT EXISTS unique_guest_number ON members(guest_number) WHERE guest_number IS NOT NULL")
            if "photo" not in member_columns:
                db().execute("ALTER TABLE members ADD COLUMN photo BLOB")
            if "in_stock" not in {row["name"] for row in db().execute("PRAGMA table_info(products)")} :
                db().execute("ALTER TABLE products ADD COLUMN in_stock INTEGER NOT NULL DEFAULT 1 CHECK(in_stock IN (0,1))")
            if not db().execute("SELECT 1 FROM settings WHERE key='staff_password_hash'").fetchone():
                db().execute("INSERT INTO settings VALUES ('staff_password_hash',?)", (generate_password_hash(app.config["STAFF_PASSWORD"]),))
            db().execute("INSERT OR IGNORE INTO settings VALUES ('credential_version','1')")
            if not db().execute("SELECT 1 FROM accounts").fetchone():
                db().execute("INSERT INTO accounts(username,password_hash,role) VALUES ('admin',?,'Admin')", (db().execute("SELECT value FROM settings WHERE key='staff_password_hash'").fetchone()[0],))
            db().execute("INSERT OR IGNORE INTO settings VALUES ('patron_base_url',?)", (normalize_base_url(app.config["PATRON_BASE_URL"]),))

    def setting(key):
        return db().execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()[0]

    def notice_source(kind, language=None):
        language = language or session.get("lang", "de")
        if language != "en":
            key = kind + "_" + language
            row = db().execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
            if row and row["value"]:
                fmt = db().execute("SELECT value FROM settings WHERE key=?", (key + "_format",)).fetchone()
                return row["value"], fmt["value"] if fmt else "html"
        return setting(kind), setting(kind + "_format")

    def notice_content(kind, language=None):
        value, fmt = notice_source(kind, language)
        return display_notice(value, fmt == "html") if value else ""

    @app.template_filter("initials")
    def initials(name):
        return "".join(word[0].upper() for word in name.split())

    @app.template_filter("money")
    def money(cents, currency="EUR"):
        symbol = "€" if currency == "EUR" else "$"
        if session.get("lang", "de") == "de":
            return f"{cents // 100:,}".replace(",", ".") + f",{cents % 100:02d} {symbol}"
        return f"{symbol}{cents // 100:,}.{cents % 100:02d}"

    @app.context_processor
    def template_context():
        if "csrf" not in session:
            session["csrf"] = secrets.token_hex(32)
        from translations import translate
        return {"csrf": session["csrf"], "t": lambda message: translate(message, session.get("lang", "de")),
                "lang": session.get("lang", "de"), "current_user": g.get("user"), "is_admin": bool(g.get("user") and g.user["role"] == "Admin")}

    @app.before_request
    def protect_forms():
        if request.method == "POST":
            token = request.form.get("csrf", "")
            if not token or not secrets.compare_digest(token.encode(), session.get("csrf", "").encode()):
                abort(400, description="This form expired. Reload the page and try again.")

        g.user = None
        if session.get("account_id"):
            user = db().execute("SELECT * FROM accounts WHERE id=? AND active=1", (session["account_id"],)).fetchone()
            if (user and user["version"] == session.get("account_version")
                    and session.get("credential_version") == setting("credential_version")):
                if user["role"] in ("Member", "Guest"):
                    profile = db().execute("SELECT active FROM members WHERE id=?", (user["member_id"],)).fetchone()
                    if profile and profile["active"]:
                        g.user = user
                else:
                    g.user = user
            if g.user is None:
                language = session.get("lang", "de")
                session.clear()
                session["lang"] = language
        session["staff"] = bool(g.user and g.user["role"] in ("Staff", "Admin"))
        public = {"login", "language", "patron", "patron_lookup", "patron_photo", "patron_email", "patron_email_sent", "patron_add_item", "legal_page", "static"}
        admin = {"settings", "mail_settings", "edit_notice", "notice_preview", "accounts", "edit_account", "add_member", "edit_member", "remove_member",
                 "add_product", "edit_product", "toggle_product", "product_stock", "catalog_upload", "catalog_preview", "catalog_import", "catalog_template",
                 "member_upload", "member_preview", "member_import", "member_template"}
        endpoint = request.endpoint
        if endpoint and endpoint not in public:
            if not g.user:
                return redirect(url_for("login"))
            if endpoint in admin:
                if g.user["role"] != "Admin":
                    abort(403, description="Administrator access required.")
            elif endpoint == "member_photo" and g.user["role"] in ("Member", "Guest"):
                if request.view_args["member_id"] != g.user["member_id"]:
                    abort(403)
            elif endpoint not in ("my_tab", "logout") and g.user["role"] not in ("Staff", "Admin"):
                abort(403, description="Staff access required.")

    @app.route("/login", methods=["GET", "POST"])
    def login():
        if request.method == "POST":
            username = request.form.get("username", "admin").strip()
            user = db().execute("SELECT * FROM accounts WHERE username=? AND active=1", (username,)).fetchone()
            authenticated = check_password_hash(user["password_hash"] if user else setting("staff_password_hash"), request.form.get("password", ""))
            if user and user["role"] in ("Member", "Guest"):
                profile = db().execute("SELECT active FROM members WHERE id=?", (user["member_id"],)).fetchone()
                authenticated = authenticated and bool(profile and profile["active"])
            if user and authenticated:
                selected_language = session.get("lang", "de")
                session.clear()
                session["lang"] = selected_language
                session["staff"] = user["role"] in ("Staff", "Admin")
                session["account_id"] = user["id"]
                session["account_version"] = user["version"]
                session["credential_version"] = setting("credential_version")
                return redirect(url_for("index" if user["role"] in ("Staff","Admin") else "my_tab"))
            flash("Incorrect username or password.", "error")
        return render_template("login.html")

    @app.route("/settings", methods=["GET", "POST"])
    @app.route("/admin", methods=["GET", "POST"])
    def settings():
        if request.method == "POST":
            try:
                new_password = request.form.get("new_password", "")
                if new_password:
                    if not check_password_hash(g.user["password_hash"], request.form.get("current_password", "")):
                        raise ValueError("Incorrect current password.")
                    if new_password != request.form.get("confirm_password", ""):
                        raise ValueError("Passwords do not match.")
                notices = {key: request.form.get(key, setting(key)).strip() for key in ("legal_notice", "privacy_notice")}
                if any(len(value) > 20000 for value in notices.values()):
                    raise ValueError("Legal notices must not exceed 20000 characters.")
                save_settings(db(), request.form.get("base_url", ""), new_password or None, request.form.get("guest_ordering") == "1", g.user["id"], request.form.get("currency", setting("currency")))
                with db():
                    db().executemany("UPDATE settings SET value=? WHERE key=?", [(value,key) for key,value in notices.items()])
                    for key in notices:
                        if key in request.form:
                            db().execute("UPDATE settings SET value='plain' WHERE key=?", (key + "_format",))
                if new_password:
                    selected_language = session.get("lang", "de")
                    session.clear()
                    session["lang"] = selected_language
                    flash("Password changed. Sign in with your new password.", "success")
                    return redirect(url_for("login"))
                flash("Settings saved.", "success")
                return redirect(url_for("settings"))
            except ValueError as error:
                flash(str(error), "error")
        return render_template("settings.html", currency=setting("currency"), base_url=setting("patron_base_url"), guest_ordering=setting("guest_ordering") == "1", legal_notice=notice_content("legal_notice"), privacy_notice=notice_content("privacy_notice"),
            members=db().execute("SELECT * FROM members WHERE active=1 AND is_guest=0 ORDER BY name").fetchall(),
            products=db().execute("SELECT * FROM products ORDER BY active DESC,name").fetchall(),
            guests=db().execute("SELECT * FROM members WHERE active=1 AND is_guest=1 ORDER BY id DESC").fetchall())

    @app.get("/legal/<kind>")
    def legal_page(kind):
        if kind not in ("legal_notice", "privacy_notice"):
            abort(404)
        return render_template("legal.html", kind=kind, notice=notice_content(kind))

    @app.route("/settings/notices/<kind>", methods=["GET", "POST"])
    @app.route("/admin/notices/<kind>", methods=["GET", "POST"])
    def edit_notice(kind):
        if kind not in ("legal_notice", "privacy_notice"):
            abort(404)
        if request.method == "POST":
            language = request.form.get("notice_language", session.get("lang", "de"))
            if language not in ("de", "en"):
                abort(400)
            key = kind if language == "en" else kind + "_" + language
            value = request.form.get("content", "")
            content_format = request.form.get("content_format", "html")
            if content_format not in ("html", "markdown"):
                abort(400)
            cleaned = sanitize_notice(value) if content_format == "html" else (value if value.strip() else "")
            if len(value) > 20000 or len(cleaned) > 20000:
                abort(400, description="Legal notices must not exceed 20000 characters.")
            with db():
                db().execute("INSERT OR REPLACE INTO settings VALUES (?,?)", (key,cleaned))
                db().execute("INSERT OR REPLACE INTO settings VALUES (?,?)", (key + "_format",content_format))
            flash("Notice saved.", "success")
            return redirect(url_for("settings"))
        source, fmt = notice_source(kind)
        return render_template("notice_editor.html", kind=kind,
            notice=notice_content(kind), source=source, source_format="html" if fmt == "html" or not source else "markdown",
            example=example_notice(kind, session.get("lang", "de")))

    @app.post("/admin/notices/preview")
    def notice_preview():
        value = request.form.get("content", "")
        if len(value) > 20000:
            abort(400, description="Legal notices must not exceed 20000 characters.")
        return Response(str(display_notice(value)), mimetype="text/html")

    @app.route("/settings/mail", methods=["GET", "POST"])
    @app.route("/admin/mail", methods=["GET", "POST"])
    def mail_settings():
        config = json.loads(setting("smtp_config"))
        if request.method == "POST":
            try:
                updated = configure_mail(request.form, config, app.config["SECRET_KEY"])
                with db():
                    db().execute("UPDATE settings SET value=? WHERE key='smtp_config'", (json.dumps(updated),))
                flash("Outbound mail settings saved.", "success")
                return redirect(url_for("mail_settings"))
            except ValueError as error:
                flash(str(error), "error")
        return render_template("mail_settings.html", config=config)

    @app.route("/products/<int:product_id>/edit", methods=["GET", "POST"])
    def edit_product(product_id):
        product = db().execute("SELECT * FROM products WHERE id=?", (product_id,)).fetchone()
        if product is None:
            abort(404)
        if request.method == "POST":
            try:
                name = text("name")
                cents = price_cents(request.form.get("price"))
                usd_cents = price_cents(request.form.get("usd_price"))
                with db():
                    db().execute("UPDATE products SET name=?,cents=?,usd_cents=?,alcohol=? WHERE id=?", (name,cents,usd_cents,1 if request.form.get("alcohol") == "1" else 0,product_id))
                flash("Product updated. Existing orders retain their original name and price.", "success")
                return redirect(url_for("settings"))
            except ValueError as error:
                flash(str(error), "error")
        return render_template("edit_product.html", product=product)

    def account_values(current=None):
        username = request.form.get("username", "").strip()
        if not re.fullmatch(r"[A-Za-z0-9_.@-]{1,80}", username):
            raise ValueError("Username must contain 1–80 letters, numbers or . _ @ -.")
        if current and current["username"] == "admin" and username != "admin":
            raise ValueError("The recovery administrator username must remain admin.")
        role = request.form.get("role", "")
        if role not in ("Member", "Guest", "Staff", "Admin"):
            raise ValueError("Choose a valid role.")
        member_id = request.form.get("member_id", "").strip()
        if member_id:
            profile = db().execute("SELECT id,is_guest FROM members WHERE id=? AND active=1", (member_id,)).fetchone()
            if not profile:
                raise ValueError("Select an active profile.")
            member_id = profile["id"]
            if role in ("Member", "Guest") and bool(profile["is_guest"]) != (role == "Guest"):
                raise ValueError("The role must match the linked member or guest profile.")
        else:
            member_id = None
        if role in ("Member", "Guest") and member_id is None:
            raise ValueError("Member and Guest accounts require a linked profile.")
        password = request.form.get("password", "")
        if (not current or password) and not 12 <= len(password) <= 256:
            raise ValueError("Staff password must contain 12–256 characters.")
        password_hash = generate_password_hash(password) if password else current["password_hash"]
        return username, password_hash, role, member_id, int(request.form.get("active") == "1")

    @app.route("/admin/accounts", methods=["GET", "POST"])
    def accounts():
        if request.method == "POST":
            try:
                with db():
                    db().execute("BEGIN IMMEDIATE")
                    values = account_values()
                    cursor = db().execute("INSERT INTO accounts(username,password_hash,role,member_id,active) VALUES (?,?,?,?,?)", values)
                    db().execute("INSERT INTO account_events(actor,subject_id,action,occurred) VALUES (?,?,?,?)", (g.user["username"],cursor.lastrowid,"created " + values[2],timestamp()))
                flash("Account saved.", "success")
                return redirect(url_for("accounts"))
            except (ValueError, sqlite3.IntegrityError) as error:
                flash("Username already exists." if isinstance(error,sqlite3.IntegrityError) else str(error), "error")
        return render_template("accounts.html", accounts=db().execute("SELECT accounts.id,username,role,accounts.active,members.name FROM accounts LEFT JOIN members ON members.id=member_id ORDER BY username").fetchall(),
            profiles=db().execute("SELECT id,name,code,is_guest FROM members WHERE active=1 ORDER BY name").fetchall())

    @app.route("/admin/accounts/<int:account_id>", methods=["GET", "POST"])
    def edit_account(account_id):
        account = db().execute("SELECT * FROM accounts WHERE id=?", (account_id,)).fetchone()
        if account is None:
            abort(404)
        if request.method == "POST":
            try:
                with db():
                    db().execute("BEGIN IMMEDIATE")
                    account = db().execute("SELECT * FROM accounts WHERE id=?", (account_id,)).fetchone()
                    values = account_values(account)
                    if account["role"] == "Admin" and account["active"] and (values[2] != "Admin" or not values[4]):
                        if db().execute("SELECT COUNT(*) FROM accounts WHERE role='Admin' AND active=1").fetchone()[0] <= 1:
                            raise ValueError("Keep at least one active Admin account.")
                    db().execute("UPDATE accounts SET username=?,password_hash=?,role=?,member_id=?,active=?,version=version+1 WHERE id=?", (*values,account_id))
                    db().execute("INSERT INTO account_events(actor,subject_id,action,occurred) VALUES (?,?,?,?)", (g.user["username"],account_id,"updated " + values[2] + (" active" if values[4] else " disabled"),timestamp()))
                flash("Account saved.", "success")
                return redirect(url_for("accounts"))
            except (ValueError, sqlite3.IntegrityError) as error:
                flash("Username already exists." if isinstance(error,sqlite3.IntegrityError) else str(error), "error")
        return render_template("edit_account.html", account=account, profiles=db().execute("SELECT id,name,code,is_guest FROM members WHERE active=1 ORDER BY name").fetchall())

    @app.get("/my-tab")
    def my_tab():
        if not g.user["member_id"]:
            return render_template("my_tab.html")
        tab = db().execute("SELECT * FROM tabs WHERE member_id=? AND guest_email_state IS NOT 'sent' AND (expires IS NULL OR expires>?) ORDER BY id DESC LIMIT 1", (g.user["member_id"],timestamp())).fetchone()
        if tab:
            return redirect(url_for("patron",code=tab["code"]))
        return render_template("my_tab.html")

    def check_member_codes(rows):
        existing = {row["code"].casefold() for row in db().execute("SELECT code FROM members")}
        if any(row["code"].casefold() in existing for row in rows):
            raise ValueError("A member code already exists. Change the CSV code or edit the existing profile.")

    @app.route("/admin/members/upload", methods=["GET", "POST"])
    def member_upload():
        if request.method == "POST":
            try:
                upload = request.files.get("members")
                if upload is None:
                    raise ValueError("Choose a CSV file.")
                rows = parse_members(upload.stream.read(MAX_CSV_BYTES + 1))
                check_member_codes(rows)
                token = secrets.token_urlsafe(32)
                with db():
                    db().execute("DELETE FROM member_imports WHERE created<?", ((datetime.now(timezone.utc)-timedelta(hours=24)).isoformat(timespec="seconds"),))
                    db().execute("DELETE FROM member_imports WHERE token=?", (session.get("member_import", ""),))
                    db().execute("INSERT INTO member_imports VALUES (?,?,?)", (token,json.dumps(rows),timestamp()))
                session["member_import"] = token
                return redirect(url_for("member_preview"))
            except (ValueError, csv.Error) as error:
                flash(str(error), "error")
        return render_template("member_upload.html")

    @app.get("/admin/members/preview")
    def member_preview():
        row = db().execute("SELECT * FROM member_imports WHERE token=?", (session.get("member_import", ""),)).fetchone()
        if row is None or datetime.now(timezone.utc)-datetime.fromisoformat(row["created"]) >= timedelta(hours=24):
            return redirect(url_for("member_upload"))
        return render_template("member_preview.html", rows=json.loads(row["payload"]),token=row["token"])

    @app.post("/admin/members/import")
    def member_import():
        token = request.form.get("token", "")
        if not token or token != session.get("member_import"):
            abort(400)
        try:
            with db():
                db().execute("BEGIN IMMEDIATE")
                row = db().execute("SELECT * FROM member_imports WHERE token=?", (token,)).fetchone()
                if row is None or datetime.now(timezone.utc)-datetime.fromisoformat(row["created"]) >= timedelta(hours=24):
                    raise ValueError("Upload preview expired. Upload the CSV again.")
                rows = json.loads(row["payload"])
                check_member_codes(rows)
                db().executemany("INSERT INTO members(name,code,active) VALUES (:name,:code,:active)", rows)
                db().execute("DELETE FROM member_imports WHERE token=?", (token,))
            session.pop("member_import", None)
            flash("Members imported.", "success")
            return redirect(url_for("settings"))
        except ValueError as error:
            flash(str(error), "error")
            return redirect(url_for("member_upload"))

    @app.get("/admin/members/template.csv")
    def member_template():
        return Response("name,code,active\nAlex Taylor,M001,true\n", mimetype="text/csv", headers={"Content-Disposition":"attachment; filename=apos-members-template.csv"})

    @app.post("/logout")
    def logout():
        language = session.get("lang", "de")
        session.clear()
        session["lang"] = language
        return redirect(url_for("login"))

    @app.post("/language")
    def language():
        value = request.form.get("lang", "de")
        if value not in ("de", "en"):
            abort(400)
        session["lang"] = value
        target = request.form.get("next", "/")
        if not target.startswith("/") or target.startswith("//") or "\\" in target or any(ord(c) < 32 for c in target):
            target = "/"
        return redirect(target)

    def text(field):
        value = request.form.get(field, "").strip()
        if not value or len(value) > 120:
            raise ValueError(f"{field.title()} must contain 1–120 characters.")
        return value

    def open_tab(tab_id):
        row = db().execute("SELECT tabs.*, members.name AS member_name, members.code AS member_code, members.photo AS member_photo, members.guest_number AS member_guest_number FROM tabs JOIN members ON members.id=tabs.member_id WHERE tabs.id=? AND closed IS NULL", (tab_id,)).fetchone()
        if row is None:
            abort(404, description="Open tab not found.")
        return row

    def timestamp():
        return datetime.now(timezone.utc).isoformat(timespec="seconds")

    def balance(tab_id):
        row = db().execute("""SELECT
            (SELECT COALESCE(SUM(cents*quantity),0) FROM lines WHERE tab_id=? AND id NOT IN (SELECT line_id FROM cancellations)) AS total,
            (SELECT COALESCE(SUM(total_cents),0) FROM receipts WHERE tab_id=?) AS paid""", (tab_id, tab_id)).fetchone()
        return row["total"], row["paid"], row["total"] - row["paid"]

    @app.after_request
    def private_pages(response):
        response.headers["Cache-Control"] = "no-store"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        return response

    @app.get("/")
    def index():
        tabs = db().execute("""SELECT tabs.id, tabs.currency, members.name, members.code, members.id AS member_id, members.photo, members.guest_number,
          COALESCE(SUM(lines.cents * lines.quantity),0) - (SELECT COALESCE(SUM(total_cents),0) FROM receipts WHERE tab_id=tabs.id) AS total
          FROM tabs JOIN members ON members.id=tabs.member_id
          LEFT JOIN lines ON lines.tab_id=tabs.id AND lines.id NOT IN (SELECT line_id FROM cancellations) WHERE tabs.closed IS NULL
          GROUP BY tabs.id ORDER BY tabs.id DESC""").fetchall()
        return render_template("index.html", tabs=tabs, currency=setting("currency"),
            members=db().execute("SELECT * FROM members WHERE active=1 AND is_guest=0 ORDER BY name").fetchall(),
            guests=db().execute("SELECT * FROM members WHERE active=1 AND is_guest=1 ORDER BY id DESC").fetchall(),
            products=db().execute("SELECT * FROM products ORDER BY active DESC, name").fetchall())

    @app.post("/guests")
    def add_guest():
        adjectives, animals = (("Dancing", "Wobbly", "Cheeky", "Bouncy", "Sleepy", "Sparkly"),
                               ("Otter", "Penguin", "Badger", "Llama", "Wombat", "Duck"))
        if session.get("lang", "de") == "de":
            adjectives, animals = (("Tanzender", "Wackeliger", "Frecher", "Hüpfender", "Schläfriger", "Glitzernder"),
                                   ("Otter", "Pinguin", "Dachs", "Lama", "Wombat", "Erpel"))
        name = secrets.choice(adjectives) + " " + secrets.choice(animals)
        with db():
            db().execute("BEGIN IMMEDIATE")
            currency = setting("currency")
            # A dedicated monotonic counter avoids reuse even if profiles are later erased.
            db().execute("INSERT OR IGNORE INTO settings VALUES ('guest_number','0')")
            while True:
                number = int(setting("guest_number")) + 1
                db().execute("UPDATE settings SET value=? WHERE key='guest_number'", (str(number),))
                code = f"G{number:06d}"
                if not db().execute("SELECT 1 FROM members WHERE code=?", (code,)).fetchone():
                    break
            member_id = db().execute("INSERT INTO members(name,code,is_guest,guest_number) VALUES (?,?,1,?)", (name,code,number)).lastrowid
            tab_id = db().execute("INSERT INTO tabs(member_id,opened,currency,code) VALUES (?,?,?,?)", (member_id,timestamp(),currency,generate_guest_code())).lastrowid
        return redirect(url_for("tab_details",tab_id=tab_id))

    @app.post("/members")
    def add_member():
        try:
            with db():
                db().execute("INSERT INTO members(name,code,photo) VALUES (?,?,?)", (text("name"), text("code"), read_photo(request.files)))
            flash("Member added.", "success")
        except sqlite3.IntegrityError:
            flash("That member code already exists.", "error")
        except ValueError as error:
            flash(str(error), "error")
        return redirect(url_for("settings"))

    @app.route("/members/<int:member_id>/edit", methods=["GET", "POST"])
    def edit_member(member_id):
        member = db().execute("SELECT * FROM members WHERE id=? AND active=1", (member_id,)).fetchone()
        if member is None:
            abort(404)
        if request.method == "POST":
            try:
                name, code = text("name"), text("code")
                photo = read_photo(request.files)
                if request.form.get("remove_photo") == "1":
                    if photo is not None:
                        raise ValueError("Choose a new photo or remove the photo, not both.")
                    photo = None
                elif photo is None:
                    photo = member["photo"]
                with db():
                    db().execute("UPDATE members SET name=?,code=?,photo=? WHERE id=?", (name,code,photo,member_id))
                flash("Member updated.", "success")
                return redirect(url_for("settings"))
            except sqlite3.IntegrityError:
                flash("That member code already exists.", "error")
            except ValueError as error:
                flash(str(error), "error")
        return render_template("edit_member.html", member=member)

    @app.route("/members/<int:member_id>/remove", methods=["GET", "POST"])
    def remove_member(member_id):
        member = db().execute("SELECT * FROM members WHERE id=? AND active=1", (member_id,)).fetchone()
        if member is None:
            abort(404)
        if request.method == "POST":
            with db():
                db().execute("BEGIN IMMEDIATE")
                if db().execute("SELECT 1 FROM accounts WHERE member_id=? AND active=1", (member_id,)).fetchone():
                    flash("Disable linked accounts before removing this profile.", "error")
                    return redirect(url_for("settings"))
                if db().execute("SELECT 1 FROM tabs WHERE member_id=? AND closed IS NULL", (member_id,)).fetchone():
                    flash("Settle or cancel the open tab before removing this member.", "error")
                    return redirect(url_for("settings"))
                db().execute("UPDATE members SET active=0,photo=NULL WHERE id=?", (member_id,))
            flash("Member removed. Historical receipts are retained.", "success")
            return redirect(url_for("settings"))
        return render_template("remove_member.html", member=member)

    @app.get("/members/<int:member_id>/photo")
    def member_photo(member_id):
        member = db().execute("SELECT photo FROM members WHERE id=? AND active=1", (member_id,)).fetchone()
        if member is None or member["photo"] is None:
            abort(404)
        return Response(member["photo"], mimetype="image/jpeg")

    @app.post("/products")
    def add_product():
        try:
            with db():
                db().execute("INSERT INTO products(name,cents,usd_cents) VALUES (?,?,?)", (text("name"), price_cents(request.form.get("price")), price_cents(request.form.get("usd_price"))))
            flash("Product added.", "success")
        except ValueError as error:
            flash(str(error), "error")
        return redirect(url_for("settings"))

    @app.post("/products/<int:product_id>/toggle")
    def toggle_product(product_id):
        with db():
            result = db().execute("UPDATE products SET active=1-active WHERE id=?", (product_id,))
            if not result.rowcount:
                abort(404)
        return redirect(url_for("settings"))

    @app.post("/products/<int:product_id>/stock")
    def product_stock(product_id):
        value = request.form.get("in_stock")
        if value not in ("0", "1"):
            abort(400)
        with db():
            result = db().execute("UPDATE products SET in_stock=? WHERE id=?", (int(value),product_id))
            if not result.rowcount:
                abort(404)
        return redirect(url_for("settings"))

    def check_import_names(rows):
        existing = {row["name"].casefold() for row in db().execute("SELECT name FROM products")}
        if any(row["name"].casefold() in existing for row in rows):
            raise ValueError("A product name already exists. Rename it in the CSV or edit the existing product.")

    @app.route("/catalog/upload", methods=["GET", "POST"])
    @app.route("/admin/catalog/upload", methods=["GET", "POST"])
    def catalog_upload():
        if request.method == "POST":
            try:
                upload = request.files.get("catalog")
                if upload is None:
                    raise ValueError("Choose a CSV file.")
                with upload.stream as stream:
                    rows = parse_catalog(stream.read(MAX_CSV_BYTES + 1), price_cents)
                clear_missing = request.form.get("clear_missing") == "1"
                snapshot = [dict(product) for product in db().execute("SELECT * FROM products ORDER BY id")]
                by_name = {product["name"].casefold(): product for product in snapshot}
                if clear_missing:
                    if len(by_name) != len(snapshot):
                        raise ValueError("Existing product names are ambiguous. Rename duplicates before synchronizing.")
                else:
                    check_import_names(rows)
                for row in rows:
                    row["action"] = "Update" if row["name"].casefold() in by_name else "Add"
                included = {row["name"].casefold() for row in rows}
                omitted = [product for product in snapshot if product["name"].casefold() not in included and product["in_stock"]] if clear_missing else []
                plan = {"rows": rows, "clear_missing": clear_missing, "snapshot": snapshot, "omitted": omitted}
                token = secrets.token_urlsafe(32)
                with db():
                    db().execute("DELETE FROM catalog_imports WHERE created<?", ((datetime.now(timezone.utc)-timedelta(hours=24)).isoformat(timespec="seconds"),))
                    if session.get("catalog_import"):
                        db().execute("DELETE FROM catalog_imports WHERE token=?", (session["catalog_import"],))
                    db().execute("INSERT INTO catalog_imports VALUES (?,?,?)", (token,json.dumps(plan),timestamp()))
                session["catalog_import"] = token
                return redirect(url_for("catalog_preview"))
            except (ValueError, csv.Error) as error:
                flash(str(error), "error")
        return render_template("catalog_upload.html")

    @app.get("/catalog/preview")
    @app.get("/admin/catalog/preview")
    def catalog_preview():
        row = db().execute("SELECT * FROM catalog_imports WHERE token=?", (session.get("catalog_import", ""),)).fetchone()
        if row is None:
            return redirect(url_for("catalog_upload"))
        plan = json.loads(row["payload"])
        return render_template("catalog_preview.html", rows=plan["rows"], omitted=plan["omitted"], clear_missing=plan["clear_missing"], token=row["token"])

    @app.post("/catalog/import")
    @app.post("/admin/catalog/import")
    def catalog_import():
        token = request.form.get("token", "")
        if not token or token != session.get("catalog_import"):
            abort(400)
        try:
            with db():
                db().execute("BEGIN IMMEDIATE")
                staged = db().execute("SELECT * FROM catalog_imports WHERE token=?", (token,)).fetchone()
                if staged is None or datetime.now(timezone.utc)-datetime.fromisoformat(staged["created"]) >= timedelta(hours=24):
                    raise ValueError("Upload preview expired. Upload the CSV again.")
                plan = json.loads(staged["payload"])
                rows = plan["rows"]
                if plan["clear_missing"]:
                    current = [dict(product) for product in db().execute("SELECT * FROM products ORDER BY id")]
                    if current != plan["snapshot"]:
                        raise ValueError("Catalog changed after preview. Upload again to review the current changes.")
                    by_name = {product["name"].casefold(): product for product in current}
                    for row in rows:
                        existing = by_name.get(row["name"].casefold())
                        if existing:
                            db().execute("UPDATE products SET name=?,cents=?,usd_cents=?,in_stock=?,active=? WHERE id=?", (row["name"],row["cents"],row["usd_cents"],row["in_stock"],row["active"],existing["id"]))
                        else:
                            db().execute("INSERT INTO products(name,cents,usd_cents,in_stock,active) VALUES (:name,:cents,:usd_cents,:in_stock,:active)", row)
                    db().executemany("UPDATE products SET in_stock=0 WHERE id=?", [(product["id"],) for product in plan["omitted"]])
                else:
                    check_import_names(rows)
                    db().executemany("INSERT INTO products(name,cents,usd_cents,in_stock,active) VALUES (:name,:cents,:usd_cents,:in_stock,:active)", rows)
                db().execute("DELETE FROM catalog_imports WHERE token=?", (token,))
            session.pop("catalog_import", None)
            flash("Catalog imported.", "success")
            return redirect(url_for("settings"))
        except ValueError as error:
            flash(str(error), "error")
            return redirect(url_for("catalog_upload"))

    @app.get("/catalog/template.csv")
    @app.get("/admin/catalog/template.csv")
    def catalog_template():
        return Response("name,price_eur,price_usd,in_stock,active\nCoffee,2.50,3.00,true,true\nTea,2.00,2.50,false,true\n", mimetype="text/csv", headers={"Content-Disposition":"attachment; filename=apos-catalog-template.csv"})

    @app.post("/tabs")
    def create_tab():
        try:
            member_id = int(request.form.get("member_id", ""))
        except ValueError:
            abort(400, description="Select a member.")
        if not db().execute("SELECT id FROM members WHERE id=? AND active=1", (member_id,)).fetchone():
            abort(404, description="Member not found.")
        opened = timestamp()
        expires = None
        with db():
            db().execute("BEGIN IMMEDIATE")
            currency = setting("currency")
            db().execute("INSERT OR IGNORE INTO tabs(member_id,opened,currency,code,expires) VALUES (?,?,?,?,?)", (member_id, opened, currency, generate_guest_code(), expires))
            row = db().execute("SELECT id FROM tabs WHERE member_id=? AND closed IS NULL", (member_id,)).fetchone()
        return redirect(url_for("tab_details", tab_id=row["id"]))

    @app.get("/tabs/<int:tab_id>")
    def tab_details(tab_id):
        tab = open_tab(tab_id)
        lines = db().execute("SELECT * FROM lines WHERE tab_id=? AND id NOT IN (SELECT line_id FROM cancellations) ORDER BY id", (tab_id,)).fetchall()
        total, paid, due = balance(tab_id)
        base_url = setting("patron_base_url")
        patron_url = (base_url + url_for("patron", code=tab["code"])
                      if base_url else url_for("patron", code=tab["code"], _external=True))
        qr_svg = io.BytesIO()
        segno.make_qr(patron_url, error="m").save(qr_svg, kind="svg", scale=6, border=4)
        qr_data = "data:image/svg+xml;base64," + base64.b64encode(qr_svg.getvalue()).decode("ascii")
        return render_template("tab_details.html", tab=tab, lines=lines,
            patron_url=patron_url, patron_qr=qr_data,
            cancellations=db().execute("SELECT lines.*, cancellations.cancelled,cancellations.reason FROM cancellations JOIN lines ON lines.id=cancellations.line_id WHERE tab_id=? ORDER BY cancelled", (tab_id,)).fetchall(),
            payment_token=secrets.token_urlsafe(24), total=total, paid=paid, due=due,
            payments=db().execute("SELECT * FROM receipts WHERE tab_id=? ORDER BY id", (tab_id,)).fetchall(),
            products=db().execute("SELECT * FROM products WHERE active=1 AND in_stock=1 ORDER BY name").fetchall())

    def insert_menu_item(tab):
        try:
            quantity = int(request.form.get("quantity", "1"))
        except ValueError:
            raise ValueError("Quantity must be a whole number.") from None
        if not 1 <= quantity <= 999:
            raise ValueError("Quantity must be between 1 and 999.")
        product = db().execute("SELECT * FROM products WHERE id=? AND active=1 AND in_stock=1", (request.form.get("product_id", ""),)).fetchone()
        if product is None:
            raise ValueError("Select an active, in-stock product.")
        if request.endpoint == "patron_add_item" and product["alcohol"]:
            raise ValueError("Alcohol must be ordered through staff for an age check.")
        cents = product["cents"] if tab["currency"] == "EUR" else product["usd_cents"]
        db().execute("INSERT INTO lines(tab_id,name,cents,quantity,ordered,product_id) VALUES (?,?,?,?,?,?)", (tab["id"],product["name"],cents,quantity,timestamp(),product["id"]))

    @app.post("/tabs/<int:tab_id>/items")
    def add_item(tab_id):
        try:
            with db():
                db().execute("BEGIN IMMEDIATE")
                insert_menu_item(open_tab(tab_id))
            flash("Item added.", "success")
        except ValueError as error:
            flash(str(error), "error")
        return redirect(url_for("tab_details", tab_id=tab_id))

    @app.post("/tabs/<int:tab_id>/items/<int:line_id>/remove")
    def remove_item(tab_id, line_id):
        with db():
            db().execute("BEGIN IMMEDIATE")
            open_tab(tab_id)
            if balance(tab_id)[1]:
                flash("Items cannot be removed after a payment. New orders can still be added.", "error")
                return redirect(url_for("tab_details", tab_id=tab_id))
            reason = request.form.get("reason", "").strip()
            if not reason or len(reason) > 500:
                abort(400, description="Enter a cancellation reason (1–500 characters).")
            line = db().execute("SELECT id FROM lines WHERE id=? AND tab_id=? AND id NOT IN (SELECT line_id FROM cancellations)", (line_id,tab_id)).fetchone()
            if line is None:
                abort(404, description="Item not found on this tab.")
            db().execute("INSERT INTO cancellations VALUES (?,?,?,?)", (line_id,timestamp(),reason,g.user["username"]))
        return redirect(url_for("tab_details", tab_id=tab_id))

    @app.post("/tabs/<int:tab_id>/checkout")
    def checkout(tab_id):
        method = request.form.get("method", "")
        if method not in ("cash", "card"):
            abort(400, description="Choose cash or card.")
        with db():
            db().execute("BEGIN IMMEDIATE")
            payment_token = request.form.get("payment_token", "")
            if not payment_token or len(payment_token) > 128:
                abort(400, description="Reload the tab before recording payment.")
            existing = db().execute("SELECT id,tab_id FROM receipts WHERE payment_token=?", (payment_token,)).fetchone()
            if existing:
                if existing["tab_id"] != tab_id:
                    abort(400)
                return redirect(url_for("receipt", receipt_id=existing["id"]))
            open_tab(tab_id)
            total, already_paid, due = balance(tab_id)
            if due == 0:
                flash("Add items before checking out.", "error")
                return redirect(url_for("tab_details", tab_id=tab_id))
            try:
                amount = price_cents(request.form.get("amount"), maximum=Decimal(10) ** 15)
            except ValueError as error:
                flash(str(error), "error")
                return redirect(url_for("tab_details", tab_id=tab_id))
            if amount > due:
                flash("Payment exceeds the outstanding balance.", "error")
                return redirect(url_for("tab_details", tab_id=tab_id))
            paid = timestamp()
            cursor = db().execute("INSERT INTO receipts(tab_id,paid,method,total_cents,payment_token,paid_after,due_after) VALUES (?,?,?,?,?,?,?)", (tab_id, paid, method, amount, payment_token, already_paid + amount, due - amount))
            db().execute("INSERT INTO receipt_lines(receipt_id,name,cents,quantity,ordered) SELECT ?,name,cents,quantity,ordered FROM lines WHERE tab_id=? AND id NOT IN (SELECT line_id FROM cancellations) ORDER BY id", (cursor.lastrowid, tab_id))
            if amount == due:
                expires = (datetime.fromisoformat(paid) + timedelta(hours=24)).isoformat(timespec="seconds")
                db().execute("UPDATE tabs SET closed=?,expires=COALESCE(expires,?) WHERE id=?", (paid, expires, tab_id))
        return redirect(url_for("receipt", receipt_id=cursor.lastrowid))

    @app.post("/tabs/<int:tab_id>/cancel")
    def cancel_tab(tab_id):
        with db():
            db().execute("BEGIN IMMEDIATE")
            open_tab(tab_id)
            if db().execute("SELECT 1 FROM lines WHERE tab_id=? AND id NOT IN (SELECT line_id FROM cancellations)", (tab_id,)).fetchone():
                flash("Only empty tabs can be cancelled. Remove items first.", "error")
                return redirect(url_for("tab_details", tab_id=tab_id))
            db().execute("UPDATE tabs SET closed=?,expires=? WHERE id=?", (timestamp(), timestamp(), tab_id))
        return redirect(url_for("index"))

    @app.get("/receipts")
    def receipts():
        rows = db().execute("""SELECT receipts.*,members.name,tabs.currency FROM receipts JOIN tabs ON tabs.id=receipts.tab_id
            JOIN members ON members.id=tabs.member_id ORDER BY receipts.id DESC""").fetchall()
        return render_template("receipts.html", receipts=rows, totals={currency: sum(r["total_cents"] for r in rows if r["currency"] == currency) for currency in ("EUR", "USD")})

    @app.get("/receipts/<int:receipt_id>")
    def receipt(receipt_id):
        row = db().execute("""SELECT receipts.*, members.name, members.code, tabs.currency, tabs.closed FROM receipts
          JOIN tabs ON tabs.id=receipts.tab_id JOIN members ON members.id=tabs.member_id WHERE receipts.id=?""", (receipt_id,)).fetchone()
        if row is None:
            abort(404, description="Receipt not found.")
        return render_template("receipt.html", receipt=row, total=row["paid_after"] + row["due_after"], paid=row["paid_after"], due=row["due_after"],
            lines=db().execute("SELECT * FROM receipt_lines WHERE receipt_id=? ORDER BY rowid", (receipt_id,)).fetchall())

    @app.route("/view", methods=["GET", "POST"])
    def patron_lookup():
        if request.method == "POST":
            code = request.form.get("code", "").strip()
            if not code or len(code) > 64:
                abort(404, description="This tab link is unavailable or has expired.")
            existing = db().execute("SELECT code FROM tabs WHERE code=?", (code,)).fetchone()
            return redirect(url_for("patron", code=existing["code"] if existing else normalize_guest_code(code)))
        return render_template("patron_lookup.html")

    def valid_guest_tab(code):
        row = db().execute("SELECT * FROM tabs WHERE code=?", (code,)).fetchone()
        if row is None:
            row = db().execute("SELECT * FROM tabs WHERE code=?", (normalize_guest_code(code),)).fetchone()
        if row is None or row["guest_email_state"] == "sent" or (row["expires"] and datetime.now(timezone.utc) >= datetime.fromisoformat(row["expires"])):
            abort(404, description="This tab link is unavailable or has expired.")
        return row

    @app.get("/view/<code>")
    def patron(code):
        row = valid_guest_tab(code)
        member = db().execute("SELECT name,photo,active FROM members WHERE id=?", (row["member_id"],)).fetchone()
        total, paid, due = balance(row["id"])
        return render_template("patron.html", tab=row, guest_initials=initials(member["name"]), guest_has_photo=bool(member["photo"]), can_upload_photo=bool(member["active"]), mail_enabled=mail_ready(json.loads(setting("smtp_config"))),
            lines=db().execute("SELECT * FROM lines WHERE tab_id=? AND id NOT IN (SELECT line_id FROM cancellations) ORDER BY id", (row["id"],)).fetchall(),
            guest_ordering=setting("guest_ordering") == "1" and row["closed"] is None and row["guest_email_state"] != "sending",
            products=db().execute("SELECT * FROM products WHERE active=1 AND in_stock=1 AND alcohol=0 ORDER BY name").fetchall(),
            total=total, paid=paid, due=due)

    @app.post("/view/<code>/items")
    def patron_add_item(code):
        tab = valid_guest_tab(code)
        try:
            with db():
                db().execute("BEGIN IMMEDIATE")
                tab = valid_guest_tab(code)
                if setting("guest_ordering") != "1":
                    abort(404)
                if tab["closed"] is not None:
                    raise ValueError("This bon is settled and cannot receive new orders.")
                if tab["guest_email_state"] == "sending":
                    raise ValueError("An email is already being sent. Please wait.")
                insert_menu_item(tab)
            flash("Item added.", "success")
        except ValueError as error:
            flash(str(error), "error")
        return redirect(url_for("patron",code=tab["code"]))

    @app.route("/view/<code>/photo", methods=["GET", "POST"])
    def patron_photo(code):
        tab = valid_guest_tab(code)
        if request.method == "POST":
            try:
                photo = read_photo(request.files)
                if request.form.get("remove_photo") == "1":
                    if photo is not None:
                        raise ValueError("Choose a new photo or remove the photo, not both.")
                elif photo is None:
                    raise ValueError("Choose one photo: upload or camera.")
                with db():
                    db().execute("BEGIN IMMEDIATE")
                    tab = valid_guest_tab(code)
                    result = db().execute("UPDATE members SET photo=? WHERE id=? AND active=1", (photo,tab["member_id"]))
                    if not result.rowcount:
                        abort(404)
                flash("Profile photo updated.", "success")
            except ValueError as error:
                flash(str(error), "error")
            return redirect(url_for("patron", code=tab["code"]))
        member = db().execute("SELECT photo FROM members WHERE id=? AND active=1", (tab["member_id"],)).fetchone()
        if member is None or member["photo"] is None:
            abort(404)
        return Response(member["photo"], mimetype="image/jpeg")

    @app.post("/view/<code>/email")
    def patron_email(code):
        tab = valid_guest_tab(code)
        config = json.loads(setting("smtp_config"))
        if not mail_ready(config):
            abort(404)
        try:
            recipient = email_address(request.form.get("email", ""))
        except ValueError as error:
            flash(str(error), "error")
            return redirect(url_for("patron", code=tab["code"]))
        with db():
            db().execute("BEGIN IMMEDIATE")
            tab = valid_guest_tab(code)
            if tab["guest_email_state"] == "sending":
                flash("An email is already being sent. Please wait.", "error")
                return redirect(url_for("patron", code=tab["code"]))
            lines = db().execute("SELECT * FROM lines WHERE tab_id=? AND id NOT IN (SELECT line_id FROM cancellations) ORDER BY id", (tab["id"],)).fetchall()
            total, paid, due = balance(tab["id"])
            html = render_template("emailed_bon.html", lines=lines,tab=tab,total=total,paid=paid,due=due)
            from translations import translate
            t = lambda value: translate(value,session.get("lang","de"))
            text = t("Your bon") + "\n\n" + "\n".join(f"{line['quantity']} × {line['name']} · {money(line['cents'],tab['currency'])} · {money(line['cents']*line['quantity'],tab['currency'])} · {line['ordered']} UTC" for line in lines)
            text += f"\n\n{t('Total ordered')}: {money(total,tab['currency'])}\n{t('Paid so far')}: {money(paid,tab['currency'])}\n{t('Outstanding balance')}: {money(due,tab['currency'])}"
            db().execute("UPDATE tabs SET guest_email_state='sending' WHERE id=?", (tab["id"],))
        try:
            send_bon(config,app.config["SECRET_KEY"],recipient,t("Your bon") + " · APOS",text,html)
        except (smtplib.SMTPException,OSError,InvalidToken):
            with db():
                db().execute("UPDATE tabs SET guest_email_state=NULL WHERE id=? AND guest_email_state='sending'",(tab["id"],))
            flash("Email could not be sent. Your guest link remains available. Please try again or ask staff.","error")
            return redirect(url_for("patron",code=tab["code"]))
        with db():
            db().execute("UPDATE tabs SET guest_email_state='sent',expires=? WHERE id=?", (timestamp(),tab["id"]))
        return redirect(url_for("patron_email_sent"))

    @app.get("/bon-sent")
    def patron_email_sent():
        return render_template("email_sent.html")

    def report_data():
        start = request.args.get("start", datetime.now(timezone.utc).strftime("%Y-%m-%d"))
        end = request.args.get("end", start)
        try:
            first = datetime.strptime(start, "%Y-%m-%d").replace(tzinfo=timezone.utc)
            last = datetime.strptime(end, "%Y-%m-%d").replace(tzinfo=timezone.utc) + timedelta(days=1)
        except (ValueError, OverflowError):
            abort(400, description="Use valid report dates.")
        if last <= first:
            abort(400, description="End date must be on or after start date.")
        args = (first.isoformat(timespec="seconds"), last.isoformat(timespec="seconds"))
        sales = db().execute("""SELECT lines.name, tabs.currency, lines.cents, SUM(quantity) AS quantity,
            SUM(lines.cents*quantity) AS total FROM lines JOIN tabs ON tabs.id=lines.tab_id
            WHERE lines.ordered>=? AND lines.ordered<? AND lines.id NOT IN (SELECT line_id FROM cancellations) GROUP BY lines.name,tabs.currency,lines.cents
            ORDER BY tabs.currency, lines.name""", args).fetchall()
        payments = db().execute("""SELECT tabs.currency, receipts.method, SUM(total_cents) AS total
            FROM receipts JOIN tabs ON tabs.id=receipts.tab_id WHERE paid>=? AND paid<?
            GROUP BY tabs.currency, receipts.method ORDER BY tabs.currency,receipts.method""", args).fetchall()
        return start, end, sales, payments

    @app.get("/reports")
    def reports():
        start, end, sales, payments = report_data()
        return render_template("reports.html", start=start, end=end, sales=sales, payments=payments)

    @app.get("/reports.csv")
    def report_csv():
        start, end, sales, payments = report_data()
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["type", "product", "currency", "unit_cents", "quantity", "payment_method", "total_cents"])
        for row in sales:
            # Spreadsheet formula characters in operator-entered names are escaped.
            name = row["name"]
            if name.lstrip().startswith(("=", "+", "-", "@")) or name.startswith(("\t", "\r", "\n")):
                name = "'" + name
            writer.writerow(["sale", name, row["currency"], row["cents"], row["quantity"], "", row["total"]])
        for row in payments:
            writer.writerow(["payment", "", row["currency"], "", "", row["method"], row["total"]])
        return Response(output.getvalue(), mimetype="text/csv", headers={"Content-Disposition": f"attachment; filename=apos-report-{start}-{end}.csv"})

    @app.errorhandler(400)
    @app.errorhandler(403)
    @app.errorhandler(404)
    @app.errorhandler(413)
    def error_page(error):
        return render_template("error.html", error=error), error.code

    return app


if __name__ == "__main__":
    create_app().run(host="127.0.0.1", port=5000)
