# 📋 Tumblr Scraper - Changelog & Enhancements

This document tracks all updates and improvements made to the tumblr-crawler scraper.

---

## 🚀 Summary of Changes

| Feature | Description | Status |
|---------|-------------|--------|
| **Srcset Fix** | Downloads highest quality from HTML srcset | ✅ Complete |
| **Video Fix** | Fixed video extraction from new Tumblr format | ✅ Complete |
| **HTML Image Extraction** | Handles images in regular-body HTML | ✅ Complete |
| **Download Statistics** | Tracks all downloads with counts and sizes | ✅ Complete |
| **Resolution Tracking** | Records resolution of each downloaded image | ✅ Complete |
| **DOWNLOADS Folder** | Organized folder structure for downloads | ✅ Complete |
| **Delay Setting** | Configurable delay between downloads | ✅ Complete |
| **Duplicate Detection** | Script to find lower-res duplicates | ✅ Complete |

---

## 🔧 Bug Fixes

### 1. Srcset Image Quality Fix
**Problem:** Original scraper only extracted `src` attribute from HTML-embedded images, getting 640px fallback instead of highest available resolution.

**Solution:** Added srcset parsing to extract and select the highest resolution variant.

```python
# Now parses srcset and selects highest width
srcset_match = re.search(r'srcset="([^"]+)"', regular_body)
if srcset_match:
    # Parse all "url NNNw" entries, sort by width, return highest
    entries.sort(reverse=True)
    return entries[0][1]  # Highest resolution URL
```

**Impact:** +43% average file size for JPG, +44% for PNG (tested on nubare)

### 2. HTML Image Extraction
**Problem:** Posts using `<regular-body>` with embedded HTML `<img>` tags were completely skipped.

**Solution:** Added fallback to extract images from regular-body HTML when no `<photo-url>` exists.

### 3. Video URL Extraction
**Problem:** Video extraction failed for newer Tumblr format with different URL patterns.

**Solution:** Updated regex patterns to handle both old and new video URL formats.

---

## ✨ New Features

### 1. Download Statistics Tracking

**File:** `download_stats.json` (auto-generated)

Automatically tracks:
- Total photos/videos per site
- Download session history with timestamps
- Duration of each download session
- Never re-counts existing files

**View statistics:**
```bash
python3 view_stats.py
```

### 2. Resolution Tracking

Tracks what resolution each downloaded image is:
- Automatically detects resolution from URL (e.g., `s1280x1920`, `_500`)
- Counts how many images at each resolution
- Tracks total size per resolution category

**Resolution detection patterns:**
```
Path-based:   https://...tumblr.com/.../s1280x1920/hash.png  → 1280px
Filename:     https://...tumblr.com/tumblr_abc_1280.jpg      → 1280px
```

### 3. Size Tracking

- Total download size per website
- Size breakdown by resolution
- Human-readable display (KB/MB/GB)

**Example output:**
```
📊 Resolution breakdown:
      1280px:  4,535 files (1.45 GB)
       640px:  2,890 files (512.3 MB)
       500px:  3,200 files (245.8 MB)
```

### 4. DOWNLOADS Folder Structure

All downloads now go to organized folder structure:

```
📁 DOWNLOADS/
├── nubare/           ← New downloads
├── dethjunkie/       ← New downloads
├── ARCHIVE/          ← Old downloads preserved
│   ├── nubare/
│   └── dethjunkie/
└── xml_backup/       ← XML response files
```

### 5. Configurable Settings

New settings in `tumblr-photo-video-ripper.py`:

```python
TIMEOUT = 10              # Request timeout in seconds
DELAY = 0.5               # Delay between downloads (0 = no delay)
THREADS = 10              # Parallel download threads
DOWNLOADS_FOLDER = "DOWNLOADS"  # Output folder
```

### 6. Duplicate Resolution Detection

**Script:** `remove_duplicate_resolutions.py`

Finds and removes lower-resolution copies when higher-resolution versions exist.

**Usage:**
```bash
# Preview what would be deleted (dry run)
python3 remove_duplicate_resolutions.py nubare

# Actually delete lower-resolution duplicates
python3 remove_duplicate_resolutions.py nubare --execute
```

**Note:** Works for traditional filenames (with _NNN suffixes). Srcset images have unique hashes per resolution and require XML analysis to correlate.

---

## 📊 Statistics JSON Format

```json
{
  "sitename": {
    "total_photos": 12225,
    "total_videos": 43,
    "total_bytes": 2315789000,
    "resolutions": {
      "1280px": 4535,
      "640px": 2890,
      "500px": 3200,
      "unknown": 1600
    },
    "resolution_bytes": {
      "1280px": 1556789000,
      "640px": 537234000
    },
    "download_sessions": [
      {
        "date": "2025-12-24 08:47:00",
        "photos_downloaded": 26856,
        "videos_downloaded": 11,
        "duration_seconds": 312.5
      }
    ]
  }
}
```

---

## 📈 Test Results

### Nubare Re-download Comparison

| Metric | Old Download | New Download | Change |
|--------|--------------|--------------|--------|
| **Total Files** | 26,850 | 26,856 | +6 |
| **Total Size** | 4.8 GB | 6.6 GB | **+37.5%** |
| **JPG avg size** | 134.6 KB | 192.6 KB | **+43%** |
| **PNG avg size** | 468.7 KB | 675.6 KB | **+44%** |

**Conclusion:** Srcset fix successfully downloads higher resolution images.

---

## 🔧 Usage Examples

### Basic Download
```bash
# Add sites to sites.txt
echo "blogname" > sites.txt

# Run scraper
python3 tumblr-photo-video-ripper.py
```

### View Statistics
```bash
python3 view_stats.py
```

### Clean Up Duplicates
```bash
python3 remove_duplicate_resolutions.py foldername --execute
```

---

## 📁 File Reference

| File | Purpose |
|------|---------|
| `tumblr-photo-video-ripper.py` | Main scraper (enhanced) |
| `sites.txt` | List of blogs to download |
| `download_stats.json` | Download statistics (auto-generated) |
| `view_stats.py` | View formatted statistics |
| `remove_duplicate_resolutions.py` | Duplicate cleanup tool |
| `DOWNLOADS/` | All downloads folder |
| `DOWNLOADS/ARCHIVE/` | Archived old downloads |

---

## ⚠️ Known Limitations

### Srcset Duplicate Detection
- Srcset images have unique content hashes per resolution
- `329d0da4...png` (1280px) and `420140e7...png` (640px) are the SAME image but different files
- Filename-based detection cannot identify these as duplicates
- **Solution:** Re-download with srcset fix; new downloads will be highest quality

### URL Prefix for Same Content
Different resolutions share the same URL prefix:
```
PREFIX: 1a93a5ef.../e52876e4.../

s640x960/420140e7...png    (640px)  ← Same image
s1280x1920/329d0da4...png  (1280px) ← Same image, different file
```

---

## 📝 Version History

- **v1.0** - Original scraper (dixudx/tumblr-crawler)
- **v1.1** - Added HTML image extraction for regular-body posts
- **v1.2** - Added srcset parsing for highest quality images
- **v1.3** - Added download statistics tracking
- **v1.4** - Added resolution and size tracking
- **v1.5** - Added DOWNLOADS folder structure and delay settings

