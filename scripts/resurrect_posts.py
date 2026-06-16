import os, requests, datetime, frontmatter, random, json
from dateutil import parser
from pathlib import Path

TOKEN = os.environ['FB_PAGE_TOKEN']
PAGE_ID = os.environ['FB_PAGE_ID']
GRAPH = "https://graph.facebook.com/v19.0"

meadow = frontmatter.load('MEADOW.md')
res = meadow.get('resurrection', {})

min_age_hours = res.get('min_age_hours', 24)
max_resurrect = res.get('max_per_run', 8)
max_likes = res.get('max_likes_to_resurrect', 5)
max_comments = res.get('max_comments_to_resurrect', 2)
cooldown_days = res.get('cooldown_days', 7)
exclude_vip = res.get('exclude_vip_commented', True)

# Load fans.json to check for VIP comments
fans = {}
if Path('fans.json').exists():
    fans = json.loads(Path('fans.json').read_text())
vip_ids = [uid for uid, data in fans.items() if data.get('comments', 0) >= 5]

# Load cooldown cache
cooldown_file = Path('.resurrection_cooldown.json')
cooldown = json.loads(cooldown_file.read_text()) if cooldown_file.exists() else {}

now = datetime.datetime.now(datetime.timezone.utc)
since = (now - datetime.timedelta(days=90)).strftime('%Y-%m-%d')

posts_url = f"{GRAPH}/{PAGE_ID}/posts?fields=id,message,created_time,likes.summary(true),comments.summary(true),comments{{from}}&since={since}&limit=100&access_token={TOKEN}"
posts = requests.get(posts_url).json().get('data', [])

candidates = []
for post in posts:
    pid = post['id']
    created = parser.parse(post['created_time'])
    age_hours = (now - created).total_seconds() / 3600

    if age_hours < min_age_hours: continue

    if pid in cooldown:
        last_bump = parser.parse(cooldown[pid])
        if (now - last_bump).days < cooldown_days: continue

    likes = post.get('likes', {}).get('summary', {}).get('total_count', 0)
    comments = post.get('comments', {}).get('summary', {}).get('total_count', 0)
    msg = post.get('message', '')

    if likes > max_likes or comments > max_comments: continue
    if 'jhammerz.github.io' not in msg: continue

    if exclude_vip and post.get('comments', {}).get('data'):
        commenter_ids = [c['from']['id'] for c in post['comments']['data']]
        if any(uid in vip_ids for uid in commenter_ids): continue

    candidates.append({
        'id': pid,
        'age_hours': int(age_hours),
        'age_days': int(age_hours / 24),
        'likes': likes,
        'comments': comments,
        'created': created.strftime('%Y-%m-%d')
    })

candidates.sort(key=lambda x: (-x['age_days'], x['likes'], x['comments']))
to_resurrect = candidates[:max_resurrect]

log = [f"# RESURRECTION_LOG\n> 24h+ Flop Run: {now.strftime('%Y-%m-%d %H:%M')} UTC\n"]
log.append(f"**Scanning for any post {min_age_hours}h+ old with ≤{max_likes}L ≤{max_comments}C**\n")

res_messages = [
    "Buried treasure: {age_days} days old, {likes} likes. Deserved better. Bump.",
    "From the vault: {created}. Still hits. Algo just missed it.",
    "Deep cut resurrection. {age_days}d old, {likes} likes. Real drums don’t age.",
    "Second chance: This dropped {age_days} days ago. You weren’t ready then.",
    "Archive dive: {created}. {likes}L {comments}C. Let’s fix that.",
    "If the algo slept on this {age_days}d ago, wake it up now.",
    "Old heads know. New heads learn today. {age_days} days in the crypt."
]

for post in to_resurrect:
    pid = post['id']

    msg = random.choice(res_messages).format(
        age_days=post['age_days'],
        created=post['created'],
        likes=post['likes'],
        comments=post['comments']
    )

    cr = requests.post(f"{GRAPH}/{pid}/comments", data={
        "message": msg,
        "access_token": TOKEN
    })

    if cr.status_code == 200:
        log.append(f"⚡ Resurrected: {post['created']} | {post['age_days']}d old | {post['likes']}L {post['comments']}C")
        log.append(f" └─ https://facebook.com/{pid}")
        cooldown[pid] = now.isoformat()
    else:
        log.append(f"❌ Failed {pid}: {cr.text}")

    import time
    time.sleep(90)

cooldown_file.write_text(json.dumps(cooldown))
Path('RESURRECTION_LOG.md').write_text("\n".join(log))
print(f"Meadow: Resurrected {len(to_resurrect)} flops older than 24h.")
