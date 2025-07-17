#!/usr/bin/env python3
"""
Video Download Utility
Lists all generated videos and provides download links
"""
import requests
import json
import os
from datetime import datetime
import pymongo

# Configuration
BACKEND_URL = "http://localhost:8001"
MONGO_URL = "mongodb://localhost:27017"
DB_NAME = "test_database"

def get_all_generated_videos():
    """Get all generated videos from the database"""
    try:
        client = pymongo.MongoClient(MONGO_URL)
        db = client[DB_NAME]
        
        # Get all completed generations
        generations = db.generations.find({
            "status": "completed"
        }).sort("created_at", -1)
        
        videos = []
        for gen in generations:
            video_info = {
                "generation_id": gen.get("generation_id"),
                "project_id": gen.get("project_id"),
                "script": gen.get("script", "")[:100] + "..." if len(gen.get("script", "")) > 100 else gen.get("script", ""),
                "created_at": gen.get("created_at"),
                "completed_at": gen.get("completed_at"),
                "video_url": gen.get("video_url"),
                "video_path": gen.get("video_path"),
                "download_url": f"{BACKEND_URL}/api/download/{gen.get('generation_id')}"
            }
            videos.append(video_info)
            
        return videos
        
    except Exception as e:
        print(f"Error getting videos from database: {e}")
        return []

def download_video(generation_id, filename=None):
    """Download a specific video"""
    try:
        url = f"{BACKEND_URL}/api/download/{generation_id}"
        response = requests.get(url, timeout=30)
        
        if response.status_code == 200:
            if not filename:
                filename = f"video_{generation_id}.mp4"
                
            with open(filename, 'wb') as f:
                f.write(response.content)
                
            print(f"✅ Downloaded: {filename} ({len(response.content)} bytes)")
            return True
        else:
            print(f"❌ Download failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Download error: {e}")
        return False

def main():
    print("🎬 VIDEO DOWNLOAD UTILITY")
    print("=" * 50)
    
    # Get all videos
    videos = get_all_generated_videos()
    
    if not videos:
        print("No completed videos found.")
        return
        
    print(f"Found {len(videos)} completed videos:")
    print()
    
    # Display videos
    for i, video in enumerate(videos, 1):
        print(f"{i}. Generation ID: {video['generation_id']}")
        print(f"   Project ID: {video['project_id']}")
        print(f"   Script: {video['script']}")
        print(f"   Created: {video['created_at']}")
        print(f"   Completed: {video['completed_at']}")
        print(f"   Download URL: {video['download_url']}")
        print()
        
    # Interactive download
    while True:
        try:
            choice = input("\nEnter video number to download (or 'all' for all videos, 'q' to quit): ").strip().lower()
            
            if choice == 'q':
                break
            elif choice == 'all':
                print("\nDownloading all videos...")
                for i, video in enumerate(videos, 1):
                    filename = f"video_{i}_{video['generation_id']}.mp4"
                    download_video(video['generation_id'], filename)
                break
            else:
                video_num = int(choice)
                if 1 <= video_num <= len(videos):
                    video = videos[video_num - 1]
                    filename = f"video_{video_num}_{video['generation_id']}.mp4"
                    download_video(video['generation_id'], filename)
                else:
                    print("Invalid video number.")
                    
        except ValueError:
            print("Invalid input. Please enter a number, 'all', or 'q'.")
        except KeyboardInterrupt:
            print("\nExiting...")
            break

if __name__ == "__main__":
    main()