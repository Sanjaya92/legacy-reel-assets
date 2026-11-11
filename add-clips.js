#!/usr/bin/env node
/**
 * add-clips.js — add new b-roll videos to clips.json the safe way.
 *
 * HOW TO USE
 *   1. Put this file in the ROOT of your legacy-reel-assets folder
 *      (the same folder that already has clips.json and the broll/ folder).
 *   2. Drop your new video files into the  broll/  folder.
 *   3. Open a terminal in that folder and run:
 *          node add-clips.js
 *   4. For each new clip it finds, type a few mood tags when asked.
 *   5. Push the result:
 *          git add -A && git commit -m "add broll clips" && git push
 *
 * WHAT IT DOES
 *   - Finds only videos in broll/ that aren't already listed in clips.json.
 *   - Auto-detects each clip's length and orientation (needs ffmpeg; if you
 *     don't have it, it fills sensible defaults and tells you to double-check).
 *   - Adds a correct entry for each. It NEVER edits or deletes your existing
 *     clips, app recordings, logo, or notes.
 */

const fs = require('fs');
const path = require('path');
const readline = require('readline');
const { execSync } = require('child_process');

const ROOT = __dirname;
const CLIPS = path.join(ROOT, 'clips.json');
const BROLL_DIR = path.join(ROOT, 'broll');
const VIDEO_EXT = ['.mp4', '.mov', '.webm', '.m4v'];

function fail(msg) { console.error('\n✖ ' + msg + '\n'); process.exit(1); }

if (!fs.existsSync(CLIPS)) fail('clips.json not found. Put this script in the repo root (next to clips.json) and run it from there.');
if (!fs.existsSync(BROLL_DIR)) fail('broll/ folder not found. Put this script in the repo root and run it from there.');

let data;
try { data = JSON.parse(fs.readFileSync(CLIPS, 'utf8')); }
catch (e) { fail('clips.json is not valid JSON, so I won\'t touch it: ' + e.message); }
if (!Array.isArray(data.broll)) fail('clips.json has no "broll" list.');

// Is ffmpeg/ffprobe available for auto-detecting length + orientation?
let haveFfprobe = true;
try { execSync('ffprobe -version', { stdio: 'ignore' }); }
catch { haveFfprobe = false; }

// Find videos in broll/ that aren't listed yet (match by filename).
const listed = new Set(data.broll.map(c => path.basename(c.file)));
const files = fs.readdirSync(BROLL_DIR)
  .filter(f => VIDEO_EXT.includes(path.extname(f).toLowerCase()))
  .filter(f => !listed.has(f))
  .sort();

if (files.length === 0) {
  console.log('\n✓ No new videos in broll/. clips.json is already up to date.\n');
  process.exit(0);
}

console.log('\nFound ' + files.length + ' new clip(s) to add:\n' + files.map(f => '  • ' + f).join('\n'));
if (!haveFfprobe) {
  console.log('\n(ffmpeg not found, so length/orientation are guessed — you can fix them later in clips.json if needed.)');
}

function probe(fullPath) {
  if (!haveFfprobe) return { orient: 'vertical', dur: 10, guessed: true };
  try {
    const out = execSync(
      'ffprobe -v error -select_streams v:0 -show_entries stream=width,height:format=duration -of json "' + fullPath + '"',
      { encoding: 'utf8' }
    );
    const j = JSON.parse(out);
    const s = (j.streams && j.streams[0]) || {};
    const w = Number(s.width) || 0;
    const h = Number(s.height) || 0;
    const dur = Math.max(1, Math.round(Number(j.format && j.format.duration) || 10));
    const orient = h >= w ? 'vertical' : 'landscape';
    return { orient, dur, guessed: false };
  } catch {
    return { orient: 'vertical', dur: 10, guessed: true };
  }
}

const rl = readline.createInterface({ input: process.stdin, output: process.stdout });
const ask = q => new Promise(res => rl.question(q, res));

(async () => {
  for (const f of files) {
    const { orient, dur, guessed } = probe(path.join(BROLL_DIR, f));
    console.log('\n── ' + f);
    console.log('   orientation: ' + orient + (guessed ? '  (guessed)' : ''));
    console.log('   length: ' + dur + 's' + (guessed ? '  (guessed)' : ''));
    console.log('   Mood tags describe the feeling/subject so the agent can match the clip to a reel line.');
    console.log('   examples: memory, mother, father, generations, writing, reflection, warmth, care, closeness, hands, window, tea, home, kitchen');
    let moods = (await ask('   Enter moods for this clip (comma-separated): ')).trim();
    while (!moods) moods = (await ask('   Please type at least one mood: ')).trim();
    const moodArr = moods.split(',').map(m => m.trim()).filter(Boolean);
    console.log('   Now one sentence on what is actually in the clip (who, where, what happens).');
    console.log('   example: An older man sits alone by a bright window, looking out.');
    const desc = (await ask('   Describe this clip (or press Enter to skip): ')).trim();
    const entry = { file: 'broll/' + f, orient: orient, dur: dur, moods: moodArr };
    if (desc) entry.desc = desc;
    data.broll.push(entry);
    console.log('   ✓ added broll/' + f + '  [' + moodArr.join(', ') + ']');
  }
  rl.close();
  fs.writeFileSync(CLIPS, JSON.stringify(data, null, 2) + '\n');
  console.log('\n✓ Updated clips.json with ' + files.length + ' new clip(s).');
  console.log('  Next:  git add -A && git commit -m "add broll clips" && git push\n');
})();
