/**
 * Cloudflare Worker that serves:
 * - Static landing page (/)
 * - Podcast RSS feed (/feed.xml)
 * - Episode audio files (/episodes/ep_XXX.mp3)
 * - Artwork (/artwork.jpg)
 *
 * All media files are served from Cloudflare R2.
 */

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    const path = url.pathname;

    // CORS headers for podcast apps
    const corsHeaders = {
      "Access-Control-Allow-Origin": "*",
      "Access-Control-Allow-Methods": "GET, HEAD, OPTIONS",
    };

    if (request.method === "OPTIONS") {
      return new Response(null, { headers: corsHeaders });
    }

    // Serve RSS feed
    if (path === "/feed.xml") {
      return serveFromR2(env.PODCAST_BUCKET, "feed.xml", "application/rss+xml; charset=utf-8", corsHeaders);
    }

    // Serve episode audio files
    if (path.startsWith("/episodes/") && path.endsWith(".mp3")) {
      const key = path.slice(1); // Remove leading /
      return serveFromR2(env.PODCAST_BUCKET, key, "audio/mpeg", corsHeaders);
    }

    // Serve artwork
    if (path === "/artwork.jpg" || path === "/artwork.png") {
      const key = path.slice(1);
      const contentType = path.endsWith(".jpg") ? "image/jpeg" : "image/png";
      return serveFromR2(env.PODCAST_BUCKET, key, contentType, corsHeaders);
    }

    // Landing page
    if (path === "/" || path === "/index.html") {
      return env.ASSETS.fetch(request);
    }

    // Static assets
    try {
      const assetResponse = await env.ASSETS.fetch(request);
      if (assetResponse.status !== 404) {
        return assetResponse;
      }
    } catch {}

    return new Response("Not Found", { status: 404 });
  },
};

async function serveFromR2(bucket, key, contentType, corsHeaders) {
  const object = await bucket.get(key);

  if (!object) {
    return new Response(`File not found: ${key}`, { status: 404 });
  }

  return new Response(object.body, {
    headers: {
      "Content-Type": contentType,
      "Cache-Control": key === "feed.xml" ? "public, max-age=900" : "public, max-age=86400",
      "Content-Length": object.size,
      ...corsHeaders,
    },
  });
}
