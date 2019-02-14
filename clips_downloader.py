import configparser
import json
import math
import os
import threading
from datetime import datetime, timedelta

import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.wait import WebDriverWait

# Read the configuration
config = configparser.ConfigParser()
config.read('config.ini')

# Costants
CLIENT_ID = config['TWITCH_API']['CLIENT_ID']
MAX_CLIPS_REQUESTED = config['TWITCH_API']['MAX_CLIPS'] # Max number of clips retrieved from Twitch API
VIDEO_DURATION_THRESHOLD = 90 # Duration threshold for the total clips duration (i.e. the duration the merged video will have)
# Game IDs
FORTNITE_ID = 33214
APEX_ID = 511224

def get_clips_week():
    """Returns the most viewed clips of the last 7 days. (Max clips: 50)
    API documentation: https://dev.twitch.tv/docs/api/reference/#get-clips
    
    Returns:
        JSON -- Array with the information of the clips, see API documentation.
    """
    twitch_endpoint = 'https://api.twitch.tv/helix/clips?game_id={game_id}&first={max_clips}&started_at={start_date}'
    last_week_day = datetime.today() - timedelta(days=7)
    start_date_RFC3339 = last_week_day.strftime('%Y-%m-%dT00:00:00Z')

    r = requests.get(twitch_endpoint.format(game_id = APEX_ID, max_clips = MAX_CLIPS_REQUESTED,
        start_date = start_date_RFC3339),
        headers={'Client-ID': CLIENT_ID})

    clips_twitch_response = json.loads(r.content)['data']

    return clips_twitch_response

def get_download_links(clips_twitch_response):
    """Returns an array with the links to the .mp4 urls for the clips files and another array with the name of the clip
    The urls of some clips could not be retrieved, in that case they will not be return by the function (i.e. If you 
    ask for 30 urls maybe the function will return only 24)

    The only way (for now) to get the clip download url is reading the html code. Twitch generated the code dynamically
    so the use of Selenium is requiered.
    
    Arguments:
        clips_twitch_response {JSON} -- Array with the information of the clips returned by the Twith API
    
    Returns:
        [string] -- Array with the urls of the clips
        [string] -- Array with the names of the clips
    """

    # Use the Chrome driver
    driver = webdriver.Chrome()

    download_links = []
    clips_names = []
    total_duration = 0
    for clip in clips_twitch_response:
        driver.get(clip['url'])
        try:
            # Wait until src attribute is generated for the video
            WebDriverWait(driver, 10).until(expected_conditions.presence_of_element_located((By.CSS_SELECTOR, "video[src]")))

            # Find the src url inside a <div class = player-video><video src = DOWNLOAD_URL><\video><\div>
            element = driver.find_element_by_css_selector("video[src]")
            url = element.get_attribute('src')

            download_links.append(url)
            clips_names.append(clip['broadcaster_name'])

            # Find the video duration
            element = driver.find_element_by_css_selector("div.player-slider[aria-valuemax]")
            duration = int(float(element.get_attribute("aria-valuemax"))) # Convert to int to have a lower bound
            total_duration += duration
            if total_duration > VIDEO_DURATION_THRESHOLD:
                break

        except Exception:
            print("ERROR - Can't get the clip download url:{}".format(clip['url']))

    driver.close()

    return download_links, clips_names

def download_clips():
    """Downloads the most-viewed clips of the last 7 days into a folder
    """
    print("Getting clips download urls")
    clips_twitch_response = get_clips_week()
    download_urls, clips_names = get_download_links(clips_twitch_response)

    # Delete old files
    print("Deleting files in clip directory")
    for file in os.listdir('./clips/'):
        os.remove("./clips/{}".format(file))

    num_threads = 4 # Number of threads for concurrent download
    clips_per_thread = math.ceil(len(download_urls)/num_threads) # Number of clips each thread will download    
    threads_list = []
    print("Downloading {} clips using {} thread - {} clips per thread".format(len(download_urls), num_threads, clips_per_thread))
    # Create the clip_downloader threads and assign to each the clips that each one will download
    for i in range(0, num_threads):
        thread = ClipsDownloaderThread(i * clips_per_thread, i * clips_per_thread + clips_per_thread, download_urls, clips_names)
        thread.start()
        threads_list.append(thread)

    for thread in threads_list:
        thread.join()

    print("Clips downloaded")

    

class ClipsDownloaderThread(threading.Thread):
    """Thread class that will perform the download of several clips
    """
    clips_downloaded_counter = 0
    lock = threading.Lock()

    def __init__(self, init_clip, end_clip, download_urls, clip_names):
        """        
        Arguments:
            init_clip {int} -- Array index, init position of the download_urls array from which the url will be retrievd
            end_clip {int} -- Array index, last url (not included) of download_urls at which the thread will stop downloading
            download_urls {string_array} -- Array of strings with the download urls
            clip_names {string_urls} -- Names that will be use to save the clips files
        """
        threading.Thread.__init__(self)
        self.init_clip = init_clip
        self.end_clip = end_clip if end_clip < len(download_urls) else len(download_urls)
        self.download_urls = download_urls
        self.clip_names = clip_names

    def run(self):
        """Download into files (it's name is given in clip_names array) the clips from the clips urls (in download_urls array) in the range [init_clip, end_clip)
        """
        for i in range(self.init_clip, self.end_clip):
            url = self.download_urls[i]
            r = requests.get(url, stream=True) # Stream download
            with open("clips/{}${}$.mp4".format(i, self.clip_names[i]), 'wb') as f:
                for chunk in r.iter_content(chunk_size=1048576): 
                    if chunk:
                        f.write(chunk)

            ClipsDownloaderThread.lock.acquire()
            ClipsDownloaderThread.clips_downloaded_counter += 1
            print("{}/{} clips downloaded".format(ClipsDownloaderThread.clips_downloaded_counter, len(self.download_urls))) # Should this be taken out of the lock block?
            ClipsDownloaderThread.lock.release()
