// Weekly health check: verifies the homepage, feed, a journal post and the
// booking flow's assets all respond. A thrown error surfaces in Netlify's
// function logs/notifications so problems get noticed without anyone
// remembering to look.

export const config = { schedule: "0 13 * * 1" }; // Mondays, 13:00 UTC

export default async function handler() {
  const base = process.env.URL || "https://www.raddolo.com";
  const paths = ["/", "/feed.xml", "/journal/keep-donate-maybe/", "/favicon.svg", "/404"];
  const failures = [];
  for (const p of paths) {
    try {
      const res = await fetch(base + p, { redirect: "follow" });
      const expected404 = p === "/404";
      const ok = expected404 ? res.status === 404 : res.ok;
      if (!ok) failures.push(`${p} -> ${res.status}`);
    } catch (e) {
      failures.push(`${p} -> ${e.message}`);
    }
  }
  if (failures.length) {
    console.error("HEALTH CHECK FAILED:", failures.join("; "));
    throw new Error("Health check failed: " + failures.join("; "));
  }
  console.log("health check ok:", paths.join(", "));
  return new Response("ok", { status: 200 });
}
