# Deployment Guide - Banking Chat API

## Server Specs
- **Droplet Type:** Premium AMD
- **CPU:** 8 vCPUs (AMD EPYC)
- **RAM:** 16 GB
- **Storage:** 320 GB NVMe SSD
- **IP:** 157.245.115.120
- **Ports:** 8000 (API), 11434 (Ollama)

---

## Initial Server Setup

### 1. Install Docker & Docker Compose
```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Verify installation
docker --version
docker compose version
```

### 2. Configure Firewall
```bash
# Allow SSH and app ports
ufw allow OpenSSH
ufw allow 8000/tcp
ufw --force enable

# Check status
ufw status
```

### 3. Clone Repository
```bash
cd /root
git clone https://github.com/YOUR_USERNAME/OnlineBanking_Chat.git
cd OnlineBanking_Chat
```

---

## Deployment

### Start Services
```bash
# From project directory
cd /root/OnlineBanking_Chat

# Build and start all containers
docker compose up -d

# Watch logs
docker compose logs -f
```

### Pull Ollama Model (First Time Only)
```bash
# Pull the LLM model
docker exec ollama ollama pull llama3.2:latest

# Verify model is downloaded
docker exec ollama ollama list
```

### Test Deployment
```bash
# Test locally on server
curl -s http://localhost:8000/chat -X POST \
  -H "Content-Type: application/json" \
  -d '{"accountId":"A123","message":"last 5 transactions"}'

# Test externally from your machine
curl -s http://157.245.115.120:8000/chat -X POST \
  -H "Content-Type: application/json" \
  -d '{"accountId":"A123","message":"last 5 transactions"}'
```

---

## Easy Redeployment

### One-Command Redeploy Script
```bash
# Create redeploy script
cat > /root/redeploy.sh << 'EOF'
#!/bin/bash
cd /root/OnlineBanking_Chat
git pull origin main
docker compose down
docker compose up -d --build
echo "✅ Redeployed successfully!"
docker compose ps
EOF

# Make executable
chmod +x /root/redeploy.sh
```

### Deploy Updates
```bash
# Simply run this whenever you push changes to GitHub
/root/redeploy.sh
```

---

## Useful Commands

### Container Management
```bash
# View running containers
docker compose ps

# View logs (all services)
docker compose logs -f

# View logs (specific service)
docker compose logs -f api
docker compose logs -f ollama

# Restart services
docker compose restart

# Stop services
docker compose down

# Start services
docker compose up -d
```

### Ollama Management
```bash
# List available models
docker exec ollama ollama list

# Pull a different model
docker exec ollama ollama pull llama3.1:8b

# Remove a model
docker exec ollama ollama rm llama3.2:latest
```

### System Monitoring
```bash
# Check disk usage
df -h

# Check memory usage
free -h

# Check Docker disk usage
docker system df

# Clean up unused Docker resources
docker system prune -a
```

### Health Checks
```bash
# Check API health endpoint
curl http://localhost:8000/health

# Check Ollama service
curl http://localhost:11434/api/tags

# View container resource usage
docker stats
```

---

## Configuration

### Environment Variables
Edit `.env` file (not tracked in git):
```bash
TOOL_BASE_URL=http://localhost:8000
OLLAMA_URL=http://ollama:11434/v1/chat/completions
OLLAMA_MODEL=llama3.2:latest
```

### Change Model
To use a different model:
1. Pull new model: `docker exec ollama ollama pull MODEL_NAME`
2. Update docker-compose.yml: `OLLAMA_MODEL=MODEL_NAME`
3. Restart: `docker compose restart api`

---

## Troubleshooting

### Containers Not Starting
```bash
# Check logs for errors
docker compose logs

# Check container status
docker compose ps

# Rebuild from scratch
docker compose down -v
docker compose up -d --build
```

### Model Not Found Error
```bash
# Ensure model is pulled
docker exec ollama ollama list

# Pull model if missing
docker exec ollama ollama pull llama3.2:latest

# Restart API container
docker compose restart api
```

### Port Already in Use
```bash
# Find process using port 8000
lsof -i :8000

# Kill the process
kill -9 <PID>

# Or change port in docker-compose.yml
```

### Out of Disk Space
```bash
# Check disk usage
df -h

# Clean Docker resources
docker system prune -a -f

# Remove old images
docker image prune -a
```

---

## Performance Optimization

### Current Setup
- Model: llama3.2:3b (~2GB)
- Expected response time: 150-300ms
- Concurrent users: 200+

### Upgrade to Larger Model
```bash
# For better accuracy (slower, ~500ms-1s)
docker exec ollama ollama pull llama3.1:8b

# Update docker-compose.yml
# OLLAMA_MODEL=llama3.1:8b

# Restart
docker compose restart api
```

---

## Backup & Recovery

### Backup Ollama Models
```bash
# Models stored in Docker volume
docker volume inspect onlinebanking_chat_ollama_data

# Create backup
docker run --rm -v onlinebanking_chat_ollama_data:/data -v $(pwd):/backup \
  ubuntu tar czf /backup/ollama_backup.tar.gz -C /data .
```

### Restore from Backup
```bash
# Restore models
docker run --rm -v onlinebanking_chat_ollama_data:/data -v $(pwd):/backup \
  ubuntu tar xzf /backup/ollama_backup.tar.gz -C /data
```

---

## Security Notes

- Firewall enabled (UFW)
- Only ports 22, 8000 exposed
- No HTTPS yet (consider adding nginx + Let's Encrypt)
- No authentication on API (add if exposing publicly)

---

## Production Checklist

- [ ] Set up domain name (optional)
- [ ] Add HTTPS/SSL with nginx reverse proxy
- [ ] Implement API authentication
- [ ] Set up monitoring (Prometheus/Grafana)
- [ ] Configure automated backups
- [ ] Add rate limiting
- [ ] Set up error tracking (Sentry)
- [ ] Create automated tests
- [ ] Set up CI/CD pipeline

---

## Quick Reference

**Redeploy:** `/root/redeploy.sh`
**Logs:** `docker compose logs -f`
**Restart:** `docker compose restart`
**Status:** `docker compose ps`
**Test API:** `curl http://localhost:8000/chat -X POST -H "Content-Type: application/json" -d '{"accountId":"A123","message":"test"}'`
