// Returns the preview image for a ShopMy link, so shop cards can be managed
// in the CMS by pasting a link — no photo upload needed.
//
// Strategy:
//   1. Collection links (shopmy.us/.../collections/<id>) → ShopMy's public
//      API exposes the collection image directly.
//   2. Anything else → try the page's og:image.
//   3. All failures → redirect to a same-origin branded fallback tile.
//
// Security: strict host allowlist (shopmy.us + its API) so this can't be
// used to fetch arbitrary URLs (SSRF); image bytes are streamed same-origin
// so the site's CSP img-src stays locked to 'self'.

const ALLOWED_HOSTS = new Set(["shopmy.us", "www.shopmy.us"]);
const CACHE = "public, max-age=86400, s-maxage=604800"; // browser 1d, CDN 7d
const FALLBACK = "/shop-fallback.svg";

const BARE_TYPES = { jpeg: "image/jpeg", jpg: "image/jpeg", png: "image/png",
                     gif: "image/gif", webp: "image/webp", avif: "image/avif" };

async function streamImage(url, trace) {
  try {
    const res = await fetch(url, { redirect: "follow", headers: { "User-Agent": "Mozilla/5.0" } });
    const raw = (res.headers.get("content-type") || "").toLowerCase().split(";")[0].trim();
    // ShopMy's CDN sends bare "jpeg" instead of "image/jpeg" — normalize,
    // and as a last resort infer from the file extension.
    let type = raw.startsWith("image/") ? raw : (BARE_TYPES[raw] || "");
    if (!type) {
      const ext = (url.split("?")[0].match(/\.(jpe?g|png|gif|webp|avif)$/i) || [])[1];
      if (ext) type = BARE_TYPES[ext.toLowerCase()] || "";
    }
    if (trace) trace.push(`${url.slice(0, 90)} -> ${res.status} ${raw} => ${type || "REJECT"}`);
    if (!res.ok || !type) return null;
    return new Response(res.body, {
      status: 200,
      headers: { "Content-Type": type, "Cache-Control": CACHE, "X-Content-Type-Options": "nosniff" },
    });
  } catch (e) {
    if (trace) trace.push(`${url.slice(0, 90)} -> ERR ${e.message}`);
    return null;
  }
}

export default async function handler(req) {
  const params = new URL(req.url).searchParams;
  const debug = params.get("debug") === "1";
  const trace = debug ? [] : null;
  const fallback = () =>
    debug
      ? new Response(JSON.stringify(trace, null, 2), { status: 200, headers: { "Content-Type": "application/json" } })
      : new Response(null, { status: 302, headers: { Location: FALLBACK, "Cache-Control": "public, max-age=3600" } });

  const u = params.get("u") || "";
  let target;
  try { target = new URL(u); } catch { return fallback(); }
  if (target.protocol !== "https:" || !ALLOWED_HOSTS.has(target.hostname)) {
    return new Response("host not allowed", { status: 403 });
  }

  try {
    // 1) collection links → public API. The collection "cover" often lives
    //    on a private S3 bucket, so prefer it but fall back to the first
    //    pin's image, which is served from ShopMy's public CDN.
    const idMatch = target.pathname.match(/\/collections\/(\d+)/);
    if (idMatch) {
      const api = await fetch(`https://api.shopmy.us/api/collections/${idMatch[1]}`, {
        headers: { "User-Agent": "Mozilla/5.0 (compatible; RadDoloSite/1.0)" },
      });
      if (trace) trace.push("api " + api.status);
      if (api.ok) {
        const data = await api.json();
        const candidates = [];
        if (typeof data.image === "string") candidates.push(data.image);
        for (const pin of (data.pins || []).slice(0, 4)) {
          if (pin && typeof pin.image === "string") candidates.push(pin.image);
        }
        for (const img of candidates) {
          if (!img.startsWith("https://")) continue;
          const out = await streamImage(img, trace);
          if (out && !debug) return out;
        }
      }
    }

    // 2) og:image from the page
    const pageRes = await fetch(target.href, {
      headers: { "User-Agent": "Mozilla/5.0 (compatible; RadDoloSite/1.0)" },
      redirect: "follow",
    });
    if (pageRes.ok) {
      const html = await pageRes.text();
      const og = html.match(/property=["']og:image["'][^>]*content=["']([^"']+)["']/) ||
                 html.match(/content=["']([^"']+)["'][^>]*property=["']og:image["']/);
      if (og) {
        const imgUrl = new URL(og[1], target.href);
        if (imgUrl.protocol === "https:") {
          const out = await streamImage(imgUrl.href, trace);
          if (out && !debug) return out;
        }
      }
    }
  } catch (e) {
    console.log("shop-image error:", e.message);
  }

  // 3) branded fallback tile
  return fallback();
}
