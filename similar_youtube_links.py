#!/usr/bin/env python3
from collections import deque
import logging
from pathlib import Path
import time
from typing import Dict, List, Set

from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

logging_args = {
    "format": "%(asctime)s %(levelname)s %(message)s",
    "level": logging.DEBUG,
    "datefmt": "%Y-%m-%d %H:%M:%S",
    "encoding": "utf-8",
}
logging.basicConfig(**logging_args)
logger = logging.getLogger()


def get_html_content(video_url) -> str:
    # Start Playwright and open the browser
    with sync_playwright() as p:
        browser = p.firefox.launch(headless=False)  # Set headless=False for debugging to see the browser open
        page = browser.new_page()

        # Go to the YouTube video page
        page.goto(video_url)

        # Wait for a known selector to appear to ensure page content is loaded
        # This selector waits for the first video thumbnail in the "related videos" section
        page.wait_for_selector('ytd-compact-video-renderer a#thumbnail', timeout=10000)  # Adjust the timeout as needed

        # Simulate scrolling to load more similar videos
        for _ in range(10):
            page.evaluate("window.scrollBy(0, window.innerHeight);")  # Scroll down by one viewport height
            time.sleep(2)

        # Extract the full page content (after it is fully loaded)
        html_content = page.content()

        # Close the browser
        browser.close()

    return html_content


def trim_link(href: str) -> str:
    i = href.find("&t=")
    return href if i == -1 else href[:i]


def get_similar_videos(html_content, seen):
    # Use BeautifulSoup to parse the page content
    soup = BeautifulSoup(html_content, 'html.parser')

    video_links = []
    rcv = (
        "rodecaster video",
        "rødecaster video",
        "rode caster video",
        "røde caster video",
    )

    for video in soup.find_all('ytd-compact-video-renderer'):
        link_tag = video.find('a', id='thumbnail')

        if link_tag and 'href' in link_tag.attrs:
            href = link_tag['href']

            # Get the video title
            title_tag = video.find('span', id='video-title')  # Corrected tag for title extraction
            if not title_tag:
                title_tag = video.find('a', id='video-title')  # Backup in case 'span' is not found
            video_title = title_tag.text.strip() if title_tag else "No title"

            if any(rc in video_title.lower() for rc in rcv):
                if href.startswith('/watch?v='):
                    href = trim_link(href)
                    video_link = f"https://www.youtube.com{href}"
                    if video_link not in seen:
                        data = {'title': video_title, 'link': video_link}
                        video_links.append(data)
                    else:
                        logger.debug(f"Already seen '{video_link}'")
            else:
                logger.debug(f"Title missing 'RodeCaster Video': '{video_title}'")

    return video_links


# Define a function to scrape YouTube similar video links
def scrape_youtube_similar_videos(video_url: str, seen: Set[str]) -> List[Dict[str, str]]:
    print(f"{'-' * 30} {video_url}")
    try:
        html_content: str = get_html_content(video_url)
    except Exception as err:
        print(f"Exception: {err}")
        return {}
    else:
        video_links: List[Dict[str, str]] = get_similar_videos(html_content, seen)
        return video_links


if __name__ == "__main__":
    new_urls: Set[str] = set()
    seen: Set[str] = set()
    p = Path("rodecaster-video-youtube.txt")
    orig: List[str] = p.read_text().splitlines()
    queue = deque(orig)

    while queue:
        youtube_url: str = queue.pop()
        if youtube_url not in seen:
            seen.add(youtube_url)
            similar_videos: List[Dict[str, str]] = scrape_youtube_similar_videos(youtube_url, seen)

            if similar_videos:
                # Hack to keep from inserting into the queue more than once
                s: Set[str] = set(queue)

                print("Similar video links:")
                for video in similar_videos:
                    if (video_link := video["link"]) not in s:
                        # Enqueue new video links
                        print(video)
                        queue.append(video_link)
                        new_urls.add(video_link)

            print(f"Queue length: {len(queue)} New urls length: {len(new_urls)}")

    print(f"{'-' * 30} New urls")
    for youtube_url in sorted(new_urls):
        print(youtube_url)
    print(f"{'-' * 30}")

