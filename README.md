# BuzzHeavier Downloader

## Simple downloader for filehosting service [BuzzHeavier](https://buzzheavier.com/), written in Python.

---
## Features

- Supports multiple mirror domains: `buzzheavier.com`, `bzzhr.co`, `fuckingfast.net`, `fuckingfast.co`
- Download single files or full episode lists (folder links)
- Filter by video quality: `540p`, `720p`, or `1080p`
- Select individual episodes or ranges (e.g. `-e 1-5`)
- Displays download progress bar with `tqdm`
- Skips files that have already been downloaded

---

## Requirements

- Python 3.x
- `requests` and `beautifulsoup4` libraries
- `tqdm` for the progress bar

Install dependencies:

```bash
pip install requests beautifulsoup4 tqdm
```

---

## Usage

### Download a Single File or Folder Link

```bash
python3 bhdownload.py <id_or_url>
```

**Examples:**

```bash
python3 bhdownload.py x7v9k2mqp4zt
python3 bhdownload.py https://buzzheavier.com/x7v9k2mqp4zt
python3 bhdownload.py https://buzzheavier.com/xyzfolder123 -e 2-4 -q 720p
```


---

| Option            | Description                                  |
| ----------------- | -------------------------------------------- |
| `-e`, `--episode` | Episode number or range (e.g., `3` or `1-5`) |
| `-q`, `--quality` | Video quality: `540p`, `720p`, or `1080p`    |
| `-d`, `--debug`   | Enable debug logging                         |

---
## Output

- Files are saved to `downloads/<title>/`
- Temporary files are stored in `temp/` during the download process
- Skips files that have already been downloaded

## Notes

- All domains are interchangeable — the script handles them automatically.
- Make sure IDs are exactly 12 characters or full URLs from supported domains.

---

## No License

Use this code however the fuck you want. With good intent or not, for profit or not. It's public domain!

---
> [!TIP]
> Star this repo if you got baited by the link and opened it... it's fake ;)
