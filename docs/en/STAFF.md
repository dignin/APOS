# APOS staff guide

[Documentation home](../README.md) · [Deutsch](../de/STAFF.md) · [Guest guide](GUEST.md) · [Administrator guide](ADMIN.md)

For accounts with the **Staff** or **Admin** role. Based on APOS 0.6. APOS records payments; collect money separately. It does not process cards, issue certified fiscal receipts or support refunds/payment reversal. Follow your association's approved operating procedure and [documented limitations](../COMPLIANCE.md).

## 1. Start your shift

1. Open the APOS address supplied by your administrator. The public project website is documentation, not your club's POS.
2. Sign in with your individual username and password. A member code or private guest viewing code is not a staff login.
3. Open **Personal menu → Language**, select **English**, then **Apply** if needed.
4. Check the operating currency on **Open tabs**. Ask an Admin to correct it before opening new tabs; existing tabs keep their original currency.
5. Confirm the product menu is ready and a patron phone can open a sample guest link. Report unavailable products to an Admin; Staff cannot change the catalog.

Staff can open/resume tabs, create non-member guests, add/cancel eligible order positions, record payments, and view receipts/reports. Accounts, profiles, product management and settings require Admin.

## 2. Open the right tab

**Member:** on **Open tabs**, use **Find member** to search by name or member code. Select the correct member, then **Open tab**. If that member already has an open tab, APOS resumes it. Ask an Admin to add a missing member.

**Non-member:** select **Add guest**. APOS immediately creates a profile with a generated name, a permanent unique guest number and a new tab. Remember the number: names can repeat or change. No real name is required. This does not create a password account.

**Existing tab:** use **Find a tab** and select its card. Check the name, member code or guest number and currency before adding orders. The card's amount is the order total, not necessarily the amount still due; check **Outstanding balance** inside the tab.

## 3. Take an order

1. Open the patron's tab.
2. Use **Find a product** if needed. Set the quantity, then tap the product tile to add it. Quantities must be whole numbers from 1 to 999.
3. Check the running order and **Total ordered**, **Paid so far**, and **Outstanding balance**.
4. Verify age before serving alcohol. Product flags are reminders, not automated age checks. Follow the association's food/allergen and service procedures.

Only active, in-stock catalog products can be ordered. If a product disappears or a submission is rejected, refresh and ask an Admin to check availability. Editing a catalog price later does not change positions already ordered.

### Correct a mistake

Before any payment, expand **Remove**, enter a meaningful **Cancellation reason**, and select **Cancel position**. APOS retains the original position and cancellation record. Cancelled positions no longer count toward the balance.

After the first payment, positions cannot be cancelled, even when the tab is still open. You may add further orders. For an incorrect recorded payment or a correction after payment, stop and involve the administrator under the association's reconciliation procedure; there is no refund or payment reversal action. Do not delete or edit database records to force the total.

Use **Cancel empty tab** only for a tab with no uncancelled positions. Its guest access ends immediately. To abandon an unpaid non-empty tab, cancel each position with a reason first.

## 4. Give the patron private access

Expand **Patron access** on the tab. Let the patron scan the QR code, or give them the private link/code. At your club's `/view` page they can also type the code; new four-word codes accept spaces and letter-case differences.

Anyone holding the code can access the tab and use enabled guest actions. Share it only with the correct patron, including on printed receipts. Guest access works while open and for 24 hours after full settlement, unless ended earlier by successful emailing or cancellation. Collapsing the QR section only hides it visually.

Guests refresh their page to see new orders/payments. Optional guest ordering is controlled by Admin. Guests cannot cancel positions or record payments. Alcohol orders go through staff.

## 5. Collect and record payment

1. Verify the patron and **Outstanding balance**.
2. Collect cash or complete payment on the separate card terminal.
3. In **Settlement**, choose **Cash** or **Card** (external terminal) to match the collected payment.
4. Enter the amount actually collected. Use **Full balance** for the entire outstanding amount, or the partial-payment control for a smaller amount. Check the amount field before submitting.
5. Select **Record payment** and wait for the receipt page. Check its amount, method and remaining balance.

Example: a €18.00 tab receives €10.00. Record €10.00 once; €8.00 remains and the tab stays open. After receiving the remaining €8.00, record it. Full settlement closes the tab and starts the 24-hour guest access period.

An amount above the balance is rejected; record the amount applied to the tab, not cash tendered before giving change. Full-balance/partial shortcuts do not themselves collect money. Do not collect again if a page times out: check **Receipts** and the tab first. APOS protects repeat submission of the same payment form, but a fresh form is a new payment request.

## 6. Receipts and end of shift

Open **Receipts** to find saved payment records. Use the browser's Print command to print or save a receipt as PDF. Each payment receipt reflects the order and balance at that payment, so an earlier partial-payment receipt can differ from a later tab. A current profile photo may appear; take care with printed copies. A receipt may show a still-valid private QR/link. These are payment summaries, not certified fiscal receipts.

In **Reports**, choose **From (UTC)** and **Through (UTC)**, then **Show report** or **Download CSV**. Both selected calendar dates are included. Order totals include unpaid orders and exclude cancellations. Payment totals count payments recorded in the period, including partial payments; EUR and USD stay separate. UTC dates can differ from your local business day. CSV money columns ending in `_cents` are integer cents. Exports omit member names, tab IDs and viewing codes, but small groups/product names may still allow inference.

At handover, identify open balances and unresolved errors, request a backup from the responsible operator, and use **Personal menu → Sign out**. Do not shut down the computer while guest access is still required.

## Problems during service

| Problem | What to do |
| --- | --- |
| No matching member/tab | Clear the search; verify the member code or guest number. Ask Admin about missing profiles. |
| Product unavailable | Refresh; ask Admin to check both active and in-stock flags. |
| Session/form expired | Sign in again if required, reload, then check whether the previous action succeeded before repeating it. |
| Phone cannot open QR | Ask Admin to check the guest-facing address, network, HTTPS and running server. Localhost on a phone points to the phone itself. |
| Link ended | Check settlement/expiry and whether the bon was emailed. Staff records remain available. |
| Payment recorded incorrectly | Preserve the records and escalate; APOS has no reversal/refund workflow. |
| Disk/database error | Stop recording further payments and contact the operator. Do not delete the database. |
