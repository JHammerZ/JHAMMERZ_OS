echo "# JHAMMERZ_OS" >> README.md
git init
git add README.md
git commit -m "first commit"
git branch -M main
git remote add origin https://github.com/JHammerZ/JHAMMERZ_OS.git
git push -u origin main

max_likes_to_resurrect: 3 # Only bump if <3 likes = stricter
max_per_run: 2 # Only 2 bumps/day = safer
min_age_days: 2 # Wait 48h instead of 24h = less desperate
