# Counter interface

## Product goal and design decisions

Designed for staff taking orders and settling running tabs on a counter touchscreen or tablet. The user chose a dark interface for pub lighting. Retain Flask/Jinja and local JavaScript, following the frontend-production-shadcn skill's instruction to respect the existing architecture. No frontend framework migration or external font/editor service is introduced.

The plan was established before implementation: a counter for finding/opening member and guest tabs, a menu beside the running order and settlement, and expandable guest access and cancellation history. Reusable Jinja components separate menu tiles, order positions and settlement.

Neutral dark surfaces, thin borders, mint primary actions, readable secondary text, 48px primary controls and visible keyboard focus form the visual system. Product tiles show names and recorded currency prices. Search filters products and open tabs locally. Quantity controls precede product selection. Native forms still work without JavaScript; search and payment shortcuts enhance them. Submission feedback prevents repeated clicks and preserves the selected product's form value.

## Layout and states

Desktop uses a flexible menu and a bounded order/settlement column. Tablet keeps two columns with two product tiles per row. Below 640px the layout stacks; a Settle tab link jumps to payment controls. Long names wrap and administrative tables scroll inside their containers. Receipts print on a white background.

Empty catalogs, empty tabs and empty search results have explanations and relevant next actions. Empty tabs cannot record payment. Partial/full amount shortcuts operate on the same validated payment form. Cash/card have explicit labels, cancellation requires a reason, and payment locks remain enforced. Server error pages retain recovery links. Role restrictions remain server-enforced, with Admin controls visible only to Admins. Form feedback, hover, keyboard focus, reduced-motion support and a skip link cover interaction states.

Pre-implementation review addressed five risks: dark contrast, small touch targets, scattered payment controls, excessive panels, and long names on tablet/phone. Visual inspection subsequently caught and corrected a quantity-label overlap.

## Verification

Run the existing suite with `.venv/bin/python -m unittest discover -s tests -q` (53 tests passed). Check JavaScript with `node --check static/app.js`. Optional browser validation uses `requirements-dev.txt`, `python -m playwright install chromium`, and `.venv/bin/python scripts/browser_smoke.py`.

The browser script creates its own temporary database and local server. It verifies product filtering, quantity changes, real order submission, partial cash payment, full card settlement, JavaScript errors, and absence of horizontal page overflow at 1440, 1024, 768 and 390px. It also checks Admin at tablet/phone sizes. Preview screenshots are written to `/tmp/apos-dark-tablet.png` and `/tmp/apos-dark-mobile.png`.

No physical touchscreen testing or comprehensive accessibility audit has been performed. Very large menus still use search rather than category navigation. The dark theme is currently the default throughout the application.
