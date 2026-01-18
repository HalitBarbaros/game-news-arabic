import feedparser
from google import genai
from google.genai import types
import os
import datetime

# 1. SETUP
# We get the key from the Environment (GitHub Secrets) for security
API_KEY = os.environ.get("GEMINI_API_KEY")
client = genai.Client(api_key=API_KEY)

rss_feeds = [
    "https://feeds.ign.com/ign/news",
    "https://www.gamespot.com/feeds/news/",
    "https://kotaku.com/rss",
]

# 2. HTML TEMPLATE (Modern, Dark Mode, Arabic RTL)
html_template = """
<!DOCTYPE html>
<html dir="rtl" lang="ar">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>أخبار الألعاب - Game News</title>
    <link href="https://fonts.googleapis.com/css2?family=Tajawal:wght@400;700&display=swap" rel="stylesheet">
    <style>
        body {{ background-color: #121212; color: #ffffff; font-family: 'Tajawal', sans-serif; margin: 0; padding: 20px; }}
        .container {{ max-width: 800px; margin: 0 auto; }}
        h1 {{ text-align: center; color: #bb86fc; }}
        .timestamp {{ text-align: center; color: #888; font-size: 0.8rem; margin-bottom: 30px; }}
        .card {{ background: #1e1e1e; border-radius: 12px; overflow: hidden; margin-bottom: 25px; box-shadow: 0 4px 6px rgba(0,0,0,0.3); border: 1px solid #333; }}
        .card img {{ width: 100%; height: 200px; object-fit: cover; }}
        .card-content {{ padding: 20px; }}
        .source-tag {{ background: #03dac6; color: #000; padding: 4px 8px; border-radius: 4px; font-size: 0.7rem; font-weight: bold; }}
        h2 {{ margin-top: 10px; font-size: 1.5rem; }}
        ul {{ padding-right: 20px; color: #ccc; line-height: 1.6; }}
        a {{ display: block; text-align: center; background: #3700b3; color: white; text-decoration: none; padding: 10px; margin-top: 15px; border-radius: 6px; }}
        a:hover {{ background: #6200ea; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🎮 أخبار الألعاب - Game News</h1>
        <div class="timestamp">آخر تحديث: {date}</div>
        {articles}
    </div>
</body>
</html>
"""

card_template = """
<div class="card">
    <img src="{image}" alt="News Image" onerror="this.src='https://placehold.co/600x400/1e1e1e/FFF?text=No+Image'">
    <div class="card-content">
        <span class="source-tag">{source}</span>
        <h2>{headline}</h2>
        <ul>{summary_points}</ul>
        <a href="{link}" target="_blank">قراءة المقال الأصلي</a>
    </div>
</div>
"""

def get_translation(title, summary):
    prompt = f"""
    Task: Translate video game news to Arabic.
    1. Translate headline to Arabic.
    2. Summarize content into 3 short Arabic bullet points (<li>Point</li>).
    English Title: {title}
    English Content: {summary}
    Output JSON: {{ "headline": "...", "bullets": "<li>...</li><li>...</li>" }}
    """
    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt,
            config=types.GenerateContentConfig(response_mime_type="application/json")
        )
        return response.parsed
    except:
        return None

def main():
    articles_html = ""
    processed_count = 0
    
    # Process feeds
    for feed_url in rss_feeds:
        feed = feedparser.parse(feed_url)
        source_name = feed.feed.title.split()[0] # e.g., "IGN" from "IGN News"
        
        for entry in feed.entries:
            if processed_count >= 10: break # Limit to top 10 stories total
            
            # Find Image
            image_url = "https://placehold.co/600x400/1e1e1e/FFF?text=Game+News"
            if 'media_content' in entry: image_url = entry.media_content[0]['url']
            elif 'links' in entry:
                for l in entry.links:
                    if l['type'].startswith('image'): image_url = l['href']; break
            
            content = getattr(entry, 'summary', getattr(entry, 'description', ''))
            
            # Call Gemini
            print(f"Translating: {entry.title}...")
            trans = get_translation(entry.title, content)
            
            if trans:
                articles_html += card_template.format(
                    image=image_url,
                    source=source_name,
                    headline=trans['headline'],
                    summary_points=trans['bullets'],
                    link=entry.link
                )
                processed_count += 1

    # Generate Final HTML
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M UTC")
    final_html = html_template.format(date=now, articles=articles_html)
    
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(final_html)
    print("✅ Website generated successfully!")

if __name__ == "__main__":
    main()
