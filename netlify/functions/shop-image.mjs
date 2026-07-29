// Proxies the preview image (og:image) of a ShopMy link, so shop cards can
// be managed in the CMS by pasting a link — no photo upload needed.
//
// Security: strict host allowlist (shopmy.us only) so this can't be used to
// fetch arbitrary URLs (SSRF), and the image bytes are streamed same-origin,
// which keeps the site's CSP img-src locked to 'self'.

const ALLOWED_HOSTS = new Set(["shopmy.us", "www.shopmy.us"]);
const CACHE = "public, max-age=86400, s-maxage=604800"; // browser 1d, CDN 7d

export default async function handler(req) {
  const u = new URL(req.url).searchParams.get("u") || "";
  let target;
  try { target = new URL(u); } catch { return new Response("bad url", { status: 400 }); }
  if (target.protocol !== "https:" || !ALLOWED_HOSTS.has(target.hostname)) {
    return new Response("host not allowed", { status: 403 });
  }

  const pageRes = await fetch(target.href, {
    headers: { "User-Agent": "Mozilla/5.0 (compatible; RadDoloSite/1.0)" },
    redirect: "follow",
  });
  if (!pageRes.ok) return new Response("upstream error", { status: 502 });
  const html = await pageRes.text();
  const og = html.match(/property=["']og:image["'][^>]*content=["']([^"']+)["']/) ||
             html.match(/content=["']([^"']+)["'][^>]*property=["']og:image["']/);
  if (!og) return new Response("no preview image", { status: 404 });

  let imgUrl;
  try { imgUrl = new URL(og[1], target.href); } catch { return new Response("bad image url", { status: 502 }); }
  if (imgUrl.protocol !== "https:") return new Response("bad image url", { status: 502 });

  const imgRes = await fetch(imgUrl.href, { redirect: "follow" });
  if (!imgRes.ok) return new Response("image fetch failed", { status: 502 });
  const type = imgRes.headers.get("content-type") || "";
  if (!type.startsWith("image/")) return new Response("not an image", { status: 502 });

  return new Response(imgRes.body, {
    status: 200,
    headers: { "Content-Type": type, "Cache-Control": CACHE, "X-Content-Type-Options": "nosniff" },
  });
}
