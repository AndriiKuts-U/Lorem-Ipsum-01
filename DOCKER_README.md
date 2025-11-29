# Docker Setup Guide

## Prerequisites
- Docker and Docker Compose installed on your system
- Environment variables configured (see below)

## Environment Variables

Copy `.env.example` to `.env` and fill in your actual values:

```bash
cp .env.example .env
```

Required environment variables:
- `OPENAI_API_KEY` - Your OpenAI API key
- `QDRANT_DATABASE_URL` - Your Qdrant database URL
- `QDRANT_API_KEY` - Your Qdrant API key

## Running the Application

### Start all services:
```bash
docker-compose up -d
```

### View logs:
```bash
docker-compose logs -f
```

### Stop all services:
```bash
docker-compose down
```

## Services

The application consists of three services:

1. **Backend** (FastAPI) - Port 8000
   - API endpoints for RAG system
   - Direct access: http://localhost:8000

2. **Frontend** (React/Vite) - Port 5173
   - User interface
   - Direct access: http://localhost:5173

3. **Nginx** (Reverse Proxy) - Port 80
   - Routes requests between frontend and backend
   - Main access point: http://localhost
   - API requests: http://localhost/api/*

## Architecture

```
Browser → Nginx (port 80) → Frontend (port 5173)
                         → Backend (port 8000) [/api/*]
```

- Frontend requests go to `/`
- Backend API requests go to `/api/*` (nginx strips the `/api` prefix)

## Development

To rebuild after code changes:

```bash
docker-compose up -d --build
```

To rebuild a specific service:

```bash
docker-compose up -d --build backend
docker-compose up -d --build frontend
```

## Troubleshooting

View service logs:
```bash
docker-compose logs backend
docker-compose logs frontend
docker-compose logs nginx
```

Access running container:
```bash
docker exec -it dtit25-backend bash
docker exec -it dtit25-frontend sh
```

Check service health:
```bash
curl http://localhost/api/
curl http://localhost:8000/
curl http://localhost:5173/
```
