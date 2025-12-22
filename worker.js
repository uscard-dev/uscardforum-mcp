import { Container } from "cloudflare:workers";

/**
 * Cloudflare Container for USCardForum MCP Server
 * 
 * This Worker acts as the entrypoint and proxy for the containerized application.
 * It uses Cloudflare's Container API (based on Durable Objects) to route traffic.
 */
export class USCardForumContainer extends Container {
  // The port your Dockerfile exposes (must match EXPOSE in Dockerfile)
  defaultPort = 8000;
}

export default {
  async fetch(request, env) {
    // Proxy all requests to the container
    // The binding name "USCARDFORUM" is defined in wrangler.jsonc
    return env.USCARDFORUM.fetch(request);
  }
};

