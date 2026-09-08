---
name: rig-docker-stack
description: Start and manage the RIG agentic tools Docker stack (n8n, LangFuse, Dify) via Colima on macOS
triggers:
  - docker stack
  - start n8n
  - start langfuse
  - start dify
  - colima start
---

# RIG Docker Stack

## Prerequisites
- Colima installed (lightweight Docker Desktop alternative)
- Docker CLI installed

## Start Colima
```bash
colima start
export DOCKER_HOST=unix://$HOME/.colima/default/docker.sock
```

## Start All Services
```bash
cd $HOME/.hermes/jake/missions/ralph-nova-week2-2026-07-08/docker-stack
export DOCKER_HOST=unix://$HOME/.colima/default/docker.sock
docker compose up -d
```

## Services
| Service | Port | URL | Credentials |
|---------|------|-----|-------------|
| n8n | 5678 | http://localhost:5678 | admin / rig2026 |
| LangFuse v2 | 3000 | http://localhost:3000 | Create account on first visit |
| Dify API | 8080 | http://localhost:8080 | - |
| Dify Web | 8081 | http://localhost:8081 | - |
| Weaviate | internal | - | - |
| PostgreSQL x2 | internal | - | langfuse:langfuse, dify:dify |
| Redis | internal | - | - |

## Health Checks
```bash
curl -s http://localhost:5678/healthz
curl -s http://localhost:3000/api/public/health
```

## Pitfalls
- Docker Desktop daemon may not start — use Colima instead
- LangFuse v3 requires ClickHouse — use v2 image (`langfuse/langfuse:2`)
- crewai/crewai Docker image does NOT exist on Docker Hub
- LangFuse container may need manual network fix: `docker network connect docker-stack_default rig-langfuse`
- If container fails to start, check: `docker logs rig-langfuse`

## docker-compose.yml Location
`$HOME/.hermes/jake/missions/ralph-nova-week2-2026-07-08/docker-stack/docker-compose.yml`

## Stop All
```bash
docker compose down
colima stop
```
