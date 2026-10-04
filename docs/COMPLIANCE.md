# German compliance coverage

Reviewed 3 October 2026. Scope: association, member/public access, alcohol, running tabs and stock planning. This is an implementation assessment, not certification or an exemption ruling. Status is based on actual capabilities, including cash/card payment recording.

## Feature coverage

| Feature | Implemented safeguards | Remaining requirements / operator action |
| --- | --- | --- |
| Orders and corrections | Product/price/time snapshots; cancellation retains original line, timestamp, reason and named-account actor (legacy shared actors retained); cancelled lines excluded from balances, receipts, emails and sales aggregates | No complete operator attribution, protected append-only archive, historical cancellation recovery or certified fiscal signing. Database administrators can alter records. Past deleted lines cannot be reconstructed. |
| Payment recording | Partial/full settlement, duplicate-submission protection, saved monetary snapshots | No certified TSE, DSFinV-K, cash reconciliation, fiscal device notification support or refund ledger. APOS is not ready as a standalone German fiscal register. |
| Guest ordering | Explicit German “Zahlungspflichtig bestellen” / English payment-obligation label; server-side menu prices, stock and tab checks; staff-only cancellation | Final quantity-dependent total should be reviewed immediately before confirmation; other consumer information depends on contract/workflow. Button wording alone does not establish compliance. |
| Alcohol | Staff can mark products as alcohol in Edit product; flagged items hidden from guest menu and rejected on direct guest submission | Staff must classify EVERY alcohol product, including CSV/demo imports, before enabling guest ordering, and verify age before serving. New products default unflagged. CSV sync preserves existing flags; new imported products require manual classification. No automated age verification. |
| Legal/provider information | Public Impressum and privacy pages, linked from footer; sanitised rich text, edited full screen from Admin; separate DE/EN notices with English fallback | Association must supply accurate, complete notices. Blank notices are explicitly shown as missing. English and German example drafts contain placeholders and are loaded only on staff request; they are not automatically published. Translations are independent; absent/empty German text falls back to English. Existing plain notices remain the fallback until edited. Association staff must replace all placeholders and verify actual operations. |
| Photos | Optional upload, metadata stripping, guest removal while link valid, staff removal | Determine and explain lawful basis; handle requests after expiry through staff. Photo removal concerns live data, not old backups. |
| Security | CSRF, password hashing, no-store, no-referrer, HttpOnly/SameSite cookies; optional Secure cookies | Configure HTTPS before real guest use; enable APOS_SECURE_COOKIES=1 behind HTTPS. LAN HTTP remains a testing configuration. No rate limiting or automatic backup scheduling; named roles are now implemented. |
| Guest expiry / email | Link revoked 24 hours after full settlement, or immediately after successful SMTP submission; internal records retained | SMTP acceptance is not delivery proof. Email processor agreements/security and backup retention require operator review. Guest link expiry is not erasure of member or transaction data. |
| Reports / stock planning | Aggregate exports omit member IDs, names and guest codes; cancelled orders excluded | Small groups or identifying product names may permit inference. Aggregates do not replace required source records. UTC reporting days may differ from German business days. EUR/USD values are separate; no fiscal EUR conversion. |

| Non-member guests | Generated pseudonym, permanent unique guest number, separate guest profile list; same private-code, stock, settlement and reporting safeguards | Pseudonymous does not mean anonymous: tabs, photos and observation may identify patrons. Profiles persist until staff archives them; archival removes photos but is not complete identity erasure. Apply the documented retention policy; no automatic guest deletion is implemented. |

## Legal basis and unresolved applicability

- **Cash-register function:** BMF guidance addresses software capable of recording and settling cash payments. APOS currently has that capability. A label such as “not accounting” does not change it. A genuinely separate tab/stock workflow requires architectural changes and assessment of its relationship to the actual settlement system. [BMF cash-register FAQ](https://www.bundesfinanzministerium.de/Content/DE/FAQ/FAQ-steuergerechtigkeit-belegpflicht.html), [§146a AO](https://www.gesetze-im-internet.de/ao_1977/__146a.html).
- **Record integrity:** Tax-relevant original entries must remain ascertainable after changes. Preserving cancellations supports this requirement but is not sufficient for overall audit compliance. [§146 AO](https://www.gesetze-im-internet.de/ao_1977/__146.html).
- **Fiscal receipts:** Required seller, tax, transaction and security fields are absent. The guest URL QR is not a fiscal QR. Electronic fiscal receipts require recipient consent and a standardised format. Existing saved/emailed bons are tab/payment summaries, not compliant fiscal receipts. [§6 KassenSichV](https://www.gesetze-im-internet.de/kassensichv/__6.html).
- **Consumer orders:** Where paid consumer contracts are concluded electronically, the final confirmation must clearly convey payment obligation and show required information immediately before ordering. The precise on-premises QR workflow needs review. [§312j BGB](https://www.gesetze-im-internet.juris.de/bgb/__312j.html).
- **Alcohol:** Public service generally restricts beer/wine to age 16 and other alcohol to 18, subject to the statutory accompanied-young-person exception. Product flags support staff checks; they do not replace them. Venue licensing and local requirements are outside this software assessment. [§9 JuSchG](https://www.gesetze-im-internet.de/juschg/__9.html).
- **Provider information:** Supply association identity, address, representative, contact and applicable registration/identification information. [§5 DDG](https://www.gesetze-im-internet.de/ddg/__5.html).
- **Privacy:** Document purposes, lawful bases, recipients, retention and rights; maintain appropriate security and processor arrangements. Remove personal data when no lawful retention basis remains. No generic template can choose these facts for the association. [Saxon data-protection authority guidance for associations](https://www.datenschutz.sachsen.de/handlungsempfehlungen-vereine.html).
- **Retention:** Categorise source records; AO periods include 10, 8 and 6 years depending on category, with possible extensions. Guest access expiry must not control internal record destruction. APOS currently has no automated legal retention policy. [§147 AO](https://www.gesetze-im-internet.de/ao_1977/__147.html).
- **Association status and tax:** Association/charitable status does not establish blanket exemption for economic activity. Configure tax treatment only after professional assessment; fiscal operation would also need versioned product tax categories. [§64 AO](https://www.gesetze-im-internet.de/ao_1977/__64.html), [§12 UStG](https://www.gesetze-im-internet.de/ustg_1980/__12.html).

## Deployment and next iteration

1. Complete notices in Admin; classify alcohol products; keep guest ordering disabled until the menu/workflow is reviewed.
2. Configure HTTPS, secure cookies and backups. Record a personal-data and accounting retention policy, including backup handling.
3. Have the association's Steuerberater assess APOS's real role in sales/settlement. Choose certified fiscal integration or a genuinely separate tab/stock architecture; do not infer an exemption from intended use.
4. Implement final order-total confirmation, complete operator audit coverage, protected audit export, retention controls and applicable food/allergen information. These are open work, not implemented compliance claims.

Every future feature iteration must reassess this matrix and its legal sources, per AGENTS.md. No blanket “German-law compliant” claim is authorised by this document.

## Rich-text editor security

Saved editor HTML is limited on the server to paragraphs, headings, emphasis, lists, quotes, code and tables. Safe HTTP(S), mailto and relative links are permitted; unsafe URLs, arbitrary attributes, scripts, images and embedded content are removed; text is escaped. Rendering sanitises stored rich HTML again, including legacy plain-text escaping. Editing requires a staff session and CSRF token. Examples are local assets; no external editor/CDN receives notices or guest data. Format controls require JavaScript; browser-based visual interaction has not been verified in this environment.

## Account roles and member import iteration

Named accounts now separate Admin-only administration from Staff POS operations and Member/Guest own-tab access. Server checks cover both new and legacy URLs; account versioning invalidates sessions after changes, and an active last Admin is protected. The migration preserves the existing password as the recovery `admin` account: rotate this formerly shared credential before deploying separate roles. Local maintenance access remains privileged and must be restricted.

Member CSV is additive and imports profile data only, without credentials or roles. Previews contain personal data, expire in 24 hours, are session-bound, and are removed after confirmation or later upload cleanup; backup copies follow the operator's retention policy. Establish a lawful basis and provide notices before bulk import. Disabled accounts and event records are retained, not automatically erased; account-event usernames need retention/access controls too. Private guest codes remain bearer capabilities, including for logged-in members: possession of another person's code is still authority to view that tab. Distribute codes carefully.

Cancellations now store the named account's username; historical shared actors remain. Account creation/updates have actor/time records. Other POS actions are not yet comprehensively attributed or protected against database-level modification. Fiscal integration, receipt completeness, total confirmation, retention automation and other previously identified gaps remain open.

## Markdown notices

Notices support Markdown source with an Admin-only, CSRF-protected server preview and the existing per-language English fallback. Markdown is rendered locally with raw HTML disabled, then passed through the same allowlist as visual-editor content. Links are restricted to safe schemes and remote images/embeds are removed, so previews do not add external image tracking. Source remains stored as Markdown unless actual visual edits replace it; legacy plain notices now interpret Markdown and existing rich HTML remains supported. Formatting does not validate legal content or make placeholder examples compliant. The association must review the final rendered notice in each language.

## Global currency setting

Admin selects one operating currency (EUR by default, or USD). Staff cannot change it, and tab/guest creation does not accept a currency override. New tabs snapshot the current setting inside their creation transaction; there is no currency choice per user or tab. The catalog's existing EUR/USD prices determine the amount charged. Changing the setting affects new tabs only: existing open/settled tabs, payment snapshots, guest pages and historical reports keep their original denomination. No currency conversion or relabelling of recorded amounts is performed. Settle open tabs before switching when a single operational currency is required. Historical reports may therefore still contain both currencies; they remain separate and are not combined without conversion.

## Touchscreen counter redesign

This iteration changes presentation and staff interaction only. Product amounts still come from the server-side catalog and tab currency; cash/card selection records a payment through the existing transaction and idempotency checks. Partial and full shortcuts do not automatically charge a patron. Cancellation still requires a reason and preserves original records; paid positions remain protected. Alcohol labels remind staff to check age, and guest alcohol restrictions remain unchanged. The redesign does not resolve fiscal certification, consumer final-order confirmation, receipt completeness or retention gaps described above.

Search runs locally over information already authorised for that page, with no remote analytics or new personal-data service. Private codes and QR links appear in an expandable staff section; collapsing it is visual organisation, not an access-control boundary. Guest access expiry, successful-mail revocation and Admin/Staff/Member/Guest server permissions are unchanged. Receipts remain readable when printed using a separate light print style.

## Settled-tab email restriction

Guest email now requires a fully settled, closed tab as well as a valid private link and configured/enabled SMTP account. The server checks closure again inside the email reservation transaction, and open or partially paid tabs cannot submit an email request. This prevents mailing an unfinished bon and prematurely revoking guest access during ordering. Successful delivery still revokes only guest access; retained staff records remain intact. Failed delivery preserves access until the usual expiry. No new personal data, legal requirement, fiscal certification or alcohol-service behaviour is introduced; previously documented receipt, retention and fiscal limitations remain. Regression coverage checks open, partially paid and closed tabs, direct requests, failure recovery and successful revocation.
