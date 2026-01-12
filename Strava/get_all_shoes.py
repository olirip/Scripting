#!/usr/bin/env python3
"""
Get all shoes/gear from Strava using OAuth redirection.
Fetches all gear IDs from activities and gets their total distance using the Gear API.
Uses Redis to cache activities and perform incremental updates.
"""

import os
import json
import requests
from typing import Dict, List, Optional, Set
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler
import webbrowser
import threading
import time
from pprint import pprint
from redis_client import StravaRedisClient


class OAuthCallbackHandler(BaseHTTPRequestHandler):
    """HTTP server handler to catch OAuth redirect."""
    code = None
    error = None
    
    def do_GET(self):
        """Handle GET request from OAuth redirect."""
        parsed_path = urllib.parse.urlparse(self.path)
        query_params = urllib.parse.parse_qs(parsed_path.query)
        
        if 'code' in query_params:
            OAuthCallbackHandler.code = query_params['code'][0]
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b'''
                <html>
                <head><title>Authorization Successful</title></head>
                <body>
                    <h1>Authorization Successful!</h1>
                    <p>You can close this window and return to the terminal.</p>
                </body>
                </html>
            ''')
        elif 'error' in query_params:
            OAuthCallbackHandler.error = query_params['error'][0]
            self.send_response(400)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(f'''
                <html>
                <head><title>Authorization Failed</title></head>
                <body>
                    <h1>Authorization Failed</h1>
                    <p>Error: {OAuthCallbackHandler.error}</p>
                </body>
                </html>
            '''.encode())
        else:
            self.send_response(400)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(b'Invalid request')
    
    def log_message(self, format, *args):
        """Suppress server log messages."""
        pass


def get_authorization_url(client_id: str, redirect_uri: str = "http://localhost:8080", scope: str = "read,activity:read") -> str:
    """Generate Strava OAuth authorization URL."""
    params = {
        'client_id': client_id,
        'response_type': 'code',
        'redirect_uri': redirect_uri,
        'scope': scope,
        'approval_prompt': 'force'
    }
    base_url = "https://www.strava.com/oauth/authorize"
    return f"{base_url}?{urllib.parse.urlencode(params)}"


def exchange_code_for_tokens(client_id: str, client_secret: str, code: str, redirect_uri: str = "http://localhost:8080") -> Optional[Dict]:
    """Exchange authorization code for access and refresh tokens."""
    url = "https://www.strava.com/oauth/token"
    data = {
        "client_id": client_id,
        "client_secret": client_secret,
        "code": code,
        "grant_type": "authorization_code",
        "redirect_uri": redirect_uri
    }
    
    try:
        response = requests.post(url, data=data)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"✗ Error exchanging code for tokens: {e}")
        if hasattr(e, 'response') and e.response is not None:
            try:
                error_data = e.response.json()
                print(f"  Error details: {error_data}")
            except:
                print(f"  Response: {e.response.text}")
        return None


def oauth_authorize(client_id: str, client_secret: str, redirect_uri: str = "http://localhost:8080", 
                   scope: str = "read,activity:read", port: int = 8080) -> Optional[Dict]:
    """Complete OAuth authorization flow."""
    auth_url = get_authorization_url(client_id, redirect_uri, scope)
    
    print("\n" + "="*80)
    print("STRAVA OAUTH AUTHORIZATION")
    print("="*80)
    print(f"\nOpening browser for authorization...")
    print(f"If the browser doesn't open automatically, visit this URL:")
    print(f"\n{auth_url}\n")
    
    # Start local server to catch redirect
    server = HTTPServer(('localhost', port), OAuthCallbackHandler)
    server_thread = threading.Thread(target=server.serve_forever)
    server_thread.daemon = True
    server_thread.start()
    
    # Open browser
    try:
        webbrowser.open(auth_url)
    except Exception as e:
        print(f"⚠ Could not open browser automatically: {e}")
        print(f"   Please visit the URL above manually")
    
    # Wait for authorization code
    print("Waiting for authorization...")
    print("(After authorizing in the browser, you'll be redirected back here)\n")
    
    timeout = 300  # 5 minutes
    elapsed = 0
    while OAuthCallbackHandler.code is None and OAuthCallbackHandler.error is None and elapsed < timeout:
        time.sleep(1)
        elapsed += 1
    
    # Shutdown server
    server.shutdown()
    server.server_close()
    
    if OAuthCallbackHandler.error:
        print(f"✗ Authorization failed: {OAuthCallbackHandler.error}")
        return None
    
    if OAuthCallbackHandler.code is None:
        print("✗ Authorization timed out or was cancelled")
        return None
    
    print("✓ Authorization code received, exchanging for tokens...")
    
    # Exchange code for tokens
    token_data = exchange_code_for_tokens(client_id, client_secret, OAuthCallbackHandler.code, redirect_uri)
    
    if token_data and 'access_token' in token_data:
        print("✓ Successfully obtained access and refresh tokens!")
        if 'scope' in token_data:
            print(f"  Scopes: {token_data['scope']}")
        return token_data
    else:
        print("✗ Failed to exchange code for tokens")
        return None


def refresh_access_token(client_id: str, client_secret: str, refresh_token: str) -> Optional[Dict]:
    """Refresh the access token if it has expired."""
    url = "https://www.strava.com/oauth/token"
    data = {
        "client_id": client_id,
        "client_secret": client_secret,
        "refresh_token": refresh_token,
        "grant_type": "refresh_token"
    }
    
    try:
        response = requests.post(url, data=data)
        if response.status_code != 200:
            print(f"✗ Error refreshing token: {response.status_code} {response.reason}")
            return None
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"✗ Error refreshing token: {e}")
        return None


def get_all_gear_ids_from_activities(access_token: str, redis_client: Optional[StravaRedisClient] = None) -> Set[str]:
    """Get all unique gear IDs from all activities, using Redis cache for incremental updates (new activities only)."""
    headers = {"Authorization": f"Bearer {access_token}"}
    base_url = "https://www.strava.com/api/v3"
    url = f"{base_url}/athlete/activities"
    
    gear_ids = set()
    page = 1
    per_page = 200  # Maximum allowed
    
    # Check if we have cached activities
    cached_activity_ids = set()
    latest_update_time = None
    if redis_client:
        try:
            cached_activity_ids = redis_client.get_all_activity_ids()
            latest_update_time = redis_client.get_latest_activity_update_time()
            if cached_activity_ids:
                print(f"Found {len(cached_activity_ids)} cached activities in Redis")
                if latest_update_time:
                    from datetime import datetime
                    print(f"  Latest cached activity update: {datetime.fromtimestamp(latest_update_time).isoformat()}")
        except Exception as e:
            print(f"⚠ Warning: Could not access Redis cache: {e}")
            redis_client = None
    
    # Determine if we should do incremental update
    # Note: Strava API doesn't support filtering by creation date directly
    # We'll fetch all activities and check which ones are new
    if redis_client and cached_activity_ids:
        print("Performing incremental update (checking for new activities)...")
    else:
        print("Fetching all activities to extract gear IDs...")
    
    params = {"per_page": per_page, "page": page}
    
    new_activities_count = 0
    cached_gear_ids = set()
    
    # First, get gear IDs from cached activities
    if redis_client and cached_activity_ids:
        cached_gear_ids = redis_client.get_gear_ids_from_cache()
        gear_ids.update(cached_gear_ids)
        print(f"  Found {len(cached_gear_ids)} unique gear IDs from cached activities")
    
    while True:
        try:
            response = requests.get(url, headers=headers, params=params)
            
            if response.status_code == 401:
                print("✗ Access token expired or invalid")
                break
            
            response.raise_for_status()
            activities = response.json()
            
            if not activities:
                break
            
            # Process activities
            all_cached_on_page = True
            for activity in activities:
                activity_id = activity.get('id')
                if not activity_id:
                    continue
                
                # Check if this is a new activity (activities don't change after creation)
                is_new = True
                if redis_client:
                    cached_activity = redis_client.get_activity(activity_id)
                    if cached_activity:
                        is_new = False
                    else:
                        all_cached_on_page = False
                
                if is_new:
                    # New activity - cache it
                    new_activities_count += 1
                    if redis_client:
                        redis_client.set_activity(activity_id, activity)
                
                # Extract gear IDs (from both new and cached activities)
                gear_id = activity.get('gear_id')
                if gear_id:
                    gear_ids.add(gear_id)
            
            print(f"  Page {page}: Found {len(activities)} activities, {len(gear_ids)} unique gear IDs so far...")
            if new_activities_count > 0:
                print(f"    (New activities: {new_activities_count})")
            
            # Optimization: Since activities are returned newest-first, if all activities
            # on this page are cached, all subsequent pages will also be cached
            # Only apply this optimization if we have cached activities and Redis is enabled
            if redis_client and cached_activity_ids and all_cached_on_page and len(activities) > 0:
                print(f"  All activities on this page are cached. Stopping fetch (remaining pages would also be cached).")
                break
            
            if len(activities) < per_page:  # Last page
                break
            
            page += 1
            params = {"per_page": per_page, "page": page}
            
        except requests.exceptions.RequestException as e:
            print(f"✗ Error fetching activities: {e}")
            break
    
    if redis_client:
        if new_activities_count > 0:
            print(f"✓ Cached {new_activities_count} new activities")
        else:
            print("✓ No new activities found")
    
    print(f"✓ Found {len(gear_ids)} unique gear IDs from activities")
    return gear_ids


def get_gear_details(access_token: str, gear_id: str, redis_client: Optional[StravaRedisClient] = None) -> Optional[Dict]:
    """Get gear details including total distance using the Gear API, with Redis caching."""
    # Check cache first
    if redis_client:
        cached_gear = redis_client.get_gear(gear_id)
        if cached_gear:
            return cached_gear
    
    headers = {"Authorization": f"Bearer {access_token}"}
    base_url = "https://www.strava.com/api/v3"
    url = f"{base_url}/gear/{gear_id}"
    
    try:
        response = requests.get(url, headers=headers)
        
        if response.status_code == 401:
            print(f"   ✗ Unauthorized for gear {gear_id}")
            return None
        elif response.status_code == 404:
            print(f"   ✗ Gear {gear_id} not found")
            return None
        
        response.raise_for_status()
        gear_data = response.json()
        
        # Cache the gear data
        if redis_client:
            redis_client.set_gear(gear_id, gear_data)
        
        return gear_data
    except requests.exceptions.RequestException as e:
        print(f"   ✗ Error fetching gear {gear_id}: {e}")
        return None


def get_all_shoes_with_distances(access_token: str, redis_client: Optional[StravaRedisClient] = None) -> List[Dict]:
    """Get all shoes/gear with their total distances, using Redis cache."""
    print("\n" + "="*80)
    print("FETCHING ALL GEAR/SHOES")
    print("="*80)
    
    # Get all gear IDs from activities (with incremental update)
    gear_ids = get_all_gear_ids_from_activities(access_token, redis_client)
    
    if not gear_ids:
        print("\nNo gear IDs found in activities.")
        return []
    
    print(f"\nFetching details for {len(gear_ids)} gear items...")
    
    shoes_data = []
    cached_count = 0
    
    for i, gear_id in enumerate(sorted(gear_ids), 1):
        # Check if we have this gear cached
        is_cached = False
        if redis_client:
            cached_gear = redis_client.get_gear(gear_id)
            if cached_gear:
                is_cached = True
                cached_count += 1
        
        cache_indicator = "[CACHED]" if is_cached else ""
        print(f"  [{i}/{len(gear_ids)}] Fetching gear {gear_id}... {cache_indicator}", end=" ")
        gear_data = get_gear_details(access_token, gear_id, redis_client)
        
        if gear_data:
            distance_meters = gear_data.get('distance', 0)
            distance_km = distance_meters / 1000
            distance_miles = distance_meters / 1609.34
            
            shoe_info = {
                'id': gear_data.get('id'),
                'name': gear_data.get('name', 'Unknown'),
                'distance_meters': distance_meters,
                'distance_km': round(distance_km, 2),
                'distance_miles': round(distance_miles, 2),
                'brand_name': gear_data.get('brand_name'),
                'model_name': gear_data.get('model_name'),
                'frame_type': gear_data.get('frame_type'),
                'resource_state': gear_data.get('resource_state'),
                'retired': gear_data.get('retired', False),
                'full_data': gear_data
            }
            
            shoes_data.append(shoe_info)
            print(f"✓ {shoe_info['name']} - {distance_miles:.2f} miles ({distance_km:.2f} km)")
        else:
            print("✗ Failed")
    
    if cached_count > 0:
        print(f"\n✓ Used cached data for {cached_count} gear items")
    
    return shoes_data


def print_shoes_summary(shoes_data: List[Dict]):
    """Print a summary of all shoes."""
    print("\n" + "="*80)
    print("ALL SHOES/GEAR SUMMARY")
    print("="*80)
    
    if not shoes_data:
        print("\nNo shoes/gear found.")
        return
    
    # Sort by distance (descending)
    sorted_shoes = sorted(shoes_data, key=lambda x: x['distance_meters'], reverse=True)
    
    print(f"\nTotal shoes/gear: {len(sorted_shoes)}\n")
    
    for i, shoe in enumerate(sorted_shoes, 1):
        print(f"{i}. {shoe['name']}")
        print(f"   ID: {shoe['id']}")
        print(f"   Total Distance: {shoe['distance_miles']:.2f} miles ({shoe['distance_km']:.2f} km)")
        if shoe.get('brand_name'):
            print(f"   Brand: {shoe['brand_name']}")
        if shoe.get('model_name'):
            print(f"   Model: {shoe['model_name']}")
        if shoe.get('frame_type'):
            print(f"   Type: {shoe['frame_type']}")
        print()
    
    # Calculate totals
    total_distance_meters = sum(shoe['distance_meters'] for shoe in sorted_shoes)
    total_distance_miles = total_distance_meters / 1609.34
    total_distance_km = total_distance_meters / 1000
    
    print("-" * 80)
    print(f"Total Distance Across All Shoes: {total_distance_miles:.2f} miles ({total_distance_km:.2f} km)")
    print("=" * 80)


def save_to_json(shoes_data: List[Dict], filename: str = "all_shoes.json"):
    """Save shoes data to JSON file with only display_name and total_distance in km."""
    export_data = []
    for shoe in shoes_data:
        export_shoe = {
            'display_name': shoe.get('name', 'Unknown'),
            'total_distance': shoe.get('distance_km', 0)
        }
        export_data.append(export_shoe)
    
    with open(filename, 'w') as f:
        json.dump(export_data, f, indent=2)
    
    print(f"\n✓ Data saved to {filename}")


def load_config(config_file: str = "config.json") -> Optional[Dict]:
    """Load configuration from JSON file."""
    if os.path.exists(config_file):
        with open(config_file, 'r') as f:
            return json.load(f)
    return None


def save_config(config: Dict, config_file: str = "config.json"):
    """Save configuration to JSON file."""
    with open(config_file, 'w') as f:
        json.dump(config, f, indent=2)
    print(f"✓ Configuration saved to {config_file}")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Get all shoes/gear from Strava with total distances')
    parser.add_argument('--config', default='config.json', help='Path to config file (default: config.json)')
    parser.add_argument('--authorize', action='store_true', help='Start OAuth authorization flow to get tokens')
    parser.add_argument('--client-id', help='Strava client ID (overrides config)')
    parser.add_argument('--client-secret', help='Strava client secret (overrides config)')
    parser.add_argument('--redirect-uri', default='http://localhost:8080', help='OAuth redirect URI (default: http://localhost:8080)')
    parser.add_argument('--scope', default='read,activity:read', help='OAuth scopes (default: read,activity:read)')
    parser.add_argument('--port', type=int, default=8080, help='Local port for OAuth callback (default: 8080)')
    parser.add_argument('--save-json', action='store_true', help='Save results to JSON file')
    parser.add_argument('--output', default='all_shoes.json', help='Output JSON filename (default: all_shoes.json)')
    parser.add_argument('--no-redis', action='store_true', help='Disable Redis caching')
    parser.add_argument('--clear-cache', action='store_true', help='Clear all cached data in Redis')
    parser.add_argument('--redis-host', default='localhost', help='Redis host (default: localhost)')
    parser.add_argument('--redis-port', type=int, default=6379, help='Redis port (default: 6379)')
    parser.add_argument('--redis-password', help='Redis password (default: from config or none)')
    parser.add_argument('--stats', action='store_true', help='Show Redis cache statistics')
    
    args = parser.parse_args()
    
    # Handle OAuth authorization flow
    if args.authorize:
        config = load_config(args.config) or {}
        
        client_id = args.client_id or config.get('client_id')
        client_secret = args.client_secret or config.get('client_secret')
        
        if not client_id or not client_secret:
            print("Error: --authorize requires --client-id and --client-secret")
            print("Usage: python get_all_shoes.py --authorize --client-id YOUR_ID --client-secret YOUR_SECRET")
            return
        
        token_data = oauth_authorize(
            client_id=client_id,
            client_secret=client_secret,
            redirect_uri=args.redirect_uri,
            scope=args.scope,
            port=args.port
        )
        
        if not token_data:
            print("\n✗ OAuth authorization failed")
            return
        
        # Save tokens to config
        config['client_id'] = client_id
        config['client_secret'] = client_secret
        config['access_token'] = token_data['access_token']
        config['refresh_token'] = token_data.get('refresh_token', '')
        if 'expires_at' in token_data:
            config['expires_at'] = token_data['expires_at']
        
        save_config(config, args.config)
        print(f"\n✓ Tokens saved to {args.config}")
        print("\nYou can now run the script without --authorize to get all shoes.")
        return
    
    # Load configuration
    config = load_config(args.config)
    
    if not config:
        print("Error: No config file found. Please use --authorize first to set up authentication.")
        return
    
    client_id = args.client_id or config.get('client_id')
    client_secret = args.client_secret or config.get('client_secret')
    access_token = config.get('access_token')
    refresh_token = config.get('refresh_token')
    
    if not access_token:
        print("Error: No access_token found in config. Please use --authorize first.")
        return
    
    # Initialize Redis client
    redis_client = None
    if not args.no_redis:
        try:
            redis_host = args.redis_host or config.get('redis_host', 'localhost')
            redis_port = args.redis_port or config.get('redis_port', 6379)
            # Default password matches docker-compose.yml
            redis_password = args.redis_password or config.get('redis_password', 'strava_redis_password')
            
            redis_client = StravaRedisClient(
                host=redis_host,
                port=redis_port,
                password=redis_password
            )
            
            # Handle clear cache request
            if args.clear_cache:
                confirm = input("Are you sure you want to clear all cached data? (yes/no): ")
                if confirm.lower() == 'yes':
                    redis_client.clear_all()
                else:
                    print("Cache clear cancelled.")
                return
            
            # Show stats if requested
            if args.stats:
                stats = redis_client.get_stats()
                print("\n" + "="*80)
                print("REDIS CACHE STATISTICS")
                print("="*80)
                print(f"Cached Activities: {stats['activity_count']}")
                print(f"Cached Gear Items: {stats['gear_count']}")
                if stats['latest_activity_update']:
                    print(f"Latest Activity Update: {stats['latest_activity_update']}")
                print("="*80)
                return
                
        except Exception as e:
            print(f"⚠ Warning: Could not connect to Redis: {e}")
            print("  Continuing without Redis caching...")
            redis_client = None
    
    # Try to refresh token if we have refresh_token
    if refresh_token and client_id and client_secret:
        print("Checking access token...")
        # Test if token is valid
        headers = {"Authorization": f"Bearer {access_token}"}
        test_response = requests.get("https://www.strava.com/api/v3/athlete", headers=headers)
        if test_response.status_code == 401:
            print("Access token expired, refreshing...")
            token_data = refresh_access_token(client_id, client_secret, refresh_token)
            if token_data and 'access_token' in token_data:
                access_token = token_data['access_token']
                config['access_token'] = access_token
                if 'refresh_token' in token_data:
                    config['refresh_token'] = token_data['refresh_token']
                save_config(config, args.config)
                print("✓ Token refreshed")
            else:
                print("✗ Failed to refresh token. Please use --authorize to get new tokens.")
                return
    
    # Get all shoes with distances
    shoes_data = get_all_shoes_with_distances(access_token, redis_client)
    
    if not shoes_data:
        print("\nNo shoes/gear found.")
        return
    
    # Print summary
    print_shoes_summary(shoes_data)
    
    # Save to JSON if requested
    if args.save_json:
        save_to_json(shoes_data, args.output)


if __name__ == "__main__":
    main()
