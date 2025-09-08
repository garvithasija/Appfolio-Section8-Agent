# Frontend Deployment Instructions

## Deploy Frontend as Static Site on Render

### Step 1: Create New Static Site
1. Go to [Render Dashboard](https://dashboard.render.com)
2. Click "New +" → "Static Site"
3. Connect your GitHub repository
4. Select the repository containing this project

### Step 2: Configure Static Site
**Basic Settings:**
- **Name**: `section8-frontend`
- **Root Directory**: `frontend`
- **Build Command**: `npm ci && npm run build`
- **Publish Directory**: `build`

**Environment Variables:**
- `NODE_ENV`: `production`
- `REACT_APP_API_URL`: `https://section8-appfolio-agent.onrender.com`

### Step 3: Advanced Settings (Optional)
- **Auto-Deploy**: Yes (deploys on main branch commits)
- **Pull Request Previews**: No (unless needed)

### Step 4: Deploy
1. Click "Create Static Site"
2. Render will automatically build and deploy
3. Your frontend will be available at: `https://section8-frontend.onrender.com`

## What This Setup Provides

### ✅ Production Configuration
- Frontend served as optimized static files
- API calls routed to your deployed backend
- WebSocket connections for real-time updates
- CORS properly configured for cross-origin requests

### ✅ Automatic Features
- **CDN Distribution**: Fast global loading
- **HTTPS**: Automatic SSL certificate
- **Auto-deploys**: Updates when you push to GitHub
- **Custom Domain**: Can add your own domain later

## Testing the Deployment

1. **Upload CSV**: Test file upload functionality
2. **WebSocket**: Verify real-time progress updates work
3. **Form Filling**: Ensure AppFolio automation works cross-domain

## Architecture Overview

```
Frontend (Static Site)     Backend (Web Service)
├── React App             ├── FastAPI Server
├── Static Files          ├── Playwright Worker
├── CDN Delivery          ├── WebSocket Support
└── https://frontend.com  └── https://backend.com
        │                          ▲
        └── API Calls ──────────────┘
        └── WebSocket ──────────────┘
```

## Cost Optimization
- **Static Site**: $0/month (free tier)
- **Backend Service**: $7/month (starter plan)
- **Total**: ~$7/month for both services

Your frontend is now ready for deployment!