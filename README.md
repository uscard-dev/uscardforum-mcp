# USCardForum MCP Server

A production-ready [Model Context Protocol (MCP)](https://modelcontextprotocol.io/) server for interacting with [USCardForum](https://www.uscardforum.com), a Discourse-based community focused on US credit cards, points, miles, and financial optimization.

## Features

- **22 Tools** organized into 4 logical groups:
  - 📰 **Discovery** (5) — Find topics via hot/new/top/search/categories
  - 📖 **Reading** (3) — Access topic content with pagination
  - 👤 **Users** (9) — Profile research, badges, activity, social
  - 🔐 **Auth** (5) — Login, notifications, bookmarks, subscriptions
- **4 Prompts** for guided research workflows (Chinese)
- **3 Resources** for quick data access
- **Multiple Transports** — stdio, SSE, Streamable HTTP
- **Strongly Typed** with Pydantic domain models
- **Rate Limiting** with exponential backoff
- **Cloudflare Bypass** via cloudscraper
- **Heroku Ready** deployment configuration

## Project Structure

```
uscardforum/
├── src/uscardforum/
│   ├── __init__.py          # Package exports
│   ├── client.py            # Main client (composes APIs)
│   ├── server.py            # FastMCP server (MCP layer)
│   ├── server_core.py       # Server configuration
│   ├── models/              # Domain models (Pydantic)
│   │   ├── topics.py        # Topic, Post, TopicInfo, TopicSummary
│   │   ├── users.py         # UserSummary, UserAction, Badge, etc.
│   │   ├── search.py        # SearchResult, SearchPost, SearchTopic
│   │   ├── categories.py    # Category, CategoryMap
│   │   └── auth.py          # Session, Notification, Bookmark, etc.
│   ├── api/                 # API modules (backend)
│   │   ├── base.py          # Base API with HTTP methods
│   │   ├── topics.py        # Topic operations
│   │   ├── users.py         # User profile operations
│   │   ├── search.py        # Search operations
│   │   └── auth.py          # Authentication operations
│   ├── server_tools/        # MCP tool definitions
│   └── utils/               # HTTP and Cloudflare utilities
├── tests/                   # Integration tests
├── .github/workflows/       # CI/CD workflows
│   ├── ci.yml               # Tests, linting, type checking
│   └── deploy.yml           # Multi-platform deployment
├── Dockerfile               # Container build
├── docker-compose.yml       # Local development
├── fly.toml                 # Fly.io configuration
├── railway.toml             # Railway configuration
├── render.yaml              # Render blueprint
├── koyeb.yaml               # Koyeb configuration
├── digitalocean-app.yaml    # DigitalOcean App Platform
├── cloudbuild.yaml          # Google Cloud Build
├── heroku.yml               # Heroku manifest
├── app.json                 # Heroku button config
├── Procfile                 # Heroku process
└── pyproject.toml           # Python package config
```

## Installation

### Using UV (Recommended)

```bash
# Clone the repository
git clone https://github.com/uscardforum/mcp-server.git
cd uscardforum

# Install with UV
uv sync

# Run the server
uv run uscardforum
```

### Using pip

```bash
# Clone the repository
git clone https://github.com/uscardforum/mcp-server.git
cd uscardforum

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows

# Install
pip install -e .

# Run
uscardforum
```

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MCP_TRANSPORT` | `stdio` | Transport mode: `stdio`, `sse`, or `streamable-http` |
| `MCP_HOST` | `0.0.0.0` | HTTP server host (for `sse`/`streamable-http`) |
| `MCP_PORT` | `8000` | HTTP server port (for `sse`/`streamable-http`) |
| `NITAN_TOKEN` | *(none)* | Bearer token for MCP auth (`streamable-http` only) |
| `USCARDFORUM_URL` | `https://www.uscardforum.com` | Forum base URL |
| `USCARDFORUM_TIMEOUT` | `15.0` | Request timeout in seconds |
| `NITAN_USERNAME` | *(none)* | Forum username for auto-login (optional) |
| `NITAN_PASSWORD` | *(none)* | Forum password for auto-login (optional) |
| `NITAN_API_KEY` | *(none)* | Discourse User API Key (optional, alternative auth) |
| `NITAN_API_CLIENT_ID` | *(none)* | Discourse API Client ID (optional, alternative auth) |

### Transport Modes

The server supports three transport modes:

- **`stdio`** (default): Standard input/output, used by Cursor and Claude Desktop
- **`sse`**: Server-Sent Events over HTTP
- **`streamable-http`**: Streamable HTTP transport (recommended for web deployments)

#### Running with Streamable HTTP

```bash
# Start server with streamable HTTP transport
MCP_TRANSPORT=streamable-http MCP_PORT=8000 uv run uscardforum

# The MCP endpoint will be available at:
# http://localhost:8000/mcp
```

#### Streamable HTTP Authentication

When using `streamable-http` transport, you can require clients to authenticate with a bearer token by setting `NITAN_TOKEN`:

```bash
# Start server with authentication required
MCP_TRANSPORT=streamable-http NITAN_TOKEN=my-secret-token uv run uscardforum

# Clients must include Authorization header:
# Authorization: Bearer my-secret-token
```

This is useful for securing public deployments. The token is only enforced for `streamable-http` transport; `stdio` and `sse` modes do not use this authentication.

### Forum Authentication

The server supports two authentication methods for accessing authenticated features (notifications, bookmarks, subscriptions):

#### Method 1: Username/Password Login (Priority)

If both `NITAN_USERNAME` and `NITAN_PASSWORD` are set, the server automatically logs into the forum on startup using username/password authentication.

#### Method 2: User API Key

Alternatively, you can use a Discourse User API Key for authentication. This method is used **only when** `NITAN_USERNAME` and `NITAN_PASSWORD` are not provided.

**Environment Variables:**
- `NITAN_API_KEY`: Your Discourse User API Key
- `NITAN_API_CLIENT_ID`: Your Discourse API Client ID

**How to obtain a User API Key:**
See https://github.com/discourse/discourse-mcp?tab=readme-ov-file#obtaining-a-user-api-key

**Usage Example:**

```bash
# Using User API Key (when username/password are not set)
export NITAN_API_KEY="your_api_key_here"
export NITAN_API_CLIENT_ID="your_client_id_here"
uv run uscardforum
```

**Authentication Priority:**
- If `NITAN_USERNAME` and `NITAN_PASSWORD` are set → Username/Password login is used
- If only `NITAN_API_KEY` and `NITAN_API_CLIENT_ID` are set → User API Key authentication is used
- If neither is set → Server runs in unauthenticated mode (limited features)

### Cursor IDE Integration

Add to `~/.cursor/mcp.json`:

**Option 1: Username/Password Authentication**
```json
{
  "mcpServers": {
    "uscardforum": {
      "command": "uv",
      "args": ["--directory", "/path/to/uscardforum", "run", "uscardforum"],
      "env": {
        "NITAN_USERNAME": "your_forum_username",
        "NITAN_PASSWORD": "your_forum_password"
      }
    }
  }
}
```

**Option 2: User API Key Authentication**
```json
{
  "mcpServers": {
    "uscardforum": {
      "command": "uv",
      "args": ["--directory", "/path/to/uscardforum", "run", "uscardforum"],
      "env": {
        "NITAN_API_KEY": "your_api_key",
        "NITAN_API_CLIENT_ID": "your_client_id"
      }
    }
  }
}
```

### Claude Desktop Integration

Add to Claude Desktop's config file:

**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

**Option 1: Username/Password Authentication**
```json
{
  "mcpServers": {
    "uscardforum": {
      "command": "uv",
      "args": ["--directory", "/path/to/uscardforum", "run", "uscardforum"],
      "env": {
        "NITAN_USERNAME": "your_forum_username",
        "NITAN_PASSWORD": "your_forum_password"
      }
    }
  }
}
```

**Option 2: User API Key Authentication**
```json
{
  "mcpServers": {
    "uscardforum": {
      "command": "uv",
      "args": ["--directory", "/path/to/uscardforum", "run", "uscardforum"],
      "env": {
        "NITAN_API_KEY": "your_api_key",
        "NITAN_API_CLIENT_ID": "your_client_id"
      }
    }
  }
}
```

## Deployment

The USCardForum MCP Server supports multiple deployment platforms. Choose the one that best fits your needs.

### Quick Comparison

| Platform | Starting Price | Pros | Best For |
|----------|----------------|------|----------|
| **Heroku** | $7/mo | Easy, one-click deploy | Quick start |
| **Railway** | $5/mo | Simple, GitHub integration | Developers |
| **Render** | $7/mo | Auto-scaling, free tier | Production |
| **Fly.io** | $0-5/mo | Edge deployment, generous free tier | Global reach |
| **Google Cloud Run** | Pay-per-use | Auto-scaling to zero | Variable traffic |
| **DigitalOcean** | $5/mo | Predictable pricing | Self-managed |
| **Koyeb** | $5/mo | Fast deploys, global edge | Low latency |
| **Cloudflare** | Free | Global edge network | Edge deployment |
| **Docker** | Self-hosted | Full control | Privacy-conscious |

---

### Heroku

[![Deploy](https://www.herokucdn.com/deploy/button.svg)](https://heroku.com/deploy?template=https://github.com/uscard-dev/uscardforum-mcp)

```bash
# Manual deployment
heroku login
heroku create your-app-name

# Set environment variables
heroku config:set NITAN_TOKEN=$(openssl rand -hex 32)
heroku config:set NITAN_USERNAME=your_username
heroku config:set NITAN_PASSWORD=your_password

# Deploy
git push heroku main
heroku ps:scale web=1
```

---

### Railway

[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/template/uscardforum-mcp)

```bash
# Install Railway CLI
npm i -g @railway/cli

# Login and deploy
railway login
railway init
railway up

# Set environment variables
railway variables set MCP_TRANSPORT=streamable-http
railway variables set NITAN_TOKEN=$(openssl rand -hex 32)
railway variables set NITAN_USERNAME=your_username
railway variables set NITAN_PASSWORD=your_password

# Open dashboard
railway open
```

---

### Render

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/uscardforum/mcp-server)

1. Connect your GitHub repository to Render
2. Create a new **Web Service**
3. Select **Docker** as the runtime
4. Set environment variables in the dashboard:
   - `MCP_TRANSPORT=streamable-http`
   - `NITAN_TOKEN=your-secret-token`
   - `NITAN_USERNAME=your-username` (optional)
   - `NITAN_PASSWORD=your-password` (optional)

Or use the blueprint file:

```bash
# render.yaml is included in the repository
# Just connect your repo and Render will auto-detect it
```

---

### Fly.io

```bash
# Install Fly CLI
curl -L https://fly.io/install.sh | sh

# Login and launch
fly auth login
fly launch --name uscardforum-mcp

# Set secrets
fly secrets set NITAN_TOKEN=$(openssl rand -hex 32)
fly secrets set NITAN_USERNAME=your_username
fly secrets set NITAN_PASSWORD=your_password

# Deploy
fly deploy

# Check status
fly status
fly logs
```

---

### Google Cloud Run

[![Open in Cloud Shell](https://gstatic.com/cloudssh/images/open-btn.svg)](https://shell.cloud.google.com/cloudshell/editor?cloudshell_git_repo=https://github.com/uscard-dev/uscardforum-mcp&cloudshell_tutorial=docs/cloudrun-tutorial.md)

After clicking, run in Cloud Shell:

```bash
# Deploy to Cloud Run
gcloud run deploy uscardforum-mcp \
  --source . \
  --region us-west1 \
  --platform managed \
  --allow-unauthenticated \
  --port 8000 \
  --memory 512Mi \
  --set-env-vars "MCP_TRANSPORT=streamable-http,MCP_HOST=0.0.0.0,MCP_PORT=8000"
```

Or deploy via CLI:

```bash
# Enable required APIs
gcloud services enable run.googleapis.com cloudbuild.googleapis.com

# Deploy directly from source
gcloud run deploy uscardforum-mcp \
  --source . \
  --region us-west1 \
  --platform managed \
  --allow-unauthenticated \
  --port 8000 \
  --memory 512Mi \
  --set-env-vars "MCP_TRANSPORT=streamable-http,MCP_HOST=0.0.0.0,MCP_PORT=8000"

# Set secrets (create them first in Secret Manager)
gcloud run services update uscardforum-mcp \
  --set-secrets="NITAN_TOKEN=nitan-token:latest"
```

Or use Cloud Build with the included `cloudbuild.yaml`:

```bash
gcloud builds submit --config cloudbuild.yaml
```

---

### DigitalOcean App Platform

```bash
# Install doctl CLI
brew install doctl  # or: snap install doctl

# Authenticate
doctl auth init

# Create app from spec
doctl apps create --spec digitalocean-app.yaml

# Or deploy via dashboard:
# 1. Go to https://cloud.digitalocean.com/apps
# 2. Create App → GitHub → Select repository
# 3. Configure environment variables
```

---

### Koyeb

```bash
# Install Koyeb CLI
curl -fsSL https://raw.githubusercontent.com/koyeb/koyeb-cli/master/install.sh | sh

# Login and deploy
koyeb login
koyeb app create uscardforum-mcp \
  --docker-image ghcr.io/uscardforum/mcp-server:latest \
  --ports 8000:http \
  --env MCP_TRANSPORT=streamable-http \
  --env MCP_PORT=8000

# Set secrets
koyeb secrets create nitan-token --value your-secret-token
koyeb app update uscardforum-mcp --env NITAN_TOKEN=@nitan-token
```

---

### Cloudflare Containers

[![Deploy to Cloudflare](https://deploy.workers.cloudflare.com/button)](https://deploy.workers.cloudflare.com/?url=https://github.com/uscard-dev/uscardforum-mcp)

---

### Docker (Self-Hosted)

```bash
# Pull from Docker Hub (recommended)
docker pull uscarddev/uscardforum-mcp:latest

# Run the container
docker run -d \
  -p 8000:8000 \
  -e MCP_TRANSPORT=streamable-http \
  -e NITAN_TOKEN=your-secret-token \
  --name uscardforum-mcp \
  uscarddev/uscardforum-mcp:latest

# Or build locally
docker build -t uscardforum-mcp .
docker run -d \
  -p 8000:8000 \
  -e MCP_TRANSPORT=streamable-http \
  -e NITAN_TOKEN=your-secret-token \
  --name uscardforum-mcp \
  uscardforum-mcp

# Or use Docker Compose
docker compose up -d

# View logs
docker compose logs -f
```

**Docker Hub**: [`uscarddev/uscardforum-mcp`](https://hub.docker.com/r/uscarddev/uscardforum-mcp)

Available tags:
- `latest` - Latest stable release
- `tagname` - Specific version tags

For production with HTTPS, use a reverse proxy like Traefik or nginx. See `docker-compose.yml` for Traefik example.

---

### Environment Variables Reference

| Variable | Default | Required | Description |
|----------|---------|----------|-------------|
| `MCP_TRANSPORT` | `stdio` | ✓ | Set to `streamable-http` for web deployment |
| `MCP_HOST` | `0.0.0.0` | | HTTP server bind address |
| `MCP_PORT` | `8000` | | HTTP server port (some platforms override this) |
| `NITAN_TOKEN` | | | Bearer token for MCP authentication |
| `USCARDFORUM_URL` | `https://www.uscardforum.com` | | Forum base URL |
| `USCARDFORUM_TIMEOUT` | `15.0` | | Request timeout in seconds |
| `NITAN_USERNAME` | | | Forum username for auto-login (priority method) |
| `NITAN_PASSWORD` | | | Forum password for auto-login (priority method) |
| `NITAN_API_KEY` | | | Discourse User API Key (alternative auth) |
| `NITAN_API_CLIENT_ID` | | | Discourse API Client ID (alternative auth) |

---

### Connecting to Your Deployed Server

After deployment, connect from Cursor or other MCP clients using the streamable HTTP URL:

```json
{
  "mcpServers": {
    "uscardforum": {
      "url": "https://your-app.fly.dev/mcp",
      "headers": {
        "Authorization": "Bearer your-nitan-token"
      }
    }
  }
}
```

Replace the URL with your deployment's URL:
- Heroku: `https://your-app.herokuapp.com/mcp`
- Railway: `https://your-app.up.railway.app/mcp`
- Render: `https://your-app.onrender.com/mcp`
- Fly.io: `https://your-app.fly.dev/mcp`
- Cloud Run: `https://your-app-xxxxx-uc.a.run.app/mcp`
- DigitalOcean: `https://your-app.ondigitalocean.app/mcp`
- Koyeb: `https://your-app.koyeb.app/mcp`

## Testing

Run integration tests against the live forum:

```bash
# Set test credentials
export NITAN_USERNAME="your_test_username"
export NITAN_PASSWORD="your_test_password"

# Run tests
uv run pytest tests/ -v

# Run with coverage
uv run pytest tests/ --cov=uscardforum --cov-report=term-missing
```

## Domain Models

All return types are strongly typed with Pydantic models:

### Topic Models

```python
from uscardforum import TopicSummary, TopicInfo, Post

# TopicSummary - for list views
topic: TopicSummary
topic.id          # int: Topic ID
topic.title       # str: Topic title
topic.posts_count # int: Number of posts
topic.views       # int: View count
topic.like_count  # int: Total likes

# TopicInfo - detailed metadata
info: TopicInfo
info.post_count          # int: Total posts
info.highest_post_number # int: Last post number

# Post - individual post
post: Post
post.id           # int: Post ID
post.post_number  # int: Position in topic
post.username     # str: Author
post.cooked       # str: HTML content
post.like_count   # int: Likes
```

### User Models

```python
from uscardforum import UserSummary, UserAction, Badge

# UserSummary - profile overview
summary: UserSummary
summary.username  # str: Username
summary.stats     # UserStats: Activity statistics
summary.badges    # List[Badge]: Earned badges

# UserAction - activity entry
action: UserAction
action.topic_id   # int: Related topic
action.excerpt    # str: Content preview
```

### Search Models

```python
from uscardforum import SearchResult, SearchPost, SearchTopic

# SearchResult - search response
result: SearchResult
result.posts   # List[SearchPost]: Matching posts
result.topics  # List[SearchTopic]: Matching topics
result.users   # List[SearchUser]: Matching users
```

### Auth Models

```python
from uscardforum import LoginResult, Session, Notification, Bookmark

# LoginResult - login response
login: LoginResult
login.success      # bool: Whether succeeded
login.requires_2fa # bool: 2FA needed

# Session - current session
session: Session
session.is_authenticated  # bool: Logged in
session.current_user      # CurrentUser: User info
```

## API Modules

The backend is split into focused API modules:

| Module | Purpose |
|--------|---------|
| `TopicsAPI` | Topic lists, posts, pagination |
| `UsersAPI` | Profiles, activity, badges, social |
| `SearchAPI` | Full-text search |
| `CategoriesAPI` | Category mappings |
| `AuthAPI` | Login, notifications, bookmarks |

Each module inherits from `BaseAPI` which provides rate-limited HTTP methods.

## Available Tools (22 Tools)

### 📰 Discovery — Find Content to Read

| Tool | Return Type | Description |
|------|-------------|-------------|
| `get_hot_topics` | `List[TopicSummary]` | Currently trending topics by engagement |
| `get_new_topics` | `List[TopicSummary]` | Latest topics by creation time |
| `get_top_topics` | `List[TopicSummary]` | Top topics by period (daily/weekly/monthly/yearly) |
| `search_forum` | `SearchResult` | Full-text search with operators |
| `get_categories` | `CategoryMap` | Category ID to name mapping |

### 📖 Reading — Access Topic Content

| Tool | Return Type | Description |
|------|-------------|-------------|
| `get_topic_info` | `TopicInfo` | Topic metadata (check post count first!) |
| `get_topic_posts` | `List[Post]` | Fetch ~20 posts starting at position |
| `get_all_topic_posts` | `List[Post]` | Fetch all posts with auto-pagination |

### 👤 Users — Profile & Activity Research

| Tool | Return Type | Description |
|------|-------------|-------------|
| `get_user_summary` | `UserSummary` | Profile overview and stats |
| `get_user_topics` | `List[Dict]` | Topics created by user |
| `get_user_replies` | `List[UserAction]` | User's reply history |
| `get_user_actions` | `List[UserAction]` | Full activity feed |
| `get_user_badges` | `UserBadges` | Badges earned by user |
| `get_user_following` | `FollowList` | Who the user follows |
| `get_user_followers` | `FollowList` | Who follows the user |
| `get_user_reactions` | `UserReactions` | Reactions given/received |
| `list_users_with_badge` | `Dict` | Find users with specific badge |

### 🔐 Auth — Authenticated Actions (requires login)

| Tool | Return Type | Description |
|------|-------------|-------------|
| `login` | `LoginResult` | Authenticate with forum credentials |
| `get_current_session` | `Session` | Check authentication status |
| `get_notifications` | `List[Notification]` | Fetch user notifications |
| `bookmark_post` | `Bookmark` | Bookmark a post for later |
| `subscribe_topic` | `SubscriptionResult` | Set topic notification level |

## Available Prompts (4 Prompts, 中文)

Guided workflows for common research tasks:

| Prompt | Args | Purpose |
|--------|------|---------|
| `research_topic` | `topic_query` | 研究论坛特定主题，总结社区共识 |
| `analyze_user` | `username` | 分析用户资料、贡献和可信度 |
| `find_data_points` | `subject` | 查找用户报告的真实数据点 |
| `compare_cards` | `card1`, `card2` | 比较两张信用卡的社区讨论 |

## Available Resources (3 Resources)

Quick-access static data:

| URI | Description |
|-----|-------------|
| `forum://categories` | Category ID → name mapping (JSON) |
| `forum://hot-topics` | Top 20 trending topics (JSON) |
| `forum://new-topics` | Top 20 latest topics (JSON) |

## Usage Examples

### Using the Client Directly

```python
from uscardforum import DiscourseClient

client = DiscourseClient()

# Browse hot topics
for topic in client.get_hot_topics():
    print(f"{topic.title} ({topic.posts_count} posts, {topic.views} views)")

# Get topic info and posts
info = client.get_topic_info(12345)
print(f"Topic has {info.post_count} posts")

posts = client.get_topic_posts(12345)
for post in posts:
    print(f"#{post.post_number} by {post.username}: {post.like_count} likes")

# Search
results = client.search("Chase Sapphire Reserve", order="latest")
for post in results.posts:
    print(f"[Topic {post.topic_id}] {post.blurb}")

# User profile
summary = client.get_user_summary("creditexpert")
print(f"{summary.username}: {summary.stats.post_count} posts")
```

### Forum Authentication

```python
# Login to forum
result = client.login("username", "password")
if result.success:
    print(f"Logged in as {result.username}")
elif result.requires_2fa:
    result = client.login("username", "password", second_factor_token="123456")

# Get notifications
notifications = client.get_notifications(only_unread=True)
for n in notifications:
    print(f"Notification {n.id}: {n.notification_type}")

# Bookmark a post
bookmark = client.bookmark_post(54321, name="Important info")
```

## Architecture

### Separation of Concerns

1. **Domain Models** (`models/`)
   - Pydantic models for all return types
   - Strong typing and validation
   - Clear documentation

2. **API Modules** (`api/`)
   - Focused functionality per domain
   - Inherits from BaseAPI for HTTP
   - Returns domain models

3. **Client** (`client.py`)
   - Composes all API modules
   - Unified interface
   - Session management

4. **MCP Server** (`server.py`)
   - FastMCP tool definitions
   - Bearer token authentication
   - Extensive docstrings (Chinese)
   - Prompts and resources

### Security

- **MCP Authentication**: Bearer token via HTTP `Authorization` header (MCP transport-level)
- **Rate Limiting**: 4 requests per second with exponential backoff
- **Cloudflare Bypass**: Automatic handling via cloudscraper

## Development

```bash
# Install dev dependencies
uv sync --group dev

# Run tests
NITAN_USERNAME="user" NITAN_PASSWORD="pass" uv run pytest

# Lint
uv run ruff check src/

# Type check
uv run mypy src/
```

## License

MIT

## Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Submit a pull request

## Acknowledgments

- Built with [FastMCP](https://github.com/jlowin/fastmcp)
- Domain models with [Pydantic](https://docs.pydantic.dev/)
- Cloudflare bypass via [cloudscraper](https://github.com/VeNoMouS/cloudscraper)
- Discourse API documentation at [docs.discourse.org](https://docs.discourse.org/)
