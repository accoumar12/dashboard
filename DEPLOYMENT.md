# Deployment Guide

## Quick Start with Docker Compose

### Prerequisites
- Docker and Docker Compose installed
- Port 80 (frontend) and 8000 (backend) available

### Deploy

```bash
# Build and start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

Visit `http://your-domain.com` to access the dashboard!

## Configuration

### Environment Variables

Edit the `docker-compose.yml` file to configure:

```yaml
environment:
  - APP_DEBUG=false
  - APP_MAX_DATABASES=100           # Maximum uploaded databases
  - APP_MAX_UPLOAD_SIZE_MB=50       # Maximum file size
  - APP_SESSION_EXPIRY_DAYS=7       # Session lifetime
  - APP_CLEANUP_INTERVAL_HOURS=6    # Cleanup frequency
  - APP_QUERY_TIMEOUT_SECONDS=30    # Query timeout
```

### Custom Domain

1. Update your DNS to point to your server
2. Modify `frontend/nginx.conf` to add your domain:
   ```nginx
   server_name yourdomain.com;
   ```
3. Rebuild: `docker-compose up -d --build frontend`

### HTTPS with SSL

For production, add SSL using a reverse proxy like Caddy or nginx:

**Option 1: Using Caddy (Recommended)**

Create `Caddyfile`:
```
yourdomain.com {
    reverse_proxy localhost:80
}
```

Run Caddy:
```bash
docker run -d \
  -p 80:80 -p 443:443 \
  -v $PWD/Caddyfile:/etc/caddy/Caddyfile \
  -v caddy_data:/data \
  caddy
```

**Option 2: Using Certbot**

```bash
# Install certbot
sudo apt install certbot

# Get certificate
sudo certbot certonly --standalone -d yourdomain.com

# Update nginx config with SSL
# Rebuild frontend
```

## Production Considerations

### 1. Resource Limits

Add to `docker-compose.yml`:
```yaml
services:
  backend:
    deploy:
      resources:
        limits:
          cpus: '1.0'
          memory: 1G
```

### 2. Persistent Data

Uploads are persisted in `./backend/uploads` via Docker volume.

### 3. Backups

```bash
# Backup uploads
tar -czf uploads-backup-$(date +%Y%m%d).tar.gz backend/uploads/

# Backup playground database
cp backend/playground.db playground-backup-$(date +%Y%m%d).db
```

### 4. Monitoring

Check health:
```bash
# Backend health
curl http://localhost:8000/api/health

# Frontend health
curl http://localhost:80
```

View logs:
```bash
docker-compose logs -f backend
docker-compose logs -f frontend
```

### 5. Updates

```bash
# Pull latest changes
git pull

# Rebuild and restart
docker-compose up -d --build

# Remove old images
docker image prune -f
```

## Troubleshooting

### Port Already in Use
```bash
# Change ports in docker-compose.yml
ports:
  - "8080:80"    # Frontend on 8080
  - "8001:8000"  # Backend on 8001
```

### Build Fails
```bash
# Clean build
docker-compose down
docker system prune -a
docker-compose up -d --build
```

### Backend Not Accessible
```bash
# Check backend logs
docker-compose logs backend

# Verify backend is running
docker-compose ps

# Test directly
curl http://localhost:8000/api/health
```

### File Upload Issues
```bash
# Check uploads directory permissions
ls -la backend/uploads
chmod 777 backend/uploads  # Or appropriate permissions
```

## Scaling

For high traffic, consider:
- Running multiple backend instances behind a load balancer
- Using external storage for uploads (S3, etc.)
- Adding Redis for session management
- Database clustering if switching to PostgreSQL
