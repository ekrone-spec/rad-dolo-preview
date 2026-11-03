# NOTES (verbatim facts for later steps)

- 2026-11-03 Inquiry form had no `email` field. Netlify docs: replies to a form
  notification go to formresponses@netlify.com unless the form has a field named
  `email`, which sets Reply-To. Fixed: two-step ask box (message, then #askEmail
  name="email"), hint line #askHint, Esc returns to step 1, native email
  validation. Commit: "Inquiry form: collect the sender's email so Rad can reply".
- Netlify site id 951c6583-4bb2-4cfe-b4ff-1777bd4ad420. Inquiry form id
  6acfc006097c2b8bd687c330. Notification hook 6acfc91b65b1c307b834d71b ->
  dolo.radmila@gmail.com. No Netlify token on file.
- Revert path for the form change: `git revert <that commit>` then push; the
  Netlify form keeps accepting the old field set, nothing else depends on it.
- 2026-11-03 Behold outage: feeds.behold.so JSON fine (newest post 2026-09-26, reel DdwdAhBu5m9) but behold.pictures (their media CDN) returns 502 for every size, so the widget renders nothing (verified on a bare page with only their embed). cdninstagram URLs in the feed are signed and return 403 outside the widget.
- 2026-11-03 Instagram token expired: latest-reel trace "refresh failed: 400", "media fetch: 400"; cache age 4142256s (last call Sep 16). Fix at source: netlify/functions/refresh-reel.mjs runs Mondays 09:00 UTC and calls latest-reel. Renewal needs a Generate-token click with Rad logged in (Meta app "Rad Dolo Website", IG app id 1783214602814239).
- 2026-11-03 PARKED until Erik is with Rad (different countries now): (a) Cloudflare migration (plan in chat Oct 4 + Nov 3; needs CLOUDFLARE_API_TOKEN, BUTTONDOWN_API_KEY, NETLIFY_TOKEN in ~/raddolo-secrets.env, GoDaddy nameserver change at the end); (b) new Instagram token (Meta app Generate token with Rad logged in -> Netlify env INSTAGRAM_ACCESS_TOKEN; the weekly refresh-reel function then keeps it alive); (c) Behold: dashboard shows no source/feed, media CDN behold.pictures 502 -> support ticket text in chat. Reel slot is empty meanwhile. Live and fine: one-field inquiry form with red in-box email notice, notifications to Rad with Reply-To.
