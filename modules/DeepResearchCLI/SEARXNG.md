# SearxNG Management Guide

This guide explains how to manage your SearxNG installation for the Deep Research CLI.

## 🎯 Quick Reference

```bash
# Check SearxNG status
./scripts/status-searxng.sh

# Start SearxNG (local)
./scripts/start-searxng.sh

# Stop SearxNG (local)
./scripts/stop-searxng.sh
```

## 📦 Installation Types

### Docker Installation (Recommended)

**Pros:**
- Easy to manage
- Isolated environment
- Automatic restart
- No Python conflicts

**Cons:**
- Requires Docker/OrbStack

**Management:**
```bash
# Check status
docker ps | grep searxng

# Start
docker start searxng

# Stop
docker stop searxng

# View logs
docker logs searxng

# Remove
docker rm -f searxng
```

### Local Installation

**Pros:**
- No Docker required
- Direct control
- Easy debugging

**Cons:**
- Manual management
- Needs Python 3
- Port conflicts possible

**Management:**
```bash
# Start (with helper script)
./scripts/start-searxng.sh

# Stop (with helper script)
./scripts/stop-searxng.sh

# Check status
./scripts/status-searxng.sh

# Manual start
cd searxng-local
source venv/bin/activate
export SEARXNG_SETTINGS_PATH=searx/settings.yml
python -m searx.webapp

# Check logs (if started by setup.sh)
tail -f logs/searxng.log
```

## 🔧 Configuration

### Change Port

**Docker:**
```bash
# Stop and remove old container
docker stop searxng
docker rm searxng

# Start with new port
docker run -d \
  --name searxng \
  -p 9090:8080 \
  -v "$(pwd)/searxng-config.yml:/etc/searxng/settings.yml:ro" \
  --restart unless-stopped \
  searxng/searxng:latest

# Update .env
sed -i.bak 's|SEARXNG_BASE_URL=.*|SEARXNG_BASE_URL=http://localhost:9090|' .env
```

**Local:**
```bash
# Edit start script to use different port
./scripts/start-searxng.sh 9090

# Or manually set in settings
# Edit searxng-local/searx/settings.yml
```

### Update SearxNG URL in .env

```bash
# Edit .env file
nano .env

# Change the line:
SEARXNG_BASE_URL=http://localhost:8080

# To your desired URL
```

## 🐛 Troubleshooting

### "Cannot connect to SearxNG"

**Check if running:**
```bash
./scripts/status-searxng.sh
```

**Docker:**
```bash
docker ps | grep searxng
# If not running:
docker start searxng
```

**Local:**
```bash
# Check if process exists
ps aux | grep searx

# Check PID file
cat searxng.pid

# Start if not running
./scripts/start-searxng.sh
```

### "Port already in use"

**Find what's using the port:**
```bash
lsof -i :8080
```

**Kill the process:**
```bash
kill <PID>
```

**Or use a different port:**
```bash
./scripts/start-searxng.sh 8081
```

### "JSON API not working"

**Check settings file:**
```bash
# Docker
docker exec searxng cat /etc/searxng/settings.yml | grep -A5 "formats:"

# Local
cat searxng-local/searx/settings.yml | grep -A5 "formats:"
```

Should include:
```yaml
formats:
  - html
  - json
```

**Restart SearxNG:**
```bash
# Docker
docker restart searxng

# Local
./scripts/stop-searxng.sh
./scripts/start-searxng.sh
```

### Check logs

**Docker:**
```bash
docker logs searxng
docker logs -f searxng  # Follow logs
```

**Local:**
```bash
tail -f logs/searxng.log

# Or if started manually
tail -f nohup.out
```

## 🔄 Switching Between Docker and Local

### From Docker to Local

```bash
# Stop Docker container
docker stop searxng

# Start local instance
./scripts/start-searxng.sh

# .env is automatically updated
```

### From Local to Docker

```bash
# Stop local instance
./scripts/stop-searxng.sh

# Start Docker container
docker start searxng

# Update .env
./setup.sh  # Or manually edit .env
```

## 📊 Performance Tips

### For Heavy Research Tasks

**Increase concurrent requests (Docker):**
```yaml
# In searxng-config.yml
server:
  limiter: false
  workers: 4
```

**Restart after changes:**
```bash
docker restart searxng
```

### Memory Issues

**Docker - increase limits:**
```bash
docker update --memory="2g" --memory-swap="2g" searxng
```

**Local - increase Python workers:**
```bash
# Edit searxng-local/searx/settings.yml
server:
  workers: 2  # Increase this
```

## 🚀 Auto-start on Boot

### Docker (already configured)
```bash
# Docker containers start automatically with --restart unless-stopped
docker update --restart=always searxng
```

### Local (macOS - launchd)

Create `~/Library/LaunchAgents/com.searxng.plist`:
```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.searxng</string>
    <key>ProgramArguments</key>
    <array>
        <string>/path/to/DeepResearchCLI/scripts/start-searxng.sh</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
</dict>
</plist>
```

Load it:
```bash
launchctl load ~/Library/LaunchAgents/com.searxng.plist
```

### Local (Linux - systemd)

Create `/etc/systemd/system/searxng.service`:
```ini
[Unit]
Description=SearxNG Search Engine
After=network.target

[Service]
Type=simple
User=your-username
WorkingDirectory=/path/to/DeepResearchCLI/searxng-local
ExecStart=/path/to/DeepResearchCLI/scripts/start-searxng.sh
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable searxng
sudo systemctl start searxng
sudo systemctl status searxng
```

## 📞 Support

If you encounter issues:

1. Check status: `./scripts/status-searxng.sh`
2. View logs (Docker: `docker logs searxng`, Local: `tail -f logs/searxng.log`)
3. Try `deep-research test-search` to diagnose
4. Restart SearxNG
5. Check [SearxNG documentation](https://docs.searxng.org/)

## 🔗 Useful Links

- [SearxNG Documentation](https://docs.searxng.org/)
- [SearxNG GitHub](https://github.com/searxng/searxng)
- [SearxNG Settings](https://docs.searxng.org/admin/settings/)
