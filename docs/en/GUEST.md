# APOS guest and member guide

[Documentation home](../README.md) · [Deutsch](../de/GUEST.md) · [Staff guide](STAFF.md)

For patrons viewing their own running tab in APOS 0.6. You do not need a staff account. Available functions depend on the club's settings and whether your tab is still open.

## Open your tab

Ask staff to open your tab and show its QR code. Scan it using your phone's camera, or open the private link they give you. Alternatively, open your club's APOS address followed by `/view` and enter the private viewing code. New codes consist of four words; spaces and uppercase/lowercase variations are accepted.

Use the club's actual address, not the public APOS project website. You may need the club's Wi-Fi. If you cannot connect, ask staff to check the network and server.

Keep the link/code private. Anyone with it can view your tab and use the guest functions enabled for it. Avoid sharing screenshots containing the code.

### If you have a Member or Guest password account

Sign in with the username and password given by the administrator. APOS opens your linked profile's latest available tab. A profile code is not a login password. A guest tab/QR code does not automatically create a password account. Account access does not extend a tab's expiry or restore access after emailing. Ask staff if no available tab exists.

Use **Personal menu → Language → English → Apply** to select English. Signed-in account holders can use **Personal menu → Sign out** when finished. With code-only access, close the page and protect the private link; closing it does not revoke the link.

## Read the amounts

- **Total ordered**: the value of current, non-cancelled orders.
- **Paid so far**: payments staff have recorded.
- **Outstanding balance**: the amount still to pay.

Each position shows the product, quantity, unit price, subtotal and order time in UTC. Refresh the page to see the latest changes; it does not update automatically. An earlier printed payment receipt may show an earlier balance.

If an order or payment looks wrong, ask staff. You cannot remove positions, change prices, record payment or reopen a settled tab.

## Place an order, when available

1. Find **Add to your bon**. If it is missing, ordering is disabled, your tab is settled, or emailing is in progress; ask staff instead.
2. Select an available product and a whole-number quantity from 1 to 999.
3. Check the selected product, unit price, quantity and resulting cost before selecting **Order with obligation to pay**. Submitting adds a paid obligation to your tab; it does not charge a card.
4. Wait for confirmation and check the new position before submitting another order.

Only active, in-stock, non-alcohol products appear. Ask staff about alcohol and food/allergen information. Availability may change while the page is open; if rejected, refresh and choose again. Ask staff promptly about a mistaken order. Guest ordering does not permit cancellation, and staff cannot cancel positions after a payment.

## Name and optional photo

For active non-member guest profiles, **Your guest name** lets you change the generated display name: enter 1–120 characters on one line and choose **Save name**. This does not change your guest number or private code. Member names must be changed by Admin.

If the photo section is available, upload a JPEG, PNG or WebP file, or use the camera option on a supported phone, then choose **Save photo**. Maximum input: 3 MiB and 20 megapixels. APOS crops and converts it to a 256×256 JPEG without image metadata. No photo is required; initials are used instead.

To remove it, select **Remove profile photo** and save without also uploading a new image. Your photo can appear on staff screens, printed/saved bons and emailed copies. Those copies cannot be remotely erased by removing your photo. Read your club's **Privacy notice** and contact the club for data questions after access ends.

## Pay your tab

Pay staff in cash or through their separate card terminal. APOS itself does not process cards. Partial payment keeps the tab open; full payment closes it. Refresh and check the recorded amount. Ask staff for a printed payment summary if needed. APOS's summary is not a certified fiscal receipt.

Private access normally lasts while open and for **24 hours after full settlement**. The displayed expiry is in UTC. Cancelled tabs lose access immediately. There is no guest extension control.

## Email a settled bon

This option appears only after the tab is fully paid and closed, while your link is still valid and the club has enabled outgoing email.

1. Review your bon and the recipient address carefully.
2. If you do not want your current profile photo included, remove it before sending.
3. Enter your email address and choose **Email bon and end guest access** once.
4. Wait for the confirmation page. Check your inbox and spam folder for the message and printable `bon.html` attachment.

When the mail server accepts the message, your private link immediately stops working, even if email delivery is delayed or the address was wrong. You cannot resend through the ended link. Mail-server acceptance does not guarantee inbox delivery. If APOS reports a send failure, the link remains available until its normal expiry; retry or ask staff.

Successful emailing clears a non-member guest's live profile photo. Otherwise non-member guest photos are cleared when no valid tab link remains, on the running server's cleanup cycle. Member photos are retained. Financial records remain with staff, and previously saved/emailed copies and backups are not erased by guest expiry or photo cleanup.

## Need help?

| What you see | What to do |
| --- | --- |
| Link unavailable or expired | Check the code; ask staff whether 24 hours passed, the tab was cancelled, or the bon was emailed. |
| No order form/products | Ask staff; guest ordering is optional and alcohol is staff-only. |
| Old amounts | Refresh. If still wrong, show staff the position or payment in question. |
| Photo rejected | Use a supported file type within the size/resolution limits; choose one input only. |
| Form expired | Reload; check whether your last action succeeded before trying again. |
| Email missing after confirmation | Check spam and ask staff. The link is already revoked after mail-server acceptance. |
