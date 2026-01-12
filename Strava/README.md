# Strava Shoe Mileage Tracker

Track the evolution of your shoes' mileage over time from your Strava activities.

## Setup

1. **Install dependencies:**
   ```bash
   uv sync
   ```
   
   This will install all dependencies including `redis` for caching support.

2. **Start Redis Stack (for activity caching):**
   ```bash
   docker-compose up -d
   ```
   
   This will start Redis Stack on:
   - Redis: `localhost:6379`
   - RedisInsight (web UI): `http://localhost:8001`
   
   The default password is `strava_redis_password` (can be changed in `docker-compose.yml`).

3. **Create a configuration file:**
   ```bash
   cp config.json.example config.json
   ```
   
   Then edit `config.json` and add your Strava API credentials:
   - `access_token`: Your current access token
   - `client_id`: Your Strava app client ID
   - `client_secret`: Your Strava app client secret
   - `refresh_token`: Your refresh token
   - `redis_host`: (optional) Redis host (default: localhost)
   - `redis_port`: (optional) Redis port (default: 6379)
   - `redis_password`: (optional) Redis password (default: strava_redis_password)

## Usage

### First-time authorization:
```bash
python get_all_shoes.py --authorize --client-id YOUR_CLIENT_ID --client-secret YOUR_CLIENT_SECRET
```

### Basic usage (with Redis caching):
```bash
uv run python get_all_shoes.py
```

Or if you've activated the virtual environment:
```bash
python get_all_shoes.py
```

The script will:
- Use Redis to cache activities and gear data
- Perform incremental updates (only fetch new/updated activities)
- Significantly reduce API calls on subsequent runs

### Disable Redis caching:
```bash
uv run python get_all_shoes.py --no-redis
```

### View cache statistics:
```bash
uv run python get_all_shoes.py --stats
```

### Clear all cached data:
```bash
uv run python get_all_shoes.py --clear-cache
```

### Save results to JSON:
```bash
uv run python get_all_shoes.py --save-json --output my_shoes.json
```

### Launch Streamlit Web App:
```bash
uv run streamlit run app.py
```

The Streamlit app provides:
- 📊 **Interactive dashboard** showing all shoes sorted by mileage (highest first)
- 📈 **Summary metrics** (total shoes, total distance in miles and km)
- 👟 **Detailed cards** for each shoe with brand, model, and type information
- 📊 **Data table** with sortable columns
- 🔄 **Redis cache integration** for faster loads
- 🔐 **Automatic token refresh** when expired
- ⚙️ **Sidebar controls** to refresh data and toggle Redis caching

The app will open in your default web browser at `http://localhost:8501`

### Fetch only recent activities (last 30 days):
```bash
uv run strava_shoe_tracker.py --days 30
```

### Export data to JSON:
```bash
uv run strava_shoe_tracker.py --export-json
```

### Export data to CSV:
```bash
uv run strava_shoe_tracker.py --export-csv
```

### Fetch detailed activity info (more accurate but slower):
```bash
uv run strava_shoe_tracker.py --fetch-details
```

### Use command-line arguments instead of config file:
```bash
uv run strava_shoe_tracker.py \
  --access-token YOUR_ACCESS_TOKEN \
  --client-id YOUR_CLIENT_ID \
  --client-secret YOUR_CLIENT_SECRET \
  --refresh-token YOUR_REFRESH_TOKEN
```

## Features

- ✅ **Redis caching**: Activities and gear data are cached in Redis for fast subsequent runs
- ✅ **Incremental updates**: Only fetches new activities (activities don't change after creation), saving API calls
- ✅ Automatically refreshes access tokens when expired
- ✅ Fetches all activities with pagination support
- ✅ Tracks cumulative mileage for each shoe/gear item
- ✅ Shows mileage milestones (100, 200, 300 miles, etc.)
- ✅ Exports data to JSON or CSV format
- ✅ Filters activities by date range

## Output

The script will display:
- Total mileage per shoe
- Number of activities per shoe
- First and last use dates
- When mileage milestones were reached
- Option to export data for further analysis

## Notes

- Make sure your activities in Strava have gear/shoes assigned to them
- The script automatically handles token refresh when needed
- Distance is displayed in miles (Strava API returns meters)
- **Redis caching**: On first run, all activities are fetched and cached. Subsequent runs only fetch new activities, making them much faster
- **Incremental updates**: The script checks if each activity already exists in cache. Since Strava activities don't change after creation, we only cache new activities. The script also optimizes by stopping early when it encounters a page where all activities are already cached (since activities are returned newest-first)

## Troubleshooting

### 401 Unauthorized Error

If you get a 401 error even after token refresh, it usually means your app doesn't have the required scopes:

1. **Check your app's authorization scopes**: Your Strava app needs the `read` or `activity:read` scope to access activities
2. **Re-authorize your app**: You may need to re-authorize your app with the correct scopes:
   ```
   https://www.strava.com/oauth/authorize?client_id=YOUR_CLIENT_ID&response_type=code&redirect_uri=YOUR_REDIRECT_URI&scope=read,activity:read
   ```
3. **Get new tokens**: After re-authorizing, you'll need to exchange the authorization code for new access and refresh tokens

### Token Refresh Issues

- Make sure your `refresh_token` is still valid (they can expire if unused for a long time)
- Verify your `client_id` and `client_secret` are correct
- Check that your app is still active in the Strava Developer Portal
