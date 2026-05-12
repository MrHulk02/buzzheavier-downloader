import os
import re
import requests
from bs4 import BeautifulSoup
import logging
from tqdm import tqdm
import argparse
from urllib.parse import urljoin

VALID_DOMAINS = [
    'buzzheavier.com',
    'bzzhr.co',
    'bzzhr.to',
    'fuckingfast.net',
    'fuckingfast.co',
    'flashbang.sh',
    'trashbytes.net',
]

QUALITY_CHOICES = ['540p', '720p', '1080p']

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger()

def resolve_url(input_str):
    input_str = input_str.strip()
    if input_str.startswith('http'):
        for domain in VALID_DOMAINS:
            if domain in input_str:
                return input_str
        raise ValueError(f"url domain not recognized: {input_str}")
    elif len(input_str) == 12:
        return f'https://{VALID_DOMAINS[0]}/{input_str}'
    else:
        raise ValueError(f"invalid input: {input_str}")

def get_download_url(url):
    if not url.startswith('http'):
        url = f'https://{VALID_DOMAINS[0]}/{url}'

    response = requests.get(url)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, 'html.parser')
    download_link = soup.find('a', attrs={'hx-get': re.compile(r'/download\?t=')})

    if download_link:
        download_url = urljoin(url, download_link['hx-get'])
    else:
        download_url = url + '/download'

    headers = {
        'hx-current-url': url,
        'hx-request': 'true',
        'referer': url
    }
    head_response = requests.head(download_url, headers=headers, allow_redirects=False)
    return head_response.headers.get('hx-redirect')

def get_ids(url):
    response = requests.get(url)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, 'html.parser')

    items = []
    for link in soup.find_all('a', href=True):
        href = link['href']
        if len(href) == 13:
            episode_match = re.search(r'(?:S\d{1,2})?E(\d{2,3})(?:[.\s_-])', link.get_text(strip=True))
            episode = episode_match.group(1).lstrip('0').zfill(2) if episode_match else None
            items.append({
                'id': href[1:],
                'title': link.get_text(strip=True),
                'episode': episode
            })
    return items

def episode_filter(items, episodes, quality):
    return [
        item for item in items
        if (not quality or quality.lower() in item['title'].lower())
        and (not episodes or item['episode'] in [f"{ep:02}" for ep in episodes])
    ]

def sanitize_name(name):
    return re.sub(r'[<>:"/\\|?*]', '', name)

def download_file(title, final_url, foldertitle=None):
    if foldertitle:
        down_path = os.path.join("downloads", foldertitle)
    else:
        down_path = os.path.join("downloads")

    temp_path = os.path.join("temp")

    os.makedirs(down_path, exist_ok=True)
    os.makedirs(temp_path, exist_ok=True)

    if os.path.exists(os.path.join(down_path, title)):
        logger.info(f"{title} already downloaded")
        return
    
    temp_file = os.path.join(temp_path, f"{title}.part.{os.getpid()}")

    file_response = requests.get(final_url, stream=True, timeout=60)
    file_response.raise_for_status()
    total_size = int(file_response.headers.get('content-length', 0))
    block_size = 1024
    with open(temp_file, 'wb') as f, tqdm(
        total=total_size, unit='B', unit_scale=True, desc=title
    ) as progress_bar:
        for chunk in file_response.iter_content(chunk_size=block_size):
            if chunk:
                f.write(chunk)
                progress_bar.update(len(chunk))

    os.replace(temp_file, os.path.join(down_path, title))

def download_buzzheavier(input_str, episode=None, quality=None, fallback_quality=False):
    url = resolve_url(input_str)
    response = requests.get(url)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, 'html.parser')
    title = sanitize_name(soup.title.string.strip())
    logger.info(f"Title: {title}")

    hx_redirect = get_download_url(url)

    if not hx_redirect:
        items = get_ids(url)
        
        if quality or episode:
            filtered_items = episode_filter(items, episode, quality)
        else:
            filtered_items = items

        if not filtered_items and fallback_quality and quality:
            logger.info(f"no matching items found for default quality: {quality}, using available quality")
            filtered_items = episode_filter(items, episode, None)
        
        if not filtered_items:
            logger.error(f"no matching items found for quality: {quality} and episode: {episode}")
            return
        
        for item in filtered_items:
            hx_redirect = get_download_url(item['id'])
            if not hx_redirect:
                logger.error(f"no download link found for id: {item['id']}")
                continue

            domain = url.split('/')[2]
            final_url = f'https://{domain}{hx_redirect}' if not hx_redirect.startswith('http') else hx_redirect
            download_file(sanitize_name(item['title']), final_url, title)
    else:
        domain = url.split('/')[2]
        final_url = f'https://{domain}{hx_redirect}' if not hx_redirect.startswith('http') else hx_redirect
        download_file(title, final_url)

def parse_episode(ep_range):
    if not ep_range:
        return None
    try:
        if '-' in ep_range:
            start, end = map(int, ep_range.split('-'))
            if start > end:
                logger.error(f'invalid range: start cannot be greater than end.')
                return None
            return [f'{x:02d}' for x in range(start, end + 1)]
        else:
            return [f'{int(ep_range):02d}']
    except ValueError:
        logger.error(f'invalid range format: "{ep_range}"')
        return None

def parse_quality(quality):
    quality = quality.lower()
    if quality in ['540', '720', '1080']:
        quality = f'{quality}p'
    if quality not in QUALITY_CHOICES:
        raise argparse.ArgumentTypeError(f"invalid choice: '{quality}' (choose from 540p, 720p, 1080p)")
    return quality
    
def main():
    parser = argparse.ArgumentParser(description='buzzheavier downloader')
    parser.add_argument('-?', action='help', help='show this help message and exit')
    parser.add_argument('input', help='id or url to download')
    parser.add_argument('-d', '--debug', action='store_true', help='debug logging')
    parser.add_argument('-e', '--episode', type=str, help='specific episode or range of episodes to process (e.g., "1" or "1-5")')
    parser.add_argument('-q', '--quality', type=parse_quality, metavar='QUALITY', help='video quality: 540/720/1080 or 540p/720p/1080p')

    args = parser.parse_args()

    if args.debug:
        logger.setLevel(logging.DEBUG)

    try:
        quality = args.quality or "720p"
        download_buzzheavier(args.input, parse_episode(args.episode), quality, fallback_quality=not args.quality)
    except Exception as e:
        logger.error(f"failed to download {args.input}: {e}")

if __name__ == '__main__':
    main()
