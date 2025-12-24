#!/usr/bin/env python3
"""
Simple script to view download statistics from download_stats.json
"""

import json
import os
from datetime import datetime

def format_number(num):
    """Format large numbers with commas"""
    return f"{num:,}"

def format_bytes(bytes_val):
    """Format bytes to human-readable size"""
    if bytes_val == 0:
        return "0 B"
    
    units = ['B', 'KB', 'MB', 'GB', 'TB']
    unit_index = 0
    size = float(bytes_val)
    
    while size >= 1024 and unit_index < len(units) - 1:
        size /= 1024
        unit_index += 1
    
    return f"{size:.2f} {units[unit_index]}"

def view_download_stats():
    """Display download statistics in a readable format"""
    stats_file = "download_stats.json"

    if not os.path.exists(stats_file):
        print("❌ No download statistics file found. Run the scraper first to create one.")
        return

    try:
        with open(stats_file, 'r') as f:
            stats = json.load(f)
    except Exception as e:
        print(f"❌ Error reading stats file: {e}")
        return

    if not stats:
        print("📊 No download statistics available yet.")
        return

    print("📈 === TUMBLR SCRAPER DOWNLOAD STATISTICS ===\n")

    # Calculate totals
    total_sites = len(stats)
    total_photos = sum(site.get('total_photos', 0) for site in stats.values())
    total_videos = sum(site.get('total_videos', 0) for site in stats.values())
    total_media = total_photos + total_videos
    total_bytes = sum(site.get('total_bytes', 0) for site in stats.values())

    print("📊 OVERALL SUMMARY:")
    print(f"   Total sites downloaded: {total_sites}")
    print(f"   Total photos: {format_number(total_photos)}")
    print(f"   Total videos: {format_number(total_videos)}")
    print(f"   Total media files: {format_number(total_media)}")
    print(f"   Total size: {format_bytes(total_bytes)}")
    print()

    # Sort sites by total media (descending)
    sorted_sites = sorted(stats.items(),
                         key=lambda x: x[1]['total_photos'] + x[1]['total_videos'],
                         reverse=True)

    print("📁 SITE-BY-SITE BREAKDOWN:")
    print("-" * 100)
    print("{:<15} {:>10} {:>10} {:>10} {:>12} {:>15}".format("Site", "Photos", "Videos", "Total", "Size", "Last Download"))
    print("-" * 100)

    for site_name, site_data in sorted_sites:
        photos = site_data.get('total_photos', 0)
        videos = site_data.get('total_videos', 0)
        total = photos + videos
        size_bytes = site_data.get('total_bytes', 0)
        sessions = len(site_data.get('download_sessions', []))

        last_session = site_data.get('download_sessions', [])[-1] if sessions > 0 else None
        last_date = last_session['date'][:10] if last_session else "N/A"  # Just date part

        print("{:<15} {:>10} {:>10} {:>10} {:>12} {:>15}".format(
            site_name[:14],  # Truncate long names
            format_number(photos),
            format_number(videos),
            format_number(total),
            format_bytes(size_bytes),
            last_date
        ))

    print("\n📝 SESSION DETAILS:")
    print("-" * 100)

    for site_name, site_data in sorted_sites:
        print(f"\n📁 {site_name.upper()}:")
        
        # Show resolution breakdown if available
        resolutions = site_data.get('resolutions', {})
        resolution_bytes = site_data.get('resolution_bytes', {})
        
        if resolutions:
            print(f"   📊 Resolution breakdown:")
            # Sort by resolution (numeric part)
            sorted_res = sorted(resolutions.items(), key=lambda x: int(x[0].replace('px', '').replace('unknown', '0')), reverse=True)
            for res, count in sorted_res:
                size = resolution_bytes.get(res, 0)
                print(f"      {res:>10}: {format_number(count):>6} files ({format_bytes(size)})")
        
        for i, session in enumerate(site_data.get('download_sessions', []), 1):
            date = session['date']
            photos = session['photos_downloaded']
            videos = session['videos_downloaded']
            duration = session.get('duration_seconds', 0)
            size = session.get('bytes_downloaded', 0)

            if duration > 0:
                duration_str = f"{duration:.1f}s"
            else:
                duration_str = "N/A"

            note = session.get('note', '')
            if note:
                note = f" ({note})"

            print(f"   Session {i}: {date} - {format_number(photos)} photos, {format_number(videos)} videos, {format_bytes(size)} ({duration_str}){note}")

if __name__ == "__main__":
    view_download_stats()
