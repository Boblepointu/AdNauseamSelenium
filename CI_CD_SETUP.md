# CI/CD Setup Guide

This guide explains how to set up continuous integration and deployment for the AdNauseam Browser Automation project using GitHub Actions and GitHub Container Registry.

---

## 📋 Prerequisites

Before setting up CI/CD, ensure you have:

1. ✅ GitHub repository (public or private)
2. ✅ GitHub account with repository write access
3. ✅ Docker installed locally for testing
4. ✅ Git installed and configured

---

## 🚀 Quick Setup (5 Minutes)

### Step 1: Push Your Code to GitHub

```bash
# Initialize git repository (if not already done)
git init

# Add all files
git add .

# Commit
git commit -m "Initial commit: Add Docker and CI/CD configuration"

# Add your GitHub repository as remote
git remote add origin https://github.com/YOUR_USERNAME/AdNauseamSelenium.git

# Push to GitHub
git push -u origin master
```

### Step 2: Verify GitHub Actions Workflow

The workflow file `.github/workflows/docker-build-push.yml` is already included. It will:

- ✅ Automatically trigger on push to `master`/`main`
- ✅ Build Docker image for `linux/amd64` and `linux/arm64`
- ✅ Push to GitHub Container Registry (ghcr.io)
- ✅ Tag with branch name, commit SHA, and `latest`

### Step 3: Enable GitHub Container Registry

GitHub Container Registry (GHCR) is automatically enabled for your repository. No additional setup needed!

The workflow uses the built-in `GITHUB_TOKEN` which has all necessary permissions.

### Step 4: Monitor First Build

1. Go to your GitHub repository
2. Click on the "Actions" tab
3. Watch the "Build and Push Docker Images" workflow run
4. Wait for it to complete (usually 3-5 minutes)

### Step 5: Verify Image Published

Once the workflow completes:

1. Go to your repository main page
2. Look for "Packages" in the right sidebar
3. Click on your package
4. You should see your Docker image with tags!

---

## 🎯 Using Your Published Images

### Pull Your Image

```bash
# For public repositories (no authentication needed)
docker pull ghcr.io/YOUR_USERNAME/adnauseamselenium:latest

# For private repositories (authenticate first)
echo $GITHUB_TOKEN | docker login ghcr.io -u YOUR_USERNAME --password-stdin
docker pull ghcr.io/YOUR_USERNAME/adnauseamselenium:latest
```

### Update docker-compose.production.yml

Replace the image name with your own:

```yaml
services:
  browser-automation-1:
    image: ghcr.io/YOUR_USERNAME/adnauseamselenium:latest
    # ... rest of configuration
```

Then run:

```bash
docker-compose -f docker-compose.production.yml up -d
```

---

## 🏷️ Versioning and Tags

### Automatic Tags

The workflow automatically creates multiple tags:

| Trigger | Tag Examples | Description |
|---------|--------------|-------------|
| Push to `main` | `latest`, `main`, `main-abc1234` | Latest stable build |
| Push to branch | `feature-xyz`, `feature-xyz-def5678` | Branch-specific builds |
| Version tag `v1.2.3` | `v1.2.3`, `v1.2`, `v1`, `latest` | Semantic versions |
| Pull request | (not pushed) | Build validation only |

### Creating Version Releases

To create a versioned release:

```bash
# Tag your commit
git tag v1.0.0

# Push the tag
git push origin v1.0.0
```

This will trigger a build and publish:
- `ghcr.io/YOUR_USERNAME/adnauseamselenium:v1.0.0`
- `ghcr.io/YOUR_USERNAME/adnauseamselenium:v1.0`
- `ghcr.io/YOUR_USERNAME/adnauseamselenium:v1`
- `ghcr.io/YOUR_USERNAME/adnauseamselenium:latest`

---

## 🔒 Making Images Public

By default, GHCR images inherit your repository's visibility (public/private).

### Make Package Public

1. Go to your GitHub repository
2. Click "Packages" in the right sidebar
3. Click on your package name
4. Click "Package settings" (bottom left)
5. Scroll to "Danger Zone"
6. Click "Change visibility"
7. Select "Public"
8. Confirm

Now anyone can pull your image without authentication!

---

## ⚙️ Customizing the Workflow

### Change Trigger Branches

Edit `.github/workflows/docker-build-push.yml`:

```yaml
on:
  push:
    branches:
      - master
      - main
      - develop  # Add more branches
```

### Build Only on Tags

For release-only builds:

```yaml
on:
  push:
    tags:
      - 'v*.*.*'
```

### Add Build Arguments

To pass build arguments:

```yaml
- name: Build and push Docker image
  uses: docker/build-push-action@v5
  with:
    context: .
    build-args: |
      VERSION=${{ github.ref_name }}
      BUILD_DATE=${{ github.event.head_commit.timestamp }}
    # ... rest of config
```

### Disable Multi-platform Builds

For faster builds (amd64 only):

```yaml
- name: Build and push Docker image
  uses: docker/build-push-action@v5
  with:
    context: .
    platforms: linux/amd64  # Remove arm64
    # ... rest of config
```

---

## 🧪 Testing Locally

### Test Docker Build

Before pushing, test your Dockerfile locally:

```bash
# Build for current platform
docker build -t test-image .

# Test the image
docker run --rm test-image python3 -c "from persona_manager import PersonaManager; print('✓ OK')"
```

### Test Multi-platform Build

Requires Docker Buildx:

```bash
# Create a buildx builder
docker buildx create --name multiarch --use

# Build for multiple platforms
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  -t test-image:multiarch \
  --load \
  .
```

---

## 📊 Monitoring Builds

### View Build Logs

1. Go to GitHub Actions tab
2. Click on a workflow run
3. Click on the "build-and-push" job
4. Expand steps to view detailed logs

### Build Failed?

Common issues and solutions:

#### Issue: Dockerfile syntax error

**Solution**: Test locally first
```bash
docker build -t test .
```

#### Issue: Missing files

**Solution**: Check `.dockerignore` isn't excluding required files

#### Issue: Authentication failed

**Solution**: Ensure `GITHUB_TOKEN` has `packages: write` permission (default: yes)

#### Issue: Build timeout

**Solution**: Optimize Dockerfile layers or disable multi-platform builds

---

## 🔐 Security Best Practices

### Image Scanning

Add vulnerability scanning to workflow:

```yaml
- name: Run Trivy vulnerability scanner
  uses: aquasecurity/trivy-action@master
  with:
    image-ref: ghcr.io/${{ github.repository }}:latest
    format: 'sarif'
    output: 'trivy-results.sarif'

- name: Upload Trivy results to GitHub Security
  uses: github/codeql-action/upload-sarif@v2
  with:
    sarif_file: 'trivy-results.sarif'
```

### Sign Images with Cosign

Add image signing:

```yaml
- name: Install Cosign
  uses: sigstore/cosign-installer@v3

- name: Sign the images
  run: |
    cosign sign --yes ghcr.io/${{ github.repository }}@${{ steps.build.outputs.digest }}
```

### Use Dependabot

Create `.github/dependabot.yml`:

```yaml
version: 2
updates:
  - package-ecosystem: "docker"
    directory: "/"
    schedule:
      interval: "weekly"
  
  - package-ecosystem: "github-actions"
    directory: "/"
    schedule:
      interval: "weekly"
```

---

## 📈 Advanced Features

### Build Cache Optimization

The workflow already uses GitHub Actions cache for Docker layers. To optimize further:

```yaml
cache-from: type=gha
cache-to: type=gha,mode=max
```

This caches intermediate layers for faster subsequent builds.

### Parallel Builds

Build multiple images in parallel:

```yaml
strategy:
  matrix:
    image:
      - automation
      - automation-light
      - automation-dev
```

### Conditional Builds

Build only on specific paths:

```yaml
on:
  push:
    paths:
      - 'Dockerfile'
      - 'crawl.py'
      - 'persona_manager.py'
      - '.github/workflows/**'
```

---

## 🌐 Using in Production

### Deploy with Docker Compose

```bash
# Pull latest image
docker-compose -f docker-compose.production.yml pull

# Restart with new image
docker-compose -f docker-compose.production.yml up -d
```

### Deploy to Kubernetes

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: browser-automation
spec:
  replicas: 5
  template:
    spec:
      containers:
      - name: automation
        image: ghcr.io/YOUR_USERNAME/adnauseamselenium:v1.0.0
        imagePullPolicy: Always
```

### Auto-deploy with Watchtower

Automatically pull and deploy new images:

```yaml
services:
  watchtower:
    image: containrrr/watchtower
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
    command: --interval 300
```

---

## 📚 Additional Resources

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [GitHub Container Registry Guide](https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-container-registry)
- [Docker Build Push Action](https://github.com/docker/build-push-action)
- [Docker Buildx Documentation](https://docs.docker.com/buildx/working-with-buildx/)

---

## 🆘 Getting Help

If you encounter issues:

1. Check workflow logs in GitHub Actions
2. Test Docker build locally
3. Review [DOCKER.md](DOCKER.md) troubleshooting section
4. Open an issue on GitHub

---

**Happy Building! 🚀**

