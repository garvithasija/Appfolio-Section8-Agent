# Render Deployment Guide

This directory contains the configuration files needed to deploy the Section 8 AppFolio Agent to Render.

## Files

- `render.yaml` - Render service configuration
- `Dockerfile` - Production Docker configuration (copies from root)
- `docker-compose.yml` - Local development setup

## Deployment Steps

1. **Connect Repository to Render**
   - Go to [Render Dashboard](https://dashboard.render.com)
   - Click "New +" → "Blueprint"
   - Connect your GitHub repository
   - Select this repository

2. **Configure Blueprint**
   - Render will automatically detect the `render.yaml` file
   - The service will be named `section8-appfolio-agent`
   - Uses Docker runtime with the Dockerfile from project root

3. **Environment Variables** (automatically set from render.yaml)
   - `PYTHONPATH`: `/app/worker:/app/backend`
   - `PLAYWRIGHT_BROWSERS_PATH`: `/ms-playwright`
   - `PORT`: `8000`

4. **Persistent Storage**
   - 1GB disk mounted at `/app/uploads` for file storage
   - CSV uploads and screenshots will persist across deployments

5. **Health Checks**
   - Health check endpoint: `/`
   - Automatic health monitoring enabled

## Service Configuration

- **Plan**: Starter (suitable for development/testing)
- **Region**: Oregon (us-west-2)
- **Auto-deploy**: Enabled on main branch commits
- **Instances**: 1 (single instance deployment)

## Access Your Application

Once deployed, your application will be available at:
`https://section8-appfolio-agent.onrender.com`

## Monitoring

- Check deployment logs in the Render dashboard
- Health check status is monitored automatically
- Application logs available in real-time via dashboard

## Scaling

To handle more traffic, you can:
1. Upgrade to a higher plan in Render dashboard
2. Increase `numInstances` in `render.yaml`
3. Add horizontal scaling configuration