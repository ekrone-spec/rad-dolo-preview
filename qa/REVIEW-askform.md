# Review: homepage ask form, two-step flow (uncommitted diff to index.html)

Verified by reading the diff and surrounding code; not run in a browser.

## Findings

1. **should-fix** | index.html:857-859, 216-218 | No way back from step 2. Once `.step2` is added, `#askInput` is `display:none` and nothing removes the class. A visitor who wants to fix a typo in the note, or who does not want to give an email, is stuck. The only exit is a reload. Fix: add a small "Back" or "Edit note" control (visible only in step 2) that removes `step2` and focuses `#askInput`. Also handle Escape in `#askEmail` the same way.

2. **should-fix** | index.html:857-859 | Step change is silent to assistive tech. The focused input is hidden, so focus drops to body until the 50ms timeout moves it. `#askReply` (aria-live) is not used for step 2. Fix: before the focus call, set a polite live-region text such as "One more thing: where should Rad reply?". Alternatively put `aria-live` on a visible hint line. Call `emailEl.focus()` synchronously rather than in a 50ms timeout, because iOS Safari may not raise the keyboard for focus outside the user gesture. The class change already forces layout.

3. **should-fix** | index.html:859-860 | Invalid or empty email gives no feedback. The handler does `focus(); return;` and nothing else, so the visitor sees nothing happen. This is a UX dead end, especially on mobile. Fix: show a message in a live region ("That email doesn't look right"), or call `emailEl.reportValidity()` after `setCustomValidity`. `checkValidity()` on an empty type=email is true everywhere including Safari, because the field has no `required`. The `!em` guard covers that correctly, so there is no logic bug there.

4. **should-fix** | index.html:845 (focusAsk), 846 | The "Send Rad a note" and "Email" links (`.ask-open`, lines 611 and 622) call `focusAsk()`, which focuses `#askInput`. In step 2 that input is `display:none`, so the click scrolls to top and focuses nothing. Fix: in `focusAsk`, focus `#askEmail` if the form has `step2`, otherwise `#askInput`.

5. **nit** | index.html:432 (button aria-label), 857 | The button's aria-label is "Send your note to Rad" in step 1, but pressing it does not send. Likewise there is no hint that a second step exists, so a visitor expects the arrow to send. Fix: update the label dynamically ("Next: add your email" in step 1, "Send" in step 2). Optionally change the step-1 placeholder to end with "(then your email)".

6. **nit** | index.html:431 (placeholder), 239-240 | "Where should I reply? Your email…" is about 34 characters. It may truncate at a 375px width next to a 44px button, since the input is `flex:1; min-width:0`. Fix: shorten to "Your email, so I can reply…".

7. **nit** | index.html:862-863 (pre-existing pattern, now more visible) | The "Thank you" overlay and `.sent` are applied before the fetch resolves. On failure the mailto fallback opens a mail client after the thank-you is already shown. Behaviour is unchanged by this diff, but a lost email address now costs more. Acceptable; flag only.

## Checked, no defect

- Cascade: `.ask.step2 #askEmail` (1 id, 2 classes) beats `.ask #askEmail` and `.ask input`. `.ask.sent input,.ask.sent button{visibility:hidden}` still hides the visible input and the button. The `display:none` field is irrelevant. The mobile rule at line 239-240 only touches padding and the button. OK.
- Enter: step 1 advances to step 2 (empty note refocuses `#askInput`). Step 2 Enter submits. OK. Empty note in step 2 cannot occur, because `#askInput` keeps its value while hidden.
- Fetch body: form-name, message, email, page and bot-field are all URL-encoded. All fields exist in the static form (lines 426-432), so Netlify registers them. OK.
- Fallback text includes the reply-to address and the message. OK. The github.io branch uses the same fallback.
- Nothing in the diff touches code outside the form (CSS, markup, handler only).

REVIEW VERDICT: FIX FIRST
