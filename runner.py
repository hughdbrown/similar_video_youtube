#!/usr/bin/env python3
from pathlib import Path
import webbrowser


def main():
    p = Path("rodecaster-video-youtube.txt")
    chrome = webbrowser.get('chrome')
    all_urls = sorted(p.read_text().splitlines())
    for i, url in enumerate(all_urls):
        print(f"{'-' * 30} {i} / {len(all_urls)} {url}")
        chrome.open_new(url)
        input("Press Enter to continue...")


if __name__ == '__main__':
    main()
