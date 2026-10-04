# APOS version one — product and implementation specification

Status: implemented local v1, pending operator acceptance and visual browser review.
Version: 1.0.0. Requirements recorded on 3 October 2026.

## 1. Purpose

APOS is an association's pub-style point of sale. Staff open a running tab, select products from a menu, add orders over time, record partial or full settlement, and produce sales reports without patron identifiers. A patron receives a private code to view their own running bon online. The link works throughout the open tab and expires exactly 24 hours after full settlement.

The first operating model is one shared local association computer. Staff share one access password, chosen through the local setup command or the protected web Admin screen. Patrons may access the service from their phones when the association network permits it. German and English are supported; German is the initial language. EUR and USD are supported as independent tab currencies.

## 2. Confirmed requirements and v1 decisions

| Area | Required behavior | Implemented decision |
| --- | --- | --- |
| Running tabs | Orders accumulate over time | One open tab per member; resume preserves its orders |
| Settlement | Partial or full payment | Positive amount against outstanding balance; each payment has a saved receipt |
| Menu | Creator selects products | Staff choose active catalog products; arbitrary custom sales and client-supplied prices are rejected |
| Languages | German and English | Per-browser language selector, including patron pages |
| Currencies | EUR and USD | Separate catalog prices; currency fixed when a tab opens; no conversion |
| Patron view | Private code; full item details | Unpredictable bearer code; read-only page with product, quantity, unit cost, subtotal, UTC order time, paid and due |
| Expiry | 24 hours after full settlement | Timestamp stored on settlement and checked on every patron request |
| Reporting | Anonymous sales reports | Product aggregates and payment-method aggregates, date-filtered, displayed and downloadable as CSV |
| Local operation | One shared computer | Python/Flask, SQLite, Waitress; loopback by default; optional LAN binding |

Additional implementation decisions: staff maintain member labels and unique internal codes; no legal name is required. Product names are operator-entered text and are not automatically translated. Staff can edit catalog names and prices; previously placed orders retain their captured values. Partial settlement applies to an amount on the entire tab, rather than selected items or individual guests. A partial payment does not start the expiry clock. No refunds or removal of items after any payment are included in v1.

## 3. People and permissions

### Staff

Sign in with the individual account's password. Create members and catalog products, activate/deactivate products, open/resume tabs, place menu orders, remove uncharged items, record payments, print saved receipts, and view/export reports. Sign-out removes staff access in that browser. Staff use individual accounts. Member/catalog administration is reserved for Admin accounts; the role matrix below controls access.

### Patron

Use `/view` and the private code, or open the supplied `/view/<code>` link. No staff account is needed. View orders and totals, switch language, and refresh to see changes. Cannot pay, delete positions, see other tabs, or access staff reports. When staff enable guest ordering in Admin, a valid code permits adding active, in-stock menu products to that open bon only, at server-determined catalog prices. A valid private code permits updating the linked member photo and requesting a bon email when outbound mail is configured and enabled. Patron views do not display full member names or internal member codes; they may display the member photo or initials. Anyone possessing the code can view that bon; possession is the access credential.

## 4. Main workflows

### First setup

1. Install the two runtime dependencies in a virtual environment.
2. Start APOS; a private database and persistent session/staff secrets are created locally.
3. Retrieve the generated staff password locally, or configure a chosen password through the environment.
4. Choose the password and guest-facing FQDN with `main.py setup`, or sign in with the initial password and use Admin. Select the language.
5. Add members using a display name and unique member code.
6. Add menu products with explicit prices in both EUR and USD.

### Open and order

1. Select a member and currency and open the tab.
2. If the member already has an open tab, resume it, retaining its original currency.
3. Let the patron scan the displayed QR code, or give them the private code and reachable patron URL.
4. Select an active menu product and quantity from 1 to 999.
5. Save the order. Its product name, unit price, quantity and time are captured.
6. Repeat for subsequent rounds. Each submission creates its own position and timestamp.

### Partial settlement

1. Read the outstanding balance.
2. Collect the chosen amount by cash or an external card terminal.
3. Select the payment method and enter the amount.
4. APOS records the payment and creates a saved receipt with the order snapshot, cumulative paid amount and remaining balance at that time.
5. The tab remains open. More menu orders and further payments are allowed.

### Full settlement

1. Collect and record the exact outstanding amount.
2. APOS atomically saves the payment, closes the tab, and sets patron expiry to settlement time plus 24 hours.
3. The closed tab cannot receive orders or have positions removed.
4. Staff can print the saved receipt. A subsequent visit opens a new tab with a new private code.
5. At the expiry boundary, requests to the old patron URL return an unavailable/expired page.

### Correct or cancel

Before any payment, staff may remove a complete order position. Quantities cannot be edited in place: remove and re-add the correct position. Once a payment exists, positions are protected; further orders remain possible. An empty tab may be cancelled, immediately disabling its patron code, without creating a payment. Nonempty tabs cannot be cancelled.

### Reporting

Staff select an inclusive start and end date in UTC. APOS displays product sales and recorded payments separately, with independent EUR and USD rows. Export creates a CSV with the same aggregates. Reporting includes no member names, member codes, tab IDs, patron codes, receipt IDs, or individual payment timestamps. Product names must not contain patron identifiers if the association wants exports to remain free of identifying text.

### Catalog CSV import

CSV files require `name,price_eur,price_usd`; optional `in_stock,active` flags default to true. UTF-8/BOM, comma or semicolon delimiters, and semicolon-file decimal commas are supported. Limits are 512 KiB and 500 products. Unknown/duplicate/missing headers, malformed rows, invalid prices/flags, and duplicate names within the file are rejected. Default additive import also rejects existing catalog names. Valid files are staged in SQLite for a browser-bound preview lasting up to 24 hours. Explicit confirmation rechecks catalog conflicts inside a write transaction and adds all rows together; a consumed confirmation cannot be reused. Upload is additive by default. An explicit synchronization checkbox updates listed products by case-insensitive name, adds new products and marks omitted products out of stock. The preview identifies add/update actions and affected omissions. Full catalog state is recorded at preview and verified under the write lock before synchronization; any intervening catalog change rejects the confirmation without modifications. Ambiguous existing names are rejected for synchronization. Historical positions and receipts retain their snapshots, and omitted catalog rows are retained.

### Optional guest ordering

A persistent `guest_ordering` setting defaults to disabled. Staff can enable it in Admin. Valid codes on open bons then expose a menu form with product and quantity only. The server rechecks the setting, expiry/revocation, open status and stock while holding the write transaction, and uses catalog prices in the bon currency. Guest-supplied tab/member IDs and price overrides are ignored. Guest removal has no public route; staff removal remains subject to the payment-protection rule. Guest ordering is blocked while sending the bon email and after settlement, expiry or successful mailing.

## 5. Money and payment rules

- All persisted monetary amounts are integer cents. Decimal parsing accepts at most two decimal places; no floating-point summation is used.
- Catalog unit prices must be positive and at most 999,999.00 in each currency.
- EUR and USD prices are set independently. No exchange rate or combined cross-currency total exists.
- A tab's currency never changes after opening. Every order and payment uses that currency.
- Tab order total = sum of unit cents × quantity across its positions.
- Paid amount = sum of recorded payments. Outstanding amount = order total − paid amount.
- Payments must be positive, valid cent amounts and at most the outstanding amount.
- A payment equal to the balance closes the tab. Empty tabs cannot be paid.
- Payment submission tokens prevent a repeated submission of the same payment form from creating another payment. A new form represents a new payment intent.
- SQLite write transactions serialize balance checking and payment insertion. Concurrent payments cannot create overpayment.
- Cash/card are records of payment collected externally. APOS does not process a bank card or reconcile a terminal.
- Receipts are payment records; this release contains no tax calculation, fiscal signing, tax registration details or legal invoice generation.

## 6. Patron access and retention

The staff tab displays a locally generated SVG QR code containing the reachable patron URL. It requires no external QR service. The tab has a cryptographically random four-word Diceware code (approximately 51.7 bits, using EFF’s full 7,776-word list), independent of its numeric database ID. Case-insensitive entry and spaces instead of hyphens are accepted. Each of the four words is selected independently and uniformly using the operating system’s cryptographic random source; repeated words are allowed. Existing prototype links retain their original codes. The code is reusable while the tab remains open. No expiry is scheduled until full settlement. Partial payment leaves it accessible. Full settlement stores an absolute UTC expiry exactly 24 hours later. Checking expiry occurs on each request and requires no timer or scheduled task.

Guests can request their bon at an entered email address only while the code is valid and a complete enabled SMTP account exists. Successful SMTP acceptance immediately revokes guest access while keeping staff accounting records. Failure leaves access available. Otherwise the ordinary 24-hour settlement expiry applies. Expired, revoked and unknown codes return the same generic 404 message. Patron responses carry `Cache-Control: no-store` and `Referrer-Policy: no-referrer`. Expiry prevents subsequent service access; it cannot revoke screenshots, printed copies, or content already loaded in a browser. Staff records remain in the local database after patron access expires. This is access expiry, rather than automatic deletion of financial records.

Tabs, order snapshots, receipts, and members persist until the association handles retention outside this v1 interface. A future retention policy may separately erase member identity after a chosen period without damaging aggregate financial records.

## 7. Language and time

Interface strings, workflows, validation messages, and monetary display support German and English. The locale is selected per browser session and preserved across sign-in. User-entered names retain their original text. German currency formatting uses comma decimal separators; English uses decimal points. HTML numeric inputs submit decimal-point values in either locale.

All order, payment and expiry timestamps are stored and labelled as UTC. Date reports use UTC calendar days, with an inclusive end date represented internally as the following midnight. A configurable association time zone is deferred to a later release.

## 8. Reports and interpretation

Orders are grouped by captured product name, unit price, and currency. Values include orders placed in the date window whether paid or unpaid. Removed positions are excluded; removal is not retained as an audit event in v1. Different historical unit prices appear as separate rows.

Payments are grouped by currency and method, based on the payment timestamp, including partial payments. Therefore an order on one day and its settlement the next day appear in different daily reports. Product order totals and received-payment totals are deliberately different measures.

CSV columns: `type`, `product`, `currency`, `unit_cents`, `quantity`, `payment_method`, `total_cents`. Amounts are exact integer cents. Potential spreadsheet formula prefixes in product names are escaped. Machine-readable CSV headings remain English irrespective of display language.

Reports remove direct patron identifiers and combine transactions. They are not a claim of mathematical anonymity against inference from very small event groups or externally known purchases.

## 9. Data model

| Entity | Principal fields | Constraints |
| --- | --- | --- |
| Settings | Guest-facing URL, staff password hash, credential version | Password changes invalidate staff sessions |
| Member | ID, display name, internal code | Unique internal code; fields 1–120 characters |
| Product | ID, name, EUR cents, USD cents, active flag | Positive prices; active controls new orders |
| Tab | ID, member ID, currency, open/close times, private code, expiry | One open tab per member; unique private code |
| Position | ID, tab ID, product ID, captured name/price, quantity, ordered time | Positive cents; quantity 1–999; snapshot retained |
| Payment receipt | ID, tab ID, paid time, method, amount, submission token, paid/due snapshots | Unique submission token; positive amount |
| Receipt position | Receipt ID, captured name/price/quantity/order time | Frozen snapshot at each payment |

Products also have an independent in-stock flag. Both active and in-stock are required for ordering, checked transactionally even for stale forms. Existing databases are migrated additively with all products initially in stock. Catalog deactivation affects new orders only. It does not change outstanding items, prior receipts, or historical reports. Member display names may identify internal records; patron views and report exports omit them.

## 10. Architecture and routes

Server-rendered Flask forms work without JavaScript. SQLite provides local persistence and foreign-key constraints. Waitress serves the application. The application factory accepts a database location and secrets, enabling isolated tests. The historical `models/` and `tab/` modules remain as legacy prototype code; v1 uses the SQLite implementation in `app.py`. The previous CLI was broken; `main.py` now starts the web POS and provides local maintenance commands. Existing in-memory prototype data has no persisted migration source.

| Route | Access | Purpose |
| --- | --- | --- |
| `GET/POST /login` | Public | Shared staff sign-in |
| `POST /logout` | Staff | End staff session |
| `GET/POST /settings` | Staff | Set guest-facing URL and change staff password |
| `GET/POST /products/<id>/edit` | Staff | Edit catalog name and currency prices |
| `POST /language` | Public | Change browser language |
| `GET /` | Staff | Dashboard, members and catalog |
| `POST /members` | Staff | Create member, optionally with photo |
| `GET/POST /members/<id>/edit` | Staff | Update member and photo |
| `GET/POST /members/<id>/remove` | Staff | Confirm removal; retain financial history |
| `GET /members/<id>/photo` | Staff | Profile image |
| `GET/POST /settings/mail` | Staff | Configure and enable outbound SMTP |
| `POST /products` | Staff | Create menu product |
| `POST /products/<id>/toggle` | Staff | Activate/deactivate product |
| `POST /products/<id>/stock` | Staff | Mark product in/out of stock |
| `GET/POST /catalog/upload` | Staff | Upload and validate CSV |
| `GET /catalog/preview` | Staff | Review pending import |
| `POST /catalog/import` | Staff | Atomically import confirmed products |
| `GET /catalog/template.csv` | Staff | Download catalog CSV template |
| `POST /tabs` | Staff | Open/resume tab |
| `GET /tabs/<id>` | Staff | Order and settle tab |
| `POST /tabs/<id>/items` | Staff | Add active menu item |
| `POST /tabs/<id>/items/<line>/remove` | Staff | Remove position before payment |
| `POST /tabs/<id>/checkout` | Staff | Record partial/full payment |
| `POST /tabs/<id>/cancel` | Staff | Cancel empty tab |
| `GET /receipts` | Staff | Recorded payment history |
| `GET /receipts/<id>` | Staff | Immutable payment snapshot |
| `GET /reports` | Staff | Date-filtered aggregate report |
| `GET /reports.csv` | Staff | Download anonymous aggregates |
| `GET/POST /view` | Public | Patron code entry |
| `GET /view/<code>` | Code holder | Bon view and optional ordering until expiry/revocation |
| `POST /view/<code>/items` | Code holder | Add menu items if staff enabled ordering and bon remains open |
| `GET/POST /view/<code>/photo` | Code holder | View/update own photo while valid |
| `POST /view/<code>/email` | Code holder | Email bon and revoke guest access on success |

All mutations require a session-specific CSRF token. Server-side checks validate input and staff privileges. SQL uses bound parameters and HTML is escaped. Chosen passwords are stored as scrypt hashes. Password changes increment the credential version, invalidating prior staff sessions. Secrets are generated with private file permissions; the supported startup applies a private file umask. All sensitive responses prohibit caching. Request bodies are limited to 4 MiB; profile photo file content is separately limited to 3 MiB; catalog file content is separately limited to 512 KiB. Debug mode is disabled in normal startup.

## 11. Deployment and operation

Default service is `127.0.0.1:5000` for the shared POS computer. For patron phones, bind the service to a reachable association-network interface, allow the port through the local firewall, and distribute a URL using the computer's LAN hostname/address. Save that address in Admin to display suitable patron links and QR codes. `APOS_PATRON_BASE_URL` initializes the address for new databases only. Phones must be on a network that can reach it; some guest Wi-Fi networks isolate clients.

An internet-accessible patron service requires a separate deployment/network decision. No public hosting, DNS, HTTPS certificate, port forwarding or internet exposure is created by this release. Exposing staff login to an untrusted network requires HTTPS, secure cookies, reverse-proxy configuration and login rate limiting; these are outside the local v1 deployment. Do not treat the included LAN server as hardened public hosting.

Keep the POS computer running during the patron access window. A network outage or stopped computer makes links unreachable until service resumes. Keep its clock accurate because access expiry and reports depend on UTC timestamps.

Back up SQLite with the included backup command, including during operation, using SQLite's consistent backup API. Save backups outside the live instance directory and copy to separate association-controlled storage. Restore only with the server stopped. Secrets should be kept privately and separately from published source. A chosen staff password is set through Admin or `main.py setup`; `APOS_STAFF_PASSWORD` supplies a bootstrap password for new databases only; the signing secret can be configured with `APOS_SECRET_KEY`. Replacing the signing secret invalidates old browser sessions.

## 12. Acceptance criteria

1. Staff can add a member and menu product, open a tab and place multiple rounds.
2. Reopening a member's open tab preserves orders and currency.
3. Product unit prices come from the server catalog; submitted alternate prices are ignored.
4. Each position displays product, quantity, price, subtotal and ordered time.
5. A partial payment reduces the balance without closing the tab or starting expiry.
6. New orders may be added after partial payment and increase the outstanding balance.
7. Full settlement closes the tab, saves a receipt, and sets expiry to exactly 24 hours later.
8. A repeated payment form records only one payment; concurrent payments cannot overpay.
9. A restarted server retains tabs, payments and historical receipts.
10. Patrons can view their private tab without staff authentication and cannot reach POS functions.
11. Unknown/expired codes return unavailable; staff records remain accessible after expiry.
12. A new visit creates a new tab and patron code after the old tab is settled.
13. German and English versions of all key screens render successfully.
14. EUR and USD sales/payments remain separate in all totals and reports.
15. A selected report period returns product aggregates and payment aggregates, with no direct patron identifiers.
16. Invalid amounts, quantities, unknown products, inactive products, overpayment and missing CSRF tokens do not change financial data.
17. Staff can cancel an empty tab; charged or paid positions are protected according to the rules above.
18. The documented local server and backup commands work.

Automated regression tests cover criteria 1–17, including restart behavior and concurrent payments. Maintenance and HTTP smoke tests cover criterion 18. Visual browser checks and operator acceptance remain separate release checks; this environment could not install a browser because its disk is full.

## 13. Explicit v1 boundaries and next versions

V1 does not include inventory, discounts, taxes, legally compliant fiscal receipts, refunds, split settlement by position/person, multi-currency conversion, named staff roles, cloud synchronization, payment processing, printer drivers, automatic refresh, or public internet hosting. Default member/product lists and receipt history are suitable for a small association; pagination and search are future work.

Next candidates: operator acceptance and browser review; safe correction/refund workflow with an audit ledger; configurable local time zones; public patron hosting with hardened access; stock control; immutable end-of-day closing reports; privacy-driven identity retention. These require their own scope and acceptance criteria.

## Compliance iteration: 3 October 2026

[COMPLIANCE.md](COMPLIANCE.md) tracks implemented safeguards, conditional obligations and outstanding gaps for every feature. Position removal now records a cancellation with original line retained, reason (1–500 characters), UTC time and shared-staff actor. Active-order queries, balances, new receipt snapshots, emails and sales aggregates exclude cancelled positions. Staff open-tab pages show cancellation history. Original payment snapshots remain unchanged.

Products have an alcohol flag, editable by Admins. Guests cannot order flagged products even by direct submission. New/imported products require staff classification. Guests can remove their own photo while their link is valid. Admin manages sanitised rich-text legal/provider and privacy notices with language-specific versions. Secure cookies can be enabled by environment configuration. Guest ordering uses an explicit payment-obligation button; full final-total confirmation remains open. These safeguards do not certify German fiscal or overall legal compliance.


## Notice editor and non-member guests

Legal/privacy notices now use a full-screen WYSIWYG page with heading, paragraph, bold, italic, list and undo controls. Saving returns to Admin, where only formatted notice content and an edit link appear. Public pages show formatted content without editing controls. Server-side allowlisting strips HTML attributes and executable/embedded content. Each notice has independent English/German storage; the selected language determines the editable version, with English fallback when the translation is absent. Empty German content clears that translation. Example drafts are local language-specific files loaded on demand; existing content is never seeded or overwritten automatically.

Staff-only POST /guests creates a pseudonymous non-member profile and an open tab atomically. The generated funny name follows staff language, currency is EUR/USD, and a persistent monotonic number is unique and independent of editable profile code. Guest numbers are public-facing identifiers, not access secrets; private Diceware tab codes remain separate. Guest profiles are listed separately from members and retain existing edit/archive/photo workflows. Reports exclude guest identity as for members. This reduces required identity collection without claiming anonymisation or a fiscal exemption.

## Role-based administration and member CSV

This section supersedes the original shared staff-login model. `accounts` stores case-insensitive ASCII usernames, scrypt password hashes, one role (Member/Guest/Staff/Admin), optional linked profile, active flag and session version. The existing staff hash bootstraps the `admin` recovery account without resetting its password. Old shared sessions do not carry an account ID and must sign in again. Login validates the database role, account activity/version, and member/guest profile activity on every request; client session role flags do not grant permissions.

Administration is `/admin` (legacy `/settings` retains the same restrictions). Catalog uploads/templates/preview/confirmation, mail configuration and notices use `/admin/...` URLs, with restricted legacy aliases. Admin manages profiles/products/accounts. Staff operates tabs, guest creation, receipts and reports. Member/Guest accounts require corresponding active profiles and resolve only their own accessible tab through `/my-tab`; request parameters cannot select another profile. Existing private-code access remains available as a bearer capability and retains expiry, email revocation and optional ordering semantics.

Account updates invalidate sessions through account version increments, and the last active Admin is protected inside a writer transaction. Local recovery resets the fixed `admin` account and invalidates sessions through the existing credential epoch. Account events retain actor, subject, action and UTC time without passwords. New cancellations identify the signed-in account; historical “shared staff” entries remain unchanged. This is not a complete fiscal audit trail.

Member CSV requires name/code with optional active. It is bounded, UTF-8, strictly validated, additive, browser-session-bound and previewed before atomic insertion. Duplicate codes are case-insensitively rejected both before staging and under the confirmation writer lock. It cannot assign account roles or import credentials. Preview expires after 24 hours; successful confirmation removes its stored personal-data payload. Importing members preserves all existing guest/member profiles, tabs, photos and payment records.

## Markdown notice rendering

Notice format is stored per language (`html` or `markdown`), with legacy translated rich HTML inferred where its format key is absent. Legacy English `plain` notices use Markdown rendering. Markdown source (including meaningful indentation) is retained, while visual edits use sanitised HTML. The full-screen editor offers Markdown source, live preview, and visual editing. Admin-only POST `/admin/notices/preview` requires CSRF and the same 20,000-character source limit. Rendering disables raw HTML, sanitises allowed output elements and URLs, removes image/embedding tags, and does not contact remote rendering services. Language fallback resolves both source and format together.

## Global currency setting

Admin selects one operating currency (EUR by default, or USD). Staff cannot change it, and tab/guest creation does not accept a currency override. New tabs snapshot the current setting inside their creation transaction; there is no currency choice per user or tab. The catalog's existing EUR/USD prices determine the amount charged. Changing the setting affects new tabs only: existing open/settled tabs, payment snapshots, guest pages and historical reports keep their original denomination. No currency conversion or relabelling of recorded amounts is performed. Settle open tabs before switching when a single operational currency is required. Historical reports may therefore still contain both currencies; they remain separate and are not combined without conversion.

Guest bon email is available only after the tab is fully settled and closed, while its private link remains valid, and only when outbound mail is configured and enabled. Open tabs and partially paid tabs cannot email a bon, including through a direct request. Successful delivery immediately revokes guest access; failed delivery preserves it.
