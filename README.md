# YTM Backend API

FastAPI backend for YouTube Music Downloader

## Features

- User authentication (JWT)
- YouTube video info & search
- Audio download & conversion (yt-dlp + ffmpeg)
- Subscription management (Stripe)
- Rate limiting (Free: 3/day, Pro: unlimited)

## Tech Stack

- **Framework:** FastAPI
- **Database:** PostgreSQL + SQLAlchemy
- **Cache:** Redis
- **YouTube:** yt-dlp
- **Audio:** FFmpeg
- **Payments:** Stripe

## Quick Start

### Docker (Recommended)

```bash
# Copy env file
cp .env.example .env

# Edit .env with your settings
nano .env

# Start services
docker-compose up -d

# API available at http://localhost:8000
```

### Manual Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export DATABASE_URL="postgresql+asyncpg://user:pass@localhost/ytm"
export SECRET_KEY="your-secret-key"

# Run migrations
alembic upgrade head

# Start server
uvicorn app.main:app --reload
```

## API Endpoints

### Authentication
- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - Login
- `POST /api/auth/refresh` - Refresh token
- `GET /api/auth/me` - Get current user

### Videos
- `GET /api/videos/info?url=` - Get video metadata
- `GET /api/videos/search?q=` - Search YouTube
- `GET /api/videos/playlist?url=` - Get playlist videos

### Downloads
- `POST /api/downloads` - Create download request
- `GET /api/downloads` - List user downloads
- `GET /api/downloads/{id}` - Get download status
- `GET /api/downloads/{id}/file` - Download file
- `DELETE /api/downloads/{id}` - Delete download

### Webhooks
- `POST /api/webhooks/stripe` - Stripe webhook

## Deployment

### Hetzner/Contabo VPS

```bash
# SSH into server
ssh root@your-server-ip

# Install Docker
curl -fsSL https://get.docker.com | sh

# Clone repo
git clone https://github.com/yourusername/ytm-backend.git
cd ytm-backend

# Setup environment
cp .env.example .env
nano .env

# Start with Docker Compose
docker-compose up -d

# Setup reverse proxy (nginx/caddy)
```

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `SECRET_KEY` | JWT signing key | required |
| `DATABASE_URL` | PostgreSQL URL | required |
| `REDIS_URL` | Redis URL | localhost:6379 |
| `STRIPE_SECRET_KEY` | Stripe API key | optional |
| `FREE_DAILY_LIMIT` | Free tier limit | 3 |

## License

Proprietary
