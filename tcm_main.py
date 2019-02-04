import requests
import json
import configparser
from bs4 import BeautifulSoup
from selenium import webdriver

# Read the configuration
config = configparser.ConfigParser()
config.read('config.ini')

# Create constants
CLIENT_ID = config['TWITCH_API']['CLIENT_ID']
FORTNITE_ID = 33214

def get_clips_week():
    r = requests.get('https://api.twitch.tv/helix/clips?game_id={}&first=5&started_at={}'.format(FORTNITE_ID, '2019-01-27T00:00:00Z'), headers={'Client-ID': CLIENT_ID})

    clips = json.loads(r.content)['data']

    return clips

def get_download_links(clips_url):
    driver = webdriver.Chrome()

    download_links = []
    for clip_url in clips_url:
        driver.get(clip_url)
        html = driver.page_source

        web_tree = BeautifulSoup(html)
        try:
            url = web_tree.find('div', class_='player-video').find('video').attrs['src']
            download_links.append(url)
        except Exception:
            download_links.append("ERROR - {}".format(clip_url))

    driver.close()

    return download_links

def download_clips(download_urls, clip_name):
    for i, url in enumerate(download_urls):
        print("Downloading clip - {}/{}".format(i, len(download_urls)))
        r = requests.get(url, stream=True)
        with open("clips/{}${}.mp4".format(i, clip_name[i]), 'wb') as f:
            for chunk in r.iter_content(chunk_size=1024): 
                if chunk:
                    f.write(chunk)


def tcm():
    clips = get_clips_week()

    clips_url = [clip['url'] for clip in clips]
    download_urls = get_download_links(clips_url)
    download_clips(download_urls, ['{}${}'.format(clip['broadcaster_name'], clip['title']) for clip in clips])


if __name__ == "__main__":
    tcm()