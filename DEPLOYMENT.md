# Deployment Guide

This guide explains how to deploy the Research System to production platforms while keeping your API keys secure.

## Security Overview

**Local Development:**
- Uses `config/config.yaml` file (gitignored)
- Simple YAML configuration

**Production Deployment:**
- Uses environment variables
- No sensitive data in git repository
- Platform-specific secrets management

---

## Option 1: Deploy to Render

### Backend Deployment

1. **Create New Web Service**
   - Go to [Render Dashboard](https://dashboard.render.com/)
   - Click "New +" → "Web Service"
   - Connect your GitHub repository

2. **Configure Service**
   - **Name:** `research-system-backend`
   - **Environment:** `Python 3`
   - **Build Command:** `pip install -r requirements-api.txt`
   - **Start Command:** `uvicorn api_server:app --host 0.0.0.0 --port $PORT`

3. **Set Environment Variables**
   
   Go to "Environment" tab and add:
   
   ```
   USE_ENV_CONFIG=true
   GITHUB_TOKEN=ghp_your_actual_token
   GEMINI_API_KEYS=["AIzaSy...","AIzaSy...","AIzaSy..."]
   GOOGLE_SEARCH_KEYS=["YOUR_KEY_1","YOUR_KEY_2"]
   GOOGLE_SEARCH_ENGINE_IDS=["YOUR_CX_1","YOUR_CX_2"]
   TAVILY_API_KEY=tvly-YOUR_KEY
   ```
   
   **Important:** Use JSON array format for multiple keys

4. **Deploy**
   - Click "Create Web Service"
   - Render will automatically deploy
   - Note the service URL: `https://research-system-backend.onrender.com`

### Frontend Deployment

1. **Create New Static Site**
   - Click "New +" → "Static Site"
   - Connect your repository

2. **Configure**
   - **Name:** `research-system-frontend`
   - **Build Command:** `cd frontend && npm install && npm run build`
   - **Publish Directory:** `frontend/out`

3. **Set Environment Variables**
   ```
   NEXT_PUBLIC_API_URL=https://research-system-backend.onrender.com
   ```

4. **Update frontend/next.config.ts:**
   ```typescript
   const nextConfig = {
     output: 'export', // Enable static export for Render
     env: {
       API_URL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
     }
   }
   ```

---

## Option 2: Deploy to Vercel

### Frontend Deployment (Vercel is frontend-focused)

1. **Install Vercel CLI**
   ```bash
   npm i -g vercel
   ```

2. **Deploy Frontend**
   ```bash
   cd frontend
   vercel
   ```

3. **Set Environment Variables**
   
   In Vercel Dashboard → Settings → Environment Variables:
   ```
   NEXT_PUBLIC_API_URL=https://your-backend-url.com
   ```

### Backend Deployment (Use Render/Railway for backend)

Vercel supports serverless functions, but the research system requires long-running processes. Use Render (above) or Railway for the backend.

---

## Option 3: Deploy to Railway

### Full Stack Deployment

1. **Create New Project**
   - Go to [Railway](https://railway.app/)
   - "New Project" → "Deploy from GitHub repo"

2. **Add Backend Service**
   - Click "New" → Select your repo
   - Railway auto-detects Python

3. **Configure Backend**
   
   **Environment Variables:**
   ```
   USE_ENV_CONFIG=true
   GITHUB_TOKEN=ghp_your_token
   GEMINI_API_KEYS=["key1","key2","key3"]
   GOOGLE_SEARCH_KEYS=["key1","key2"]
   GOOGLE_SEARCH_ENGINE_IDS=["cx1","cx2"]
   TAVILY_API_KEY=tvly-key
   PORT=8000
   ```
   
   **Start Command:**
   ```
   uvicorn api_server:app --host 0.0.0.0 --port $PORT
   ```

4. **Add Frontend Service**
   - Click "New" → Same repo → Different service
   - Set Root Directory: `frontend`
   
   **Build Command:**
   ```
   npm install && npm run build
   ```
   
   **Start Command:**
   ```
   npm start
   ```
   
   **Environment Variables:**
   ```
   NEXT_PUBLIC_API_URL=${{backend.RAILWAY_STATIC_URL}}
   ```

---

## Option 4: Docker Deployment

### Build Images

**Backend Dockerfile:**
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements-api.txt .
RUN pip install --no-cache-dir -r requirements-api.txt

COPY . .

CMD ["uvicorn", "api_server:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Frontend Dockerfile:**
```dockerfile
FROM node:20-alpine

WORKDIR /app

COPY frontend/package*.json ./
RUN npm ci

COPY frontend .
RUN npm run build

CMD ["npm", "start"]
```

**docker-compose.yml:**
```yaml
version: '3.8'

services:
  backend:
    build:
      context: .
      dockerfile: Dockerfile.backend
    ports:
      - "8000:8000"
    environment:
      - USE_ENV_CONFIG=true
      - GITHUB_TOKEN=${GITHUB_TOKEN}
      - GEMINI_API_KEYS=${GEMINI_API_KEYS}
      - GOOGLE_SEARCH_KEYS=${GOOGLE_SEARCH_KEYS}
      - GOOGLE_SEARCH_ENGINE_IDS=${GOOGLE_SEARCH_ENGINE_IDS}
      - TAVILY_API_KEY=${TAVILY_API_KEY}
  
  frontend:
    build:
      context: .
      dockerfile: Dockerfile.frontend
    ports:
      - "3000:3000"
    environment:
      - NEXT_PUBLIC_API_URL=http://backend:8000
    depends_on:
      - backend
```

**Deploy:**
```bash
docker-compose up -d
```

---

## Environment Variable Format Reference

### Single Values
```bash
GITHUB_TOKEN=ghp_xxxxxxxxxxxxx
TAVILY_API_KEY=tvly-xxxxxxxxxx
```

### JSON Arrays (for multiple keys)
```bash
# Gemini API Keys (25 keys recommended)
GEMINI_API_KEYS=["AIzaSyKey1","AIzaSyKey2","AIzaSyKey3"]

# Google Search Keys
GOOGLE_SEARCH_KEYS=["GoogleKey1","GoogleKey2"]
GOOGLE_SEARCH_ENGINE_IDS=["cx-id-1","cx-id-2"]
```

**Important:** 
- No spaces in JSON arrays for environment variables
- Use double quotes inside arrays
- Entire array must be on one line

---

## Testing Production Configuration Locally

1. **Create .env file:**
   ```bash
   cp .env.example .env
   ```

2. **Edit .env with your real keys:**
   ```bash
   USE_ENV_CONFIG=true
   GITHUB_TOKEN=ghp_real_token
   GEMINI_API_KEYS=["real_key1","real_key2"]
   # ... etc
   ```

3. **Load environment variables:**
   ```bash
   export $(cat .env | xargs)
   ```

4. **Run backend:**
   ```bash
   python api_server.py
   ```

5. **Verify:**
   - Check logs for successful API key loading
   - Test with a research query

---

## Security Checklist

- [ ] `config/config.yaml` is in `.gitignore`
- [ ] `.env` is in `.gitignore`
- [ ] `config.yaml.example` has no real keys
- [ ] Environment variables set in hosting platform
- [ ] `USE_ENV_CONFIG=true` set in production
- [ ] Test deployment with a simple query
- [ ] Monitor logs for API key errors

---

## Troubleshooting

### "No configuration found" error

**Problem:** Backend can't find API keys

**Solutions:**
1. Verify `USE_ENV_CONFIG=true` is set
2. Check environment variable names match exactly
3. Ensure JSON arrays have proper format
4. Check platform logs for variable loading errors

### "Invalid JSON" error for arrays

**Problem:** JSON parsing fails for array environment variables

**Solution:**
```bash
# ❌ Wrong (has spaces)
GEMINI_API_KEYS=["key1", "key2", "key3"]

# ✅ Correct (no spaces)
GEMINI_API_KEYS=["key1","key2","key3"]
```

### Frontend can't connect to backend

**Problem:** CORS or connection errors

**Solutions:**
1. Set `NEXT_PUBLIC_API_URL` to backend URL
2. Update CORS settings in `api_server.py` if needed
3. Ensure backend is accessible from frontend domain

---

## Cost Optimization

### Free Tier Recommendations

**Render:**
- Free tier available for both frontend and backend
- Backend may sleep after 15 min inactivity
- Use paid plan ($7/mo) for always-on backend

**Vercel:**
- Free for frontend (hobby projects)
- 100GB bandwidth/month

**Railway:**
- $5 credit/month on free plan
- Pay only for usage beyond that

### API Key Costs

- **GitHub Models:** FREE (GPT-5/GPT-4o)
- **Google Gemini:** FREE (rate-limited)
- **Google Search:** FREE (100 queries/day per key)
- **Tavily:** FREE tier available

**Total:** Can run completely free with rate limits, or ~$7/mo for always-on hosting

---

## Support

For deployment issues:
- Check platform-specific logs
- Verify all environment variables are set
- Test configuration locally first with `.env`
- Review [README.md](README.md) for system requirements
