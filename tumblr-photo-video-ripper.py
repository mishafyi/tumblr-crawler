# -*- coding: utf-8 -*-

import os
import sys
import requests
import xmltodict
from six.moves import queue as Queue
from threading import Thread
import re
import json
import time
from collections import defaultdict


# Setting timeout
TIMEOUT = 10

# Delay between downloads (in seconds) - set to 0 for no delay
DELAY = 0.5  # Wait 0.5 seconds between each download

# Retry times
RETRY = 5

# Medium Index Number that Starts from
START = 0

# Numbers of photos/videos per page
MEDIA_NUM = 50

# Numbers of downloading threads concurrently
THREADS = 10

# Do you like to dump each post as separate json (otherwise you have to extract from bulk xml files)
# This option is for convenience for terminal users who would like to query e.g. with ./jq (https://stedolan.github.io/jq/)
EACH_POST_AS_SEPARATE_JSON = False

# Downloads folder - all downloaded sites will be saved here
DOWNLOADS_FOLDER = "DOWNLOADS"

# Download statistics tracking
DOWNLOAD_STATS_FILE = "download_stats.json"


class DownloadTracker:
    """Tracks download statistics for Tumblr blogs"""

    def __init__(self):
        self.stats = self.load_stats()
        self.current_session = defaultdict(lambda: {
            'photos_downloaded': 0,
            'videos_downloaded': 0,
            'start_time': None,
            'end_time': None,
            'total_bytes': 0,
            'resolutions': defaultdict(int),  # Track count per resolution
            'resolution_bytes': defaultdict(int)  # Track size per resolution
        })

    def load_stats(self):
        """Load existing download statistics from file"""
        if os.path.exists(DOWNLOAD_STATS_FILE):
            try:
                with open(DOWNLOAD_STATS_FILE, 'r') as f:
                    return json.load(f)
            except:
                print("Warning: Could not load existing stats file, starting fresh")
                return {}
        return {}

    def save_stats(self):
        """Save download statistics to file"""
        try:
            with open(DOWNLOAD_STATS_FILE, 'w') as f:
                json.dump(self.stats, f, indent=2, default=str)
        except Exception as e:
            print(f"Warning: Could not save stats: {e}")

    def start_site_download(self, site_name):
        """Mark the start of downloading for a site"""
        self.current_session[site_name]['start_time'] = time.time()
        print(f"📊 Started downloading from {site_name}")

    def record_download(self, site_name, medium_type, file_size=0, resolution=None):
        """Record a successful download with size and resolution info"""
        if medium_type == "photo":
            self.current_session[site_name]['photos_downloaded'] += 1
        elif medium_type == "video":
            self.current_session[site_name]['videos_downloaded'] += 1
        
        # Track total size
        self.current_session[site_name]['total_bytes'] += file_size
        
        # Track resolution
        if resolution:
            self.current_session[site_name]['resolutions'][resolution] += 1
            self.current_session[site_name]['resolution_bytes'][resolution] += file_size

    def finish_site_download(self, site_name):
        """Mark the completion of downloading for a site"""
        self.current_session[site_name]['end_time'] = time.time()

        # Update overall stats
        if site_name not in self.stats:
            self.stats[site_name] = {
                'total_photos': 0,
                'total_videos': 0,
                'total_bytes': 0,
                'resolutions': {},
                'resolution_bytes': {},
                'download_sessions': []
            }

        # Convert defaultdicts to regular dicts for JSON serialization
        session_resolutions = dict(self.current_session[site_name]['resolutions'])
        session_resolution_bytes = dict(self.current_session[site_name]['resolution_bytes'])
        
        # Add current session to stats
        session_data = {
            'date': time.strftime('%Y-%m-%d %H:%M:%S'),
            'photos_downloaded': self.current_session[site_name]['photos_downloaded'],
            'videos_downloaded': self.current_session[site_name]['videos_downloaded'],
            'bytes_downloaded': self.current_session[site_name]['total_bytes'],
            'resolutions': session_resolutions,
            'resolution_bytes': session_resolution_bytes,
            'duration_seconds': round(self.current_session[site_name]['end_time'] - self.current_session[site_name]['start_time'], 2)
        }

        self.stats[site_name]['total_photos'] += session_data['photos_downloaded']
        self.stats[site_name]['total_videos'] += session_data['videos_downloaded']
        self.stats[site_name]['total_bytes'] += session_data['bytes_downloaded']
        
        # Merge resolution counts
        for res, count in session_resolutions.items():
            self.stats[site_name]['resolutions'][res] = self.stats[site_name]['resolutions'].get(res, 0) + count
        
        # Merge resolution bytes
        for res, size in session_resolution_bytes.items():
            self.stats[site_name]['resolution_bytes'][res] = self.stats[site_name]['resolution_bytes'].get(res, 0) + size
        
        self.stats[site_name]['download_sessions'].append(session_data)

        # Save updated stats
        self.save_stats()

        # Print summary
        total_media = session_data['photos_downloaded'] + session_data['videos_downloaded']
        duration = session_data['duration_seconds']
        size_mb = session_data['bytes_downloaded'] / (1024 * 1024)
        print(f"📊 Finished {site_name}: {session_data['photos_downloaded']} photos, {session_data['videos_downloaded']} videos ({total_media} total, {size_mb:.1f} MB) in {duration}s")

    def get_site_summary(self, site_name):
        """Get summary statistics for a site"""
        if site_name not in self.stats:
            return None

        site_stats = self.stats[site_name]
        total_sessions = len(site_stats['download_sessions'])
        last_session = site_stats['download_sessions'][-1] if total_sessions > 0 else None

        return {
            'site': site_name,
            'total_photos': site_stats['total_photos'],
            'total_videos': site_stats['total_videos'],
            'total_media': site_stats['total_photos'] + site_stats['total_videos'],
            'download_sessions': total_sessions,
            'last_download': last_session['date'] if last_session else None,
            'last_duration_seconds': last_session['duration_seconds'] if last_session else None
        }

    def get_all_sites_summary(self):
        """Get summary for all sites"""
        summary = {}
        for site_name in self.stats:
            summary[site_name] = self.get_site_summary(site_name)
        return summary

    def print_overall_summary(self):
        """Print a summary of all downloaded sites"""
        print("\n📈 === DOWNLOAD STATISTICS SUMMARY ===")
        all_sites = self.get_all_sites_summary()

        if not all_sites:
            print("No download statistics available yet.")
            return

        total_sites = len(all_sites)
        total_photos = sum(site['total_photos'] for site in all_sites.values())
        total_videos = sum(site['total_videos'] for site in all_sites.values())
        total_media = total_photos + total_videos

        print(f"Total sites downloaded: {total_sites}")
        print(f"Total photos: {total_photos}")
        print(f"Total videos: {total_videos}")
        print(f"Total media files: {total_media}")
        print()

        # Sort sites by total media count (descending)
        sorted_sites = sorted(all_sites.items(), key=lambda x: x[1]['total_media'], reverse=True)

        for site_name, site_stats in sorted_sites:
            print(f"📁 {site_name}:")
            print(f"   Photos: {site_stats['total_photos']}, Videos: {site_stats['total_videos']}, Total: {site_stats['total_media']}")
            if site_stats['last_download']:
                print(f"   Last download: {site_stats['last_download']} ({site_stats['download_sessions']} sessions)")
            print()

# Global tracker instance
download_tracker = DownloadTracker()


def video_source_match():
    """Extract video URL from <source src="..."> tags (current Tumblr format)"""
    source_pattern = re.compile(r'<source\s+src="([^"]*\.mp4[^"]*)"[^>]*>', re.IGNORECASE)

    def match(video_player):
        source_match = source_pattern.search(video_player)
        if source_match is not None:
            try:
                return source_match.group(1)
            except:
                return None
        return None
    return match


def video_hd_match():
    """Extract HD video URL from JSON data-crt-options (legacy format)"""
    hd_pattern = re.compile(r'.*"hdUrl":("([^\s,]*)"|false),')

    def match(video_player):
        hd_match = hd_pattern.search(video_player)
        try:
            if hd_match is not None and hd_match.group(1) != 'false':
                return hd_match.group(2).replace('\\', '')
        except:
            return None
    return match


def video_default_match():
    """Extract video URL from src attributes (legacy iframe format)"""
    default_pattern = re.compile(r'.*src="(\S*)" ', re.DOTALL)

    def match(video_player):
        default_match = default_pattern.match(video_player)
        if default_match is not None:
            try:
                return default_match.group(1)
            except:
                return None
    return match


class DownloadWorker(Thread):
    def __init__(self, queue, proxies=None):
        Thread.__init__(self)
        self.queue = queue
        self.proxies = proxies
        self._register_regex_match_rules()

    def run(self):
        while True:
            medium_type, post, target_folder = self.queue.get()
            self.download(medium_type, post, target_folder)
            self.queue.task_done()

    def download(self, medium_type, post, target_folder):
        try:
            medium_url = self._handle_medium_url(medium_type, post)
            if medium_url is not None:
                self._download(medium_type, medium_url, target_folder, post.get('@id', 'unknown'))
        except TypeError:
            pass

    # can register different regex match rules
    def _register_regex_match_rules(self):
        # will iterate all the rules
        # the first matched result will be returned
        self.regex_rules = [video_source_match(), video_hd_match(), video_default_match()]

    def _handle_medium_url(self, medium_type, post):
        try:
            if medium_type == "photo":
                # First try the traditional photo-url format
                try:
                    return post["photo-url"][0]["#text"]
                except:
                    # If no photo-url, check for images embedded in HTML regular-body
                    try:
                        regular_body = post["regular-body"]
                        
                        # First try to extract from srcset attribute (highest quality)
                        srcset_match = re.search(r'srcset="([^"]+)"', regular_body)
                        if srcset_match:
                            srcset = srcset_match.group(1)
                            # Parse srcset entries: "url 640w, url 1280w, ..."
                            entries = []
                            for entry in srcset.split(','):
                                entry = entry.strip()
                                # Extract URL and width from "https://...url NNNw" format
                                url_width_match = re.search(r'(https://[^\s]+)\s+(\d+)w', entry)
                                if url_width_match:
                                    url = url_width_match.group(1)
                                    width = int(url_width_match.group(2))
                                    entries.append((width, url))
                            
                            # Sort by width descending and return highest quality
                            if entries:
                                entries.sort(reverse=True)  # Sort by width (first element of tuple)
                                return entries[0][1]  # Return URL of highest width
                        
                        # Fall back to src attribute if no srcset
                        img_matches = re.findall(r'<img[^>]*src="([^"]+)"', regular_body)
                        if img_matches:
                            return img_matches[0]  # Return the first image found
                    except:
                        pass
                raise Exception("No photo-url or embedded images found")

            if medium_type == "video":
                video_player = post["video-player"][1]["#text"]
                for regex_rule in self.regex_rules:
                    matched_url = regex_rule(video_player)
                    if matched_url is not None:
                        return matched_url
                else:
                    raise Exception
        except:
            raise TypeError("Unable to find the right url for downloading. "
                            "Please open a new issue on "
                            "https://github.com/dixudx/tumblr-crawler/"
                            "issues/new attached with below information:\n\n"
                            "%s" % post)

    def _download(self, medium_type, medium_url, target_folder, post_id='unknown'):
        # Extract site name from target folder path
        site_name = os.path.basename(target_folder)

        # If URL is already complete (starts with http), use it directly
        if medium_url.startswith('http'):
            final_url = medium_url
        else:
            # For legacy relative URLs, construct full URL
            medium_name = medium_url.split("/")[-1].split("?")[0]
            if not medium_name.startswith("tumblr"):
                medium_name = "_".join([medium_url.split("/")[-2],
                                        medium_name])
            medium_name += ".mp4"
            final_url = 'https://vt.tumblr.com/' + medium_name

        medium_name = final_url.split("/")[-1].split("?")[0]
        
        # Extract resolution from URL if present (e.g., s1280x1920, _1280)
        resolution = None
        if 's' in final_url and 'x' in final_url:
            # Format: s1280x1920
            res_match = re.search(r'/s(\d+)x\d+/', final_url)
            if res_match:
                resolution = f"{res_match.group(1)}px"
        elif '_1280' in final_url or '_500' in final_url:
            # Format: _1280.jpg
            res_match = re.search(r'_(\d+)\.(jpg|png|gif)', final_url)
            if res_match:
                resolution = f"{res_match.group(1)}px"
        
        if not resolution:
            resolution = "unknown"

        file_path = os.path.join(target_folder, medium_name)
        if not os.path.isfile(file_path):
            print("Downloading %s from %s.\n" % (medium_name,
                                                 final_url))
            retry_times = 0
            while retry_times < RETRY:
                try:
                    resp = requests.get(final_url,
                                        stream=True,
                                        proxies=self.proxies,
                                        timeout=TIMEOUT)
                    if resp.status_code == 403:
                        retry_times = RETRY
                        print("Access Denied when retrieve %s.\n" % final_url)
                        raise Exception("Access Denied")
                    
                    file_size = 0
                    with open(file_path, 'wb') as fh:
                        for chunk in resp.iter_content(chunk_size=1024):
                            fh.write(chunk)
                            file_size += len(chunk)
                    
                    # Record successful download with size and resolution
                    download_tracker.record_download(site_name, medium_type, file_size, resolution)
                    
                    # Add delay between downloads if configured
                    if DELAY > 0:
                        time.sleep(DELAY)
                    break
                except:
                    # try again
                    pass
                retry_times += 1
            else:
                try:
                    os.remove(file_path)
                except OSError:
                    pass
                print("Failed to retrieve %s from %s.\n" % (medium_type,
                                                          final_url))


class CrawlerScheduler(object):

    def __init__(self, sites, proxies=None):
        self.sites = sites
        self.proxies = proxies
        self.queue = Queue.Queue()
        self.scheduling()

    def scheduling(self):
        # create workers
        for x in range(THREADS):
            worker = DownloadWorker(self.queue,
                                    proxies=self.proxies)
            # Setting daemon to True will let the main thread exit
            # even though the workers are blocking
            worker.daemon = True
            worker.start()

        for site in self.sites:
            self.download_media(site)

    def download_media(self, site):
        # Track start of site download
        download_tracker.start_site_download(site)

        self.download_photos(site)
        self.download_videos(site)

        # Track completion of site download
        download_tracker.finish_site_download(site)

    def download_videos(self, site):
        self._download_media(site, "video", START)
        # wait for the queue to finish processing all the tasks from one
        # single site
        self.queue.join()
        print("Finish Downloading All the videos from %s" % site)

    def download_photos(self, site):
        self._download_media(site, "photo", START)
        # wait for the queue to finish processing all the tasks from one
        # single site
        self.queue.join()
        print("Finish Downloading All the photos from %s" % site)

    def _download_media(self, site, medium_type, start):
        current_folder = os.getcwd()
        # Use DOWNLOADS folder if configured
        downloads_folder = os.path.join(current_folder, DOWNLOADS_FOLDER)
        if not os.path.isdir(downloads_folder):
            os.makedirs(downloads_folder)
        target_folder = os.path.join(downloads_folder, site)
        if not os.path.isdir(target_folder):
            os.mkdir(target_folder)

        base_url = "https://{0}.tumblr.com/api/read?type={1}&num={2}&start={3}"
        start = START
        while True:
            media_url = base_url.format(site, medium_type, MEDIA_NUM, start)
            response = requests.get(media_url,
                                    proxies=self.proxies)
            if response.status_code == 404:
                print("Site %s does not exist" % site)
                break

            try:
                xml_cleaned = re.sub(u'[^\x20-\x7f]+',
                                     u'', response.content.decode('utf-8'))

                response_file = os.path.join(target_folder, "{0}_{1}_{2}_{3}.response.xml".format(site, medium_type, MEDIA_NUM, start))
                with open(response_file, "w") as text_file:
                    text_file.write(xml_cleaned)

                data = xmltodict.parse(xml_cleaned)
                posts = data["tumblr"]["posts"]["post"]
                for post in posts:
                    # by default it is switched to false to generate less files,
                    # as anyway you can extract this from bulk xml files.
                    if EACH_POST_AS_SEPARATE_JSON:
                        post_json_file = os.path.join(target_folder, "{0}_post_id_{1}.post.json".format(site, post['@id']))
                        with open(post_json_file, "w") as text_file:
                            text_file.write(json.dumps(post))

                    try:
                        # if post has photoset, walk into photoset for each photo
                        photoset = post["photoset"]["photo"]
                        for photo in photoset:
                            self.queue.put((medium_type, photo, target_folder))
                    except:
                        # select the largest resolution
                        # usually in the first element
                        self.queue.put((medium_type, post, target_folder))
                start += MEDIA_NUM
            except KeyError:
                break
            except UnicodeDecodeError:
                print("Cannot decode response data from URL %s" % media_url)
                continue
            except Exception as e:
                import traceback
                print("Error from URL %s: %s" % (media_url, str(e)))
                traceback.print_exc()
                continue


def usage():
    print("1. Please create file sites.txt under this same directory.\n"
          "2. In sites.txt, you can specify tumblr sites separated by "
          "comma/space/tab/CR. Accept multiple lines of text\n"
          "3. Save the file and retry.\n\n"
          "Sample File Content:\nsite1,site2\n\n"
          "Or use command line options:\n\n"
          "Sample:\npython tumblr-photo-video-ripper.py site1,site2\n\n\n")
    print(u"未找到sites.txt文件，请创建.\n"
          u"请在文件中指定Tumblr站点名，并以 逗号/空格/tab/表格鍵/回车符 分割，支持多行.\n"
          u"保存文件并重试.\n\n"
          u"例子: site1,site2\n\n"
          u"或者直接使用命令行参数指定站点\n"
          u"例子: python tumblr-photo-video-ripper.py site1,site2")


def illegal_json():
    print("Illegal JSON format in file 'proxies.json'.\n"
          "Please refer to 'proxies_sample1.json' and 'proxies_sample2.json'.\n"
          "And go to http://jsonlint.com/ for validation.\n\n\n")
    print(u"文件proxies.json格式非法.\n"
          u"请参照示例文件'proxies_sample1.json'和'proxies_sample2.json'.\n"
          u"然后去 http://jsonlint.com/ 进行验证.")


def parse_sites(filename):
    with open(filename, "r") as f:
        raw_sites = f.read().rstrip().lstrip()

    raw_sites = raw_sites.replace("\t", ",") \
                         .replace("\r", ",") \
                         .replace("\n", ",") \
                         .replace(" ", ",")
    raw_sites = raw_sites.split(",")

    sites = list()
    for raw_site in raw_sites:
        site = raw_site.lstrip().rstrip()
        if site:
            sites.append(site)
    return sites


if __name__ == "__main__":
    cur_dir = os.path.dirname(os.path.realpath(__file__))
    sites = None

    proxies = None
    proxy_path = os.path.join(cur_dir, "proxies.json")
    if os.path.exists(proxy_path):
        with open(proxy_path, "r") as fj:
            try:
                proxies = json.load(fj)
                if proxies is not None and len(proxies) > 0:
                    print("You are using proxies.\n%s" % proxies)
            except:
                illegal_json()
                sys.exit(1)

    if len(sys.argv) < 2:
        # check the sites file
        filename = os.path.join(cur_dir, "sites.txt")
        if os.path.exists(filename):
            sites = parse_sites(filename)
        else:
            usage()
            sys.exit(1)
    else:
        sites = sys.argv[1].split(",")

    if len(sites) == 0 or sites[0] == "":
        usage()
        sys.exit(1)

    # Run the crawler
    CrawlerScheduler(sites, proxies=proxies)

    # Print final statistics summary
    download_tracker.print_overall_summary()
