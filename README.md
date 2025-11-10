# AdNauseam Browser Automation

<div align="center">

![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?logo=docker&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.11-3776AB?logo=python&logoColor=white)
![Selenium](https://img.shields.io/badge/Selenium-4.15-43B02A?logo=selenium&logoColor=white)
![GitHub Workflow Status](https://img.shields.io/github/actions/workflow/status/Boblepointu/AdNauseamSelenium/docker-build-push.yml)
![License](https://img.shields.io/github/license/Boblepointu/AdNauseamSelenium)

**Advanced browser automation with sophisticated anti-fingerprinting and persona management**

[Features](#-features) • [Quick Start](#-quick-start) • [Documentation](#-documentation) • [Contributing](#-contributing)

</div>

---

## 🎯 Overview

AdNauseam Browser Automation is a sophisticated browser automation framework designed for:

- 🎭 **Anti-Fingerprinting** - Advanced techniques to avoid browser fingerprinting
- 🔄 **Persona Management** - Persistent browser identities across sessions
- 🤖 **Human-like Behavior** - Natural mouse movements, typing patterns, and scrolling
- 🌐 **Multi-Browser Support** - Chrome, Firefox, Edge across multiple versions
- 📊 **Scalable** - Selenium Grid architecture for distributed execution
- 🐳 **Docker-First** - Fully containerized with pre-built images

---

## ✨ Features

### Advanced Anti-Fingerprinting

- **Hardware Diversity**: Randomized CPU cores, memory, GPU configurations
- **Connection Simulation**: Various connection types (4G, wifi, ethernet, etc.)
- **Battery API Spoofing**: Realistic battery status randomization
- **Media Devices**: Simulated cameras and microphones
- **Custom Font Sets**: Unique font lists per persona
- **WebRTC Protection**: Leak prevention and IP masking
- **Plugin Randomization**: Browser extensions and plugins diversity
- **Canvas Fingerprinting**: Protection against canvas-based tracking

### Human-like Behavior

- **Bézier Curve Mouse Movement**: Natural cursor trajectories
- **Realistic Typing**: Variable speed with occasional typos
- **Natural Scrolling**: Smooth, human-like scroll patterns
- **Random Pauses**: Unpredictable wait times between actions
- **Cookie Banner Handling**: Automatic detection and interaction
- **Micro-movements**: Small, realistic cursor adjustments

### Persistent Persona Management

- **Save/Load Fingerprints**: Reuse browser identities across sessions
- **Rotation Strategies**: Weighted, random, round-robin, or always-new
- **Automatic Cleanup**: Remove old or overused personas
- **Statistics Tracking**: Monitor persona usage and effectiveness
- **Docker Volume Integration**: Persistent storage across container restarts

---

## 🚀 Quick Start

### Using Pre-built Images (Recommended)

```bash
# Pull the latest image from GitHub Container Registry
docker pull ghcr.io/boblepointu/adnauseamselenium:latest

# Run with production docker-compose
docker-compose -f docker-compose.production.yml up -d

# View logs
docker-compose -f docker-compose.production.yml logs -f
```

### Building from Source

```bash
# Clone the repository
git clone https://github.com/Boblepointu/AdNauseamSelenium.git
cd AdNauseamSelenium

# Build the Docker image
docker build -t adnauseam-automation:local .

# Run with the full development stack
docker-compose up -d
```

### Manual Execution (Development)

```bash
# Install dependencies
pip install -r requirements.txt

# Run locally (requires Selenium Grid)
export SELENIUM_HUB=localhost:4444
python3 crawl.py
```

---

## 📚 Documentation

- **[DOCKER.md](DOCKER.md)** - Complete Docker and CI/CD documentation
- **[ANTI_DETECTION.md](doc/ANTI_DETECTION.md)** - Anti-detection techniques
- **[BOT_CHALLENGE_BYPASS.md](doc/BOT_CHALLENGE_BYPASS.md)** - Bot challenge bypass strategies
- **[FINGERPRINTING_COVERAGE.md](doc/FINGERPRINTING_COVERAGE.md)** - Fingerprinting protection coverage
- **[COOKIE_BANNERS_UPDATE.md](doc/COOKIE_BANNERS_UPDATE.md)** - Cookie banner handling

---

## 🏗️ Architecture

### Selenium Grid Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Selenium Hub                         │
│                   (Load Balancer)                       │
└─────────────────────────────────────────────────────────┘
                         │
         ┌───────────────┼───────────────┐
         │               │               │
┌────────▼────────┐ ┌───▼────────┐ ┌───▼────────┐
│  Chrome Nodes   │ │Firefox Nodes│ │ Edge Nodes │
│  Multiple       │ │  Multiple   │ │  Multiple  │
│  Versions       │ │  Versions   │ │  Versions  │
└─────────────────┘ └─────────────┘ └────────────┘
         │               │               │
         └───────────────┴───────────────┘
                         │
         ┌───────────────┴───────────────┐
         │                               │
┌────────▼────────┐            ┌─────────▼────────┐
│   Automation    │    ...     │   Automation     │
│   Instance 1    │            │   Instance N     │
│   (Container)   │            │   (Container)    │
└─────────────────┘            └──────────────────┘
```

### Components

- **Selenium Hub**: Orchestrates browser sessions
- **Browser Nodes**: Chrome (v95-latest), Firefox (v98-latest), Edge (v114-latest)
- **Automation Instances**: Python containers running the automation scripts
- **Shared Volume**: Persistent persona storage

---

## ⚙️ Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `SELENIUM_HUB` | `selenium-hub:4444` | Selenium Grid hub address |
| `PERSONA_ROTATION_STRATEGY` | `weighted` | Persona rotation strategy |
| `PERSONA_MAX_AGE_DAYS` | `30` | Maximum age for reusable personas (days) |
| `PERSONA_MAX_USES` | `100` | Maximum uses per persona |

### Persona Rotation Strategies

- **`weighted`** - Favors less-used personas (recommended for diversity)
- **`random`** - Completely random selection
- **`round-robin`** - Least recently used first
- **`new`** - Always create new personas (no reuse)

---

## 🐳 Docker Images

### Available Tags

Images are automatically built and published to GitHub Container Registry:

- `latest` - Latest stable build
- `v*.*.*` - Semantic version tags
- `main` - Latest build from main branch
- `<branch>-<sha>` - Specific commit builds

### Multi-platform Support

- ✅ `linux/amd64` (Intel/AMD)
- ✅ `linux/arm64` (ARM, including Apple Silicon)

### Example Usage

```bash
# Pull specific version
docker pull ghcr.io/boblepointu/adnauseamselenium:v1.0.0

# Run with custom configuration
docker run --rm \
  -e SELENIUM_HUB=my-grid:4444 \
  -e PERSONA_ROTATION_STRATEGY=random \
  -v personas:/app/data/personas \
  ghcr.io/boblepointu/adnauseamselenium:latest
```

---

## 📦 Project Structure

```
AdNauseamSelenium/
├── .github/
│   └── workflows/
│       └── docker-build-push.yml    # CI/CD workflow
├── doc/                              # Documentation
│   ├── ANTI_DETECTION.md
│   ├── BOT_CHALLENGE_BYPASS.md
│   ├── FINGERPRINTING_COVERAGE.md
│   └── ...
├── crawl.py                          # Main automation script (5800+ lines)
├── persona_manager.py                # Persona management system
├── websites.txt                      # Target website list
├── Dockerfile                        # Production Docker image
├── docker-compose.yml                # Development stack (20+ services)
├── docker-compose.production.yml     # Production stack (GHCR images)
├── docker-entrypoint.sh              # Container entrypoint
├── requirements.txt                  # Python dependencies
├── .dockerignore                     # Docker build exclusions
├── DOCKER.md                         # Docker documentation
└── README.md                         # This file
```

---

## 🔧 Development

### Prerequisites

- Docker 24.0+ and Docker Compose
- Python 3.11+ (for local development)
- Git

### Local Development Setup

```bash
# Clone the repository
git clone https://github.com/Boblepointu/AdNauseamSelenium.git
cd AdNauseamSelenium

# Start the full development stack
docker-compose up -d

# View Selenium Grid status
open http://localhost:4444

# Watch automation logs
docker-compose logs -f browser-automation-1

# Stop all services
docker-compose down
```

### Building Custom Images

```bash
# Build with custom tag
docker build -t my-automation:custom .

# Build for specific platform
docker buildx build --platform linux/arm64 -t my-automation:arm64 .

# Build multi-platform
docker buildx build --platform linux/amd64,linux/arm64 -t my-automation:multi .
```

---

## 🚀 Deployment

### Docker Compose (Production)

```bash
# Use pre-built images from GHCR
docker-compose -f docker-compose.production.yml up -d

# Scale automation instances
docker-compose -f docker-compose.production.yml up -d --scale browser-automation=10

# Update to latest image
docker-compose -f docker-compose.production.yml pull
docker-compose -f docker-compose.production.yml up -d
```

### Kubernetes

See [DOCKER.md](DOCKER.md) for Kubernetes deployment examples.

### Cloud Platforms

The Docker images work on all major cloud platforms:
- ✅ AWS ECS/Fargate
- ✅ Google Cloud Run
- ✅ Azure Container Instances
- ✅ DigitalOcean App Platform
- ✅ Fly.io

---

## 🧪 Testing

### Local Testing

```bash
# Test the Docker image build
docker build -t test-automation .

# Validate Python imports
docker run --rm test-automation python3 -c "from persona_manager import PersonaManager; print('✓ OK')"

# Run with test configuration
docker run --rm \
  -e SELENIUM_HUB=selenium-hub:4444 \
  test-automation
```

### CI/CD Testing

All pull requests automatically trigger:
- ✅ Docker image build validation
- ✅ Multi-platform build tests
- ✅ Layer optimization checks

---

## 📊 Monitoring

### Container Health

```bash
# Check health status
docker ps --filter "health=healthy"

# View health check logs
docker inspect <container_id> | jq '.[0].State.Health'
```

### Application Logs

```bash
# Follow logs for all automation instances
docker-compose logs -f --tail=100

# Filter by service
docker-compose logs -f browser-automation-1

# Search for errors
docker-compose logs | grep ERROR
```

### Persona Statistics

Personas are stored in `/app/data/personas/personas.json`:

```bash
# View persona statistics
docker exec <container> cat /app/data/personas/personas.json | jq '.metadata'
```

---

## 🛠️ Troubleshooting

### Issue: Selenium Hub connection failed

```bash
# Verify hub is running
docker-compose ps selenium-hub

# Check hub status
curl http://localhost:4444/status

# View hub logs
docker-compose logs selenium-hub
```

### Issue: Personas not persisting

```bash
# Check volume mount
docker volume inspect adnauseamselenium_personas-data

# Verify permissions
docker exec <container> ls -la /app/data/personas
```

### Issue: Out of memory

```bash
# Increase Docker memory limit
docker-compose up -d --scale browser-automation=5

# Set memory limits in docker-compose.yml
services:
  browser-automation:
    mem_limit: 4g
    shm_size: 2gb
```

For more troubleshooting, see [DOCKER.md](DOCKER.md#-troubleshooting).

---

## 🤝 Contributing

Contributions are welcome! Here's how to get started:

1. **Fork** the repository
2. **Create** a feature branch (`git checkout -b feature/amazing-feature`)
3. **Commit** your changes (`git commit -m 'Add amazing feature'`)
4. **Push** to the branch (`git push origin feature/amazing-feature`)
5. **Open** a Pull Request

### Development Guidelines

- Follow PEP 8 style guide for Python code
- Add docstrings to all functions and classes
- Update documentation for new features
- Test Docker builds locally before submitting PR
- Keep commits atomic and well-described

---

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- **[Selenium](https://www.selenium.dev/)** - Browser automation framework
- **[AdNauseam](https://adnauseam.io/)** - Inspiration for anti-fingerprinting techniques
- **[Docker](https://www.docker.com/)** - Containerization platform
- **[GitHub Actions](https://github.com/features/actions)** - CI/CD automation

---

## 📞 Support

- 🐛 **Issues**: [GitHub Issues](https://github.com/Boblepointu/AdNauseamSelenium/issues)
- 💬 **Discussions**: [GitHub Discussions](https://github.com/Boblepointu/AdNauseamSelenium/discussions)
- 📖 **Documentation**: [Project Wiki](https://github.com/Boblepointu/AdNauseamSelenium/wiki)

---

## 🗺️ Roadmap

- [ ] Web UI for persona management
- [ ] Prometheus metrics export
- [ ] Grafana dashboards
- [ ] Tor network integration
- [ ] Proxy rotation support
- [ ] Browser extension injection
- [ ] CAPTCHA solving integration
- [ ] Distributed persona sharing

---

<div align="center">

**Made with ❤️ for privacy and automation**

⭐ Star this repository if you find it useful!

</div>

