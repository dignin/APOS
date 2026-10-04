# APOS v1 operating guide

## Install and start

Follow README setup, then run `.venv/bin/python main.py`. APOS serves on the POS computer at http://127.0.0.1:5000 with debug mode disabled. To stop it, press Ctrl+C in that terminal. A restart preserves all saved data.

The initial generated secrets are stored in `instance/secret.key` and `instance/staff.key`; the latter is the initial staff password. Custom passwords are stored as hashes in SQLite. Retrieve it locally with `.venv/bin/python main.py password`. Keep it private. `APOS_STAFF_PASSWORD` supplies the initial password when a new database is created. Existing databases use their stored password hash; change that through Admin or the local setup command. `APOS_SECRET_KEY` optionally supplies the browser-session signing secret. Neither belongs in Git.

## Choose a password and guest-facing FQDN

Run `.venv/bin/python main.py setup` locally to choose/reset the staff password and guest-facing URL. Password input is hidden and requires confirmation and at least 12 characters. This command can run while APOS is serving and invalidates existing staff sessions. The old generated password can no longer sign in after a change; `main.py password` then reports that a custom password cannot be displayed.

In the web interface, choose **Admin**. Enter the URL/FQDN; to change the password, enter the current password and new password twice. Blank password fields preserve the current password. Settings are persisted immediately and survive restarts. Use a complete origin without a path or query; a bare FQDN is interpreted as HTTPS. Leave the guest URL empty to use the current request origin.

FQDN configuration updates QR codes and links, but does not configure DNS, TLS, firewalls or a reverse proxy. Configure those separately before handing out hostname-based QR codes.

## Rename a menu product

In Product catalog / Sortiment, select the product's **Edit / Bearbeiten** link. Update its name and/or the two currency prices and save. Only future orders use the changes. Existing positions, saved receipts and their historical report names remain unchanged. Deactivated products can be edited too.

## Members and photos

Use the member Edit link to change the name, internal code, or photo. Member codes remain unique, including removed records. Upload JPEG, PNG or WebP (maximum 3 MiB and 20 megapixels), or use the camera-capture option on a supported phone. Desktop browsers may show a file picker instead of a camera. Uploaded photos are center-cropped, resized to 256×256 JPEG and stripped of metadata. They are stored in SQLite and included in backups.

Circular avatars show the image, or initials for every whitespace-separated name part. Guests may upload their own photo through a valid private guest link. Staff photo URLs require staff sign-in; guest photo URLs require the private code and stop working after expiry or successful emailing.

Removing a member requires confirmation and no open tab. The member is hidden from the member list and cannot open new tabs; the photo is cleared. Existing financial history remains linked to the removed record. Name/code updates apply to the linked member identity in staff views.

## Guest ordering

The Admin checkbox **Allow guests to add menu items to their own bon** enables ordering through private guest links. It is disabled by default and saved in SQLite. Guest pages show available products and quantity controls only for open bons with valid links. The server determines the bon from the code and prices from the catalog; submitted alternative IDs/prices cannot change the target or price.

Disabling the option immediately rejects guest submissions, including stale forms. Inactive/out-of-stock products, invalid quantities, missing CSRF tokens, settled/expired/revoked links and a send-in-progress state cannot create guest orders. Guests cannot delete positions. Staff removal rules, including protection after payment, still apply. Staff orders use the same menu validation.

## Outbound email setup and guest-link revocation

Configure **Admin → Outbound mail account** with hostname, port, sender, connection security and any username/password. STARTTLS is the default; select TLS/SSL for implicit TLS, or no encryption only for an appropriate local relay. Enable the account explicitly. Saving an incomplete enabled account is rejected. The guest email option appears only after full settlement and closure, with a configured and enabled account; disabling it immediately hides the form and blocks email submissions.

Mail passwords are encrypted in the database using the application signing secret. Back up `instance/secret.key` or your configured `APOS_SECRET_KEY` privately alongside the database; changing that secret requires re-entering the mail password. Stored passwords are never displayed. Changing the server/username clears the old password unless a new one is entered.

Guests enter their recipient address only after full settlement and closure, while their private link is valid. Open or partially paid tabs cannot email a bon, including by direct request. The message contains order positions, product names, quantities, unit/subtotal prices, UTC order times, total/paid/due, and a printable self-contained `bon.html` attachment. It does not include the member name or private guest code. On SMTP acceptance the link and guest photo access are revoked immediately; staff tabs, receipts and reporting data remain. On a send error the link remains usable. Otherwise expiry is 24 hours after full settlement.

A send-in-progress flag prevents repeated submissions while SMTP is working. If the process crashes during delivery, a tab can remain flagged `sending`; staff must reconcile whether the message was accepted before resetting that flag. SMTP acceptance is not confirmation of inbox delivery; delayed bounces do not reactivate the link. No real mail account is enabled by default, and development tests use mocked delivery.

## CSV catalog import and out-of-stock products

Select **Upload catalog CSV** in the catalog. Download the template and upload a UTF-8 file with required columns `name,price_eur,price_usd` and optional `in_stock,active`. Boolean flags accept true/false, 1/0, yes/no or ja/nein; omitted flags default to true. Comma and semicolon separators are supported, including UTF-8 BOM. Semicolon CSV may use decimal commas. Limits: 500 products, 512 KiB.

Review the preview before confirming import. The entire file is validated before any product is added. Duplicate names within the file (case-insensitive), invalid prices and malformed rows reject the import. Default upload adds new products and rejects existing names. For catalog refresh, select **Update listed products and mark omitted products out of stock**. This mode matches existing names case-insensitively, updates listed prices/flags and adds new products; omitted products are retained but marked out of stock. Preview lists every add/update and the products becoming unavailable. An already-open tab retains its original positions; old receipts and sales remain intact. If someone changes the catalog after preview, confirmation rejects the stale plan without making changes. Existing ambiguous duplicate names must be corrected before synchronization. The preview is bound to your staff browser session and expires after 24 hours. Confirmation checks for newly conflicting names again and imports all rows in one transaction. Retrying a consumed confirmation cannot add duplicates.

Mark a product out of stock using its dashboard button. It immediately disappears from available menu choices, and stale order submissions are rejected. Mark it in stock to restore ordering. An inactive product stays unavailable even if marked in stock. Existing positions, receipts and reports remain intact. The availability flag does not track inventory counts.

## Demo catalog

Run `.venv/bin/python main.py demo-stock` to add eight demo products with sample EUR/USD prices. Six start available and two out of stock. Existing names are skipped without modifying their prices or stock flags; repeated runs do not add duplicates. The same catalog is available at `data/demo_catalog.csv` for upload testing. Deactivate demo items when finished testing.

## Daily use

1. Sign in and choose Deutsch or English.
2. Add members with a display name and unique code. Do not put member identifiers in product names.
3. Add menu products with separate EUR and USD prices. Deactivate products unavailable for new orders.
4. Select a member and currency. Open or resume their tab.
5. Let the patron scan the displayed QR code, or hand them the private code/link. Add selected products and quantities for each round.
6. Collect partial or full payment externally, select cash/card and record the amount.
7. A partial payment keeps the tab open. Full payment closes it and starts the 24-hour patron window.
8. Print the payment receipt using the browser's Print command. Each receipt retains its payment-time snapshot.
9. Open Reports and choose the UTC date range. Download CSV for association reporting.
10. Make a backup after the event and sign out when leaving the station.

Removal is available only before the first payment. After a payment, more orders may be added, but existing positions cannot be removed. V1 does not support refunds or payment reversal. Report order totals include unpaid orders; payment totals reflect received money. Do not interpret them as the same measure.

## Allow patron phones on the association network

Choose a stable LAN address or local hostname for the POS computer. Example only: `192.168.1.50`. Start the service using the real address:

```sh
APOS_PATRON_BASE_URL=http://192.168.1.50:5000 .venv/bin/python main.py --host 0.0.0.0
```

Allow incoming TCP port 5000 in the computer's firewall for the association network. Connect patron phones to a Wi-Fi network that can reach the computer. Open `http://192.168.1.50:5000/view` and enter the code, or distribute the full patron link shown in the staff interface. Test this from a patron phone before opening service. The staff machine may continue using localhost.

The example address is not configured automatically. APOS does not change firewall rules, Wi-Fi isolation, DNS or routers. Default localhost links cannot be reached from another device. A stopped computer or disconnected network makes the links unavailable. Keep the service and computer running until the last patron link expires.

Local plain HTTP is a local-network operating mode. For untrusted networks or internet access, use a separately configured HTTPS service with appropriate staff-login protection and secure session cookies. The current release does not provide public deployment or login rate limiting. Never expose it publicly through port forwarding as-is.

## Back up

Choose a new filename; the command refuses to overwrite existing files:

```sh
.venv/bin/python main.py backup --output /path/to/association-backups/apos-2026-10-03.sqlite3
```

The parent directory must exist. This command uses SQLite's backup API and may run while staff use APOS. Copy the resulting file to separate controlled storage. The database contains member labels, tabs, access codes and payment records; protect it accordingly. Back up secrets privately if retaining existing browser sessions and the generated staff password matters.

## Restore

Stop APOS first. Keep the current database as a fallback. Copy a verified backup to `instance/apos.sqlite3` (or to the configured `APOS_DATABASE` path), with private permissions, then restart APOS. Restoring rewinds orders, payments and expiry to the backup state. Reconcile any real-world payments made after the backup before taking new orders. Never overwrite the database while the server is running.

## Configuration

| Variable | Purpose | Default |
| --- | --- | --- |
| `APOS_DATABASE` | SQLite path; parent directory must exist | `instance/apos.sqlite3` |
| `APOS_SECRET_KEY` | Browser-session signing secret | Generated private persistent file |
| `APOS_STAFF_PASSWORD` | Initial password for a new database; later changes use Admin | Generated initial private file |
| `APOS_PATRON_BASE_URL` | Initial guest URL for a new database; later changes use Admin | Current request origin |

CLI options: `--host`, `--port`; commands: `serve` (default), `setup`, `password`, `demo-stock`, `backup --output PATH`. Use a single service process for the station. UTC timestamps depend on the system clock; keep it synchronized.

## Troubleshooting

- Sign-in does not work: retrieve the initial local password, or reset a custom password through `main.py setup`. Environment passwords initialize new databases only.
- Expired form: reload the page and submit again. Logging out or replacing the session secret invalidates old forms.
- Patron phone cannot connect: test the base URL; verify server binding, firewall, Wi-Fi isolation and the POS computer's power/network.
- Patron code expired: expiry begins at full settlement and cannot be extended in v1. Staff receipts remain available.
- Report and cash total differ: orders and payments are reported separately; unpaid/partially paid tabs and different payment dates explain differences.
- Product unavailable: activate it in the menu. Deactivation preserves earlier orders.
- Disk full: free space under the computer operator's control before taking further payments. Do not delete the live database or backups. V1 does not provide an automatic recovery workflow for filesystem failures.

## Release validation

Automated tests cover partial/full settlement, repeated and concurrent payments, restart persistence, price snapshots, menu-only ordering, invalid input, code expiry, staff protection, anonymous reports, CSV formula protection and German/English page rendering. Run the README verification command after updates.

Before a live association event, perform operator acceptance with sample members and products, a real patron phone, partial/full payment, printing, expiry, and backup/restore on disposable data. Browser visual verification was unavailable in the development machine because its disk was full. No public server has been deployed.

## Compliance setup

Read [feature-based German compliance coverage](COMPLIANCE.md) before live use. Admin displays the saved Impressum and privacy notices as formatted text. Choose “Edit full screen” to edit, switch language, or load a German/English example. Replace placeholders with actual association details before saving. English is the fallback for a missing translation. Existing notices are preserved; examples are not published automatically. Edit each alcohol product and enable its alcohol flag before allowing guest ordering, including newly imported/demo products. Staff still verify age before serving. Configure HTTPS and `APOS_SECURE_COOKIES=1` for real guest access; do not enable Secure cookies on the existing HTTP test service.

Position removal now requires a cancellation reason and retains the original order in staff cancellation history. New cancellations identify the signed-in account; historical shared-password entries retain “shared staff”. The 24-hour guest access limit and email revocation do not erase underlying records. APOS still has no certified fiscal integration or automatic legal retention enforcement.

### Non-member guests

Choose **Add guest** on the home page; the Admin currency setting is used. APOS generates a playful name and a unique guest number and opens a tab immediately. Names can repeat; the number identifies the guest and never changes when the display name/code is edited. Guests appear separately from members. Use their tab QR/code as usual. Staff can edit/archive profiles through the guest list; open tabs must be settled or cancelled before removal. No real name is required.

## Admin and account roles

The former Setup screen is now **Admin** at `/admin`. Members, guest profile management, catalog products, both CSV uploads, mail configuration and legal notice editing are Admin-only. Staff still open member tabs, add non-member guests, place/cancel orders, record payments and view receipts/reports. Hiding a link is not the access control: direct requests to management endpoints are checked on the server.

Existing installations migrate the current shared-password hash into a recovery account named **admin**; use your existing password with that username. Old shared sessions must sign in again. Create individual accounts under **Admin → Accounts and roles**. Roles are:

| Role | Access |
| --- | --- |
| Admin | Staff operations plus administration, profiles, products, uploads and account/role management |
| Staff | POS operations, guest creation, receipts and aggregate reports; no administration or catalog/profile changes |
| Member | Own linked active member profile's available tab; guest-page ordering follows the existing staff setting |
| Guest | Own linked active non-member profile's available tab; same guest-page restrictions |

Member and Guest login accounts require a matching active profile. A generated guest profile/private QR link does not automatically create a password account. Profile/member codes are not usernames or passwords. Role changes, password resets and deactivation invalidate that account's sessions; the last active Admin cannot be disabled or demoted. The recovery username `admin` is fixed; local `main.py setup` resets its password and restores its Admin role. Existing holders of the old shared password can use the migrated account, so rotate it and provide separate Staff accounts before real use. Keep local server access restricted.

## Member CSV upload

In Admin's Members section, choose **Upload members CSV**. Required headers are `name,code`; optional `active` accepts true/false, 1/0, yes/no or ja/nein (default true). UTF-8/BOM and comma/semicolon delimiters are supported, with a maximum of 500 members and 512 KiB. Names/codes must contain 1–120 characters. Review the preview, then confirm all rows together. Codes must be unique case-insensitively within the file and must not match any existing member/guest code, including archived records. A conflict arising after preview rejects the whole import.

Uploads add member profiles only: no credentials, privileged roles, photos, updates or deletion of omitted members. Create login accounts separately. Inactive imported profiles are retained but hidden from the active lists and cannot receive tabs/accounts; import active profiles for ordinary use. A preview belongs to the uploading session, expires after 24 hours and cannot be reused after confirmation. Consumed staging data is deleted; expired staging data is removed on a subsequent member upload. The staged preview contains personal data and is included in database backups.

### Markdown notices

In the full-screen notice editor, choose **Markdown** to write or paste headings (`#`), bold (`**text**`), italic (`*text*`), lists, links, quotes, code blocks or tables. The adjoining live preview shows the saved-page formatting. Choose **Visual editor** to continue editing formatted text. Switching to visual view without making changes preserves the Markdown source; actual visual edits save rich text. Public pages and Admin display rendered content. English/German versions remain independent, with English fallback. Scripts, unsafe links, remote images and embeds are not rendered. Existing plain notices also interpret Markdown; existing rich-text notices retain their formatting.

## Global currency setting

Admin selects one operating currency (EUR by default, or USD). Staff cannot change it, and tab/guest creation does not accept a currency override. New tabs snapshot the current setting inside their creation transaction; there is no currency choice per user or tab. The catalog's existing EUR/USD prices determine the amount charged. Changing the setting affects new tabs only: existing open/settled tabs, payment snapshots, guest pages and historical reports keep their original denomination. No currency conversion or relabelling of recorded amounts is performed. Settle open tabs before switching when a single operational currency is required. Historical reports may therefore still contain both currencies; they remain separate and are not combined without conversion.
