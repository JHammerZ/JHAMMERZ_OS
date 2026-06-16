import os, requests
from pathlib import Path

TOKEN = os.environ['FB_PAGE_TOKEN']
PAGE_ID = os.environ['FB_PAGE_ID']
GRAPH = "https://graph.facebook.com/v19.0"

# Get last 90 days of posts
posts_url = f"{GRAPH}/{PAGE_ID}/posts?fields=id,message,created_time&limit=100&access_token={TOKEN}"
posts = requests.get(posts_url).json().get('data', [])

broken = []
for post in posts:
    msg = post.get('message', '')
    if 'jhammerz.github.io' in msg:
        # Extract URLs - lazy check
        for word in msg.split():
            if 'jhammerz.github.io' in word:
                url = word.strip('()[]')
                try:
                    r = requests.head(url, timeout=5, allow_redirects=True)
                    if r.status_code >= 400:
                        broken.append(f"Post {post['id']}: {url} → {r.status_code}")
                except:
                    broken.append(f"Post {post['id']}: {url} → TIMEOUT/DEAD")

report = "# BROKEN_LINKS\n> Auto-generated nightly\n\n"
if broken:
    report += f"**Found {len(broken)} broken links:**\n\n" + "\n".join(f"- {b}" for b in broken)
else:
    report += "**All links healthy. Your back catalog is immortal 🤘**"

Path('BROKEN_LINKS.md').write_text(report)
print(f"Meadow: Link health scan complete. {len(broken)} issues found.")
