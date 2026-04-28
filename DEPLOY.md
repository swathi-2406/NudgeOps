# Deploying NudgeOps + HabitFlow

## Step 1 — Deploy Backend to Render.com (free)

1. Go to https://render.com and sign up
2. Click "New" → "Web Service"
3. Connect your GitHub repo
4. Set these settings:
   - Name: nudgeops-api
   - Runtime: Python 3
   - Build Command: `pip install -r backend/requirements.txt`
   - Start Command: `cd backend && uvicorn main:app --host 0.0.0.0 --port $PORT`
5. Add environment variables:
   - SECRET_KEY: (generate a random 32-char hex string)
   - ENVIRONMENT: production
   - CORS_ORIGINS: https://your-habitflow.netlify.app
6. Click "Create Web Service"
7. Wait ~5 minutes for first deploy
8. Copy your Render URL (e.g. https://nudgeops-api.onrender.com)

## Step 2 — Update HabitFlow API URL

Open habitflow/src/utils/api.js and change:
  const http = axios.create({ baseURL: 'http://localhost:8000/api/v1/habitflow' ...

To:
  const http = axios.create({ baseURL: 'https://nudgeops-api.onrender.com/api/v1/habitflow' ...

## Step 3 — Deploy HabitFlow to Netlify (free)

1. Go to https://netlify.com and sign up
2. Click "Add new site" → "Import from Git"
3. Connect your GitHub repo
4. Set these build settings:
   - Base directory: habitflow
   - Build command: npm run build
   - Publish directory: habitflow/dist
5. Click "Deploy site"
6. Your app is live at https://random-name.netlify.app

## Step 4 — Install as PWA on phone

1. Open the Netlify URL on your phone
2. iPhone: tap Share → "Add to Home Screen"
3. Android: tap the 3-dot menu → "Add to Home Screen"

HabitFlow now appears as an app icon on your phone!

## Step 5 — Share with beta testers

Send them the Netlify URL. They can add it to their home screen too.
