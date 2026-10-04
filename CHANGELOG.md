# Changelog

## 0.6

- Guest bon email is available only after full settlement and closure, with enabled outbound mail and a valid guest link.
- Saved profile photos appear on bons, staff payment records, email and the printable attachment.
- Successful email clears non-member guest photos; expired guest photos are cleared automatically. Member photos remain. Delivered/downloaded copies retain their images.
- Active non-member guests can edit their displayed name through a valid patron link without changing their number, access code or roles.
- Admin can set a tagline displayed in app headers, page titles and bons.
- Staff receipts retain the patron link, private code and QR while guest access is valid, including after full settlement.
- Regression and browser coverage expanded; privacy, retention and operating documentation updated.

Expiry cleanup runs every 30 seconds in the supported server and catches up on requests/restart. Another valid guest tab preserves the shared profile photo until its remaining link ends. Existing fiscal certification and compliance limitations remain documented.

## 0.5

First published persistent APOS release implementing the version-one specification.

- Running tabs, partial/full cash and card recording, saved receipts and anonymised sales reports.
- Dark touchscreen counter with product search, quantity controls and adjacent settlement.
- German and English, with an Admin-controlled EUR/USD operating currency.
- Named accounts and roles; Admin-only catalog, members, CSV imports and configuration.
- Four-word Diceware guest access and QR codes, profile photos and optional guest ordering.
- Configurable outbound mail with guest-access revocation after successful delivery.
- Multilingual legal/privacy notices with fullscreen visual and Markdown editing.
- Traceable cancellations and documented German compliance coverage and remaining gaps.

APOS is not TSE-certified. Review the compliance and operations guides before public use.
