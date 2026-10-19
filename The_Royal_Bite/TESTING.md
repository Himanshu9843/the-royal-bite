# Advanced v3 — local verification

- Nine routes at 1440 px and 390 px: Home, Menu, Chef’s Special, Kitty Party, Birthday Party, Celebrations, Gallery, Visit and Admin. No horizontal viewport overflow or uncaught JS errors.
- All 137 items and every category remain available; 16 Chef’s Specials have no invented descriptions. Dual prices are preserved.
- Search, category/reset/saved filters, detail dialog, favourites persisted across reload, carousel controls, mobile navigation, gallery filters, photo arrows and keyboard controls verified.
- Offline original-menu PDF download matched the supplied PDF’s SHA-256 hash.
- Motion pause/resume and reduced-motion handling verified. Animation includes heading/photograph entry, scrolling ribbon, staggered reveals, image parallax and hover transitions.
- All routes and key dialog, empty, mobile navigation, login error and upload success states visually inspected.
- Admin API: wrong passwords, unauthenticated writes, foreign Origin, missing CSRF, invalid images and missing consent rejected. Upload, persistence after restart, delete and logout verified.
- Browser admin tests passed on desktop and mobile. Test credentials and uploads are excluded from the ZIP.

These are local checks, not a production penetration test or a claim of live deployment. HTTPS hosting, password setup, verified contact details and a deployment smoke test remain necessary.
