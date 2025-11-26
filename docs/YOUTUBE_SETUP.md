# YouTube Shorts Setup Guide

## What Gets Posted?
✅ **Instagram:** Feed Post + Reel + Story (all 3!)
✅ **YouTube:** Shorts Video

## YouTube API Setup

### Step 1: Create Google Cloud Console Project

1. Go to: https://console.cloud.google.com
2. Create a new project (or select an existing one)
3. Project Name: e.g., "Auto Poster"

### Step 2: Enable YouTube Data API v3

1. In Google Cloud Console → "APIs & Services" → "Library"
2. Search for "YouTube Data API v3"
3. Click "Enable"

### Step 3: Create OAuth 2.0 Credentials

1. Go to "APIs & Services" → "Credentials"
2. Click "Create Credentials" → "OAuth client ID"
3. Application type: **"Desktop app"**
4. Name: e.g., "Auto Poster Desktop"
5. Click "Create"
6. **Save:**
   - Client ID (looks like: `xxx.apps.googleusercontent.com`)
   - Client Secret

### Step 4: Generate Refresh Token

You need a **Refresh Token** to upload videos permanently.

#### Option A: Using Python Script (Easiest Method)

1. Install the Google Auth Library (if not already installed):
   ```bash
   cd backend
   poetry add google-auth-oauthlib
   ```

2. Create a file `get_youtube_token.py`:
   ```python
   from google_auth_oauthlib.flow import InstalledAppFlow
   import json

   # Replace with your values
   CLIENT_ID = "YOUR_CLIENT_ID.apps.googleusercontent.com"
   CLIENT_SECRET = "YOUR_CLIENT_SECRET"

   # Scopes we need
   SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]

   # Start OAuth Flow
   flow = InstalledAppFlow.from_client_config(
       {
           "installed": {
               "client_id": CLIENT_ID,
               "client_secret": CLIENT_SECRET,
               "auth_uri": "https://accounts.google.com/o/oauth2/auth",
               "token_uri": "https://oauth2.googleapis.com/token",
               "redirect_uris": ["http://localhost"]
           }
       },
       scopes=SCOPES
   )

   # Browser opens - sign in with your YouTube account
   credentials = flow.run_local_server(port=8080)

   # Display Refresh Token
   print("\n" + "="*60)
   print("REFRESH TOKEN (save this in .env):")
   print("="*60)
   print(credentials.refresh_token)
   print("="*60)
   ```

3. Run the script:
   ```bash
   poetry run python get_youtube_token.py
   ```

4. Browser opens → Sign in with your YouTube account
5. Copy the **Refresh Token**

#### Option B: Using OAuth Playground

1. Go to: https://developers.google.com/oauthplayground
2. Click Settings (gear icon top right)
3. Enable "Use your own OAuth credentials"
4. Enter your Client ID and Client Secret
5. On the left: Select "YouTube Data API v3" → "https://www.googleapis.com/auth/youtube.upload"
6. Click "Authorize APIs"
7. Sign in with your YouTube account
8. Click "Exchange authorization code for tokens"
9. Copy the **Refresh token**

### Step 5: Add Credentials to .env

Open `.env` file in project root and add:

```env
# YouTube API Credentials
YOUTUBE_CLIENT_ID=your_client_id.apps.googleusercontent.com
YOUTUBE_CLIENT_SECRET=your_client_secret
YOUTUBE_REFRESH_TOKEN=your_refresh_token
```

### Step 6: Restart Backend

```bash
cd backend
# Stop Backend (Ctrl+C)
poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## What Gets Posted?

With each upload, the following is automatically created:

### Instagram (3 Posts):
1. **Feed Post** - Photo with caption
2. **Reel** - Video with template, zoom effect, caption
3. **Story** - Video with template, zoom effect

### YouTube:
1. **Shorts** - Same video as Instagram Reel

## Troubleshooting

### "YouTube API credentials not configured"
→ Check if all 3 values are entered in `.env`

### "YouTube authentication failed"
→ Refresh Token is invalid or expired - generate a new one

### "The request cannot be completed because you have exceeded your quota"
→ YouTube API has a Daily Quota (10,000 units/day)
→ 1 Upload = approx. 1600 units
→ You can upload about 6 videos per day
→ Quota resets at midnight Pacific Time

### "Invalid credentials"
→ Client ID or Secret incorrect - check if they were copied correctly

## Tips

- **Shorts must be vertical (9:16)** ✅ (automatically created)
- **Title with #Shorts** → Automatically added by code
- **Max. 60 seconds** ✅ (set to 15 seconds)
- **Thumbnail is automatically generated**

## Check Status

After upload, you will see in the frontend:
- ✅ Instagram: success → Feed + Reel + Story posted
- ✅ YouTube: success → Short uploaded

If errors occur:
- ❌ failed → See error message in frontend
- Check console logs in backend terminal
