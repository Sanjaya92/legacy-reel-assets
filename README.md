# Legacy — Reel Assets

Asset library for the Legacy marketing reel agent. **Do not put product code here.**

- `broll/` — license-clear stock clips (Pexels/Pixabay/etc.), named by mood.
- `app/` — screen recordings of the Legacy app (unique, renewable — re-record as the app evolves).
- `logo/` — brand marks.
- `clips.json` — catalog + mood tags the `footage-assembler` skill uses to match footage to each reel's beats.
- `used.json` — rotation log (the agent updates this so clips don't repeat too often).

## Topping up b-roll
The agent flags, in each content pack, which moods it's short on. When that happens, download a few license-clear vertical-or-landscape clips (no text/watermark) from pexels.com/videos or mixkit.co, drop them in `broll/`, add an entry to `clips.json`, and push. 10 minutes, roughly monthly.
