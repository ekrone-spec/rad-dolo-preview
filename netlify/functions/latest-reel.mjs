// Returns the permalink of the newest Instagram Reel so the homepage can
// render Instagram's official embed for it. We do this (instead of pulling
// the video file) because Instagram withholds media for music-flagged reels
// from third-party embeds/widgets, but permalinks stay public and Instagram's
// own embed player can still render the post.
//
// Env var:
//   INSTAGRAM_ACCESS_TOKEN — seed long-lived Instagram API with Instagram
//   Login (Business) token. Used only if no fresher token is in Blobs yet.
//
// Netlify Blobs store "latest-reel":
//   key "token" -> JSON { token, refreshedAt }  (refreshedAt = ISO string)
//   key "cache" -> JSON { permalink, timestamp, checkedAt }
//
// Refresh policy: a token is refreshed (via /refresh_access_token) if it is
// older than 7 days since refreshedAt, or if refreshedAt is unknown. The
// refreshed token is persisted back to Blobs. The media cache is considered
// fresh for 24h; within that window we just return the cached result.
//
// If Blobs is unavailable for any reason, every Blobs call is wrapped in
// try/catch so the function still works statelessly off the env token.

import { getStore } from "@netlify/blobs";

const GRAPH = "https://graph.instagram.com/v21.0";
const TOKEN_MAX_AGE_MS = 7 * 24 * 60 * 60 * 1000; // 7 days
const CACHE_MAX_AGE_MS = 24 * 60 * 60 * 1000; // 24 hours

const FRESH_CACHE_HEADERS = { "Cache-Control": "public, max-age=600, s-maxage=3600" };
const NONE_CACHE_HEADERS = { "Cache-Control": "public, max-age=300" };

function mask(token) {
  if (!token) return null;
  return token.slice(0, 6) + "…";
}

function json(body, headers, trace) {
  const out = trace ? { ...body, trace } : body;
  return new Response(JSON.stringify(out), {
    status: 200,
    headers: { "Content-Type": "application/json", ...headers },
  });
}

async function getStoreSafe(trace) {
  try {
    return getStore("latest-reel");
  } catch (e) {
    if (trace) trace.push(`getStore failed: ${e.message}`);
    return null;
  }
}

async function readBlobJSON(store, key, trace) {
  if (!store) return null;
  try {
    const val = await store.get(key, { type: "json" });
    if (trace) trace.push(`blob get ${key}: ${val ? "hit" : "miss"}`);
    return val || null;
  } catch (e) {
    if (trace) trace.push(`blob get ${key} failed: ${e.message}`);
    return null;
  }
}

async function writeBlobJSON(store, key, value, trace) {
  if (!store) return;
  try {
    await store.setJSON(key, value);
    if (trace) trace.push(`blob set ${key}: ok`);
  } catch (e) {
    if (trace) trace.push(`blob set ${key} failed: ${e.message}`);
  }
}

async function resolveToken(store, trace) {
  const stored = await readBlobJSON(store, "token", trace);
  let token = stored?.token || process.env.INSTAGRAM_ACCESS_TOKEN || null;
  let refreshedAt = stored?.token ? stored?.refreshedAt : null;

  if (trace) trace.push(`token source: ${stored?.token ? "blob" : "env"} (${mask(token)})`);

  if (!token) return null;

  const age = refreshedAt ? Date.now() - new Date(refreshedAt).getTime() : Infinity;
  if (age > TOKEN_MAX_AGE_MS) {
    if (trace) trace.push("token needs refresh");
    try {
      const res = await fetch(
        `${GRAPH.replace("v21.0", "")}refresh_access_token?grant_type=ig_refresh_token&access_token=${encodeURIComponent(token)}`
      );
      if (res.ok) {
        const data = await res.json();
        if (data.access_token) {
          token = data.access_token;
          refreshedAt = new Date().toISOString();
          await writeBlobJSON(store, "token", { token, refreshedAt }, trace);
          if (trace) trace.push(`refreshed token: ${mask(token)}`);
        }
      } else if (trace) {
        trace.push(`refresh failed: ${res.status}`);
      }
    } catch (e) {
      if (trace) trace.push(`refresh error: ${e.message}`);
    }
  }

  return token;
}

export default async function handler(req) {
  const params = new URL(req.url).searchParams;
  const debug = params.get("debug") === "1";
  const trace = debug ? [] : null;

  const store = await getStoreSafe(trace);

  // 1) Serve fresh cache if present.
  const cached = await readBlobJSON(store, "cache", trace);
  if (cached && cached.checkedAt) {
    const age = Date.now() - new Date(cached.checkedAt).getTime();
    if (age < CACHE_MAX_AGE_MS) {
      if (trace) trace.push(`cache fresh (age ${Math.round(age / 1000)}s)`);
      return json(
        {
          permalink: cached.permalink || null,
          timestamp: cached.timestamp || null,
          source: "cache",
          checkedAt: cached.checkedAt,
        },
        FRESH_CACHE_HEADERS,
        trace
      );
    }
    if (trace) trace.push(`cache stale (age ${Math.round(age / 1000)}s)`);
  }

  // 2) Resolve token (refreshing if needed).
  const token = await resolveToken(store, trace);
  const checkedAt = new Date().toISOString();

  if (!token) {
    if (trace) trace.push("no token available");
    return json({ permalink: null, timestamp: null, source: "none", checkedAt }, NONE_CACHE_HEADERS, trace);
  }

  // 3) Call the API and pick the newest reel.
  try {
    const url = `${GRAPH}/me/media?fields=id,media_type,media_product_type,permalink,timestamp&limit=25&access_token=${encodeURIComponent(token)}`;
    const res = await fetch(url);
    if (trace) trace.push(`media fetch: ${res.status}`);
    if (!res.ok) {
      return json({ permalink: null, timestamp: null, source: "none", checkedAt }, NONE_CACHE_HEADERS, trace);
    }
    const data = await res.json();
    const items = Array.isArray(data.data) ? data.data : [];

    let pick = items.find((it) => it.media_product_type === "REELS");
    if (!pick) pick = items.find((it) => it.media_type === "VIDEO");

    if (!pick) {
      if (trace) trace.push("no matching reel/video found");
      return json({ permalink: null, timestamp: null, source: "none", checkedAt }, NONE_CACHE_HEADERS, trace);
    }

    const result = { permalink: pick.permalink, timestamp: pick.timestamp, checkedAt };
    await writeBlobJSON(store, "cache", result, trace);

    return json({ ...result, source: "api" }, FRESH_CACHE_HEADERS, trace);
  } catch (e) {
    if (trace) trace.push(`media fetch error: ${e.message}`);
    return json({ permalink: null, timestamp: null, source: "none", checkedAt }, NONE_CACHE_HEADERS, trace);
  }
}
