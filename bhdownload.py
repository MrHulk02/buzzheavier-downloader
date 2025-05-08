import requests
from bs4 import BeautifulSoup
import logging
from tqdm import tqdm
import argparse

VALID_DOMAINS = [
    'buzzheavier.com',
    'bzzhr.co',
    'fuckingfast.net',
    'fuckingfast.co'
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
            items.append({
                'id': href[1:],
                'title': link.get_text(strip=True)
            })
    return items

def filter_by_quality(items, quality):
    return [item for item in items if quality.lower() in item['title'].lower()]

def download_file(title, final_url):
    file_response = requests.get(final_url, stream=True)
    file_response.raise_for_status()
    total_size = int(file_response.headers.get('content-length', 0))
    block_size = 1024
    with open(title, 'wb') as f, tqdm(
        total=total_size, unit='B', unit_scale=True, desc=title
    ) as progress_bar:
        for chunk in file_response.iter_content(chunk_size=block_size):
            if chunk:
                f.write(chunk)
                progress_bar.update(len(chunk))

def download_buzzheavier(input_str, quality=None):
    url = resolve_url(input_str)
    response = requests.get(url)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, 'html.parser')
    title = soup.title.string.strip()
    logger.info(f"Title: {title}")

    hx_redirect = get_download_url(url)

    if not hx_redirect:
        items = get_ids(url)
        if quality:
            items = filter_by_quality(items, quality)

        if not items:
            logger.error(f"no matching items found for quality: {quality}")
            return

        for item in items:
            hx_redirect = get_download_url(item['id'])
            if not hx_redirect:
                logger.error(f"no download link found for id: {item['id']}")
                continue

            domain = url.split('/')[2]
            final_url = f'https://{domain}{hx_redirect}' if not hx_redirect.startswith('http') else hx_redirect
            download_file(item['title'], final_url)
    else:
        domain = url.split('/')[2]
        final_url = f'https://{domain}{hx_redirect}' if not hx_redirect.startswith('http') else hx_redirect
        download_file(title, final_url)

def main():
    parser = argparse.ArgumentParser(description='buzzheavier downloader')
    parser.add_argument('input', help='id or url to download')
    parser.add_argument('-q', '--quality', choices=QUALITY_CHOICES, help='video quality')
    parser.add_argument('-d', '--debug', action='store_true', help='debug logging')

    args = parser.parse_args()

    if args.debug:
        logger.setLevel(logging.DEBUG)

    try:
        download_buzzheavier(args.input, quality=args.quality)
    except Exception as e:
        logger.error(f"failed to download {args.input}: {e}")

if __name__ == '__main__':
    main()
