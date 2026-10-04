import csv
import io
import re
import sqlite3
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from pathlib import Path

from app import create_app, price_cents, DICEWARE_WORDS


class POSTest(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.database = str(Path(self.directory.name) / "test.sqlite3")
        self.config = {"TESTING": True, "DATABASE": self.database, "SECRET_KEY": "test-key", "STAFF_PASSWORD": "test-password"}
        self.app = create_app(self.config)
        self.client = self.app.test_client()
        self.sign_in(self.client)
        with self.client.session_transaction() as session:
            session["lang"] = "en"
            self.csrf = session["csrf"]

    def tearDown(self):
        self.directory.cleanup()

    def sign_in(self, client):
        client.get("/login")
        with client.session_transaction() as session:
            token = session["csrf"]
        response = client.post("/login", data={"csrf": token, "password": "test-password"})
        self.assertEqual(response.status_code, 302)
        client.get("/")

    def post(self, path, **data):
        return self.client.post(path, data={"csrf": self.csrf, **data})

    def rows(self, query, args=()):
        with sqlite3.connect(self.database) as connection:
            return connection.execute(query, args).fetchall()

    def execute(self, query, args=()):
        with sqlite3.connect(self.database) as connection:
            connection.execute(query, args)

    def open_tab(self, currency="EUR"):
        self.post("/admin", currency=currency)
        self.post("/members", name="Alice PRIVATE", code="M001")
        self.post("/products", name="Tea", price="2.50", usd_price="3.75")
        response = self.post("/tabs", member_id="1", currency=currency)
        self.assertEqual(response.status_code, 302)
        return response.headers["Location"]

    def token(self, tab):
        page = self.client.get(tab).get_data(as_text=True)
        return re.search(r'name="payment_token" value="([^"]+)"', page).group(1)

    def pay(self, tab, amount, method="cash", token=None):
        return self.post(tab + "/checkout", amount=amount, method=method, payment_token=token or self.token(tab))

    def test_partial_payment_new_orders_full_settlement_restart_and_repeat(self):
        tab = self.open_tab()
        self.post(tab + "/items", product_id="1", quantity="2")
        token = self.token(tab)
        response = self.pay(tab, "2.00", token=token)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.rows("SELECT closed,expires FROM tabs"), [(None, None)])
        self.assertEqual(self.pay(tab, "2.00", token=token).headers["Location"], response.headers["Location"])
        self.assertEqual(len(self.rows("SELECT * FROM receipts")), 1)
        self.post(tab + "/items", product_id="1", quantity="1")
        self.assertIn("€5.50", self.client.get(tab).get_data(as_text=True))
        self.assertEqual(self.post("/tabs", member_id="1", currency="USD").headers["Location"], tab)
        self.assertEqual(self.rows("SELECT currency FROM tabs"), [("EUR",)])
        self.post(tab + "/items/1/remove")
        self.assertEqual(len(self.rows("SELECT * FROM lines")), 2)
        final = self.pay(tab, "5.50", method="card")
        self.assertEqual(self.rows("SELECT total_cents,method FROM receipts ORDER BY id"), [(200, "cash"), (550, "card")])
        closed, expiry = self.rows("SELECT closed,expires FROM tabs")[0]
        self.assertEqual(datetime.fromisoformat(expiry)-datetime.fromisoformat(closed), timedelta(hours=24))
        restarted = create_app(self.config).test_client()
        self.sign_in(restarted)
        self.assertEqual(restarted.get(final.headers["Location"]).status_code, 200)
        self.assertEqual(restarted.get(tab).status_code, 404)
        self.assertEqual(self.post(tab + "/items", product_id="1", quantity="1").status_code, 404)
        self.assertEqual(self.post(tab + "/items/1/remove").status_code, 404)
        self.assertNotEqual(self.post("/tabs", member_id="1").headers["Location"], tab)

    def test_partial_receipt_remains_unchanged_after_new_orders_and_settlement(self):
        tab = self.open_tab()
        self.post(tab + "/items", product_id="1", quantity="1")
        response = self.pay(tab, "1.00")
        receipt = response.headers["Location"]
        snapshot = self.client.get(receipt).get_data(as_text=True)
        self.post(tab + "/items", product_id="1", quantity="2")
        self.pay(tab, "6.50")
        self.assertEqual(snapshot, self.client.get(receipt).get_data(as_text=True))
        self.assertEqual(self.rows("SELECT quantity FROM receipt_lines WHERE receipt_id=1"), [(1,)])

    def test_usd_menu_prices_and_price_snapshots(self):
        tab = self.open_tab("USD")
        self.post(tab + "/items", product_id="1", quantity="2", price="0.01", name="Forged price")
        self.assertEqual(self.rows("SELECT name,cents,quantity FROM lines"), [("Tea", 375, 2)])
        self.execute("UPDATE products SET cents=900,usd_cents=950,name='New name'")
        self.assertIn("$7.50", self.client.get(tab).get_data(as_text=True))
        self.pay(tab, "7.50")
        self.assertEqual(self.rows("SELECT total_cents FROM receipts"), [(750,)])

    def test_patron_code_read_only_no_identity_and_expiry(self):
        tab = self.open_tab()
        self.post(tab + "/items", product_id="1", quantity="1")
        code = self.rows("SELECT code FROM tabs")[0][0]
        patron = self.app.test_client()
        page = patron.get("/view/" + code)
        self.assertEqual(page.status_code, 200)
        self.assertNotIn("Alice PRIVATE", page.get_data(as_text=True))
        self.assertIn("Tea", page.get_data(as_text=True))
        self.assertIn(self.rows("SELECT ordered FROM lines")[0][0], page.get_data(as_text=True))
        for path in ("/", tab, "/reports", "/reports.csv", "/receipts"):
            self.assertEqual(patron.get(path).headers["Location"], "/login")
        with patron.session_transaction() as session:
            token = session["csrf"]
        self.assertEqual(patron.post(tab + "/items", data={"csrf": token,"product_id":"1","quantity":"9"}).headers["Location"], "/login")
        self.assertEqual(len(self.rows("SELECT * FROM lines")), 1)
        self.assertEqual(patron.get("/view/not-a-real-code").status_code, 404)
        self.pay(tab, "1.00")
        self.assertEqual(patron.get("/view/" + code).status_code, 200)
        self.pay(tab, "1.50")
        self.assertEqual(patron.get("/view/" + code).status_code, 200)
        self.execute("UPDATE tabs SET expires=?", ((datetime.now(timezone.utc)-timedelta(seconds=1)).isoformat(),))
        self.assertEqual(patron.get("/view/" + code).status_code, 404)
        self.assertEqual(self.client.get("/receipts/2").status_code, 200)
        self.assertEqual(page.headers["Cache-Control"], "no-store")
        self.assertEqual(page.headers["Referrer-Policy"], "no-referrer")

    def test_invalid_prices_menu_quantities_and_overpayment(self):
        tab = self.open_tab()
        for value in ("", "abc", "nan", "inf", "-1", "0", "1.001", "1000000"):
            self.post("/products", name="Invalid", price=value, usd_price="1")
        self.assertEqual(len(self.rows("SELECT * FROM products")), 1)
        for quantity in ("0", "-1", "1000", "abc", "1.5"):
            self.post(tab + "/items", product_id="1", quantity=quantity)
        self.post(tab + "/items", name="Custom", price="1", quantity="1")
        self.post(tab + "/items", product_id="999", quantity="1")
        self.assertEqual(self.rows("SELECT * FROM lines"), [])
        self.post(tab + "/items", product_id="1", quantity="1")
        for value in ("0", "-1", "nan", "abc", "1.001", "2.51"):
            self.pay(tab, value)
        self.assertEqual(self.rows("SELECT * FROM receipts"), [])
        self.assertEqual(self.pay(tab, "1", method="other").status_code, 400)

    def test_anonymous_reports_separate_orders_payments_and_currencies(self):
        tab = self.open_tab()
        self.post(tab + "/items", product_id="1", quantity="2")
        self.pay(tab, "1.00")
        self.post("/members", name="Bob PRIVATE", code="M002")
        self.post("/admin", currency="USD")
        usd = self.post("/tabs", member_id="2", currency="USD").headers["Location"]
        self.post(usd + "/items", product_id="1", quantity="1")
        self.pay(usd, "3.75", method="card")
        day = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        page = self.client.get("/reports?start="+day+"&end="+day)
        self.assertEqual(page.status_code, 200)
        exported = self.client.get("/reports.csv?start="+day+"&end="+day)
        text = exported.get_data(as_text=True)
        self.assertNotIn("PRIVATE", text)
        self.assertNotIn("M001", text)
        for code, in self.rows("SELECT code FROM tabs"):
            self.assertNotIn(code, text)
        rows = list(csv.DictReader(io.StringIO(text)))
        self.assertEqual([(r["currency"],r["total_cents"]) for r in rows if r["type"] == "sale"], [("EUR","500"),("USD","375")])
        self.assertEqual([(r["currency"],r["total_cents"]) for r in rows if r["type"] == "payment"], [("EUR","100"),("USD","375")])
        self.assertEqual(self.client.get("/reports?start=bad").status_code, 400)
        self.assertEqual(self.client.get("/reports?start=2026-02-02&end=2026-01-01").status_code, 400)
        self.assertNotIn("Tea", self.client.get("/reports.csv?start=2000-01-01&end=2000-01-01").get_data(as_text=True))

    def test_reports_escape_spreadsheet_formulas(self):
        tab = self.open_tab()
        self.post("/products", name="=1+1", price="1", usd_price="1")
        self.post(tab + "/items", product_id="2", quantity="1")
        self.assertIn("'=1+1", self.client.get("/reports.csv").get_data(as_text=True))

    def test_german_english_and_language_redirect_validation(self):
        self.post("/language", lang="de", next="/")
        page = self.client.get("/").get_data(as_text=True)
        self.assertIn("Offene Bons", page)
        self.assertIn('lang="de"', page)
        self.post("/language", lang="en", next="/")
        self.assertIn("Open tabs", self.client.get("/").get_data(as_text=True))
        self.assertEqual(self.post("/language", lang="xx").status_code, 400)
        for target in ("https://example.com", "//example.com", "/\\example.com"):
            self.assertEqual(self.post("/language", lang="en", next=target).headers["Location"], "/")

    def test_csrf_login_logout_and_html_escaping(self):
        self.assertEqual(self.client.post("/members", data={"name":"X","code":"X"}).status_code, 400)
        self.post("/members", name="<script>alert(1)</script>", code="X")
        self.post("/members", name="Duplicate", code="X")
        self.assertEqual(len(self.rows("SELECT * FROM members")), 1)
        page = self.client.get("/").get_data(as_text=True)
        self.assertIn("&lt;script&gt;", page)
        self.assertNotIn("<script>alert(1)</script>", page)
        self.post("/logout")
        self.assertEqual(self.client.get("/").headers["Location"], "/login")
        self.client.get("/login")
        with self.client.session_transaction() as session:
            token = session["csrf"]
        response = self.client.post("/login", data={"csrf":token,"password":"wrong"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.client.get("/").headers["Location"], "/login")

    def test_remove_cancel_and_inactive_products(self):
        tab = self.open_tab()
        self.post(tab + "/items", product_id="1", quantity="1")
        self.post(tab + "/cancel")
        self.assertEqual(self.client.get(tab).status_code, 200)
        self.post("/products/1/toggle")
        self.post(tab + "/items", product_id="1", quantity="1")
        self.assertEqual(len(self.rows("SELECT * FROM lines")), 1)
        self.assertEqual(self.post(tab + "/items/1/remove").status_code, 400)
        self.post(tab + "/items/1/remove", reason="Wrong order")
        self.assertEqual(len(self.rows("SELECT * FROM lines")), 1)
        self.assertEqual(self.rows("SELECT reason,actor FROM cancellations"), [("Wrong order", "admin")])
        self.assertNotIn("Wrong order", self.client.get("/reports.csv").get_data(as_text=True))
        code = self.rows("SELECT code FROM tabs")[0][0]
        self.post(tab + "/cancel")
        self.assertEqual(self.app.test_client().get("/view/"+code).status_code, 404)
        self.assertEqual(self.rows("SELECT * FROM receipts"), [])

    def test_concurrent_payments_do_not_overpay(self):
        tab = self.open_tab()
        self.post(tab + "/items", product_id="1", quantity="1")
        clients = [self.app.test_client(), self.app.test_client()]
        for client in clients:
            self.sign_in(client)
        def attempt(client):
            page = client.get(tab).get_data(as_text=True)
            payment_token = re.search(r'name="payment_token" value="([^"]+)"', page).group(1)
            with client.session_transaction() as session:
                token = session["csrf"]
            return client.post(tab + "/checkout", data={"csrf":token,"payment_token":payment_token,"method":"cash","amount":"2.00"}).status_code
        with ThreadPoolExecutor(max_workers=2) as pool:
            codes = list(pool.map(attempt, clients))
        self.assertEqual(codes, [302,302])
        self.assertEqual(self.rows("SELECT SUM(total_cents) FROM receipts"), [(200,)])

    def test_setup_password_changes_persist_and_invalidate_other_sessions(self):
        second = self.app.test_client()
        self.sign_in(second)
        password = "new-chosen-password"
        response = self.post("/settings", base_url="apos.example.org", current_password="test-password", new_password=password, confirm_password=password)
        self.assertEqual(response.headers["Location"], "/login")
        self.assertEqual(second.get("/").headers["Location"], "/login")
        self.assertEqual(self.rows("SELECT value FROM settings WHERE key='patron_base_url'"), [("https://apos.example.org",)])
        hashed = self.rows("SELECT value FROM settings WHERE key='staff_password_hash'")[0][0]
        self.assertNotIn(password, hashed)
        restarted = create_app(self.config).test_client()
        restarted.get("/login")
        with restarted.session_transaction() as session:
            csrf = session["csrf"]
        restarted.post("/login", data={"csrf":csrf,"password":"test-password"})
        self.assertEqual(restarted.get("/").headers["Location"], "/login")
        restarted.post("/login", data={"csrf":csrf,"password":password})
        self.assertEqual(restarted.get("/").status_code, 200)

    def test_setup_rejects_bad_passwords_and_addresses_without_mutation(self):
        before = self.rows("SELECT * FROM settings ORDER BY key")
        for values in (
            {"base_url":"https://good.example.org","current_password":"wrong","new_password":"long-enough-password","confirm_password":"long-enough-password"},
            {"base_url":"https://good.example.org","current_password":"test-password","new_password":"short","confirm_password":"short"},
            {"base_url":"https://good.example.org","current_password":"test-password","new_password":"long-enough-password","confirm_password":"different-password"},
            {"base_url":"javascript://bad"}, {"base_url":"https://user:secret@example.org"},
            {"base_url":"https://example.org/path"}, {"base_url":"https://example.org:bad"}):
            self.post("/settings", **values)
            self.assertEqual(self.rows("SELECT * FROM settings ORDER BY key"), before)
        guest = self.app.test_client()
        self.assertEqual(guest.get("/settings").headers["Location"], "/login")

    def test_configured_fqdn_updates_guest_links_immediately(self):
        tab = self.open_tab()
        self.post("/settings", base_url="http://192.0.2.10:5000/")
        code = self.rows("SELECT code FROM tabs")[0][0]
        page = self.client.get(tab).get_data(as_text=True)
        self.assertIn("http://192.0.2.10:5000/view/"+code, page)
        self.assertIn("data:image/svg+xml;base64,", page)
        self.post("/settings", base_url="guest.example.org")
        self.assertIn("https://guest.example.org/view/"+code, self.client.get(tab).get_data(as_text=True))

    def test_product_edit_changes_future_orders_and_preserves_history(self):
        tab = self.open_tab()
        self.post(tab+"/items",product_id="1",quantity="1")
        self.pay(tab,"1.00")
        snapshot = self.client.get("/receipts/1").get_data(as_text=True)
        self.assertEqual(self.client.get("/products/1/edit").status_code, 200)
        self.post("/products/1/edit",name="Coffee",price="4.00",usd_price="5.00")
        self.post(tab+"/items",product_id="1",quantity="1")
        self.assertEqual(self.rows("SELECT name,cents FROM lines ORDER BY id"),[("Tea",250),("Coffee",400)])
        self.client.get(tab)  # Consume operation notices before comparing the receipt snapshot.
        self.assertEqual(snapshot,self.client.get("/receipts/1").get_data(as_text=True))
        self.post("/products/1/edit",name=" ",price="4.00",usd_price="5.00")
        self.assertEqual(self.rows("SELECT name FROM products"),[("Coffee",)])
        self.assertEqual(self.client.get("/products/999/edit").status_code,404)
        self.assertEqual(self.app.test_client().get("/products/1/edit").headers["Location"],"/login")

    def test_human_readable_codes_accept_lowercase_spaces_and_legacy_links(self):
        tab = self.open_tab()
        code = self.rows("SELECT code FROM tabs")[0][0]
        self.assertEqual(len(DICEWARE_WORDS), 7776)
        self.assertEqual(len(set(DICEWARE_WORDS)), 7776)
        self.assertEqual(len(code.split("-")), 4)
        self.assertTrue(all(word in DICEWARE_WORDS for word in code.split("-")))
        self.assertEqual(self.app.test_client().get("/view/"+code.lower()).status_code,200)
        patron = self.app.test_client()
        patron.get("/view")
        with patron.session_transaction() as session:
            csrf = session["csrf"]
        response = patron.post("/view",data={"csrf":csrf,"code":code.upper().replace("-"," ")})
        self.assertEqual(response.headers["Location"],"/view/"+code)
        previous = "R7KM-P4TN-V8CX-H3AW-6BQS"
        self.execute("UPDATE tabs SET code=?", (previous,))
        self.assertEqual(patron.get("/view/"+previous.lower()).status_code,200)
        legacy = "old_CaseSensitive-GuestCode12345678"
        self.execute("UPDATE tabs SET code=?",(legacy,))
        self.assertEqual(patron.get("/view/"+legacy).status_code,200)
        self.assertEqual(patron.post("/view",data={"csrf":csrf,"code":legacy}).headers["Location"],"/view/"+legacy)

    def upload_catalog(self, contents, **options):
        response = self.post("/catalog/upload", catalog=(io.BytesIO(contents), "catalog.csv"), **options)
        response.request.environ["wsgi.input"].close()
        return response

    def import_token(self):
        with self.client.session_transaction() as session:
            return session["catalog_import"]

    def test_csv_preview_atomic_import_stock_flags_and_repeat(self):
        response = self.upload_catalog(b"name,price_eur,price_usd,in_stock,active\nCoffee,2.50,3.00,true,true\nTea,1.20,1.50,false,true\n")
        self.assertEqual(response.headers["Location"],"/admin/catalog/preview")
        self.assertEqual(self.rows("SELECT * FROM products"),[])
        self.assertEqual(self.client.get("/catalog/preview").status_code,200)
        token = self.import_token()
        self.post("/catalog/import",token=token)
        self.assertEqual(self.rows("SELECT name,cents,usd_cents,in_stock,active FROM products ORDER BY id"),[("Coffee",250,300,1,1),("Tea",120,150,0,1)])
        self.assertEqual(self.post("/catalog/import",token=token).status_code,400)
        self.assertEqual(len(self.rows("SELECT * FROM products")),2)
        self.assertEqual(self.rows("SELECT * FROM catalog_imports"),[])

    def test_csv_invalid_rows_leave_catalog_unchanged(self):
        self.open_tab()
        before = self.rows("SELECT * FROM products")
        for content in (
            b"", b"wrong,headers\na,b\n", b"name,price_eur,price_usd\nValid,1,2\nInvalid,nan,2\n",
            b"name,price_eur,price_usd\nTea,1,2\n", b"name,price_eur,price_usd\nSame,1,2\nsame,1,2\n",
            b"name,price_eur,price_usd,in_stock\nInvalid,1,2,maybe\n", b"name,price_eur,price_usd\nBad,1\n",
            b"name,price_eur,price_usd\nBad,1,2,extra\n", b"\xff", b"x" * (512 * 1024 + 1),
            b"name,price_eur,price_usd\n" + b"".join(f"P{i},1,2\n".encode() for i in range(501))):
            with self.subTest(content=content[:50]):
                self.assertEqual(self.upload_catalog(content).status_code,200)
                self.assertEqual(self.rows("SELECT * FROM products"),before)

    def test_csv_utf8_bom_semicolon_decimal_comma_and_conflict_recheck(self):
        content = "name;price_eur;price_usd\nKäsekuchen;2,50;3,75\n".encode("utf-8-sig")
        self.upload_catalog(content)
        token = self.import_token()
        self.post("/products",name="Käsekuchen",price="1",usd_price="2")
        self.post("/catalog/import",token=token)
        self.assertEqual(self.rows("SELECT name,cents FROM products"),[("Käsekuchen",100)])
        self.execute("DELETE FROM products")
        self.upload_catalog(content)
        self.post("/catalog/import",token=self.import_token())
        self.assertEqual(self.rows("SELECT name,cents,usd_cents,in_stock,active FROM products"),[("Käsekuchen",250,375,1,1)])

    def test_out_of_stock_prevents_stale_orders_and_preserves_history(self):
        tab = self.open_tab()
        self.post(tab+"/items",product_id="1",quantity="1")
        self.pay(tab,"1.00")
        snapshot = self.client.get("/receipts/1").get_data(as_text=True)
        self.post("/products/1/stock",in_stock="0")
        self.post(tab+"/items",product_id="1",quantity="3")
        self.assertEqual(self.rows("SELECT quantity FROM lines"),[(1,)])
        page = self.client.get(tab).get_data(as_text=True)
        self.assertNotIn('option value="1"',page)
        self.assertEqual(snapshot,self.client.get("/receipts/1").get_data(as_text=True))
        self.post("/products/1/stock",in_stock="1")
        self.post(tab+"/items",product_id="1",quantity="2")
        self.assertEqual(self.rows("SELECT quantity FROM lines ORDER BY id"),[(1,),(2,)])
        self.assertEqual(self.post("/products/1/stock",in_stock="bad").status_code,400)
        self.assertEqual(self.post("/products/999/stock",in_stock="0").status_code,404)
        self.assertEqual(self.client.get("/catalog/template.csv").status_code,200)
        guest = self.app.test_client()
        for path in ("/catalog/upload","/catalog/preview","/catalog/template.csv"):
            self.assertEqual(guest.get(path).headers["Location"],"/login")
        self.assertEqual(self.client.post("/catalog/import",data={"token":"anything"}).status_code,400)

    def test_csv_sync_updates_listed_marks_missing_and_preserves_orders(self):
        tab = self.open_tab()
        self.post("/products",name="Omitted",price="1",usd_price="2")
        self.post(tab+"/items",product_id="2",quantity="1")
        self.upload_catalog(b"name,price_eur,price_usd\ntea,4.00,5.00\nNew,1.50,2.00\n",clear_missing="1")
        token = self.import_token()
        preview = self.client.get("/catalog/preview").get_data(as_text=True)
        self.assertIn("Omitted",preview)
        self.assertIn("Products to mark out of stock",preview)
        self.assertEqual(self.rows("SELECT in_stock FROM products WHERE id=2"),[(1,)])
        self.post("/catalog/import",token=token)
        self.assertEqual(self.rows("SELECT name,cents,in_stock FROM products ORDER BY id"),[("tea",400,1),("Omitted",100,0),("New",150,1)])
        self.assertEqual(self.rows("SELECT name,cents FROM lines"),[("Omitted",100)])
        self.post(tab+"/items",product_id="2",quantity="1")
        self.assertEqual(len(self.rows("SELECT * FROM lines")),1)

    def test_csv_sync_refuses_stale_preview_and_invalid_file_without_stock_changes(self):
        self.open_tab()
        self.upload_catalog(b"name,price_eur,price_usd\nNew,1,2\n",clear_missing="1")
        token = self.import_token()
        self.post("/products",name="Added later",price="1",usd_price="2")
        before = self.rows("SELECT * FROM products ORDER BY id")
        self.post("/catalog/import",token=token)
        self.assertEqual(self.rows("SELECT * FROM products ORDER BY id"),before)
        self.upload_catalog(b"name,price_eur,price_usd\nBad,nan,2\n",clear_missing="1")
        self.assertEqual(self.rows("SELECT * FROM products ORDER BY id"),before)

    def photo_bytes(self):
        from PIL import Image
        result = io.BytesIO()
        Image.new("RGB",(640,480),(30,140,80)).save(result,format="PNG")
        return result.getvalue()

    def test_member_edit_initials_remove_and_photo(self):
        self.post("/members",name="Alex Robin Taylor",code="S001")
        page = self.client.get("/admin").get_data(as_text=True)
        self.assertIn("ART",page)
        for name, expected in (("Alex","A"),("Alex Taylor","AT")):
            self.post("/members/1/edit",name=name,code="S001")
            self.assertIn(expected,self.client.get("/admin").get_data(as_text=True))
        self.post("/members/1/edit",name="Alex",code="S001",photo=(io.BytesIO(self.photo_bytes()),"avatar.png"))
        image = self.client.get("/members/1/photo")
        self.assertEqual(image.status_code,200)
        from PIL import Image
        with Image.open(io.BytesIO(image.data)) as avatar:
            self.assertEqual(avatar.size,(256,256))
            self.assertEqual(avatar.format,"JPEG")
        self.assertEqual(self.app.test_client().get("/members/1/photo").headers["Location"],"/login")
        self.post("/members/1/edit",name="Alex",code="S001",remove_photo="1")
        self.assertEqual(self.client.get("/members/1/photo").status_code,404)
        tab = self.post("/tabs",member_id="1").headers["Location"]
        self.post("/members/1/remove")
        self.assertEqual(self.rows("SELECT active FROM members"),[(1,)])
        self.post(tab+"/cancel")
        self.post("/members/1/remove")
        self.assertEqual(self.rows("SELECT active FROM members"),[(0,)])
        self.assertEqual(self.post("/tabs",member_id="1").status_code,404)
        self.assertEqual(self.client.get("/members/1/edit").status_code,404)

    def test_invalid_member_photo_and_duplicate_code_are_atomic(self):
        self.post("/members",name="A",code="A")
        self.post("/members",name="B",code="B")
        self.post("/members/1/edit",name="Changed",code="B")
        self.assertEqual(self.rows("SELECT name,code FROM members WHERE id=1"),[("A","A")])
        self.post("/members/1/edit",name="Changed",code="A",photo=(io.BytesIO(b"not an image"),"image.png"))
        self.assertEqual(self.rows("SELECT name,photo FROM members WHERE id=1"),[("A",None)])
        self.assertEqual(self.client.post("/members/1/remove").status_code,400)

    def test_guest_can_upload_camera_photo_only_for_own_member_until_expiry(self):
        tab = self.open_tab()
        self.post("/members",name="Other",code="OTHER")
        code = self.rows("SELECT code FROM tabs")[0][0]
        guest = self.app.test_client()
        guest.get("/view/"+code)
        with guest.session_transaction() as session:
            csrf = session["csrf"]
        path = "/view/"+code+"/photo"
        self.assertEqual(guest.post(path,data={"csrf":csrf,"member_id":"2","camera":(io.BytesIO(self.photo_bytes()),"capture.jpg")}).status_code,302)
        self.assertIsNotNone(self.rows("SELECT photo FROM members WHERE id=1")[0][0])
        self.assertIsNone(self.rows("SELECT photo FROM members WHERE id=2")[0][0])
        self.assertEqual(guest.get(path).status_code,200)
        self.assertEqual(guest.post(path,data={"photo":(io.BytesIO(self.photo_bytes()),"image.png")}).status_code,400)
        self.execute("UPDATE tabs SET expires=?",((datetime.now(timezone.utc)-timedelta(seconds=1)).isoformat(),))
        self.assertEqual(guest.get(path).status_code,404)
        self.assertEqual(guest.post(path,data={"csrf":csrf,"photo":(io.BytesIO(self.photo_bytes()),"image.png")}).status_code,404)

    def enable_mail(self, **overrides):
        values = {"host":"smtp.example.org","port":"587","security":"starttls","sender":"apos@example.org","username":"","password":"","enabled":"1"}
        values.update(overrides)
        return self.post("/settings/mail",**values)

    def guest_client(self, code):
        guest = self.app.test_client()
        guest.get("/view/"+code)
        with guest.session_transaction() as session:
            csrf = session["csrf"]
        return guest, csrf

    def test_guest_mail_hidden_until_configured_enabled_and_success_revokes_all_access(self):
        from unittest.mock import patch
        tab = self.open_tab()
        self.post(tab+"/items",product_id="1",quantity="2")
        code = self.rows("SELECT code FROM tabs")[0][0]
        guest, csrf = self.guest_client(code)
        self.assertNotIn('name="email"',guest.get("/view/"+code).get_data(as_text=True))
        self.assertEqual(guest.post("/view/"+code+"/email",data={"csrf":csrf,"email":"guest@example.org"}).status_code,404)
        self.enable_mail()
        with patch("app.send_bon") as send:
            self.assertNotIn('name="email"',guest.get("/view/"+code).get_data(as_text=True))
            self.assertEqual(guest.post("/view/"+code+"/email",data={"csrf":csrf,"email":"guest@example.org"}).status_code,404)
            self.pay(tab,"2.00")
            self.assertNotIn('name="email"',guest.get("/view/"+code).get_data(as_text=True))
            self.assertEqual(guest.post("/view/"+code+"/email",data={"csrf":csrf,"email":"guest@example.org"}).status_code,404)
            send.assert_not_called()
        self.assertEqual(self.rows("SELECT guest_email_state FROM tabs"),[(None,)])
        self.pay(tab,"3.00")
        self.assertIn('name="email"',guest.get("/view/"+code).get_data(as_text=True))
        with patch("app.send_bon") as send:
            response = guest.post("/view/"+code+"/email",data={"csrf":csrf,"email":"guest@example.org"})
            self.assertEqual(response.headers["Location"],"/bon-sent")
            self.assertEqual(guest.get(response.headers["Location"]).status_code,200)
            send.assert_called_once()
            args = send.call_args.args
            self.assertEqual(args[2],"guest@example.org")
            self.assertIn("Tea",args[4])
            self.assertIn("Tea",args[5])
            self.assertNotIn("Alice PRIVATE",args[5])
        self.assertEqual(guest.get("/view/"+code).status_code,404)
        self.assertEqual(guest.get("/view/"+code+"/photo").status_code,404)
        self.assertEqual(self.client.get("/receipts/1").status_code,200)
        self.assertEqual(len(self.rows("SELECT * FROM receipts")),2)
        self.assertEqual(len(self.rows("SELECT * FROM lines")),1)
        self.assertEqual(self.rows("SELECT guest_email_state FROM tabs"),[("sent",)])
        self.assertEqual(guest.post("/view/"+code+"/email",data={"csrf":csrf,"email":"guest@example.org"}).status_code,404)

    def test_failed_mail_invalid_email_and_disabled_account_do_not_revoke_link(self):
        import smtplib
        from unittest.mock import patch
        tab = self.open_tab()
        self.post(tab+"/items",product_id="1",quantity="1")
        self.pay(tab,"2.50")
        code = self.rows("SELECT code FROM tabs")[0][0]
        guest, csrf = self.guest_client(code)
        self.enable_mail()
        with patch("app.send_bon",side_effect=smtplib.SMTPException("test failure")) as send:
            guest.post("/view/"+code+"/email",data={"csrf":csrf,"email":"bad\r\nBcc:other@example.org"})
            send.assert_not_called()
            guest.post("/view/"+code+"/email",data={"csrf":csrf,"email":"guest@example.org"})
            send.assert_called_once()
        self.assertEqual(guest.get("/view/"+code).status_code,200)
        self.assertEqual(self.rows("SELECT guest_email_state FROM tabs"),[(None,)])
        self.enable_mail(enabled="0")
        self.assertNotIn('name="email"',guest.get("/view/"+code).get_data(as_text=True))
        self.assertEqual(guest.post("/view/"+code+"/email",data={"csrf":csrf,"email":"guest@example.org"}).status_code,404)

    def test_mail_configuration_is_validated_encrypted_and_staff_only(self):
        import json
        from mail_delivery import cipher
        before = self.rows("SELECT value FROM settings WHERE key='smtp_config'")
        self.enable_mail(host="",sender="")
        self.assertEqual(self.rows("SELECT value FROM settings WHERE key='smtp_config'"),before)
        self.enable_mail(username="smtp-user",password="mail-password")
        config = json.loads(self.rows("SELECT value FROM settings WHERE key='smtp_config'")[0][0])
        self.assertNotIn("mail-password",config["password"])
        self.assertEqual(cipher("test-key").decrypt(config["password"].encode()).decode(),"mail-password")
        self.assertNotIn(config["password"],self.client.get("/settings/mail").get_data(as_text=True))
        self.enable_mail(username="smtp-user",password="")
        self.assertEqual(json.loads(self.rows("SELECT value FROM settings WHERE key='smtp_config'")[0][0])["password"],config["password"])
        self.assertEqual(self.app.test_client().get("/settings/mail").headers["Location"],"/login")

    def test_compliance_cancellation_preserves_history_and_excludes_sale(self):
        tab = self.open_tab()
        self.post(tab + "/items", product_id="1", quantity="2")
        self.post(tab + "/items/1/remove", reason="Duplicate order")
        self.assertEqual(self.post(tab + "/items/1/remove", reason="Again").status_code, 404)
        code = self.rows("SELECT code FROM tabs")[0][0]
        guest, csrf = self.guest_client(code)
        self.assertNotIn("Tea", guest.get("/view/"+code).get_data(as_text=True))
        self.assertNotIn("Tea", self.client.get("/reports.csv").get_data(as_text=True))
        self.assertIn("Duplicate order", self.client.get(tab).get_data(as_text=True))
        self.post(tab + "/items", product_id="1", quantity="1")
        self.pay(tab, "2.50")
        self.assertEqual(self.rows("SELECT quantity FROM receipt_lines"), [(1,)])
        self.assertEqual(len(self.rows("SELECT * FROM lines")), 2)

    def test_alcohol_is_blocked_for_guests_but_available_to_staff(self):
        tab = self.open_tab()
        self.post("/products/1/edit", name="Beer", price="2.50", usd_price="3.75", alcohol="1")
        self.post("/settings", base_url="", guest_ordering="1")
        code = self.rows("SELECT code FROM tabs")[0][0]
        guest, csrf = self.guest_client(code)
        self.assertNotIn("Beer", guest.get("/view/"+code).get_data(as_text=True))
        guest.post("/view/"+code+"/items", data={"csrf":csrf,"product_id":"1","quantity":"1"})
        self.assertEqual(self.rows("SELECT * FROM lines"), [])
        self.post(tab + "/items", product_id="1", quantity="1")
        self.assertEqual(len(self.rows("SELECT * FROM lines")), 1)

    def test_public_notices_escape_markup_and_guest_can_remove_photo(self):
        self.open_tab()
        self.post("/settings", base_url="", legal_notice="Association <script>alert(1)</script>", privacy_notice="Privacy contact")
        public = self.app.test_client()
        page = public.get("/legal/legal_notice")
        self.assertEqual(page.status_code, 200)
        self.assertIn("&lt;script&gt;", page.get_data(as_text=True))
        self.assertEqual(public.get("/legal/unknown").status_code, 404)
        self.execute("UPDATE members SET photo=?", (b"photo",))
        code = self.rows("SELECT code FROM tabs")[0][0]
        guest, csrf = self.guest_client(code)
        guest.post("/view/"+code+"/photo", data={"csrf":csrf,"remove_photo":"1"})
        self.assertEqual(self.rows("SELECT photo FROM members"), [(None,)])

    def test_guest_ordering_is_optional_scoped_and_uses_catalog_prices(self):
        self.open_tab("USD")
        code = self.rows("SELECT code FROM tabs")[0][0]
        guest, csrf = self.guest_client(code)
        path = "/view/"+code+"/items"
        self.assertNotIn(path,guest.get("/view/"+code).get_data(as_text=True))
        self.assertEqual(guest.post(path,data={"csrf":csrf,"product_id":"1","quantity":"1"}).status_code,404)
        self.post("/settings",base_url="",guest_ordering="1")
        self.assertIn(path,guest.get("/view/"+code).get_data(as_text=True))
        self.post("/members",name="Other",code="OTHER")
        self.post("/tabs",member_id="2")
        self.assertEqual(guest.post(path,data={"csrf":csrf,"product_id":"1","quantity":"2","tab_id":"2","member_id":"2","price":"0.01","name":"Forged"}).status_code,302)
        self.assertEqual(self.rows("SELECT tab_id,name,cents,quantity FROM lines"),[(1,"Tea",375,2)])
        self.assertEqual(guest.post("/tabs/1/items/1/remove",data={"csrf":csrf}).headers["Location"],"/login")
        self.assertEqual(guest.post("/view/"+code+"/items/1/remove",data={"csrf":csrf}).status_code,404)
        self.post("/settings",base_url="")
        self.assertEqual(guest.post(path,data={"csrf":csrf,"product_id":"1","quantity":"1"}).status_code,404)
        self.assertEqual(len(self.rows("SELECT * FROM lines")),1)

    def test_guest_orders_validate_stock_csrf_closed_and_expired_links(self):
        tab = self.open_tab()
        code = self.rows("SELECT code FROM tabs")[0][0]
        guest, csrf = self.guest_client(code)
        path = "/view/"+code+"/items"
        self.post("/settings",base_url="",guest_ordering="1")
        self.assertEqual(guest.post(path,data={"product_id":"1","quantity":"1"}).status_code,400)
        for quantity in ("0","1000","abc"):
            guest.post(path,data={"csrf":csrf,"product_id":"1","quantity":quantity})
        self.post("/products/1/stock",in_stock="0")
        guest.post(path,data={"csrf":csrf,"product_id":"1","quantity":"1"})
        self.assertEqual(self.rows("SELECT * FROM lines"),[])
        self.post("/products/1/stock",in_stock="1")
        guest.post(path,data={"csrf":csrf,"product_id":"1","quantity":"1"})
        self.pay(tab,"2.50")
        guest.post(path,data={"csrf":csrf,"product_id":"1","quantity":"1"})
        self.assertEqual(len(self.rows("SELECT * FROM lines")),1)
        self.assertNotIn(path,guest.get("/view/"+code).get_data(as_text=True))
        self.execute("UPDATE tabs SET expires=?",((datetime.now(timezone.utc)-timedelta(seconds=1)).isoformat(),))
        self.assertEqual(guest.post(path,data={"csrf":csrf,"product_id":"1","quantity":"1"}).status_code,404)

    def test_all_pages_render_both_languages(self):
        tab = self.open_tab()
        self.post(tab + "/items", product_id="1", quantity="1")
        code = self.rows("SELECT code FROM tabs")[0][0]
        self.pay(tab, "1.00")
        for lang in ("de","en"):
            self.post("/language", lang=lang, next="/")
            for path in ("/",tab,"/receipts","/receipts/1","/reports","/view","/view/"+code,"/login","/members/1/edit","/members/1/remove","/settings/mail"):
                with self.subTest(lang=lang,path=path):
                    self.assertEqual(self.client.get(path).status_code, 200)


    def test_notice_translations_fallback_and_rich_text_safety(self):
        endpoint = "/settings/notices/legal_notice"
        self.assertEqual(self.app.test_client().post(endpoint).status_code, 400)
        self.assertEqual(self.app.test_client().get(endpoint).headers["Location"], "/login")
        self.assertEqual(self.client.post(endpoint, data={"content":"bad"}).status_code, 400)
        self.post(endpoint, notice_language="en", content='<h2 onclick="bad()">English legal</h2><img src=x onerror="bad()"><script>alert(1)</script>')
        public = self.app.test_client()
        html = public.get("/legal/legal_notice").get_data(as_text=True)
        self.assertIn("<h2>English legal</h2>", html)
        notice_html = re.search(r'<section class="panel notice-text">(.*?)</section>', html, re.S).group(1)
        for unsafe in ('onclick=', '<img', '<script>'):
            self.assertNotIn(unsafe, notice_html)
        editor_page = self.client.get(endpoint).get_data(as_text=True)
        self.assertIn("English legal", editor_page)
        self.assertIn("<h2>Legal notice — example</h2>", editor_page)
        self.assertIn('contenteditable="true"', editor_page)
        self.post(endpoint, notice_language="de", content="<p>Deutscher Text</p>")
        self.assertIn("Deutscher Text", public.get("/legal/legal_notice").get_data(as_text=True))
        with public.session_transaction() as session:
            session["lang"] = "en"
        self.assertIn("English legal", public.get("/legal/legal_notice").get_data(as_text=True))
        self.post(endpoint, notice_language="de", content="<p><br></p>")
        with public.session_transaction() as session:
            session["lang"] = "de"
        self.assertIn("English legal", public.get("/legal/legal_notice").get_data(as_text=True))
        self.assertEqual(self.post(endpoint, notice_language="fr", content="Invalid").status_code, 400)
        self.assertEqual(self.post(endpoint, notice_language="en", content="x" * 20001).status_code, 400)
        self.post("/settings", base_url="")
        self.assertIn("<h2>English legal</h2>", public.get("/legal/legal_notice").get_data(as_text=True))

    def test_non_member_guests_have_unique_numbers_and_normal_tab_lifecycle(self):
        self.assertEqual(self.client.post("/guests").status_code, 400)
        self.assertEqual(self.app.test_client().get("/").headers["Location"], "/login")
        self.assertEqual(self.post("/admin", currency="GBP").status_code, 200)
        self.post("/admin", currency="USD")
        self.post("/members", name="Existing", code="G000001")
        first = self.post("/guests", currency="USD").headers["Location"]
        self.post("/admin", currency="EUR")
        second = self.post("/guests", currency="EUR").headers["Location"]
        self.assertNotEqual(first, second)
        guests = self.rows("SELECT name,code,guest_number FROM members WHERE is_guest=1 ORDER BY id")
        self.assertEqual([row[2] for row in guests], [2,3])
        self.assertTrue(all(len(row[0].split()) == 2 for row in guests))
        self.assertEqual(self.rows("SELECT currency FROM tabs ORDER BY id"), [("USD",),("EUR",)])
        self.assertEqual(self.rows("SELECT COUNT(DISTINCT code) FROM tabs"), [(2,)])
        self.post("/members/2/edit", name="Custom Guest", code="CUSTOM")
        self.assertEqual(self.rows("SELECT guest_number FROM members WHERE id=2"), [(2,)])
        self.post("/products", name="Tea", price="2.50", usd_price="3.75")
        self.post(first + "/items", product_id="1", quantity="1")
        self.pay(first,"3.75")
        code = self.rows("SELECT code FROM tabs WHERE id=1")[0][0]
        self.assertEqual(self.app.test_client().get("/view/"+code).status_code,200)
        self.assertNotIn("Custom Guest", self.client.get("/reports.csv").get_data(as_text=True))

    def account_client(self, username, password="long-test-password"):
        client = self.app.test_client()
        client.get("/login")
        with client.session_transaction() as state:
            csrf = state["csrf"]
        response = client.post("/login", data={"csrf":csrf,"username":username,"password":password})
        self.assertEqual(response.status_code,302)
        client.get("/login")
        with client.session_transaction() as state:
            csrf = state["csrf"]
        return client, csrf

    def create_account(self, username, role, member_id=""):
        response = self.post("/admin/accounts", username=username, role=role, member_id=member_id,
                             password="long-test-password", active="1")
        self.assertEqual(response.status_code,302)
        return self.rows("SELECT id FROM accounts WHERE username=?", (username,))[0][0]

    def test_roles_enforce_admin_and_staff_boundaries_on_direct_requests(self):
        tab = self.open_tab()
        self.post("/guests",currency="EUR")
        self.create_account("operator", "Staff")
        self.create_account("member-login", "Member", "1")
        self.create_account("guest-login", "Guest", "2")
        self.assertEqual(self.client.get("/admin/accounts").status_code,200)
        self.assertEqual(self.client.get("/admin/accounts/1").status_code,200)
        self.assertIn("Product catalog",self.client.get("/admin").get_data(as_text=True))
        home=self.client.get("/").get_data(as_text=True)
        self.assertNotIn("Product catalog",home)
        self.assertNotIn('action="/members"',home)
        admin_gets=("/admin/mail","/admin/notices/legal_notice","/admin/catalog/upload","/admin/catalog/preview","/admin/catalog/template.csv","/admin","/settings","/settings/mail","/settings/notices/legal_notice","/admin/accounts","/admin/accounts/1","/catalog/upload","/catalog/preview","/catalog/template.csv","/admin/members/upload","/admin/members/preview","/admin/members/template.csv","/members/1/edit","/members/1/remove","/products/1/edit")
        admin_posts=("/admin/mail","/admin/notices/legal_notice","/admin/catalog/upload","/admin/catalog/import","/admin","/settings","/settings/mail","/settings/notices/legal_notice","/admin/accounts","/admin/accounts/1","/members","/members/1/edit","/members/1/remove","/products","/products/1/edit","/products/1/toggle","/products/1/stock","/catalog/upload","/catalog/import","/admin/members/upload","/admin/members/import")
        for username in ("operator","member-login","guest-login"):
            client,csrf=self.account_client(username)
            for path in admin_gets:
                self.assertEqual(client.get(path).status_code,403,(username,path))
            for path in admin_posts:
                self.assertEqual(client.post(path,data={"csrf":csrf}).status_code,403,(username,path))
            if username != "operator":
                for path in ("/",tab,"/receipts","/reports","/reports.csv","/members/3/photo"):
                    self.assertEqual(client.get(path).status_code,403,(username,path))
                self.assertEqual(client.post("/guests",data={"csrf":csrf}).status_code,403)
            else:
                self.assertEqual(client.get("/").status_code,200)
                self.assertEqual(client.post(tab+"/items",data={"csrf":csrf,"product_id":"1","quantity":"1"}).status_code,302)
                self.assertEqual(self.rows("SELECT name FROM lines"),[("Tea",)])
            self.assertEqual(client.get("/legal/legal_notice").status_code,200)

    def test_member_and_guest_accounts_only_resolve_their_own_tab(self):
        tab=self.open_tab()
        other=self.post("/guests",currency="EUR").headers["Location"]
        self.create_account("member-own","Member","1")
        self.create_account("guest-own","Guest","2")
        for username,member_id in (("member-own",1),("guest-own",2)):
            client,csrf=self.account_client(username)
            code=self.rows("SELECT code FROM tabs WHERE member_id=?",(member_id,))[0][0]
            self.assertEqual(client.get("/my-tab?member_id=999").headers["Location"],"/view/"+code)
            self.assertEqual(client.get("/my-tab",follow_redirects=True).status_code,200)
            self.assertEqual(client.get("/members/"+str(3-member_id)+"/photo").status_code,403)
            self.assertEqual(client.post("/logout",data={"csrf":csrf}).status_code,302)
            self.assertEqual(client.get("/my-tab").headers["Location"],"/login")
        self.execute("UPDATE tabs SET guest_email_state='sent' WHERE member_id=1")
        client,csrf=self.account_client("member-own")
        self.assertIn("Kein zugänglicher Bon",client.get("/my-tab").get_data(as_text=True))

    def test_account_role_changes_invalidate_sessions_and_protect_last_admin(self):
        account_id=self.create_account("worker","Staff")
        staff,csrf=self.account_client("worker")
        self.post("/admin/accounts/"+str(account_id),username="worker",role="Staff",active="0")
        self.assertEqual(staff.get("/").headers["Location"],"/login")
        response=self.post("/admin/accounts/1",username="admin",role="Staff",active="1")
        self.assertEqual(response.status_code,200)
        self.assertEqual(self.rows("SELECT role,active FROM accounts WHERE id=1"),[("Admin",1)])
        self.assertIn("Keep at least one",response.get_data(as_text=True))
        self.assertEqual(self.post("/admin/accounts",username="badmember",role="Member",password="long-test-password",active="1").status_code,200)
        self.assertEqual(self.rows("SELECT COUNT(*) FROM accounts"),[(2,)])
        self.create_account("second-admin","Admin")
        self.assertEqual(self.post("/admin/accounts/1",username="admin",role="Staff",active="1").status_code,302)
        self.assertEqual(self.client.get("/admin").headers["Location"],"/login")
        self.assertEqual(self.rows("SELECT COUNT(*) FROM account_events"),[(4,)])

    def test_member_csv_is_previewed_atomic_and_never_grants_accounts(self):
        data="\ufeffname;code;active\nAlex;S001;ja\nAlex;A002;false\n".encode()
        response=self.post("/admin/members/upload",members=(io.BytesIO(data),"members.csv"))
        self.assertEqual(response.headers["Location"],"/admin/members/preview")
        self.assertEqual(self.rows("SELECT * FROM members"),[])
        self.assertIn("Alex",self.client.get("/admin/members/preview").get_data(as_text=True))
        with self.client.session_transaction() as state:
            token=state["member_import"]
        foreign,csrf=self.account_client("admin","test-password")
        self.assertEqual(foreign.post("/admin/members/import",data={"csrf":csrf,"token":token}).status_code,400)
        self.assertEqual(self.post("/admin/members/import",token=token).status_code,302)
        self.assertEqual(self.rows("SELECT name,code,active,is_guest FROM members ORDER BY id"),[("Alex","S001",1,0),("Alex","A002",0,0)])
        self.assertEqual(self.rows("SELECT COUNT(*) FROM accounts"),[(1,)])
        self.assertEqual(self.post("/admin/members/import",token=token).status_code,400)
        for content in ("name,code,role\nBad,BAD,Admin\n", "name,code\nA,A\nB,a\n", "name,code,active\nA,B,maybe\n", "name,code\nA,S001\n", "name,code\nA\n"):
            self.assertEqual(self.post("/admin/members/upload",members=(io.BytesIO(content.encode()),"bad.csv")).status_code,200)
            self.assertEqual(self.rows("SELECT COUNT(*) FROM members"),[(2,)])

    def test_member_csv_conflict_and_expiry_reject_whole_import(self):
        def stage(content):
            self.post("/admin/members/upload",members=(io.BytesIO(content.encode()),"members.csv"))
            with self.client.session_transaction() as state:
                return state["member_import"]
        token=stage("name,code\nFirst,FIRST\nConflict,COLLIDE\n")
        self.post("/members",name="Existing",code="collide")
        self.post("/admin/members/import",token=token)
        self.assertEqual(self.rows("SELECT name FROM members"),[("Existing",)])
        token=stage("name,code\nExpired,EXPIRED\n")
        self.execute("UPDATE member_imports SET created=? WHERE token=?",((datetime.now(timezone.utc)-timedelta(hours=25)).isoformat(),token))
        self.assertEqual(self.client.get("/admin/members/preview").status_code,302)
        self.post("/admin/members/import",token=token)
        self.assertEqual(self.rows("SELECT name FROM members"),[("Existing",)])

    def test_markdown_notices_preserve_source_render_formatting_and_language_fallback(self):
        endpoint="/admin/notices/legal_notice"
        markdown="# Contact\n\n**Association** and *privacy*\n\n- One\n- Two\n\n[Email](mailto:contact@example.org)\n\n| Purpose | Data |\n| --- | --- |\n| Tabs | Orders |\n"
        self.assertEqual(self.post(endpoint,notice_language="en",content_format="markdown",content=markdown).status_code,302)
        self.assertEqual(self.rows("SELECT value FROM settings WHERE key='legal_notice'"),[(markdown,)])
        public=self.app.test_client()
        html=public.get("/legal/legal_notice").get_data(as_text=True)
        for expected in ('<h1>Contact</h1>','<strong>Association</strong>','<em>privacy</em>','<li>One</li>','href="mailto:contact@example.org"','<table>'):
            self.assertIn(expected,html)
        editor=self.client.get(endpoint).get_data(as_text=True)
        self.assertIn('value="markdown"',editor)
        self.assertIn('# Contact',editor)
        self.post(endpoint,notice_language="de",content_format="markdown",content="## Datenschutz\n\n**Deutsch**")
        self.assertIn('<h2>Datenschutz</h2>',public.get("/legal/legal_notice").get_data(as_text=True))
        self.post(endpoint,notice_language="de",content_format="markdown",content=" \n ")
        self.assertIn('<h1>Contact</h1>',public.get("/legal/legal_notice").get_data(as_text=True))
        self.assertEqual(self.post(endpoint,notice_language="en",content_format="invalid",content="Bad").status_code,400)
        self.post(endpoint,notice_language="en",content_format="markdown",content="    code\n")
        self.assertEqual(self.rows("SELECT value FROM settings WHERE key='legal_notice'"),[("    code\n",)])
        self.assertIn('<pre><code>code',public.get("/legal/legal_notice").get_data(as_text=True))

    def test_markdown_preview_blocks_active_content_and_requires_admin(self):
        path="/admin/notices/preview"
        self.assertEqual(self.client.post(path,data={"content":"test"}).status_code,400)
        payload='<script>alert(1)</script>\n\n[x](javascript:alert(1))\n\n![track](https://example.org/image.png)\n\n[Safe](https://example.org/privacy)\n'
        response=self.post(path,content=payload)
        self.assertEqual(response.status_code,200)
        html=response.get_data(as_text=True)
        self.assertNotIn('<script>',html)
        self.assertNotIn('<img',html)
        self.assertNotIn('href="javascript:',html)
        self.assertIn('href="https://example.org/privacy"',html)
        self.assertEqual(self.post(path,content="x"*20001).status_code,400)
        self.create_account("preview-staff","Staff")
        staff,csrf=self.account_client("preview-staff")
        self.assertEqual(staff.post(path,data={"csrf":csrf,"content":"test"}).status_code,403)
        self.post("/admin/notices/privacy_notice",notice_language="en",content_format="html",content='<h2>Keep HTML</h2><a href="javascript:alert(1)" onclick="bad()">Unsafe</a><a href="https://example.org">Safe</a>')
        rendered=self.app.test_client().get("/legal/privacy_notice").get_data(as_text=True)
        self.assertIn('<h2>Keep HTML</h2>',rendered)
        self.assertNotIn('href="javascript:',rendered)
        self.assertNotIn('onclick=',rendered)
        self.assertIn('href="https://example.org"',rendered)

    def test_global_currency_applies_to_all_new_tabs_and_ignores_request_overrides(self):
        self.post("/members",name="Member",code="CURRENCY")
        self.post("/admin",currency="USD")
        member_tab=self.post("/tabs",member_id="1",currency="EUR").headers["Location"]
        guest_tab=self.post("/guests",currency="GBP").headers["Location"]
        self.assertEqual(self.rows("SELECT currency FROM tabs ORDER BY id"),[("USD",),("USD",)])
        self.assertNotIn('name="currency"',self.client.get("/").get_data(as_text=True))
        self.assertIn('name="currency"',self.client.get("/admin").get_data(as_text=True))
        self.create_account("currency-staff","Staff")
        staff,csrf=self.account_client("currency-staff")
        self.assertEqual(staff.post("/admin",data={"csrf":csrf,"currency":"EUR"}).status_code,403)
        staff.post("/guests",data={"csrf":csrf,"currency":"EUR"})
        self.assertEqual(self.rows("SELECT currency FROM tabs ORDER BY id"),[("USD",),("USD",),("USD",)])
        create_app(self.config)
        self.assertEqual(self.rows("SELECT value FROM settings WHERE key='currency'"),[("USD",)])
        self.post("/admin",currency="EUR")
        self.assertEqual(self.post("/tabs",member_id="1").headers["Location"],member_tab)
        self.post("/guests",currency="USD")
        self.assertEqual(self.rows("SELECT currency FROM tabs ORDER BY id"),[("USD",),("USD",),("USD",),("EUR",)])

    def test_global_currency_validation_preserves_settings_and_payment_history(self):
        tab=self.open_tab("USD")
        self.post(tab+"/items",product_id="1",quantity="1")
        self.pay(tab,"3.75")
        self.assertEqual(self.post("/admin",currency="JPY",base_url="https://should-not-save.example").status_code,200)
        self.assertEqual(self.rows("SELECT value FROM settings WHERE key='currency'"),[("USD",)])
        self.assertEqual(self.rows("SELECT value FROM settings WHERE key='patron_base_url'"),[("",)])
        self.post("/admin",currency="EUR")
        receipt=self.client.get("/receipts/1").get_data(as_text=True)
        self.assertIn("$3.75",receipt)
        self.assertEqual(self.rows("SELECT currency FROM tabs"),[("USD",)])
        self.assertEqual(self.rows("SELECT total_cents FROM receipts"),[(375,)])


class MoneyTest(unittest.TestCase):
    def test_exact_cents(self):
        self.assertEqual(price_cents("0.10"), 10)
        self.assertEqual(price_cents("1.20"), 120)
        self.assertEqual(price_cents("999999"), 99999900)


if __name__ == "__main__":
    unittest.main()
