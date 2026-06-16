echo "# JHAMMERZ_OS" >> README.md
git init
git add README.md
git commit -m "first commit"
git branch -M main
git remote add origin https://github.com/JHammerZ/JHAMMERZ_OS.git
git push -u origin main

## Resurrection
- dead_post_resurrection: true
- resurrection:
    min_age_hours: 24 # Any post older than 24h qualifies
    max_per_run: 8 # More aggressive since pool is bigger
    max_likes_to_resurrect: 5 # Flop = 5 likes or less
    max_comments_to_resurrect: 2 # And 2 comments or less
    cooldown_days: 7 # Don't re-bump same post for 7 days
    exclude_vip_commented: true # Skip if Tami or other VIPs already commented
