# APOS administrator guide

[Documentation home](../README.md) · [Deutsch](../de/ADMIN.md) · [Staff guide](STAFF.md) · [Guest guide](GUEST.md)

For operators and **Admin** accounts, based on APOS 0.6. Follow the staff guide for counter operations. This guide covers installation, configuration, accounts, profiles, products and recovery.

## 1. Prepare the installation

APOS requires Python 3.10 or newer; Python 3.12 is tested. Download or clone the project, open a terminal in its directory and run:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python main.py
```

Open `http://127.0.0.1:5000`. Keep the terminal and computer running. Stop with Ctrl+C. Saved data survives restarts. On Windows, use `.venv\Scripts\python.exe` instead of `.venv/bin/python`.

In another terminal in the same directory, retrieve the initial recovery administrator password:

```sh
.venv/bin/python main.py password
```

Sign in as **admin**. On migrated installations, use the previous shared password with that username. Rotate it and create individual Staff accounts before service. `password` cannot display a custom password.

To choose/reset the recovery password and guest address locally:

```sh
.venv/bin/python main.py setup
```

Enter a password of 12–256 characters twice and the guest-facing origin. The command restores the fixed `admin` account's Admin role and active status and invalidates existing sessions. Restrict access to the server terminal.

## 2. General settings and networking

Open **Admin → General settings**. Set the optional **APOS tagline** (one line, at most 120 characters), **Currency**, and **Guest-facing URL / FQDN**. Save settings. Currency affects new member and guest tabs only; existing tabs and receipts retain their recorded currency. EUR and USD prices are independent, not automatically converted.

Use a reachable origin such as `https://apos.example.org` (placeholder; replace it), without a path/query. A bare hostname implies HTTPS. Blank uses the request origin, which can accidentally produce localhost links when staff use localhost. Changing this setting changes generated links/QR codes; it does not configure DNS, HTTPS, firewall rules or Wi-Fi.

For a disposable LAN test, bind the server to an address reachable by phones:

```sh
.venv/bin/python main.py --host 0.0.0.0 --port 5000
```

Set the guest URL to the computer's actual LAN address with `http://` and port `5000`; connect phones to a network that can reach it. Allow that port only on the intended network. Test the QR from a phone. This HTTP test configuration is not a public deployment recipe. For real guest access, configure HTTPS separately and set `APOS_SECURE_COOKIES=1`. Secure cookies do not work over plain HTTP. APOS has no login rate limiting; do not expose it through public port forwarding as-is. Keep the computer running while guest access is required.

**Change password** in General settings changes the currently signed-in Admin's password, requiring their current password and matching new entries. Leave those fields blank to preserve it. This setting invalidates existing sessions globally. Resetting an account under Accounts and roles invalidates that account's sessions instead.

## 3. Accounts and permissions

Open **Admin → Accounts and roles**. Enter a username, password, role, optional linked profile and active status, then **Save account**. Usernames are 1–80 characters using letters A–Z/a–z, digits or `. _ @ -`; passwords are 12–256 characters.

| Role | Access and profile requirement |
| --- | --- |
| Admin | Counter operations plus all administration; no linked profile required. |
| Staff | Tabs, non-member guest creation, orders/cancellations, payments, receipts and reports; no administration. |
| Member | Own available tab; requires an active member profile. |
| Guest | Own available tab; requires an active non-member guest profile. |

Create the profile before creating Member/Guest accounts. Choose the matching profile type; accounts do not grant access to other people's tabs. A profile code or QR is not a username/password. Creating a guest or importing members does not create accounts.

Use **Edit** to reset a password, change a role/link or deactivate an account. Leave the password blank to keep it. Saving an edited account invalidates its existing sessions. APOS prevents disabling/demoting the last active Admin; the recovery username `admin` cannot be renamed. Use individual staff accounts so new cancellation records identify the operator.

## 4. Members, guests and photos

In **Admin → Members**, enter a display name and unique member code, optionally add a photo, then add the member. Names/codes are limited to 120 characters. Use **Edit** for subsequent changes. Profiles and login accounts are separate.

Staff create non-member profiles using **Add guest** on Open tabs. Admin manages them under **Guest profiles**. The generated permanent guest number distinguishes duplicate/edited names. Guests with valid links can edit their own non-member display name, but not a member name or their guest number/code.

Photos accept JPEG/PNG/WebP up to 3 MiB and 20 megapixels. They are cropped to 256×256 JPEG with metadata stripped and stored in SQLite. They appear on current bons/receipts and can be included in guest emails. Inform patrons using your actual privacy notice. Removing a live photo does not remove printed/emailed copies or backups.

To remove/archive a profile, first disable its linked active accounts and settle or cancel any open tab. Select **Remove**, review the confirmation, and confirm. The profile disappears from active lists and its photo is cleared; historical financial records remain. Codes from archived profiles are not available for reuse. There is no automatic complete profile deletion or retention schedule.

### Import members

Choose **Upload members CSV**, download the template, and prepare UTF-8 CSV with `name,code` and optional `active`. For example:

```csv
name,code,active
Alex Taylor,M001,true
Robin Lee,M002,true
```

Comma/semicolon separators and UTF-8 BOM are accepted. Flags accept true/false, 1/0, yes/no or ja/nein; omitted `active` defaults to true. Limit: 500 profiles and 512 KiB. Codes must be unique case-insensitively in the file and must not conflict with existing member/guest codes, including archived records.

Upload, review the preview, then confirm. The preview belongs to your browser session, expires after 24 hours and is single-use. A new conflict after preview rejects the whole import. Import creates profiles only: no passwords, roles, photos, updates to existing profiles or deletion of omitted profiles. Inactive imports are retained but cannot receive tabs/accounts until active.

## 5. Products and availability

Under **Product catalog**, add a name and separate positive EUR/USD prices. Use **Edit** to change names/prices and set the alcohol flag. Existing positions and receipt snapshots retain their original product names/prices.

Classify every alcohol product before enabling guest ordering, including new CSV/demo products; new products default to unflagged. Flagged products are excluded from guest ordering and rejected on direct guest submissions. Staff must still check age before serving.

**Deactivate** stops new orders. **Mark out of stock** also stops new orders but is a separate flag. Restoring stock does not reactivate an inactive product. These are manual availability flags, not inventory counts. Existing orders/receipts remain intact.

### Import or synchronize a catalog

Choose **Upload catalog CSV**. Required headers: `name,price_eur,price_usd`; optional: `in_stock,active` (default true). Both currency prices are required. Example:

```csv
name,price_eur,price_usd,in_stock,active
Sparkling water,2.50,3.00,true,true
Pretzel,2.00,2.50,false,true
```

UTF-8/BOM, comma/semicolon separators and the member-import boolean spellings are supported. Decimal commas require semicolon-separated CSV. Limit: 500 products and 512 KiB. Invalid prices/rows and duplicate names in the file reject the import.

Default import adds new products and rejects existing names. **Update listed products and mark omitted products out of stock** matches names case-insensitively, updates prices/flags, adds new products and marks omitted products out of stock without deleting them. Review every preview action, especially omitted products, before confirming. Catalog changes after preview reject a stale synchronization plan. Previews are session-bound, expire after 24 hours and cannot be reused. Existing alcohol flags are preserved by synchronization; classify newly added products manually.

For disposable demonstrations, `main.py demo-stock` adds eight sample products, skipping existing names. Deactivate samples afterward; check alcohol classifications before guest ordering.

## 6. Guest ordering and outgoing mail

Guest ordering is off by default. Enable **Allow guests to add menu items to their own bon** in General settings only after checking catalog, alcohol classification, service procedures and consumer information. Disabling it rejects even already-open forms. Guests need a valid link and open tab; they cannot cancel positions or order alcohol.

Under **Admin → Outbound mail account**, enter the SMTP hostname, port, security mode, sender and any credentials required by your provider. Use STARTTLS or implicit TLS/SSL according to the provider; unencrypted mode is for an appropriate local relay. Enable email explicitly and save. Incomplete enabled configurations are rejected. Test on disposable data with an address you control.

The stored SMTP password is encrypted using the application signing secret. Blank preserves it for the same host/username; changing host/username clears it unless replaced. Preserve the secret with backups; changing it requires re-entering the SMTP password. Stored passwords are not displayed.

Only fully settled, closed tabs with valid links can email. The message contains order/payment totals and printable `bon.html`; a current profile photo is included when present. SMTP acceptance immediately revokes guest access and clears a non-member guest's live photo, but does not erase accounting records. A send failure keeps the link available until ordinary expiry. Acceptance is not proof of inbox delivery.

If a crash leaves a tab marked `sending`, have the responsible maintainer reconcile SMTP logs before any reset. There is no administrator screen to reset it. Do not blindly retry or improvise database changes. Disabling mail hides the form and blocks new sends.

## 7. Legal/privacy notices and operating limitations

In Admin, open **Legal notice** or **Privacy notice → Edit full screen**. Edit German and English separately; load an example only as a draft, replace every placeholder, preview and save. Examples are not automatically published. Missing translations fall back to English. The tagline does not replace the operator's identity or required notices. Do not invent legal identity, tax status, legal basis or retention periods.

Read the [compliance assessment](../COMPLIANCE.md) before operational use. APOS is not TSE-certified and is not ready as a standalone German fiscal register. Its payment recording, receipt, consumer-ordering and retention gaps remain. QR links are guest access, not fiscal QR codes. Financial records survive guest expiry and profile archival. Define appropriate access, backup, retention, food/alcohol service and privacy procedures for the actual association; this guide does not establish legal compliance.

## 8. Back up and restore

Use a new filename in an existing private backup directory:

```sh
.venv/bin/python main.py backup --output /path/to/private-backups/apos-event.sqlite3
```

Replace the example path. SQLite's backup API permits this while APOS is running; existing files are not overwritten. Copy the result to separate controlled storage and verify it through a disposable restore. The database includes profiles/photos, accounts, private codes, orders, receipts, settings and encrypted mail credentials. Back up the effective signing secret (`instance/secret.key` or securely stored `APOS_SECRET_KEY`) separately and privately; retain `instance/staff.key` if preserving the generated recovery password matters. Do not commit any of these to Git.

Restore procedure:

1. Stop APOS and keep the current database as a fallback.
2. Verify the backup, then copy it to `instance/apos.sqlite3` or the configured `APOS_DATABASE` path with private filesystem permissions.
3. Restore the matching secret if needed, then restart.
4. Reconcile real payments/orders after the backup before service; restore rewinds account changes and guest expiry/revocation too. Old access can become valid again in the restored state.
5. Test login, balances, guest access and mail configuration. Do not send real mail during a test restore.

Never overwrite a running database. There is no automatic backup scheduler or built-in refund/reversal recovery workflow.

## 9. Configuration reference

| Variable | Purpose |
| --- | --- |
| `APOS_DATABASE` | SQLite path; default `instance/apos.sqlite3`; parent directory must exist. |
| `APOS_SECRET_KEY` | Persistent signing/encryption secret; otherwise generated in `instance/secret.key`. |
| `APOS_STAFF_PASSWORD` | Initial recovery password for a new database; does not replace a saved password. |
| `APOS_PATRON_BASE_URL` | Initial guest origin for a new database; later changes use Admin/setup. |
| `APOS_SECURE_COOKIES` | Set to `1` when serving through HTTPS; default off. |

CLI commands: `serve` (default), `setup`, `password`, `demo-stock`, `backup --output PATH`; serving accepts `--host` and `--port`. Use one service process and a synchronized system clock. The supported launcher cleans expired non-member guest photos every 30 seconds, plus startup/request cleanup. A custom WSGI deployment needs its own scheduled cleanup invocation.

## 10. Acceptance and troubleshooting

Before an event or after updating, back up and test on disposable data: separate Admin/Staff logins and denied Admin access for Staff; member/guest tabs; phone QR; order and reasoned cancellation; partial/full cash/card recording; receipt printing; reports; configured email and immediate link revocation; backup/restore. Run the project's regression suite after software updates:

```sh
.venv/bin/python -m unittest discover -s tests -v
```

For forgotten recovery credentials use local `main.py setup`. For missing members/products check profile status and both availability flags. For QR failures check binding, actual guest origin, DNS/TLS, firewall and Wi-Fi isolation. For SMTP failures check provider settings, effective secret and logs without disclosing credentials. For disk/database errors stop further payment recording and investigate without deleting financial history. Escalate incorrect payments under the association's reconciliation procedure; APOS cannot reverse them.
