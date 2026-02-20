import feedparser
import json
import datetime
import os
import time
import re

# Create data directory if it doesn't exist
if not os.path.exists('data'):
    os.makedirs('data')

# Your newly expanded sources list!
SOURCES = [
    {"name": "BBC News", "url": "http://feeds.bbci.co.uk/news/rss.xml", "category": "General"},
    {"name": "ESPN", "url": "https://www.espn.com/espn/rss/news", "category": "Sports"},
    {"name": "The Verge", "url": "https://www.theverge.com/rss/index.xml", "category": "Tech"},
    {"name": "CinemaBlend", "url": "https://www.cinemablend.com/rss/news", "category": "Movies"},
    {"name": "The Guardian", "url": "http://feeds.theguardian.com/xml/uk_news_rss.xml", "category": "General"},
    {"name": "The New York Times", "url": "https://www.nytimes.com/svc/collections/v2/pages/index.html?doc_id=THE_NEW_YORK_TIMES", "category": "General"},
    {"name": "CNN", "url": "http://rss.cnn.com/rss/edition_world.rss", "category": "World"},
    {"name": "Reuters", "url": "http://xml.reuters.com/data/xml/synopsis.xml", "category": "World"}
]

# --- NEW: Grabs the REAL time the article was posted ---
def get_real_time(entry):
    try:
        # Feedparser automatically finds the published date in the RSS
        time_struct = entry.published_parsed or entry.updated_parsed
        # Convert it to our standard SQLite format
        real_time = datetime.datetime.fromtimestamp(time.mktime(time_struct))
        return real_time.strftime('%Y-%m-%d %H:%M:%S')
    except:
        # If the news site forgets to include a time, fallback to right now
        return datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

# --- NEW: Grabs the REAL image URL of the article ---
def get_image(entry):
    if 'media_content' in entry and len(entry.media_content) > 0:
        return entry.media_content[0]['url']
    if 'media_thumbnail' in entry and len(entry.media_thumbnail) > 0:
        return entry.media_thumbnail[0]['url']
    if 'enclosures' in entry:
        for enc in entry.enclosures:
            if 'image' in enc.get('type', ''):
                return enc.get('href')
    if 'links' in entry:
        for link in entry.links:
            if 'image' in link.get('type', ''):
                return link.get('href')

    # Search inside the HTML text for a hidden image tag
    html_content = ""
    if 'content' in entry and len(entry.content) > 0:
        html_content = entry.content[0].value
    elif 'summary' in entry:
        html_content = entry.summary
        
    match = re.search(r'img.*?src="([^"]+)"', html_content)
    if match:
        return match.group(1)

    return "https://images.unsplash.com/photo-1504711434969-e33886168f5c?q=80&w=1000"

# --- Main Loop to fetch and save the articles ---
all_articles = []

for src in SOURCES:
    print(f"Fetching {src['name']}...")
    try:
        feed = feedparser.parse(src['url'])
        for entry in feed.entries[:15]: 
            all_articles.append({
                "id": entry.link,
                "title": entry.title,
                "imageUrl": get_image(entry),
                "source": src['name'],
                "category": src['category'],
                "link": entry.link,
                "timestamp": get_real_time(entry),
                "isSaved": 0
            })
        time.sleep(2) 
    except Exception as e:
        print(f"Failed to fetch {src['name']}: {e}")

# Save to JSON
with open('data/news.json', 'w') as f:
    json.dump(all_articles, f, indent=4)
    
print("News successfully scraped and saved!")
