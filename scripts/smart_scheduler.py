import os, yaml, requests, time, frontmatter
from pathlib import Path

TOKEN = os.environ.get('FB_PAGE_TOKEN')
GRAPH = "https://graph.facebook.com/v19.0"

# Load configs
meadow = frontmatter.load('MEADOW.md')
groups_data = yaml.safe_load(Path('groups.yml').read_text())

# Get track info
title = os.environ.get('TRACK_TITLE') or "New JhammerZ Track"
link = os.environ.get('TRACK_LINK') or "https://jhammerz.github.io"

# Meadow overrides
sleep_time = meadow.get('throttles', {}).get('group_post_spacing_seconds', 180)
max_posts = meadow.get('throttles', {}).get('max_groups_per_run', 50)

posted = 0
log = []

for group in groups_data['groups']:
    if not group.get('active', True): continue
    if posted >= max_posts: break
    
    gid = group['id']
    template = group['post_template']
    msg = template.replace('{title}', title).replace('{link}', link)
    
    # Ban_links handling: post text only, link in comment later
    if group.get('ban_links'):
        msg = msg.replace(link, '').strip()
    
    # Post to group
    url = f"{GRAPH}/{gid}/feed"
    r = requests.post(url, data={"message": msg, "access_token": TOKEN})
    
    if r.status_code == 200:
        post_id = r.json()['id']
        log.append(f"✅ {group['name']}: {post_id}")
        
        # If ban_links, drop link as comment after delay
        if group.get('ban_links') and group.get('comment_after_min'):
            time.sleep(group['comment_after_min'] * 60)
            comment_url = f"{GRAPH}/{post_id}/comments"
            requests.post(comment_url, data={"message": f"Link: {link}", "access_token": TOKEN})
            log.append(f"   └─ Link dropped as comment")
    else:
        log.append(f"❌ {group['name']}: {r.text}")
    
    posted += 1
    time.sleep(sleep_time) # Respect Meadow throttle

# Write run log
Path('POST_LOG.md').write_text("# Last Scheduler Run\n\n" + "\n".join(log))
print(f"Meadow: Posted to {posted} groups. Log saved.")
