#!/usr/bin/env python3
"""
Script to find and remove lower-resolution duplicate images after downloading higher-res versions.

This script identifies images that exist in multiple resolutions (e.g., same content hash
but different resolution suffixes in the URL), and removes the lower-resolution versions
while keeping the highest quality one.
"""

import os
import re
import sys
from collections import defaultdict

def extract_content_hash(filename, url_path=""):
    """
    Extract the content hash from filename or URL.
    Tumblr uses content-addressable filenames where the hash identifies the image content.
    
    Examples:
        329d0da4eefa30f9c25e75a2776e709716e4013a.png (s1280x1920 version)
        420140e71398807b80aa7d542d2e83e6cb80a9fc.png (s640x960 version)
        
    These would have different hashes but come from the same post in srcset.
    We need to look at the URL structure instead.
    """
    # For now, return the full filename as each resolution has a unique hash
    # We'll need to track duplicates by analyzing XML srcset data
    return None

def extract_resolution(filename):
    """
    Extract resolution from filename if present.
    
    Examples:
        tumblr_abc123_1280.jpg -> 1280
        tumblr_xyz789_500.jpg -> 500
    """
    # Pattern for _NNNpx or _NNN suffix
    match = re.search(r'_(\d{3,4})(?:px)?\.(?:jpg|png|gif|webp)', filename)
    if match:
        return int(match.group(1))
    
    return None

def find_resolution_duplicates(directory):
    """
    Find potential resolution duplicates by analyzing filenames.
    Groups files by their base name (without resolution suffix).
    
    Returns:
        dict: {base_name: [(resolution, filename, filepath)]}
    """
    groups = defaultdict(list)
    
    for filename in os.listdir(directory):
        filepath = os.path.join(directory, filename)
        
        # Skip non-files and XML files
        if not os.path.isfile(filepath) or filename.endswith('.xml'):
            continue
        
        # Extract resolution
        resolution = extract_resolution(filename)
        
        if resolution:
            # Extract base name (everything before _NNN)
            base_match = re.match(r'(.*?)_\d{3,4}(?:px)?\.', filename)
            if base_match:
                base_name = base_match.group(1)
                file_size = os.path.getsize(filepath)
                groups[base_name].append((resolution, filename, filepath, file_size))
    
    # Filter to only groups with multiple resolutions
    duplicates = {k: v for k, v in groups.items() if len(v) > 1}
    
    return duplicates

def analyze_srcset_duplicates(directory, xml_directory=None):
    """
    Analyze XML files to find images that were downloaded in multiple resolutions
    from the same srcset attribute.
    
    This is the accurate way to find duplicates caused by the srcset bug.
    """
    if xml_directory is None:
        xml_directory = directory
    
    print(f"🔍 Analyzing srcset data in {xml_directory}...")
    
    # This would require parsing XML files and tracking which images
    # came from the same srcset. For now, we'll use filename analysis.
    
    # TODO: Implement XML parsing to find srcset groups
    print("   (XML analysis not yet implemented, using filename analysis)")
    
    return {}

def remove_lower_resolutions(duplicates, dry_run=True):
    """
    Remove lower resolution versions, keeping only the highest quality.
    
    Args:
        duplicates: dict from find_resolution_duplicates()
        dry_run: if True, only print what would be deleted
    """
    total_removed = 0
    total_bytes_freed = 0
    
    for base_name, versions in duplicates.items():
        # Sort by resolution descending
        versions.sort(reverse=True, key=lambda x: x[0])
        
        highest_res, highest_file, highest_path, highest_size = versions[0]
        
        print(f"\n📁 {base_name}:")
        print(f"   ✅ KEEP: {highest_file} ({highest_res}px, {highest_size:,} bytes)")
        
        # Remove all lower resolutions
        for resolution, filename, filepath, file_size in versions[1:]:
            if dry_run:
                print(f"   ❌ WOULD DELETE: {filename} ({resolution}px, {file_size:,} bytes)")
            else:
                try:
                    os.remove(filepath)
                    print(f"   ❌ DELETED: {filename} ({resolution}px, {file_size:,} bytes)")
                    total_removed += 1
                    total_bytes_freed += file_size
                except Exception as e:
                    print(f"   ⚠️  ERROR deleting {filename}: {e}")
    
    return total_removed, total_bytes_freed

def main():
    """Main function to find and remove duplicate resolutions"""
    
    if len(sys.argv) < 2:
        print("Usage: python remove_duplicate_resolutions.py <directory> [--execute]")
        print("\nOptions:")
        print("  <directory>  Directory to scan for duplicate resolutions")
        print("  --execute    Actually delete files (default is dry-run)")
        print("\nExample:")
        print("  python remove_duplicate_resolutions.py nubare")
        print("  python remove_duplicate_resolutions.py nubare --execute")
        sys.exit(1)
    
    directory = sys.argv[1]
    execute = '--execute' in sys.argv
    
    if not os.path.isdir(directory):
        print(f"❌ Error: Directory '{directory}' not found")
        sys.exit(1)
    
    print(f"{'🔍' if not execute else '🗑️ '} {'DRY RUN - ' if not execute else ''}Scanning {directory} for resolution duplicates...\n")
    
    # Find duplicates by filename pattern
    duplicates = find_resolution_duplicates(directory)
    
    if not duplicates:
        print("✅ No resolution duplicates found!")
        print("\nNote: This script detects duplicates with _NNN resolution suffixes.")
        print("If images have unique content hashes per resolution (common with srcset),")
        print("they won't be detected as duplicates by filename alone.")
        return
    
    print(f"📊 Found {len(duplicates)} groups with multiple resolutions\n")
    
    total_removed, total_bytes_freed = remove_lower_resolutions(duplicates, dry_run=not execute)
    
    print("\n" + "="*70)
    if execute:
        print(f"✅ Removed {total_removed} lower-resolution files")
        print(f"💾 Freed {total_bytes_freed:,} bytes ({total_bytes_freed / (1024*1024):.2f} MB)")
    else:
        print(f"📊 DRY RUN SUMMARY:")
        print(f"   Would remove: {total_removed} files")
        print(f"   Would free: {total_bytes_freed:,} bytes ({total_bytes_freed / (1024*1024):.2f} MB)")
        print(f"\n💡 Run with --execute to actually delete files")

if __name__ == "__main__":
    main()

