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
