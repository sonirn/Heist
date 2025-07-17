#!/usr/bin/env python3
"""
Simple Video Download Utility
Lists all available generated videos and allows downloading them
"""
import os
import glob
import shutil
from datetime import datetime
import requests

# Configuration
BACKEND_URL = "http://localhost:8001"
OUTPUT_DIR = "/tmp/output"
DOWNLOAD_DIR = "/tmp/downloaded_videos"

def get_available_videos():
    """Get all available video files from the output directory"""
    video_files = glob.glob(os.path.join(OUTPUT_DIR, "final_video_*.mp4"))
    videos = []
    
    for video_path in video_files:
        filename = os.path.basename(video_path)
        # Extract generation ID from filename: final_video_{generation_id}.mp4
        generation_id = filename.replace("final_video_", "").replace(".mp4", "")
        
        # Get file stats
        stat = os.stat(video_path)
        file_size = stat.st_size
        created_time = datetime.fromtimestamp(stat.st_ctime)
        
        videos.append({
            "generation_id": generation_id,
            "filename": filename,
            "file_path": video_path,
            "file_size": file_size,
            "created_time": created_time,
            "download_url": f"{BACKEND_URL}/api/download/{generation_id}"
        })
    
    # Sort by creation time (newest first)
    videos.sort(key=lambda x: x["created_time"], reverse=True)
    return videos

def download_video_file(video_info, download_dir):
    """Download a video file via API or copy directly"""
    try:
        # Create download directory if it doesn't exist
        os.makedirs(download_dir, exist_ok=True)
        
        # Try API download first
        try:
            response = requests.get(video_info["download_url"], timeout=30)
            if response.status_code == 200:
                download_path = os.path.join(download_dir, video_info["filename"])
                with open(download_path, 'wb') as f:
                    f.write(response.content)
                print(f"✅ Downloaded via API: {download_path}")
                return download_path
        except:
            pass
        
        # Fallback to direct file copy
        download_path = os.path.join(download_dir, video_info["filename"])
        shutil.copy2(video_info["file_path"], download_path)
        print(f"✅ Copied directly: {download_path}")
        return download_path
        
    except Exception as e:
        print(f"❌ Failed to download {video_info['filename']}: {e}")
        return None

def format_file_size(size_bytes):
    """Format file size in human readable format"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} TB"

def main():
    print("🎬 VIDEO DOWNLOAD UTILITY")
    print("=" * 60)
    
    # Get available videos
    videos = get_available_videos()
    
    if not videos:
        print("❌ No generated videos found.")
        print(f"Looking in: {OUTPUT_DIR}")
        return
    
    print(f"📁 Found {len(videos)} generated videos:")
    print()
    
    # Display video list
    for i, video in enumerate(videos, 1):
        print(f"{i:2d}. Generation ID: {video['generation_id']}")
        print(f"     Filename: {video['filename']}")
        print(f"     Size: {format_file_size(video['file_size'])}")
        print(f"     Created: {video['created_time'].strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"     Download URL: {video['download_url']}")
        print()
    
    # Interactive download
    print("📥 DOWNLOAD OPTIONS:")
    print("   • Enter video number to download individual video")
    print("   • Enter 'all' to download all videos")
    print("   • Enter 'q' to quit")
    print()
    
    while True:
        try:
            choice = input("Your choice: ").strip().lower()
            
            if choice == 'q':
                print("👋 Goodbye!")
                break
                
            elif choice == 'all':
                print(f"\n📦 Downloading all {len(videos)} videos...")
                print(f"Download directory: {DOWNLOAD_DIR}")
                
                success_count = 0
                for i, video in enumerate(videos, 1):
                    print(f"\n[{i}/{len(videos)}] Downloading {video['filename']}...")
                    result = download_video_file(video, DOWNLOAD_DIR)
                    if result:
                        success_count += 1
                        
                print(f"\n✅ Downloaded {success_count}/{len(videos)} videos to {DOWNLOAD_DIR}")
                break
                
            else:
                try:
                    video_num = int(choice)
                    if 1 <= video_num <= len(videos):
                        video = videos[video_num - 1]
                        print(f"\n📥 Downloading {video['filename']}...")
                        result = download_video_file(video, DOWNLOAD_DIR)
                        if result:
                            print(f"✅ Video saved to: {result}")
                        else:
                            print("❌ Download failed")
                    else:
                        print(f"❌ Invalid number. Please enter 1-{len(videos)}")
                        
                except ValueError:
                    print("❌ Invalid input. Please enter a number, 'all', or 'q'")
                    
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break

if __name__ == "__main__":
    main()