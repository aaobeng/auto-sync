import feedparser
import json
import datetime
import os
import time
import re
import math
import requests
import random
from bs4 import BeautifulSoup
from newspaper import Article
import newspaper

# --- CONFIGURATION ---
DATA_DIR = 'data'
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

# Realistic browser pool to mimic different devices and avoid bot detection
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.3.1 Safari/605.1.15",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Linux; Android 13; SM-S901B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Mobile Safari/537.36"
]

# Cleanly organized sources with specific categories
SOURCES = [
    # FOOTBALL
    {"name": "The Sun - Football", "url": "https://www.thesun.co.uk/sport/football/feed/", "category": "Football"},
    {"name": "Mirror Football", "url": "https://www.mirror.co.uk/sport/football/rss.xml", "category": "Football"},
    {"name": "Sky Sports Football", "url": "https://www.skysports.com/rss/12040", "category": "Football"},
    {"name": "The Guardian Football", "url": "https://www.theguardian.com/football/rss", "category": "Football"},
    {"name": "TalkSport Football", "url": "https://talksport.com/football/feed/", "category": "Football"},

    # OTHER SPORTS & BOXING
    {"name": "Daily Mail Sport", "url": "https://www.dailymail.co.uk/sport/index.rss", "category": "Sports"},
    {"name": "Mirror Sport", "url": "https://www.mirror.co.uk/sport/rss.xml", "category": "Sports"},
    {"name": "ESPN", "url": "https://www.espn.com/espn/rss/news", "category": "Sports"},
    {"name": "Sky Sports General", "url": "https://www.skysports.com/rss/12020", "category": "Sports"},
    {"name": "Daily Mail Boxing", "url": "https://www.dailymail.co.uk/sport/boxing/index.rss", "category": "Boxing"},
    {"name": "TalkSport Boxing", "url": "https://talksport.com/sport/boxing/feed/", "category": "Boxing"},

    # GENERAL & WORLD NEWS
    {"name": "The Sun - News", "url": "https://www.thesun.co.uk/news/feed/", "category": "News"},
    {"name": "Mirror News", "url": "https://www.mirror.co.uk/news/rss.xml", "category": "News"},
    {"name": "BBC News", "url": "https://feeds.bbci.co.uk/news/rss.xml", "category": "News"},
    {"name": "CNN Top Stories", "url": "http://rss.cnn.com/rss/edition.rss", "category": "World"},
    {"name": "Al Jazeera World", "url": "https://www.aljazeera.com/xml/rss/all.xml", "category": "World"},
    {"name": "NYT World", "url": "https://rss.nytimes.com/services/xml/rss/nyt/World.xml", "category": "World"},

    # GHANA NEWS 
    {"name": "MyJoyOnline", "url": "https://www.myjoyonline.com/feed/", "category": "Ghana News"},
    {"name": "Citi Newsroom", "url": "https://citinewsroom.com/feed/", "category": "Ghana News"},
    {"name": "Pulse Ghana", "url": "https://www.pulse.com.gh/rss", "category": "Ghana News"},
    {"name": "GhanaWeb General", "url": "https://cdn.ghanaweb.com/feed/newsfeed.xml", "category": "Ghana News"},

    # TECH
    {"name": "The Verge", "url": "https://www.theverge.com/rss/index.xml", "category": "Tech"},
    {"name": "TechCrunch", "url": "https://techcrunch.com/feed/", "category": "Tech"},
    {"name": "Wired", "url": "https://www.wired.com/feed/rss", "category": "Tech"},
    {"name": "CNET", "url": "https://www.cnet.com/rss/news/", "category": "Tech"},
]

def get_random_headers():
    return {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Referer": random.choice(["https://www.google.com/", "https://twitter.com/", "https://www.bing.com/"]),
        "Accept-Language": "en-US,en;q=0.5",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1"
    }

def get_full_article_data(url):
    """Deep Scrapes the text, cleans it, and calculates reading time."""
    try:
        config = newspaper.Config()
        config.browser_user_agent = random.choice(USER_AGENTS)
        config.request_timeout = 15 # Give it more time to load full pages
        article = Article(url, config=config)
        article.download()
        article.parse()
        
        full_text = article.text
        
        # --- INTELLIGENCE: Clean up the junk ---
        junk_patterns = [
            r"Follow us on.*", r"Sign up for.*", r"Advertisement", 
            r"Read more:.*", r"Share this:.*", r"Story continues below.*"
        ]
        for pattern in junk_patterns:
            full_text = re.sub(pattern, "", full_text, flags=re.IGNORECASE)

        full_text = full_text.strip()
        
        # If we got a good chunk of text, calculate read time
        if len(full_text) > 200:
            word_count = len(full_text.split())
            read_time_mins = max(1, math.ceil(word_count / 200)) # Avg reading speed is 200 wpm
            return {
                "content": full_text,
                "readTime": f"{read_time_mins} min read"
            }
        else:
            return {
                "content": "Full article could not be extracted. This might be a video or interactive page.",
                "readTime": "1 min read"
            }
    except Exception:
        return {
            "content": "Content unavailable for offline reading.",
            "readTime": "1 min read"
        }

def get_image(entry, link):
    url = None

    # 1. RSS MEDIA TAGS
    if 'media_content' in entry and len(entry.media_content) > 0:
        url = entry.media_content[0].get('url')
    elif 'media_thumbnail' in entry and len(entry.media_thumbnail) > 0:
        url = entry.media_thumbnail[-1].get('url')

    # 2. AT-ALL-COSTS DEEP SCRAPE
    if not url or "unsplash" in url:
        try:
            time.sleep(random.uniform(0.5, 1.5)) 
            
            resp = requests.get(link, timeout=10, headers=get_random_headers())
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, 'html.parser')
                meta = soup.find("meta", property="og:image") or soup.find("meta", attrs={"name": "twitter:image"})
                if meta:
                    url = meta.get("content")
                
                if not url:
                    hidden_images = re.findall(r'(https://a\d?\.espncdn\.com/[^"\']+\.(?:jpg|png))', resp.text)
                    if hidden_images:
                        for img in hidden_images:
                            if '16x9' in img or 'picture' in img:
                                url = img
                                break
                        if not url: 
                            url = hidden_images[0]

                if not url:
                    scripts = soup.find_all("script", type="application/ld+json")
                    for s in scripts:
                        if not s.string:
                            continue
                        try:
                            data = json.loads(s.string)
                            items = data if isinstance(data, list) else [data]
                            for item in items:
                                if isinstance(item, dict) and 'image' in item:
                                    img_data = item['image']
                                    url = img_data.get('url') if isinstance(img_data, dict) else img_data
                                    break
                            if url: 
                                break
                        except json.JSONDecodeError: 
                            continue
        except Exception: 
            pass 

    # 3. SPEED & SPINNER FIX
    if url and isinstance(url, str) and len(url) > 10:
        if "espn" not in url:
            url = url.split('?')[0] 
        
        if url.startswith('//'): 
            url = 'https:' + url
        
        url = re.sub(r'/\d+x\d+/', '/400x300/', url)
        if "espn" in url and "?width=" not in url: 
            url += "?width=400"
        if "thesun.co.uk" in url: 
            url = url.replace("original", "thumbnail")
        
        return url
    
    return "https://images.unsplash.com/photo-1504711434969-e33886168f5c?w=400&q=80"

# --- EXECUTION ---

grouped_articles = {
    "Football": [],
    "News": [],
    "Boxing": [],
    "Sports": [],
    "Ghana News": [],
    "World": [],
    "Tech": []
}

seen_links = set()
total_items = 0

for src in SOURCES:
    print(f"🔄 Scrutinizing {src['name']}...")
    try:
        headers = get_random_headers()
        feed_response = requests.get(src['url'], headers=headers, timeout=15)
        feed = feedparser.parse(feed_response.content)
        
        for entry in feed.entries[:8]:
            link = entry.get('link', '')
            if not link or link in seen_links: 
                continue
            
            img = get_image(entry, link)
            
            # THE MAGIC: Get the full text AND read time
            time.sleep(random.uniform(0.5, 1.5))
            article_info = get_full_article_data(link)
            
            if hasattr(entry, 'published_parsed') and entry.published_parsed:
                published_time = datetime.datetime.fromtimestamp(time.mktime(entry.published_parsed)).strftime('%Y-%m-%d %H:%M:%S')
            else:
                published_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            article_data = {
                "id": link,
                "title": entry.get('title', 'No Title'),
                "imageUrl": img,
                "source": src['name'],
                "category": src['category'],
                "link": link,
                "timestamp": published_time, 
                "isSaved": 0,
                "readTime": article_info["readTime"], # Added intelligence
                "content": article_info["content"]    # Full deep-scraped text
            }
            
            cat = src['category']
            if cat not in grouped_articles:
                grouped_articles[cat] = []
                
            grouped_articles[cat].append(article_data)
            seen_links.add(link)
            total_items += 1
            
        time.sleep(random.uniform(0.5, 2.0)) 
            
    except Exception as e:
        print(f"❌ Error with {src['name']}: {e}")

# Final JSON Save
filepath = os.path.join(DATA_DIR, 'news.json')
with open(filepath, 'w', encoding='utf-8') as f:
    json.dump(grouped_articles, f, indent=4, ensure_ascii=False)

print(f"✅ SUCCESS! {total_items} items processed and grouped by category.")
