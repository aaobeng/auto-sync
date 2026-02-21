import feedparser
import json
import datetime
import os
import time
import re
import requests
from bs4 import BeautifulSoup

# --- CONFIGURATION ---
feedparser.USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"

if not os.path.exists('data'):
    os.makedirs('data')

SOURCES = [
    # --- GENERAL & WORLD ---
    {"name": "BBC News", "url": "https://feeds.bbci.co.uk/news/rss.xml", "category": "General"},
    {"name": "The Guardian", "url": "https://www.theguardian.com/world/rss", "category": "General"},
    {"name": "NYT Home", "url": "https://rss.nytimes.com/services/xml/rss/nyt/HomePage.xml", "category": "General"},
    {"name": "Reuters Global", "url": "https://news.google.com/rss/search?q=world+news+when:24h", "category": "World"},
    {"name": "AP News", "url": "https://news.google.com/rss/search?q=AP+Top+News+when:24h", "category": "World"},
    {"name": "Al Jazeera", "url": "https://www.aljazeera.com/xml/rss/all.xml", "category": "World"},

    # --- SPORTS ---
    {"name": "ESPN", "url": "https://www.espn.com/espn/rss/news", "category": "Sports"},
    {"name": "Sky Sports", "url": "https://www.skysports.com/rss/12040", "category": "Sports"},
    {"name": "Fox Sports", "url": "https://api.foxsports.com/v2/content/optimized-rss?partnerKey=MB0ByRq3p6W9bsY&size=30", "category": "Sports"},
    {"name": "Yahoo Sports", "url": "https://sports.yahoo.com/rss/", "category": "Sports"},

    # --- TECH & SCIENCE ---
    {"name": "The Verge", "url": "https://www.theverge.com/rss/index.xml", "category": "Tech"},
    {"name": "TechCrunch", "url": "https://techcrunch.com/feed/", "category": "Tech"},
    {"name": "Wired", "url": "https://www.wired.com/feed/rss", "category": "Tech"},
    {"name": "NASA News", "url": "https://www.nasa.gov/news-release/feed/", "category": "Science"},
    {"name": "Space.com", "url": "https://www.space.com/feeds/all", "category": "Science"},

    # --- GAMING ---
    {"name": "IGN", "url": "https://feeds.ign.com/ign/news", "category": "Gaming"},
    {"name": "Polygon", "url": "https://www.polygon.com/rss/index.xml", "category": "Gaming"},
    {"name": "GameSpot", "url": "https://www.gamespot.com/feeds/news/", "category": "Gaming"},
    {"name": "Kotaku", "url": "https://kotaku.com/rss", "category": "Gaming"},

    # --- BUSINESS ---
    {"name": "CNBC Business", "url": "https://search.cnbc.com/rs/search/combinedcms/view.xml?profile=120000000&id=10001147", "category": "Business"},
    {"name": "Fortune", "url": "https://fortune.com/feed/fortune-feeds/?id=3230629", "category": "Business"},
    {"name": "Investing.com", "url": "https://www.investing.com/rss/news.rss", "category": "Business"},

    # --- MOVIES & ENTERTAINMENT ---
    {"name": "Variety", "url": "https://variety.com/feed/", "category": "Movies"},
    {"name": "CinemaBlend", "url": "https://www.cinemablend.com/rss/news", "category": "Movies"},
    {"name": "The Hollywood Reporter", "url": "https://www.hollywoodreporter.com/feed/", "category": "Movies"},
]

def get_real_time(entry):
    try:
        ts = entry.get('published_parsed') or entry.get('updated_parsed')
        if ts: return datetime.datetime.fromtimestamp(time.mktime(ts)).strftime('%Y-%m-%d %H:%M:%S')
    except: pass
    return datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

def get_image(entry):
    url = None
    link = entry.get('link', '')

    # 1. Handle YouTube Links immediately
    if 'youtube.com' in link or 'youtu.be' in link:
        video_id = None
        if 'v=' in link: video_id = link.split('v=')[1].split('&')[0]
        elif 'youtu.be/' in link: video_id = link.split('youtu.be/')[1].split('?')[0]
        if video_id: return f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg"

    # 2. Check RSS Media Content/Thumbnails
    if 'media_content' in entry and len(entry.media_content) > 0:
        url = entry.media_content[0].get('url')
    elif 'media_thumbnail' in entry and len(entry.media_thumbnail) > 0:
        url = entry.media_thumbnail[-1].get('url')
    elif 'enclosures' in entry:
        for e in entry.enclosures:
            if 'image' in e.get('type',''):
                url = e.get('href')
                break

    # 3. Regex for HTML summaries (if still no image)
    if not url:
        txt = entry.get('summary','') + entry.get('content',[{}])[0].get('value','')
        m = re.search(r'<img[^>]+src=["\']([^"\']+)["\']', txt)
        if m: url = m.group(1)

    # 4. DEEP SCRAPE (The Fix for Video Thumbnails)
    # If we still have no image, we visit the actual page to find the Open Graph image.
    if not url or "unsplash" in url:
        try:
            headers = {"User-Agent": feedparser.USER_AGENT}
            response = requests.get(link, timeout=5, headers=headers)
            soup = BeautifulSoup(response.text, 'html.parser')
            # Look for social media preview images (standard for all news videos)
            meta_og = soup.find("meta", property="og:image") or soup.find("meta", attrs={"name": "twitter:image"})
            if meta_og:
                url = meta_og.get("content")
        except:
            pass

    if url:
        if url.startswith('//'): url = 'https:' + url
        url = url.split('?')[0] # Clean trackers
        url = re.sub(r'/\d+x\d+/', '/800x600/', url) # Fix resolution
        return url
    
    # Final Fallback
    return "https://images.unsplash.com/photo-1504711434969-e33886168f5c?auto=format&fit=crop&w=800&q=80"

all_articles = []
seen_links = set()

for src in SOURCES:
    print(f"Scraping {src['name']}...")
    try:
        feed = feedparser.parse(src['url'])
        for entry in feed.entries[:25]:
            link = entry.get('link', '')
            if not link or link in seen_links: continue
            
            article_time_str = get_real_time(entry)
            article_time = datetime.datetime.strptime(article_time_str, '%Y-%m-%d %H:%M:%S')
            
            # Keep articles from last 48 hours
            if (datetime.datetime.now() - article_time).total_seconds() <= 172800:
                all_articles.append({
                    "id": link,
                    "title": entry.get('title', 'No Title'),
                    "imageUrl": get_image(entry),
                    "source": src['name'],
                    "category": src['category'],
                    "link": link,
                    "timestamp": article_time_str,
                    "isSaved": 0
                })
                seen_links.add(link)
        time.sleep(1) # Be polite
    except Exception as e:
        print(f"Error scraping {src['name']}: {e}")

# Save to data/news.json
with open('data/news.json', 'w', encoding='utf-8') as f:
    json.dump(all_articles, f, indent=4, ensure_ascii=False)

print(f"✅ Finished! Total Articles: {len(all_articles)}")
