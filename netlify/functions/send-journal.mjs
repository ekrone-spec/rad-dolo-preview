// Scheduled function: when a new journal post appears in feed.xml, email it
// to the Buttondown list. Runs daily; no-ops until BUTTONDOWN_API_KEY is set
// (Netlify: Site configuration → Environment variables).
//
// Dedup is stateless: we list existing Buttondown emails and skip any post
// whose URL has already been sent.

export const config = { schedule: "0 15 * * *" }; // daily, 15:00 UTC (~10am Minneapolis)

const API = "https://api.buttondown.email/v1";

export default async function handler() {
  const key = process.env.BUTTONDOWN_API_KEY;
  if (!key) {
    console.log("BUTTONDOWN_API_KEY not set; skipping.");
    return new Response("skipped", { status: 200 });
  }

  // Read our own feed from the deployed site
  const siteUrl = process.env.URL || "https://www.raddolo.com";
  const feedRes = await fetch(`${siteUrl}/feed.xml`);
  if (!feedRes.ok) return new Response("feed unavailable", { status: 200 });
  const xml = await feedRes.text();

  const items = [...xml.matchAll(/<item>([\s\S]*?)<\/item>/g)].map((m) => {
    const block = m[1];
    const pick = (tag) =>
      (block.match(new RegExp(`<${tag}>([\\s\\S]*?)</${tag}>`)) || [])[1]?.trim() || "";
    return { title: pick("title"), link: pick("link"), desc: pick("description") };
  });
  if (!items.length) return new Response("no items", { status: 200 });

  const auth = { Authorization: `Token ${key}`, "Content-Type": "application/json" };

  // What has already been sent?
  const sentRes = await fetch(`${API}/emails`, { headers: auth });
  const sentBodies = sentRes.ok
    ? JSON.stringify((await sentRes.json()).results || [])
    : "";

  // Send the newest unsent post (one per run keeps sends gentle)
  for (const item of items) {
    if (!item.link || sentBodies.includes(item.link)) continue;
    const body = [
      item.desc,
      "",
      `[Read the full note on raddolo.com →](${item.link})`,
      "",
      "—Rad",
    ].join("\n");
    // JOURNAL_EMAIL_MODE=send → emails go out automatically.
    // Anything else (default) → created as a DRAFT in Buttondown for review.
    const status = process.env.JOURNAL_EMAIL_MODE === "send" ? "about_to_send" : "draft";
    const res = await fetch(`${API}/emails`, {
      method: "POST",
      headers: auth,
      body: JSON.stringify({ subject: item.title, body, status }),
    });
    console.log(`sent "${item.title}":`, res.status);
    break;
  }
  return new Response("ok", { status: 200 });
}
