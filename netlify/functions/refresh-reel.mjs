// Keeps the Instagram token alive. latest-reel refreshes the token only when
// it is called, and if the homepage never calls it (Behold working) the token
// silently expires after 60 days (happened Nov 2026). This runs weekly and
// simply hits latest-reel, which refreshes a token older than 7 days.
export const config = { schedule: "0 9 * * 1" }; // Mondays, 09:00 UTC

export default async function handler() {
  const base = process.env.URL || "https://www.raddolo.com";
  const res = await fetch(`${base}/.netlify/functions/latest-reel?debug=1`);
  const body = await res.json().catch(() => ({}));
  console.log("refresh-reel:", res.status, body.source, (body.trace || []).join(" | "));
  return new Response(null, { status: res.ok ? 200 : 500 });
}
