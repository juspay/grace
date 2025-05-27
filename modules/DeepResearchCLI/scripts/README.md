# Helper Scripts

This directory contains utility scripts for managing the Deep Research CLI.

## 📝 Scripts Overview

### SearxNG Management

| Script | Purpose | Usage |
|--------|---------|-------|
| `start-searxng.sh` | Start local SearxNG instance | `./scripts/start-searxng.sh [port]` |
| `stop-searxng.sh` | Stop local SearxNG instance | `./scripts/stop-searxng.sh` |
| `status-searxng.sh` | Check SearxNG status (Docker & local) | `./scripts/status-searxng.sh` |

## 🚀 Quick Start

### Check SearxNG Status
```bash
./scripts/status-searxng.sh
```

Shows:
- Docker container status
- Local installation status
- Running processes
- Connectivity test
- JSON API test

### Start SearxNG (Local)
```bash
# Default port (32768 - matches Docker)
./scripts/start-searxng.sh

# Custom port
./scripts/start-searxng.sh 9090
```

Features:
- Activates virtual environment
- Sets environment variables
- Updates .env automatically
- Starts in background
- Shows access URL

### Stop SearxNG (Local)
```bash
./scripts/stop-searxng.sh
```

Features:
- Finds process by PID file
- Gracefully stops process
- Cleans up PID file
- Force kills if needed

## 📋 Examples

### Typical Workflow

```bash
# 1. Check if SearxNG is running
./scripts/status-searxng.sh

# 2. Start if not running
./scripts/start-searxng.sh

# 3. Test with deep-research
deep-research test-search

# 4. Stop when done
./scripts/stop-searxng.sh
```

### Troubleshooting

```bash
# Check detailed status
./scripts/status-searxng.sh

# View logs (if started by setup.sh)
tail -f logs/searxng.log

# Restart SearxNG
./scripts/stop-searxng.sh
./scripts/start-searxng.sh

# Use different port
./scripts/start-searxng.sh 8081
```

### Docker vs Local

```bash
# Check what's running
./scripts/status-searxng.sh

# Output shows both Docker and local status
# Use the appropriate commands for your setup
```

## 🔧 Script Details

### start-searxng.sh

**Arguments:**
- `$1` (optional): Port number (default: 8080)

**Environment Variables Set:**
- `SEARXNG_SETTINGS_PATH`: Path to settings.yml

**Actions:**
1. Checks for SearxNG installation
2. Activates Python virtual environment
3. Sets configuration path
4. Starts SearxNG server
5. Updates .env with correct URL

**Example:**
```bash
# Start on default port
./scripts/start-searxng.sh

# Start on port 9090
./scripts/start-searxng.sh 9090
```

### stop-searxng.sh

**No arguments required**

**Actions:**
1. Reads PID from `searxng.pid`
2. Checks if process is running
3. Sends SIGTERM to process
4. Waits 2 seconds
5. Force kills if still running
6. Removes PID file

**Example:**
```bash
./scripts/stop-searxng.sh
```

### status-searxng.sh

**No arguments required**

**Checks:**
- .env configuration
- Docker container status
- Local installation
- Process status (via PID file)
- HTTP connectivity
- JSON API functionality

**Example:**
```bash
./scripts/status-searxng.sh
```

## 📁 Related Files

- `searxng.pid` - Process ID of running SearxNG (created by setup.sh or start script)
- `logs/searxng.log` - Output log (if started by setup.sh)
- `.env` - Configuration file (updated by scripts)
- `SEARXNG.md` - Comprehensive SearxNG management guide

## 🐛 Common Issues

### "Command not found"
Make sure scripts are executable:
```bash
chmod +x scripts/*.sh
```

### "SearxNG not found"
Run setup first:
```bash
./setup.sh
```

### "Port already in use"
Use a different port:
```bash
./scripts/start-searxng.sh 8081
```

### "Cannot connect"
Check if SearxNG is running:
```bash
./scripts/status-searxng.sh
ps aux | grep searx
```

## 📞 Support

For more detailed SearxNG management:
- See [SEARXNG.md](../SEARXNG.md)
- Run `./scripts/status-searxng.sh` for diagnostics
- Check logs: `tail -f logs/searxng.log`

## ✨ Tips

1. **Auto-start on boot**: See SEARXNG.md for systemd/launchd setup
2. **Multiple instances**: Use different ports for multiple SearxNG instances
3. **Monitoring**: Use status script in cron jobs for monitoring
4. **Logs**: Check `logs/searxng.log` for debugging

---

*Part of GRACE Deep Research CLI*
