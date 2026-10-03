# APOS

A pub-style association point of sale with persistent running tabs, partial/full payment, menu products, private patron viewing codes and anonymous reports.

Version 0.5 implements the version-one specification and supports German and English, EUR and USD, and one shared local POS computer. Patron access remains available until 24 hours after full settlement. Payments are recorded after collection by cash or an external card terminal.

Read the [complete v1 specification](docs/SPECIFICATION.md) and [operating guide](docs/OPERATIONS.md).

## Start locally

Requires Python 3.10 or newer. Python 3.12 is tested.

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python main.py
```

Open http://127.0.0.1:5000. In another local terminal, retrieve the generated staff password:

```sh
.venv/bin/python main.py password
```

## Initial setup and settings

To choose a staff password and guest-facing FQDN before using APOS, run the interactive setup command in the server terminal:

```sh
.venv/bin/python main.py setup
```

Enter a password of 12–256 characters, confirm it, and enter the guest-facing address, such as `https://apos.example.org` or `http://192.0.2.10:5000` for LAN testing. Password entry is hidden. A bare hostname uses HTTPS. Settings persist in SQLite and can be changed while the server runs.

Alternatively, sign in using the initial generated password and select **Admin**. Set the guest-facing URL and optionally replace the staff password by entering the current password, the new password and confirmation. Changing the password signs out all staff sessions. Custom passwords are stored as hashes and cannot be displayed; the local setup command can reset a forgotten password.

The guest-facing URL is used in guest links and QR codes. Configuring an FQDN here does not create its DNS record or install HTTPS: configure DNS to reach the server and an HTTPS reverse proxy separately. Replace example addresses with your server’s reachable address; `192.0.2.10` is a documentation placeholder.

## Manage menu products

Select a product's **Edit / Bearbeiten** link in the **Product catalog / Sortiment** to change its name and EUR/USD prices. Save the product to apply changes to future orders. Existing tab positions and receipts retain their original product names and prices. Use Activate/Deactivate to control availability for new orders.

Sign in, add members and menu products, then open a tab. The catalog requires independent EUR and USD prices. Choose the operating currency under Admin before opening new tabs.

For Windows, use `.venv\Scripts\python.exe` in place of `.venv/bin/python`.

## Members and profile photos

In **Members / Mitglieder**, select **Edit / Bearbeiten** to update the member name, code or picture. Add or replace a photo with **Upload photo / Foto hochladen** or **Take photo / Foto aufnehmen**. Camera capture works on supported phones; other devices show a file picker. Photos may be JPEG, PNG or WebP, up to 3 MiB and 20 megapixels, and are resized to a metadata-free 256×256 JPEG.

Photos appear as circles. Without a photo, avatars show initials from each name part: Alex → A, Alex Taylor → AT, Alex Robin Taylor → ART. Guests can update their own photo from their valid private guest page, without staff sign-in.

**Remove / Entfernen** opens a confirmation page. Settle or cancel an open tab first. Removed members disappear from the member list and their photos are cleared; historical tabs and receipts remain available to staff.

## Optional guest ordering

In **Admin**, enable **Allow guests to add menu items to their own bon** and save. This is off by default. While their private link is valid and their bon remains open, guests can select active, in-stock menu products and quantities. Prices come from the catalog in the bon's currency. Guests cannot remove positions or order on another bon. Disabling the option immediately blocks further guest submissions, including forms already open in a browser.

Staff continue to control removal under the existing rules. Fully settled, expired or emailed guest links cannot accept orders; guest ordering pauses while a bon email is being sent.

## Configure guest bon email

Open **Admin → Outbound mail account / Postausgangskonto**. Enter SMTP hostname, port, security mode (STARTTLS, TLS/SSL or a local relay), sender address and any authentication credentials. Tick **Enable guest email** and save. Until a complete account is configured and enabled, guests do not see the email option. SMTP passwords are encrypted in SQLite using the persistent application secret; blank password input preserves a saved password for the same server and username.

While their guest link is valid, guests can enter an email address and receive the bon as a message with a printable `bon.html` attachment. After the SMTP server accepts the message, guest access is immediately revoked, including photo access. Staff accounting records remain intact. A failed send leaves the link available. Without successful emailing, guest access expires 24 hours after full settlement as usual. SMTP acceptance does not guarantee delivery to an inbox.

## Upload a catalog and manage availability

In **Product catalog / Sortiment**, choose **Upload catalog CSV / Sortiment als CSV hochladen**. Download the template, select your CSV, review the preview, then choose **Import all products**. By default, import adds new products; duplicate names and invalid rows reject the upload without changing the catalog. To refresh the catalog, tick **Update listed products and mark omitted products out of stock**. This matches existing names case-insensitively, updates their prices and flags, adds new products, and marks products absent from the file out of stock. The preview lists each add/update and every omitted product affected. Nothing is deleted, and existing tab positions and receipts remain intact. If the catalog changes after preview, synchronization is rejected until you upload and review again.

```csv
name,price_eur,price_usd,in_stock,active
Coffee,2.50,3.00,true,true
Tea,2.00,2.50,false,true
```

Required columns: `name`, `price_eur`, `price_usd`. Optional `in_stock` and `active` default to `true`. Use UTF-8, commas or semicolons, at most 500 rows and 512 KiB. Semicolon-separated files may use decimal commas. Both currency prices are required.

Use **Mark out of stock / Als ausverkauft markieren** to stop new orders for a product, then **Mark in stock / Als vorrätig markieren** when available again. This flag is separate from product activation. Existing orders, receipts and reports retain their recorded values. Availability is a manual flag; automatic stock quantities are not tracked.

For sample products with sample prices (six available, two out of stock), run:

```sh
.venv/bin/python main.py demo-stock
```

This adds eight clearly labelled demo products and skips existing names. Repeating the command does not duplicate products or replace your values. A ready-to-upload file is provided at `data/demo_catalog.csv`.

## Verify

```sh
.venv/bin/python -m unittest discover -s tests -v
```

## Patron phones and reports

See the operating guide to enable access on the association network and configure a reachable patron URL. Internet hosting is a separate setup. New guest codes use four independently selected Diceware words from EFF’s 7,776-word list, separated by hyphens; uppercase/lowercase and spaces are accepted when typing. Existing links remain valid. A guest can scan the QR code on the staff tab page or enter the private code for read-only access to one bon. Staff reports separate ordered sales from received payments, grouped by currency; exports omit member and tab identifiers.

The v1 web implementation uses SQLite in `instance/apos.sqlite3`. The earlier in-memory CLI/model modules are legacy prototype code and are not used by v1. No actual card processing, tax invoice generation or refunds are included.

## German compliance status

See [feature-based compliance coverage](docs/COMPLIANCE.md) for implemented safeguards, setup obligations and outstanding requirements. APOS has no certified TSE or compliant fiscal receipt generation. Its cash/card recording capability must be assessed even when intended only for tabs and stock planning. Future feature iterations must maintain this assessment under [project guidance](AGENTS.md).

Non-members can be added with **Add guest**, which creates a funny name, unique guest number and tab. Admin's legal/privacy notices use a full-screen WYSIWYG editor with German/English example drafts and English fallback for missing translations. Replace example placeholders before publication.

Administration is now **Admin**. Sign in as **admin** with the existing password, then create individual Member, Guest, Staff and Admin accounts under **Accounts and roles**. Admin contains member/catalog management and both CSV uploads. Member CSV requires `name,code` with optional `active`; it imports profiles without passwords or role grants. See the operating guide for the access matrix and migration details.

Choose the operating currency under **Admin → Currency**. All new member and guest tabs use it automatically; existing records retain their original currency.

The counter uses a dark touchscreen layout with searchable product tiles, quantity controls and adjacent partial/full settlement. See [counter design and browser verification](docs/FRONTEND_DESIGN.md).
