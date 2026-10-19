# The Royal Bite — advanced animated website v3

## What is ready
- Responsive, animated Home, Our Menu, Chef’s Special, Kitty Party, Birthday Party, Celebrations, Gallery, Visit, and Admin page views.
- Complete supplied menu: 137 items with prices and approximate calories; 121 descriptions, with the 16 Chef’s Special descriptions deliberately blank.
- Search, category filters, illustrative menu gallery and Chef’s Special seven-photo collage.
- Original 14-page PDF available through Download menu; optimized images are served locally, without external services.
- New dark-teal / warm-ivory / gold editorial design; photographic hero, animated heading reveals, gentle image parallax, floating accents, a moving brand ribbon, staggered scroll reveals, image zoom and hover interactions.
- Sticky navigation with reading progress, touch-friendly category carousel, back-to-top control, and explicit Pause / Resume animations. System reduced-motion preferences are respected.
- Dish detail dialogs show source descriptions and prices; hearts save a browser-local wish list. This is not an order, reservation or customer account.
- Photo lightbox includes previous/next controls, keyboard arrows, Escape and focus handling. Static illustrative menu images remain separate from real event uploads.
- Password authentication verified only on the Python server; scrypt-hashed password, HTTP-only sessions, CSRF checks, login throttling.
- Admin uploads and deletes photos; photos persist in SQLite + files, appear on the selected event page and in Gallery.
- Re-encodes real image pixels to WebP, limits size, strips metadata, escapes captions and generates random filenames.

## See the design now
Open `The_Royal_Bite_Advanced.html` (included at the ZIP root and delivered separately) in a browser. It embeds images and the original PDF and can be about 23 MB. The ZIP is the hosted version; run its server to serve the local images and PDF correctly. This offline preview has working page navigation and animations. **Uploads/login are deliberately disabled offline.** No local-storage password or fake authentication.

## Run locally (Python 3.11+)
```
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python setup_admin.py
python server.py
```
Open http://localhost:8000. Admin: http://localhost:8000/admin.
Enter the requested password in the setup prompt; it is not embedded in the public website. The password spelling previously interpreted in the conversation was `TheRoyalBite55`; confirm that spelling before setup. A stronger unique password is recommended because this one has been shared in chat.

## Public deployment — not yet done
Hosting/domain credentials were not supplied. This package does not create a public URL.
Use a Python host or VM with persistent disk and an HTTPS reverse proxy (e.g. Caddy/nginx). Do not deploy only the HTML if you need uploads.
1. Set `DATA_DIR` to a persistent, private folder outside any public static directory. Back up the entire folder (database, credential hash, uploads) together.
2. Run password setup with the same `DATA_DIR` and restart the server after password changes.
3. Set `PUBLIC_ORIGIN=https://YOUR-REAL-DOMAIN` exactly (no trailing slash/path), `HOST=127.0.0.1`, `PORT=8000`. The HTTPS origin activates Secure session cookies. Forward requests through the reverse proxy without rewriting the Origin header. Do not trust arbitrary forwarded headers.
4. Run `server.py` under a service supervisor. For this small-business build use one process; sessions and rate limiting are in-memory and restart on process restart. Scaling to multiple processes requires shared session/rate-limit storage.
5. Limit request size to ~14 MB at the proxy, configure TLS, HTTPS redirect, request timeouts, upload rate limits, IP-based login throttling at the edge, and backups. The built-in per-IP limiter sees the proxy IP behind a reverse proxy; edge throttling is necessary for a public deployment.
6. Verify public pages, rejected wrong passwords, persistent uploads, deletion, mobile layout, cookie flags and backup restore on your host before launch. A local functional test is not a production security audit.
7. Never publish the `data` directory, credential file, backups or server source as static files.

## Supplied content and remaining gaps
The supplied `The_Royal_Bite_Menu_Chef_Seven_Photo_Collage.pdf` is included unchanged as `site/menu.pdf`. Dish names, price text, descriptions and approximate calories are extracted from its pages 3–14. Menu JSON and UTF-8 CSV are included for developer use. Two prices for Veg Manchurian are preserved without guessing which variant maps to which price. Unusual source spellings and prices have not been silently corrected.

Fourteen optimized menu images, including the seven-photo Chef’s Special collage, are extracted from the PDF. The PDF says the food imagery is illustrative; the site labels it accordingly and does not present it as real celebration photos. Static menu images do not appear in event-only galleries and cannot be deleted through the event-upload admin panel. No real event photos were supplied.

Before launch, restaurant staff should confirm descriptions, allergens, calories, current prices, and tax treatment. Images are illustrative, not a promise of exact presentation or portion size.

Still needed: full address, Maps link, phone/WhatsApp, opening hours, email/social links, domain, reservations/delivery preferences and links, tax policy, event capacity, rates and packages. Visit page marks unavailable details honestly. No booking form, payment or ordering integration is included.

## Publishing photographs
Sign in → choose the event page → enter a descriptive caption and optional date → select JPG/PNG/WebP under 10 MB → confirm permission → upload. The photo is public immediately; obtain consent before uploading, particularly for children. Deletion removes the live file, but backup copies follow your retention policy.

## Accessibility
Keyboard focus, labelled forms, mobile navigation, reduced motion, semantic sections, image descriptions, an accessible native photo dialog, and no information conveyed solely by animation. Restaurant content is in English per the supplied brief; Hindi UI is not included.
