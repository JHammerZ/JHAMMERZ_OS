import os, requests, datetime, frontmatter, random
from dateutil import parser
from pathlib import Path

TOKEN = os.environ['FB_PAGE_TOKEN']
PAGE_ID = os.environ['FB_PAGE_ID']
GRAPH = "https://graph.facebook.com/v19.0"

# Load Meadow settings
meadow = frontmatter.load('MEADOW.md')
res_settings = meadow.get('resurrection', {})
min_age_days = res_settings.get('min_age_days', 365) # Only touch posts 1yr+ old
max_resurrect_per_run = res_settings.get('max_per_run', 3)
min_likes = res_settings.get('max_likes_to_resurrect', 10) # Only "flops"

# Get old posts
since_date = (datetime.datetime.now() - datetime.timedelta(days=min_age_days*2)).strftime('%Y-%m-%d')
posts_url = f"{GRAPH}/{PAGE_ID}/posts?fields=id,message,created_time,likes.summary(true),comments.summary(true)&since={since_date}&limit=100&access_token={TOKEN}"
posts = requests.get(posts_url).json().get('data', [])

candidates = []
now = datetime.datetime.now(datetime.timezone.utc)

for post in posts:
    created = parser.parse(post['created_time'])
    age_days = (now - created).days
    likes = post.get('likes', {}).get('summary', {}).get('total_count', 0)
    comments = post.get('comments', {}).get('summary', {}).get('total_count', 0)
    msg = post.get('message', '')
    
    # Is it old, unloved, and about your music?
    if age_days >= min_age_days and likes <= min_likes and 'jhammerz.github.io' in msg:
        candidates.append({
            'id': post['id'],
            'age_days': age_days,
            'likes': likes,
            'comments': comments,
            'message': msg[:100],
            'created': created.strftime('%Y-%m-%d')
        })

# Pick the worst performers first - they need love most
candidates.sort(key=lambda x: (x['likes'], x['age_days']))
to_resurrect = candidates[:max_resurrect_per_run]

log = [f"# RESURRECTION_LOG\n> Ran {now.strftime('%Y-%m-%d %H:%M')} UTC\n"]

resurrection_messages = [
    "Anniversary bump: This dropped {age} days ago. Still hits.",
    "{age} days later and this one still rips. Real drums, real humans.",
    "From the vault: {date}. {likes} likes then, let’s see about now.",
    "Throwback: {age} days ago. Who was there when this dropped?",
    "Deep cut resurrection. This one got buried. Deserved better."
]

for post in to_resurrect:
    pid = post['id']
    
    # 1. Check/fix link first
    # Extract first jhammerz link
    url = None
    for word in post['message'].split():
        if 'jhammerz.github.io' in word:
            url = word.strip('()[]')
            break
    
    if url:
        try:
            r = requests.head(url, timeout=5)
            if r.status_code >= 400:
                # Link dead - try to fix to /archive/
                fixed_url = url.replace('/tracks/', '/archive/')
                new_msg = post['message'].replace(url, fixed_url)
                requests.post(f"{GRAPH}/{pid}", data={
                    "message": new_msg,
                    "access_token": TOKEN
                })
                log.append(f"🔧 Fixed dead link on {post['created']}: {pid}")
        except: pass
    
    # 2. Post resurrection comment
    template = random.choice(resurrection_messages)
    comment = template.format(
        age=post['age_days'],
        date=post['created'],
        likes=post['likes']
    )
    
    comment_url = f"{GRAPH}/{pid}/comments"
    cr = requests.post(comment_url, data={
        "message": comment,
        "access_token": TOKEN
    })
    
    if cr.status_code == 200:
        log.append(f"⚡ Resurrected: {post['created']} | {post['likes']} likes | {post['age_days']} days old")
        log.append(f"   └─ https://facebook.com/{pid}")
    else:
        log.append(f"❌ Failed to resurrect {pid}: {cr.text}")
    
    # Respect FB - sleep between resurrections
    import time
    time.sleep(30)

if not to_resurrect:
    log.append("**No dead posts found. Your catalog is already immortal.**")

Path('RESURRECTION_LOG.md').write_text("\n".join(log))
print(f"Meadow: Resurrection complete. {len(to_resurrect)} posts touched.")
