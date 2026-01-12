#!/usr/bin/env python3
"""
Redis client wrapper for caching Strava activities and gear data.
"""

import json
import redis
from typing import Dict, List, Optional, Set
from datetime import datetime


class StravaRedisClient:
    """Redis client for caching Strava data."""
    
    def __init__(self, host: str = 'localhost', port: int = 6379, 
                 password: Optional[str] = None, db: int = 0):
        """Initialize Redis connection."""
        self.client = redis.Redis(
            host=host,
            port=port,
            password=password,
            db=db,
            decode_responses=True  # Automatically decode responses to strings
        )
        # Test connection
        try:
            self.client.ping()
            print("✓ Connected to Redis")
        except redis.ConnectionError as e:
            raise ConnectionError(f"Failed to connect to Redis: {e}")
    
    def get_activity(self, activity_id: int) -> Optional[Dict]:
        """Get a single activity from Redis."""
        key = f"activity:{activity_id}"
        data = self.client.get(key)
        if data:
            return json.loads(data)
        return None
    
    def set_activity(self, activity_id: int, activity_data: Dict):
        """Store a single activity in Redis."""
        key = f"activity:{activity_id}"
        self.client.set(key, json.dumps(activity_data))
        # Also add to sorted set for tracking update times
        updated_at = activity_data.get('updated_at')
        if updated_at:
            self.client.zadd("activities:updated_at", {str(activity_id): updated_at})
    
    def get_all_activity_ids(self) -> Set[int]:
        """Get all cached activity IDs."""
        keys = self.client.keys("activity:*")
        activity_ids = set()
        for key in keys:
            try:
                activity_id = int(key.split(":")[1])
                activity_ids.add(activity_id)
            except (ValueError, IndexError):
                continue
        return activity_ids
    
    def get_latest_activity_update_time(self) -> Optional[float]:
        """Get the timestamp of the most recently updated activity."""
        result = self.client.zrange("activities:updated_at", -1, -1, withscores=True)
        if result:
            return result[0][1]  # Return the score (timestamp)
        return None
    
    def get_activities_updated_after(self, timestamp: float) -> List[Dict]:
        """Get all activities updated after a given timestamp."""
        activity_ids = self.client.zrangebyscore(
            "activities:updated_at", 
            f"({timestamp}",  # Exclusive lower bound
            "+inf"
        )
        activities = []
        for activity_id_str in activity_ids:
            activity_id = int(activity_id_str)
            activity = self.get_activity(activity_id)
            if activity:
                activities.append(activity)
        return activities
    
    def get_gear_ids_from_cache(self) -> Set[str]:
        """Get all gear IDs from cached activities."""
        gear_ids = set()
        activity_ids = self.get_all_activity_ids()
        for activity_id in activity_ids:
            activity = self.get_activity(activity_id)
            if activity and activity.get('gear_id'):
                gear_ids.add(activity['gear_id'])
        return gear_ids
    
    def get_gear(self, gear_id: str) -> Optional[Dict]:
        """Get gear details from Redis."""
        key = f"gear:{gear_id}"
        data = self.client.get(key)
        if data:
            return json.loads(data)
        return None
    
    def set_gear(self, gear_id: str, gear_data: Dict):
        """Store gear details in Redis."""
        key = f"gear:{gear_id}"
        self.client.set(key, json.dumps(gear_data))
    
    def clear_all(self):
        """Clear all cached data (use with caution!)."""
        self.client.flushdb()
        print("✓ Cleared all Redis data")
    
    def get_stats(self) -> Dict:
        """Get statistics about cached data."""
        activity_count = len(self.get_all_activity_ids())
        gear_keys = self.client.keys("gear:*")
        gear_count = len(gear_keys)
        
        latest_update = self.get_latest_activity_update_time()
        latest_update_str = None
        if latest_update:
            latest_update_str = datetime.fromtimestamp(latest_update).isoformat()
        
        return {
            'activity_count': activity_count,
            'gear_count': gear_count,
            'latest_activity_update': latest_update_str
        }
