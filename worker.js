import { Container } from "@cloudflare/containers";

/**
 * Cloudflare Container for USCardForum MCP Server
 */
export class USCardForumContainer extends Container {
  defaultPort = 8000;
  // Sleep after 5 minutes of inactivity to save costs
  sleepAfter = '5m';
  
  // Optional hooks for debugging
  override onStart() {
    console.log('USCardForum Container started');
  }

  override onError(error) {
    console.error('USCardForum Container error:', error);
  }
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    
    // Simple load balancing / singleton pattern
    // We use a fixed name "default" to reuse the same container instance
    // similar to a singleton service.
    const container = env.USCARDFORUM.getByName("default");
    
    return await container.fetch(request);
  }
};
