
import feedparser
import json
import datetime
import os
import time

# Create data directory if it doesn't exist
if not os.path.exists('data'):
    os.makedirs('data')

# Add or remove feeds here. The Flutter app will automatically adapt!
SOURCES = [
    {"name": "BBC News", "url": "http://feeds.bbci.co.uk/news/rss.xml", "category": "General"},
    {"name": "ESPN", "url": "https://www.espn.com/espn/rss/news", "category": "Sports"},
    {"name": "The Verge", "url": "https://www.theverge.com/rss/index.xml", "category": "Tech"}
]

def get_image(entry):
    if 'media_content' in entry:
        return entry.media_content[0]['url']
    if 'links' in entry:
        for link in entry.links:
            if 'image' in link.get('type', ''):
                return link.get('href')
    # Premium fallback image if the news site forgets to include one
    return "https://images.unsplash.com/photo-1504711434969-e33886168f5c?q=80&w=1000"

all_articles = []

for src in SOURCES:
    print(f"Fetching {src['name']}...")
    try:
        feed = feedparser.parse(src['url'])
        for entry in feed.entries[:15]: # Grab top 15 stories per source
            all_articles.append({
                "id": entry.link,
                "title": entry.title,
                "imageUrl": get_image(entry),
                "source": src['name'],
                "category": src['category'],
                "link": entry.link,
                "timestamp": datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                "isSaved": 0
            })
        time.sleep(2) # Polite delay so we don't get blocked
    except Exception as e:
        print(f"Failed to fetch {src['name']}: {e}")

# Save to JSON
with open('data/news.json', 'w') as f:
    json.dump(all_articles, f, indent=4)
