// Scheduled: when a journal post appears in feed.xml that has never been
// emailed, build a branded email from the live article page and create it in
// Buttondown. Default is DRAFT mode (review in the dashboard, click send);
// set JOURNAL_EMAIL_MODE=send to fully automate.
//
// The email mirrors the site: serif wordmark, category eyebrow, the full
// article body restyled with inline CSS (email clients ignore stylesheets),
// a "Read on raddolo.com" button, and site / Instagram / TikTok links.

export const config = { schedule: "0 15 * * *" }; // daily, 15:00 UTC (~10am Minneapolis)

const API = "https://api.buttondown.email/v1";
const SITE = "https://www.raddolo.com";
const IG = "https://www.instagram.com/raddydolo";
const TT = "https://www.tiktok.com/@raddydolo";

const P = 'style="font-family:Georgia,\'Times New Roman\',serif;font-size:16px;line-height:1.65;color:#333333;margin:0 0 16px;"';
const LEAD = 'style="font-family:Georgia,\'Times New Roman\',serif;font-size:18px;line-height:1.6;color:#333333;margin:0 0 18px;"';
const H2 = 'style="font-family:Georgia,\'Times New Roman\',serif;font-size:20px;letter-spacing:1px;text-transform:uppercase;color:#141414;margin:26px 0 10px;"';
const UL = 'style="margin:0 0 16px;padding:0 0 0 20px;"';
const LI = 'style="font-family:Georgia,\'Times New Roman\',serif;font-size:16px;line-height:1.6;color:#333333;margin:0 0 8px;"';
const LBL = "font-family:Arial,Helvetica,sans-serif;letter-spacing:2px;text-transform:uppercase;color:#6e6e6e;";

function buildEmail(title, meta, proseHtml, link) {
  const body = proseHtml
    .replace(/<p class="lead">/g, `<p ${LEAD}>`)
    .replace(/<p>/g, `<p ${P}>`)
    .replace(/<h2>/g, `<h2 ${H2}>`)
    .replace(/<ul>/g, `<ul ${UL}>`)
    .replace(/<li>/g, `<li ${LI}>`);
  return `<div style="max-width:560px;margin:0 auto;padding:8px;">
  <p style="text-align:center;font-family:Georgia,'Times New Roman',serif;font-size:22px;letter-spacing:5px;color:#141414;margin:10px 0 4px;">RAD&nbsp;DOLO</p>
  <p style="text-align:center;${LBL}font-size:10px;margin:0 0 26px;">Personal Stylist &nbsp;&middot;&nbsp; The Journal</p>
  ${meta ? `<p style="${LBL}font-size:10px;margin:0 0 10px;">${meta}</p>` : ""}
  <h1 style="font-family:Georgia,'Times New Roman',serif;font-size:30px;line-height:1.08;letter-spacing:.5px;text-transform:uppercase;color:#141414;margin:0 0 20px;">${title}</h1>
  ${body}
  <p style="text-align:center;margin:30px 0 26px;">
    <a href="${link}" style="display:inline-block;border:1.5px solid #141414;color:#141414;text-decoration:none;font-family:Arial,Helvetica,sans-serif;font-size:11px;letter-spacing:2px;text-transform:uppercase;padding:12px 24px;">Read on raddolo.com</a>
  </p>
  <hr style="border:none;border-top:1px solid #e4e4e4;margin:0 0 18px;">
  <p style="text-align:center;${LBL}font-size:11px;letter-spacing:1px;">
    <a href="${SITE}/" style="color:#141414;">raddolo.com</a> &nbsp;&middot;&nbsp;
    <a href="${IG}" style="color:#141414;">Instagram</a> &nbsp;&middot;&nbsp;
    <a href="${TT}" style="color:#141414;">TikTok</a>
  </p>
</div>`;
}

export default async function handler() {
  const key = process.env.BUTTONDOWN_API_KEY;
  if (!key) { console.log("BUTTONDOWN_API_KEY not set; skipping."); return new Response("skipped", { status: 200 }); }

  const siteUrl = process.env.URL || SITE;
  const feedRes = await fetch(`${siteUrl}/feed.xml`);
  if (!feedRes.ok) return new Response("feed unavailable", { status: 200 });
  const xml = await feedRes.text();

  const items = [...xml.matchAll(/<item>([\s\S]*?)<\/item>/g)].map((m) => {
    const block = m[1];
    const pick = (tag) => (block.match(new RegExp(`<${tag}>([\\s\\S]*?)</${tag}>`)) || [])[1]?.trim() || "";
    return { title: pick("title"), link: pick("link"), desc: pick("description") };
  });
  if (!items.length) return new Response("no items", { status: 200 });

  const auth = { Authorization: `Token ${key}`, "Content-Type": "application/json" };
  const sentRes = await fetch(`${API}/emails`, { headers: auth });
  const sentBodies = sentRes.ok ? JSON.stringify((await sentRes.json()).results || []) : "";

  for (const item of items) {
    if (!item.link || sentBodies.includes(item.link)) continue;

    // pull the real article from the live site
    const path = new URL(item.link).pathname;
    const pageRes = await fetch(siteUrl + path);
    let prose = `<p>${item.desc}</p>`, meta = "";
    if (pageRes.ok) {
      const page = await pageRes.text();
      prose = (page.match(/<div class="wrap prose">([\s\S]*?)<\/div>/) || [null, prose])[1];
      meta = (page.match(/post-meta">([^<]+)</) || [null, ""])[1];
    }

    const status = process.env.JOURNAL_EMAIL_MODE === "send" ? "about_to_send" : "draft";
    const res = await fetch(`${API}/emails`, {
      method: "POST",
      headers: auth,
      body: JSON.stringify({ subject: item.title, body: buildEmail(item.title, meta, prose, item.link), status }),
    });
    console.log(`${status} "${item.title}":`, res.status);
    break; // one per run
  }
  return new Response("ok", { status: 200 });
}
