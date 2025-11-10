# AdNauseam Browser Automation - Docker Images

<div align="center">

![Docker Image Version](https://img.shields.io/docker/v/ghcr.io/boblepointu/adnauseamselenium/latest?logo=docker)
![Docker Image Size](https://img.shields.io/docker/image-size/ghcr.io/boblepointu/adnauseamselenium/latest)
![GitHub Workflow Status](https://img.shields.io/github/actions/workflow/status/Boblepointu/AdNauseamSelenium/docker-build-push.yml)
![License](https://img.shields.io/github/license/Boblepointu/AdNauseamSelenium)

**Advanced browser automation with sophisticated anti-fingerprinting capabilities**

</div>

---

## 🚀 Quick Start

### Using Pre-built Images from GitHub Container Registry

```bash
# Pull the latest image
docker pull ghcr.io/boblepointu/adnauseamselenium:latest

# Run with docker-compose (recommended)
docker-compose up -d
```

### Building Locally

```bash
# Build the image
docker build -t adnauseam-automation:local .

# Run it
docker run --rm \
  -e SELENIUM_HUB=selenium-hub:4444 \
  -e PERSONA_ROTATION_STRATEGY=weighted \
  --network selenium \
  adnauseam-automation:local
```

---

## 📦 Available Images

Images are automatically built and published to GitHub Container Registry (GHCR) on every push to the main branch.

### Tags

- `latest` - Latest stable build from main branch
- `v*.*.*` - Semantic version tags (e.g., `v1.0.0`, `v1.2.3`)
- `main` - Latest build from main branch
- `<branch>-<sha>` - Specific commit builds
- `pr-<number>` - Pull request builds (not pushed to registry)

### Platforms

- `linux/amd64` (x86_64)
- `linux/arm64` (ARM 64-bit)

---

## 🏗️ Architecture

This project uses a **Selenium Grid** architecture with multiple browser nodes and automation instances:

```
┌─────────────────────────────────────────────────────────┐
│                    Selenium Hub                         │
│                   (Orchestrator)                        │
└─────────────────────────────────────────────────────────┘
                         │
         ┌───────────────┼───────────────┐
         │               │               │
┌────────▼────────┐ ┌───▼────────┐ ┌───▼────────┐
│  Chrome Nodes   │ │Firefox Nodes│ │ Edge Nodes │
│  (v95-latest)   │ │ (v98-latest)│ │(v114-latest)│
└─────────────────┘ └─────────────┘ └────────────┘
         │               │               │
         └───────────────┼───────────────┘
                         │
         ┌───────────────┴───────────────┐
         │                               │
┌────────▼────────┐            ┌─────────▼────────┐
│   Automation    │    ...     │   Automation     │
│   Instance 1    │            │   Instance 20    │
└─────────────────┘            └──────────────────┘
```

---

## 🔧 Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `SELENIUM_HUB` | `selenium-hub:4444` | Selenium Hub address |
| `PERSONA_ROTATION_STRATEGY` | `weighted` | Persona rotation strategy (`weighted`, `random`, `round-robin`, `new`) |
| `PERSONA_MAX_AGE_DAYS` | `30` | Maximum age of reusable personas (days) |
| `PERSONA_MAX_USES` | `100` | Maximum uses per persona |

### Persona Rotation Strategies

- **`weighted`** - Favors less-used personas (recommended)
- **`random`** - Completely random selection
- **`round-robin`** - Least recently used first
- **`new`** - Always create new personas (no reuse)

---

## 📚 Docker Image Contents

The automation image includes:

- **Python 3.11** (slim base)
- **Selenium WebDriver** (v4.15.2)
- **NumPy** (v1.26.2) - For advanced fingerprinting
- **Faker** (v20.1.0) - For realistic data generation
- **crawl.py** - Main automation script (5800+ lines)
- **persona_manager.py** - Persistent persona management
- **websites.txt** - Target website list

### Features

✅ **Advanced Anti-Fingerprinting**
- Hardware diversity (CPU cores, memory, GPU)
- Connection type randomization
- Battery API spoofing
- Media devices simulation
- Custom font sets per persona
- WebRTC leak prevention
- Plugin/extension randomization

✅ **Human-like Behavior**
- Bézier curve mouse movements
- Natural typing patterns with typos
- Realistic scroll behavior
- Random pauses and micro-movements
- Cookie banner handling

✅ **Persistent Personas**
- Save/load browser fingerprints
- Rotation across sessions
- Weighted selection algorithms
- Automatic cleanup of old personas

---

## 🛠️ GitHub Actions CI/CD

### Workflow Overview

The project uses GitHub Actions to automatically build and publish Docker images to GitHub Container Registry (GHCR).

**Workflow file:** `.github/workflows/docker-build-push.yml`

### Triggers

- **Push to `main`/`master`** - Builds and pushes `latest` + branch tags
- **Version tags** (`v*.*.*`) - Builds and pushes semantic version tags
- **Pull Requests** - Builds but doesn't push (validation only)
- **Manual dispatch** - Can be triggered manually from Actions tab

### Build Process

1. **Checkout** - Clones the repository
2. **Setup Buildx** - Enables multi-platform builds
3. **Login to GHCR** - Authenticates using `GITHUB_TOKEN`
4. **Extract Metadata** - Generates tags and labels
5. **Build & Push** - Builds for amd64/arm64 and pushes to GHCR
6. **Attestation** - Generates build provenance for security

### Multi-platform Support

Images are built for:
- `linux/amd64` (Intel/AMD 64-bit)
- `linux/arm64` (ARM 64-bit, including Apple Silicon M1/M2/M3)

### Caching

- Uses GitHub Actions cache to speed up builds
- Caches Docker layers between runs
- Significantly reduces build times for incremental changes

---

## 📖 Usage Examples

### Example 1: Docker Compose (Full Stack)

```yaml
version: '3.8'

services:
  selenium-hub:
    image: selenium/hub:latest
    ports:
      - "4444:4444"

  chrome:
    image: selenium/node-chrome:latest
    depends_on:
      - selenium-hub
    environment:
      - SE_EVENT_BUS_HOST=selenium-hub
      - SE_EVENT_BUS_PUBLISH_PORT=4442
      - SE_EVENT_BUS_SUBSCRIBE_PORT=4443
    shm_size: 2gb

  automation:
    image: ghcr.io/boblepointu/adnauseamselenium:latest
    depends_on:
      - selenium-hub
      - chrome
    environment:
      - SELENIUM_HUB=selenium-hub:4444
      - PERSONA_ROTATION_STRATEGY=weighted
    volumes:
      - personas-data:/app/data/personas

volumes:
  personas-data:
```

### Example 2: Kubernetes Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: browser-automation
spec:
  replicas: 5
  selector:
    matchLabels:
      app: automation
  template:
    metadata:
      labels:
        app: automation
    spec:
      containers:
      - name: automation
        image: ghcr.io/boblepointu/adnauseamselenium:latest
        env:
        - name: SELENIUM_HUB
          value: "selenium-hub-service:4444"
        - name: PERSONA_ROTATION_STRATEGY
          value: "weighted"
        volumeMounts:
        - name: personas
          mountPath: /app/data/personas
      volumes:
      - name: personas
        persistentVolumeClaim:
          claimName: personas-pvc
```

### Example 3: Standalone with External Selenium Grid

```bash
# Run automation against external Selenium Grid
docker run --rm \
  -e SELENIUM_HUB=my-selenium-grid.example.com:4444 \
  -e PERSONA_ROTATION_STRATEGY=random \
  -v $(pwd)/personas:/app/data/personas \
  ghcr.io/boblepointu/adnauseamselenium:latest
```

---

## 🔐 Security & Permissions

### GitHub Container Registry Access

Images are **public** by default. To use them:

```bash
# No authentication needed for public images
docker pull ghcr.io/boblepointu/adnauseamselenium:latest
```

For **private** repositories, authenticate first:

```bash
# Create a Personal Access Token (PAT) with read:packages scope
echo $GITHUB_TOKEN | docker login ghcr.io -u USERNAME --password-stdin

# Then pull
docker pull ghcr.io/boblepointu/adnauseamselenium:latest
```

### Required GitHub Permissions

The workflow uses `GITHUB_TOKEN` which automatically has:
- ✅ `contents: read` - Read repository contents
- ✅ `packages: write` - Push to GHCR
- ✅ `id-token: write` - Generate attestations

No additional secrets needed!

---

## 🧪 Testing

### Build Locally

```bash
# Build the image
docker build -t adnauseam-test .

# Test the build
docker run --rm adnauseam-test python3 -c "from persona_manager import PersonaManager; print('✓ OK')"
```

### Validate Multi-platform Build

```bash
# Build for multiple platforms locally (requires Docker Buildx)
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  -t adnauseam-test:multiarch \
  .
```

---

## 🐛 Troubleshooting

### Issue: Cannot connect to Selenium Hub

**Symptom:** `Selenium Hub not available after 30 attempts`

**Solutions:**
1. Ensure Selenium Hub is running and accessible
2. Check network connectivity between containers
3. Verify `SELENIUM_HUB` environment variable is correct
4. Check Docker network configuration

```bash
# Verify hub is accessible
curl http://selenium-hub:4444/status
```

### Issue: Personas not persisting

**Symptom:** Personas are lost after container restart

**Solutions:**
1. Mount a volume to `/app/data/personas`
2. Check volume permissions (should be writable)
3. Verify volume is not marked as read-only

```bash
# Check volume mount
docker inspect <container_id> | grep Mounts -A 20
```

### Issue: Out of memory errors

**Symptom:** Container crashes with OOM

**Solutions:**
1. Increase Docker memory limit
2. Reduce number of concurrent automation instances
3. Increase `shm_size` for browser nodes (minimum 2gb)

```bash
# Run with increased memory
docker run --rm --memory=4g --shm-size=2g ...
```

---

## 📊 Monitoring

### Health Checks

The image includes a health check that verifies Selenium Hub connectivity:

```bash
# Check container health
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
```

### Logs

```bash
# View automation logs
docker logs -f <container_name>

# View only errors
docker logs <container_name> 2>&1 | grep ERROR
```

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

**Note:** All PRs will trigger a Docker build to validate the changes.

---

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

## 🙏 Acknowledgments

- **Selenium** - Browser automation framework
- **GitHub Actions** - CI/CD platform
- **Docker** - Containerization platform
- **AdNauseam** - Inspiration for anti-fingerprinting techniques

---

## 📞 Support

- **Issues:** [GitHub Issues](https://github.com/Boblepointu/AdNauseamSelenium/issues)
- **Discussions:** [GitHub Discussions](https://github.com/Boblepointu/AdNauseamSelenium/discussions)
- **Documentation:** [Project Wiki](https://github.com/Boblepointu/AdNauseamSelenium/wiki)

---

<div align="center">

**⭐ Star this repository if you find it useful! ⭐**

</div>

