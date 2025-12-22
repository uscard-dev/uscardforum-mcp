import { DurableObject } from "cloudflare:workers";

/**
 * Cloudflare Container for USCardForum MCP Server
 * 
 * Implements the container proxy manually using DurableObject
 * because the 'Container' helper class export might not be available
 * in all environments yet.
 */
export class USCardForumContainer extends DurableObject {
  constructor(ctx, env) {
    super(ctx, env);
    // Start the container when the DO is instantiated.
    // The container configuration (image, etc.) is defined in wrangler.jsonc
    if (this.ctx.container) {
        this.ctx.container.start();
    }
  }

  async fetch(request) {
    // Proxy requests to the container running on localhost:8000
    // The container shares the network namespace with this Durable Object.
    const url = new URL(request.url);
    const containerUrl = new URL(`http://127.0.0.1:8000${url.pathname}${url.search}`);
    
    // Create a new request to forward to the container
    const newRequest = new Request(containerUrl, {
        method: request.method,
        headers: request.headers,
        body: request.body,
        redirect: "manual" 
    });

    try {
        return await fetch(newRequest);
    } catch (err) {
        return new Response(`Container Proxy Error: ${err.message}`, { status: 502 });
    }
  }
}

export default {
  async fetch(request, env) {
    // Proxy all requests to the container via the Durable Object binding
    // The binding name "USCARDFORUM" is defined in wrangler.jsonc
    // We use a fixed ID "default" to keep a single persistent container instance (singleton-like)
    // or we could generate a new one. For an MCP server, a singleton is usually fine 
    // unless we want per-user isolation.
    // Let's use a singleton for simplicity and resource efficiency.
    const id = env.USCARDFORUM.idFromName("default");
    const stub = env.USCARDFORUM.get(id);
    return stub.fetch(request);
  }
};
