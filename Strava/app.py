#!/usr/bin/env python3
"""
Streamlit app to display Strava shoes/gear sorted by mileage.
"""

import streamlit as st
import sys
import os
from pathlib import Path

# Add the current directory to path to import our modules
sys.path.insert(0, str(Path(__file__).parent))

from get_all_shoes import (
    load_config,
    save_config,
    refresh_access_token,
    get_all_shoes_with_distances,
)
from redis_client import StravaRedisClient


def initialize_session_state():
    """Initialize session state variables."""
    if 'shoes_data' not in st.session_state:
        st.session_state.shoes_data = None
    if 'last_refresh' not in st.session_state:
        st.session_state.last_refresh = None


def get_redis_client(config):
    """Initialize and return Redis client."""
    try:
        redis_host = config.get('redis_host', 'localhost')
        redis_port = config.get('redis_port', 6379)
        redis_password = config.get('redis_password', 'strava_redis_password')
        
        return StravaRedisClient(
            host=redis_host,
            port=redis_port,
            password=redis_password
        )
    except Exception as e:
        st.warning(f"Could not connect to Redis: {e}. Continuing without caching.")
        return None


def refresh_token_if_needed(config):
    """Refresh access token if expired."""
    client_id = config.get('client_id')
    client_secret = config.get('client_secret')
    refresh_token = config.get('refresh_token')
    access_token = config.get('access_token')
    
    if not access_token:
        return None, "No access token found in config"
    
    if not (refresh_token and client_id and client_secret):
        return access_token, None
    
    # Test if token is valid
    import requests
    headers = {"Authorization": f"Bearer {access_token}"}
    test_response = requests.get("https://www.strava.com/api/v3/athlete", headers=headers)
    
    if test_response.status_code == 401:
        # Token expired, refresh it
        token_data = refresh_access_token(client_id, client_secret, refresh_token)
        if token_data and 'access_token' in token_data:
            config['access_token'] = token_data['access_token']
            if 'refresh_token' in token_data:
                config['refresh_token'] = token_data['refresh_token']
            save_config(config, 'config.json')
            return token_data['access_token'], "Token refreshed successfully"
        else:
            return None, "Failed to refresh token. Please re-authorize."
    
    return access_token, None


def format_distance(meters):
    """Format distance in kilometers."""
    km = meters / 1000
    return f"{km:,.2f} km"


def main():
    st.set_page_config(
        page_title="Strava Shoe Tracker",
        page_icon="👟",
        layout="wide"
    )
    
    initialize_session_state()
    
    st.title("👟 Strava Shoe Distance Tracker")
    st.markdown("---")
    
    # Load configuration
    config = load_config('config.json')
    
    if not config:
        st.error("❌ No config file found. Please run the CLI script first to set up authentication.")
        st.info("Run: `python get_all_shoes.py --authorize --client-id YOUR_ID --client-secret YOUR_SECRET`")
        return
    
    # Sidebar for controls
    with st.sidebar:
        st.header("⚙️ Settings")
        
        use_redis = st.checkbox("Use Redis Cache", value=True, help="Enable Redis caching for faster loads")
        refresh_data = st.button("🔄 Refresh Data", type="primary")
        
        if use_redis:
            try:
                redis_client = get_redis_client(config)
                if redis_client:
                    stats = redis_client.get_stats()
                    st.success("✓ Redis Connected")
                    st.caption(f"Cached Activities: {stats['activity_count']}")
                    st.caption(f"Cached Gear: {stats['gear_count']}")
            except Exception as e:
                st.warning(f"Redis unavailable: {e}")
                redis_client = None
                use_redis = False
        else:
            redis_client = None
    
    # Refresh token if needed
    access_token, token_message = refresh_token_if_needed(config)
    
    if not access_token:
        st.error(f"❌ {token_message}")
        return
    
    if token_message:
        st.success(f"✓ {token_message}")
    
    # Load or refresh shoes data
    if refresh_data or st.session_state.shoes_data is None:
        with st.spinner("Fetching shoes data from Strava... This may take a moment."):
            try:
                # Suppress print output during fetch (it will still show in terminal)
                import io
                import contextlib
                
                # Redirect stdout temporarily to reduce console noise
                f = io.StringIO()
                with contextlib.redirect_stdout(f):
                    shoes_data = get_all_shoes_with_distances(
                        access_token, 
                        redis_client if use_redis else None
                    )
                
                st.session_state.shoes_data = shoes_data
                st.session_state.last_refresh = "now"
                # Count shoes vs bikes, and active vs retired
                all_shoes = [s for s in shoes_data if s.get('frame_type') is None]
                active_shoes = [s for s in all_shoes if not s.get('retired', False)]
                retired_shoes = [s for s in all_shoes if s.get('retired', False)]
                bikes_count = len([s for s in shoes_data if s.get('frame_type') is not None])
                st.success(f"✓ Loaded {len(shoes_data)} items ({len(active_shoes)} active shoes, {len(retired_shoes)} retired shoes, {bikes_count} bikes/other)")
            except Exception as e:
                st.error(f"❌ Error fetching data: {e}")
                st.exception(e)  # Show full traceback in expander
                return
    else:
        shoes_data = st.session_state.shoes_data
    
    if not shoes_data:
        st.warning("No shoes/gear found. Make sure you have activities with gear assigned in Strava.")
        return
    
    # Filter to only show active (non-retired) shoes (frame_type is None for shoes, not None for bikes)
    shoes_only = [
        shoe for shoe in shoes_data 
        if shoe.get('frame_type') is None and not shoe.get('retired', False)
    ]
    
    if not shoes_only:
        st.warning("No active shoes found. Only retired shoes or bikes/other gear items were found.")
        return
    
    # Sort by distance (highest first)
    sorted_shoes = sorted(shoes_only, key=lambda x: x['distance_meters'], reverse=True)
    
    # Display summary metrics
    total_distance_meters = sum(shoe['distance_meters'] for shoe in sorted_shoes)
    total_km = total_distance_meters / 1000
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Total Shoes", len(sorted_shoes))
    with col2:
        st.metric("Total Distance", f"{total_km:,.2f} km")
    
    st.markdown("---")
    
    # Display shoes in a table
    st.subheader("📊 Shoes Sorted by Distance (Highest First)")
    
    # Create table data
    table_data = []
    for i, shoe in enumerate(sorted_shoes, 1):
        table_data.append({
            "Rank": i,
            "Name": shoe['name'],
            "Distance (km)": f"{shoe['distance_km']:,.2f}",
            "Brand": shoe.get('brand_name', '—'),
            "Model": shoe.get('model_name', '—'),
            "ID": shoe['id']
        })
    
    # Display as dataframe with styling
    import pandas as pd
    df = pd.DataFrame(table_data)
    
    # Style the dataframe
    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Rank": st.column_config.NumberColumn("Rank", width="small"),
            "Name": st.column_config.TextColumn("Shoe Name", width="large"),
            "Distance (km)": st.column_config.TextColumn("Distance (km)", width="medium"),
            "Brand": st.column_config.TextColumn("Brand", width="medium"),
            "Model": st.column_config.TextColumn("Model", width="medium"),
            "ID": st.column_config.TextColumn("ID", width="small"),
        }
    )
    
    st.markdown("---")
    
    # Display detailed cards
    st.subheader("👟 Detailed View")
    
    # Create columns for cards (2 per row)
    cols = st.columns(2)
    
    for idx, shoe in enumerate(sorted_shoes):
        col = cols[idx % 2]
        
        with col:
            with st.container():
                # Card header with distance
                distance_pct = (shoe['distance_meters'] / total_distance_meters * 100) if total_distance_meters > 0 else 0
                
                st.markdown(f"### {shoe['name']}")
                
                # Distance as a metric
                st.metric("Distance", f"{shoe['distance_km']:,.2f} km")
                
                # Additional info
                info_text = []
                if shoe.get('brand_name'):
                    info_text.append(f"**Brand:** {shoe['brand_name']}")
                if shoe.get('model_name'):
                    info_text.append(f"**Model:** {shoe['model_name']}")
                info_text.append(f"**ID:** {shoe['id']}")
                
                if info_text:
                    st.markdown(" | ".join(info_text))
                
                # Progress bar showing percentage of total distance
                st.progress(distance_pct / 100, text=f"{distance_pct:.1f}% of total distance")
                
                st.markdown("---")


if __name__ == "__main__":
    main()
