import os
import sqlite3
import subprocess
import tempfile
import unittest
from pathlib import Path
import sys


class OperationsTest(unittest.TestCase):
    def test_first_start_generates_private_persistent_secrets(self):
        from app import create_app
        with tempfile.TemporaryDirectory() as directory:
            from unittest.mock import patch
            import flask
            original = flask.Flask.__init__
            def isolated_init(instance, *args, **kwargs):
                kwargs["instance_path"] = directory
                original(instance, *args, **kwargs)
            with patch.object(flask.Flask, "__init__", isolated_init):
                config = {"DATABASE": str(Path(directory) / "test.sqlite3"), "SECRET_KEY": None, "STAFF_PASSWORD": None}
                first = create_app(config)
                second = create_app(config)
            for name, key in (("secret.key", "SECRET_KEY"), ("staff.key", "STAFF_PASSWORD")):
                self.assertTrue(first.config[key])
                self.assertEqual(first.config[key], second.config[key])
                self.assertEqual((Path(directory) / name).stat().st_mode & 0o777, 0o600)

    def test_interactive_setup_persists_password_and_hostname(self):
        import main
        from unittest.mock import patch
        from werkzeug.security import check_password_hash
        with tempfile.TemporaryDirectory() as directory:
            live = Path(directory) / "setup.sqlite3"
            env = {"APOS_DATABASE":str(live),"APOS_SECRET_KEY":"test-secret","APOS_STAFF_PASSWORD":"bootstrap-password"}
            with patch.dict(os.environ,env), patch.object(sys,"argv",["main.py","setup"]), patch.object(main,"getpass",side_effect=["my-chosen-password","my-chosen-password"]), patch("builtins.input",return_value="apos.example.org"), patch("builtins.print"):
                main.main()
            with sqlite3.connect(live) as db:
                values = dict(db.execute("SELECT key,value FROM settings").fetchall())
            self.assertTrue(check_password_hash(values["staff_password_hash"],"my-chosen-password"))
            self.assertFalse(check_password_hash(values["staff_password_hash"],"bootstrap-password"))
            self.assertEqual(values["patron_base_url"],"https://apos.example.org")

    def test_existing_catalog_is_migrated_without_losing_products(self):
        from app import create_app
        with tempfile.TemporaryDirectory() as directory:
            live = Path(directory) / "legacy.sqlite3"
            with sqlite3.connect(live) as connection:
                connection.execute("CREATE TABLE products(id INTEGER PRIMARY KEY,name TEXT NOT NULL,cents INTEGER NOT NULL,usd_cents INTEGER NOT NULL,active INTEGER NOT NULL DEFAULT 1)")
                connection.execute("INSERT INTO products(name,cents,usd_cents,active) VALUES ('Existing',100,200,0)")
            config = {"DATABASE":str(live),"SECRET_KEY":"test-secret","STAFF_PASSWORD":"test-password"}
            create_app(config)
            create_app(config)
            with sqlite3.connect(live) as connection:
                self.assertEqual(connection.execute("SELECT name,cents,usd_cents,active,in_stock FROM products").fetchall(),[("Existing",100,200,0,1)])

    def test_demo_stock_is_idempotent_and_preserves_existing_products(self):
        from app import create_app
        with tempfile.TemporaryDirectory() as directory:
            live = Path(directory) / "demo.sqlite3"
            config = {"DATABASE":str(live),"SECRET_KEY":"test-secret","STAFF_PASSWORD":"test-password"}
            create_app(config)
            with sqlite3.connect(live) as connection:
                connection.execute("INSERT INTO products(name,cents,usd_cents,in_stock) VALUES ('Demo Coffee',123,234,0)")
            env = {**os.environ,"APOS_DATABASE":str(live),"APOS_SECRET_KEY":"test-secret","APOS_STAFF_PASSWORD":"test-password"}
            for _ in range(2):
                result = subprocess.run([sys.executable,"main.py","demo-stock"],env=env,capture_output=True,text=True)
                self.assertEqual(result.returncode,0,result.stderr)
            with sqlite3.connect(live) as connection:
                self.assertEqual(connection.execute("SELECT COUNT(*) FROM products").fetchone()[0],8)
                self.assertEqual(connection.execute("SELECT cents,usd_cents,in_stock FROM products WHERE name='Demo Coffee'").fetchone(),(123,234,0))
                self.assertEqual(connection.execute("SELECT COUNT(*) FROM products WHERE in_stock=0").fetchone()[0],3)

    def test_backup_retains_records_and_refuses_overwrite(self):
        from app import create_app
        with tempfile.TemporaryDirectory() as directory:
            live = Path(directory) / "live.sqlite3"
            backup = Path(directory) / "backup.sqlite3"
            settings = {"DATABASE":str(live),"SECRET_KEY":"test-secret","STAFF_PASSWORD":"test-password"}
            create_app(settings)
            with sqlite3.connect(live) as db:
                db.execute("INSERT INTO members(name,code) VALUES ('Backup member','B001')")
            env = {**os.environ,"APOS_DATABASE":str(live),"APOS_SECRET_KEY":"test-secret","APOS_STAFF_PASSWORD":"test-password"}
            command = [sys.executable,"main.py","backup","--output",str(backup)]
            result = subprocess.run(command,env=env,capture_output=True,text=True)
            self.assertEqual(result.returncode,0,result.stderr)
            with sqlite3.connect(backup) as db:
                self.assertEqual(db.execute("SELECT name,code FROM members").fetchall(),[("Backup member","B001")])
                self.assertEqual(db.execute("PRAGMA integrity_check").fetchone()[0],"ok")
            self.assertNotEqual(subprocess.run(command,env=env,capture_output=True).returncode,0)
            self.assertNotEqual(subprocess.run([sys.executable,"main.py","backup","--output",str(live)],env=env,capture_output=True).returncode,0)

    def test_server_serves_login_over_http(self):
        import socket
        import time
        import urllib.request
        with tempfile.TemporaryDirectory() as directory:
            env = {**os.environ,"APOS_DATABASE":str(Path(directory)/"http.sqlite3"),"APOS_SECRET_KEY":"test-secret","APOS_STAFF_PASSWORD":"test-password"}
            with socket.socket() as sock:
                sock.bind(("127.0.0.1",0))
                port = sock.getsockname()[1]
            process = subprocess.Popen([sys.executable,"main.py","--port",str(port)],env=env,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)
            try:
                for _ in range(50):
                    if process.poll() is not None:
                        self.fail(process.stderr.read().decode())
                    try:
                        with urllib.request.urlopen(f"http://127.0.0.1:{port}/login",timeout=1) as response:
                            self.assertEqual(response.status,200)
                            self.assertIn("APOS",response.read().decode())
                            self.assertEqual(response.headers["Cache-Control"],"no-store")
                        break
                    except OSError:
                        time.sleep(0.1)
                else:
                    self.fail("Server did not start")
            finally:
                process.terminate()
                process.wait(timeout=5)
                process.stderr.close()
