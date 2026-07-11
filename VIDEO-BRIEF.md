# Rad Dolo — Hero Video Brief: "The Snap"

One continuous-feeling shot: Rad rises from a chair in an infinite white space,
snaps her fingers, and her outfit changes on every snap — until she's close to
camera and snaps one last time *for the visitor*, revealing the ask box.

## The spec

| | |
|---|---|
| Total length | **12–14 seconds** (hero videos over ~15s lose people; under 10s feels rushed) |
| Looks | **5 outfits** (rise in look 1, snap into 2–4, close-up in 5) |
| Snaps | **5** — four in-video outfit changes + one final snap at the lens |
| Format | 4K master → web: 1080p **WebM (AV1/VP9) + MP4 fallback, muted, ≤ 4 MB**, poster frame |
| Camera | Locked-off wide, slow dolly-in only on the final beat. Never cut angles — the snap is the only "edit" |
| Set | White cyclorama (or clean white wall + white floor), soft even light, faint contact shadow so she doesn't float |
| Sound | Master WITH snap sounds for TikTok/Reels; site version muted (browsers require it) — the site plays a synthesized snap on the visitor's final click instead |

### Timeline
- **0:00–0:03** — Look 1: she rises from the chair, walks a step forward
- **0:03 / 0:05 / 0:07** — snap → Look 2, snap → Look 3, snap → Look 4 (each ~2s hold: settle, small pose, eye contact)
- **0:07–0:11** — she walks toward camera (or slow dolly-in), Look 5 lands on a snap mid-walk
- **0:11–0:13** — close-up, she raises her hand, fingers ready… **freeze**. (The site holds this frame; the visitor's click triggers the final "snap" + the ask box.)

### The five looks (suggest pulling exact outfits from her photos)
1. **Off-duty** — denim, white tee: "real Rad," the friend who lends you clothes
2. **Tailored** — camel blazer: the LA-fashion résumé
3. **Evening** — black slip dress / suiting: date night, events
4. **Street** — utility, sneakers: everyday elevated
5. **The statement** — one unforgettable piece (the site's accent is oxblood — a red look here ties the video to the design)

## Tool recommendation

**Decision (Jul 2026): AI-generated now, possible real shoot later.**
Rad has given the green light on her likeness — keep a written/text record of
that consent, and disclose AI-generated content when posting to TikTok/Reels
(platform policy requires the label).

**Primary: Google Veo 3.1 inside Flow** (Google AI Pro plan, ~$20/mo, uses
Gemini login — fits the "she's already on Google" setup).
Best-in-class people/fabric motion, takes **reference images** (her face + the
exact outfits from your photos), native audio for the snap sounds, and Flow's
"ingredients/frames to video" fits the segment pipeline below. Runner-up:
**Kling 2.5 with Elements** (strong multi-image character consistency, 10s clips).
For the segment stills, use **Gemini image editing (Nano Banana Pro)** — it's the
best at "same person, same framing, different outfit."

Voice: her real voice beats any clone — have her read the script into her phone
in a quiet room for the social cut. (ElevenLabs clone from your examples is the
fallback if she can't record.)

## Day-of runbook (checklist form)

1. **Gather references from her content** (30 min)
   - 2–3 clear photos of Rad: front-facing, full body if possible, even light,
     hair how she'd wear it in the video. These anchor her identity in every prompt.
   - 5 outfit references — screenshots from her IG/TikTok/LTK are fine. Favor
     outfits she's actually worn on camera (the model matches real drape better).
   - Crop each image tight and clean; name them `rad-face-1.jpg`, `outfit-1-denim.jpg`, etc.
2. **Generate the 6 anchor stills in Gemini** (~1 hr) — the 5 standing stills
   (prompt below) **plus one seated still** (Look 1 in a minimal white chair) for
   the opening clip. Consistency trick: generate Look 1 first, then edit *that
   result* for each next look — "same woman, same pose, same framing and camera
   distance, replace her outfit with the one in the attached photo." Chaining
   edits keeps framing and identity locked. Look 5 is the exception: reframe
   waist-up, closer.
   - Reject any still where the face drifts. It's cheaper to fix identity here
     than in video.
3. **Animate in Flow / Veo 3.1** (~1–2 hr): one clip per still, ~4s each, using
   the clip prompts below. Generate 2–3 takes per clip and keep the one where
   (a) the snap is crisp, (b) fingers have five, (c) the background stays pure
   white. Hands are the #1 failure mode — re-roll, don't settle.
4. **Cut in CapCut** (~1 hr): sequence clips 1→5, trim so the outgoing frame of
   each clip is the exact snap and the incoming frame is the next look settling.
   Match white levels across clips (white point tool) so the void doesn't flicker.
   Add snap SFX + her recorded VO on the social cut.
5. **Export three files**:
   - `rad-hero.webm` — 1080p, muted, ≤4 MB, ends frozen on the raised hand
   - `rad-hero.mp4` — same, H.264 fallback
   - `rad-hero-poster.jpg` — the freeze frame
   - (social) 9:16 vertical cut with audio for TikTok/Reels/LTK
6. **Budget expectation**: one afternoon, one Google AI Pro sub, roughly 25–40
   generations across stills and takes.

## The reliable pipeline (don't one-shot it)

No generator will reliably do 4 instant outfit swaps in one prompt. The pro
move is the same as the real-shoot trick: **generate one segment per look with
identical framing, then hard-cut on the snap frames.**

**Step 0 — The character master (Gemini / Nano Banana Pro).** Attach 2–3 clear
reference photos of Rad (front-facing, even light, video-day hair) and generate
the identity anchor every other image chains from:

> Create a photorealistic full-body editorial photograph of this exact woman —
> same face, same skin tone, same hair, same body proportions as in the attached
> photos. Do not idealize or alter her features.
>
> She stands centered in an infinite pure-white studio: seamless white cyclorama
> background with no walls, corners, or horizon line, soft even diffused
> lighting, and a faint natural contact shadow under her feet so she doesn't
> float. She wears a casual off-duty outfit: relaxed denim and a white tee. Her
> right hand is raised at chest height, fingers poised mid-snap. Her expression
> is confident and warm — direct eye contact with the camera, a hint of a
> knowing smile.
>
> Shot on a 35mm lens at eye level, camera roughly 4 meters away, full body in
> frame with generous white space above and beside her. Fashion editorial
> photography, crisp focus, true-to-life color. Landscape 16:9.

Generate 3–4 candidates; keep the one her friends would recognize instantly
(face, build, posture, five-fingered snap hand). If likeness is off, improve the
reference photo rather than the prompt. All later images must be *edits of this
approved master* — never fresh prompts — or identity drifts between clips.

**Step 1 — Five stills (Gemini / Nano Banana Pro).** Edit the master, one look
at a time (outfit reference attached):

> Full-body editorial photo of this exact woman wearing the outfit from the
> second image, standing centered in an infinite pure-white studio (white
> cyclorama, soft even lighting, faint natural contact shadow under her feet).
> Right hand raised at chest height, fingers mid-snap. Confident, warm,
> slight smile. Shot on 35mm, fashion editorial, photorealistic. Same camera
> distance and height as the previous image.

(Looks 1–4: full body, identical framing. Look 5: reframe waist-up, closer.)

**Step 2 — Animate each still (Veo 3.1 image-to-video, ~4s per segment).**

> Clip 1 (from a seated still): She rises smoothly from a minimal chair in a
> pure-white infinite studio and takes one step toward camera, then raises her
> hand and snaps her fingers. Locked-off camera, no camera movement, soft even
> light, photorealistic fabric motion, white seamless background stays pure white.

> Clips 2–4 (from each standing still): Her snapped hand lowers as she settles
> into a relaxed confident pose — small weight shift, fabric settling, direct
> eye contact with a hint of a smile — then she raises her hand and snaps again.
> Locked-off camera, no camera movement, pure-white seamless background,
> soft editorial light, photorealistic.

> Clip 5 (from the waist-up still): Slow dolly-in as she walks two steps toward
> the lens, stops close, looks straight into camera, raises her hand with
> fingers poised to snap — and holds. Shallow depth of field, pure-white
> background, cinematic, photorealistic.

**Step 3 — Cut on the snaps** (CapCut/Premiere): trim each clip so the outgoing
frame is the exact snap and the incoming frame is the next look's settle. The
instant swap *is* the cut. Export the master with snap SFX; export the site
version muted, ending frozen on the raised hand.

## Script (Rad's voice — for the social/VO cut, ~13s)

> My friends call me Rad — you should too.
> LA taught me fashion. Minneapolis is home.
> Here's what I know: your energy introduces you before you ever say a word.
> So… tell me about your closet.

## On-screen words (the muted site cut, synced to snaps)

| Beat | Text |
|---|---|
| Rise | HEY — I'M **RAD.** (chunky white grotesque caps, same treatment as her IG photo overlays) |
| Snap 1 | Your energy |
| Snap 2 | introduces you |
| Snap 3 | before you ever |
| Snap 4 (close) | say a *word.* |
| Final snap (visitor's click) | → "Say the word." + **Tell me about your closet…** input |

## Site wiring — DONE (Jul 2026)

`YOUR ENERGY.mp4` (6.76s, 1080p, white background) is wired into `index.html`,
full-bleed with `mix-blend-mode:multiply` melting the white into the page.
Snap timestamps detected from the audio track: **0.49 / 1.51 / 2.50 / 3.43 /
5.03s**. The first four drive the word swaps ("Your energy → introduces you →
before you ever → say a word."); the final snap at 5.03s turns the same text
element into "Say the word." and reveals the ask box. On-screen words are HTML
overlays — **keep every future video cut clean, no burned-in text**.

If a new cut replaces Snap.m4v, update `SNAPS` and `FREEZE` in the script
(timestamps in seconds). For launch, also export a WebM + poster frame and
compress to ≤4 MB.
