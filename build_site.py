import feedparser
from google import genai
from google.genai import types
import os
import datetime

# 1. SETUP
API_KEY = os.environ.get("GEMINI_API_KEY")
client = genai.Client(api_key=API_KEY)

# 2. SOURCE: Steam News (Does not block robots)
rss_feeds = [
    "https://store.steampowered.com/feeds/news.xml"
]

# 3. HTML TEMPLATE
html_template = """
<!DOCTYPE html>
<html dir="rtl" lang="ar">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Steam News - LIVE</title>
    <link href="https://fonts.googleapis.com/css2?family=Tajawal:wght@400;700&display=swap" rel="stylesheet">
    <style>
        body {{ background-color: #121212; color: #ffffff; font-family: 'Tajawal', sans-serif; margin: 0; padding: 20px; }}
        .container {{ max-width: 800px; margin: 0 auto; }}
        
        /* Green Title = New Script is Active */
        h1 {{ text-align: center; color: #00ff00; border-bottom: 2px solid #00ff00; padding-bottom: 10px; }}
        
        .card {{ background: #1e1e1e; border-radius: 12px; margin-bottom: 25px; border: 1px solid #333; overflow: hidden; }}
        .card img {{ width: 100%; height: 200px; object-fit: cover; }}
        .card-content {{ padding: 20px; }}
        h2 {{ margin-top: 0; color: #fff; }}
        ul {{ padding-right: 20px; color: #ccc; }}
        .timestamp {{ text-align: center; color: #888; margin-bottom: 20px; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>✅ SYSTEM ONLINE (Steam)</h1>
        <div class="timestamp">Updated: {date}</div>
        {articles}
    </div>
</body>
</html>
"""

card_template = """
<div class="card">
    <img src="{image}" onerror="this.src='https://placehold.co/600x400/1e1e1e/FFF?text=Steam+News'">
    <div class="card-content">
        <h2>{headline}</h2>
        <ul>{summary_points}</ul>
        <a href="{link}" style="color:#00ff00; display:block; text-align:center; margin-top:15px;" target="_blank">Read Article</a>
    </div>
</div>
"""

def get_translation(title, summary):
    prompt = f"""
    Task: Translate video game news to Arabic.
    1. Translate headline to Arabic.
    2. Summarize content into 2 short bullet points.
    English Title: {title}
    English Content: {summary}
    Output JSON: {{ "headline": "...", "bullets": "<li>...</li><li>...</li>" }}
    """
    try:
        response = client.models.generate_content(
            model="gemini-1.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(response_mime_type="application/json")
        )
        return response.parsed
    except:
        return None

def main():
    articles_html = ""
    processed_count = 0
    
    for feed_url in rss_feeds:
        try:
            feed = feedparser.parse(feed_url)
            for entry in feed.entries:
                if processed_count >= 5: break
                
                # Simple image logic
                image_url = "https://placehold.co/600x400/1e1e1e/FFF?text=Steam+News"
                content = getattr(entry, 'summary', getattr(entry, 'description', ''))
                
                trans = get_translation(entry.title, content)
                
                if trans:
                    articles_html += card_template.format(
                        image=image_url,
                        headline=trans['headline'],
                        summary_points=trans['bullets'],
                        link=entry.link
                    )
                    processed_count += 1
        except Exception as e:
            print(f"Error: {e}")

    # Fallback Test Article
    if processed_count == 0:
        articles_html += """
        <div class="card">
            <div class="card-content">
                <h2>⚠️ Test Article (System Check)</h2>
                <ul>
                    <li>If you see this, the code updated successfully!</li>
                    <li>Steam feed was empty, so this is a placeholder.</li>
                </ul>
            </div>
        </div>
        """

    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M UTC")
    final_html = html_template.format(date=now, articles=articles_html)
    
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(final_html)

if __name__ == "__main__":
    main()
