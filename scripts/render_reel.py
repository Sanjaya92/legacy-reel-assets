#!/usr/bin/env python3
"""
Legacy reel render engine.  Turns a reel SPEC (JSON) + the asset repo into a
1080x1920 silent .mp4 in Legacy's brand (parchment / clay / Fraunces).

Usage:
  python3 scripts/render_reel.py --spec spec.json --root . --out reel.mp4 [--work /tmp/reelwork]

SPEC shape:
{
 "scenes": [
   {"type":"hook","broll":"broll/window-reflection.mp4",
     "lines":[{"t":"You'll keep her photos."},{"t":"The stories are harder to hold.","em":true}],
     "cue":"Keep watching →","dur":3.6},
   {"type":"broll","broll":"broll/hands-photo.mp4",
     "lines":[{"t":"A photo shows the moment — not the story behind it."}],"dur":3.4},
   {"type":"app","clip":"app/app-typing.mov",
     "cap":[{"t":"Legacy asks "},{"t":"one gentle question","em":true},{"t":" at a time."}],"dur":4.4},
   {"type":"memoir","who":"Mom","q":"What did your mother's house smell like?",
     "a":"Cardamom and wood smoke...","dur":4.8},
   {"type":"closer","broll":"broll/writing.mp4",
     "lines":[{"t":"Start while she can "},{"t":"still tell it.","em":true,"inline":true}],"dur":3.4},
   {"type":"end","dur":3.8}
 ]
}
Honest copy rule: Legacy keeps stories as TEXT in the parent's own words.
Never claim it records/keeps/plays back their voice or audio.
"""
import os, sys, json, glob, argparse, subprocess

INK="#2A2520"; ACC="#A85530"; BG="#F1E7D2"; MUT="#6E6354"; DARK="#17120E"; GOLD="#C6A15B"; CREAM="#F3E9D5"

def ensure_fonts(work):
    cand=glob.glob(os.path.join(work,"node_modules/@fontsource/fraunces/files"))
    if not cand:
        subprocess.run(["npm","init","-y"],cwd=work,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        subprocess.run(["npm","install","@fontsource/fraunces"],cwd=work,check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        cand=glob.glob(os.path.join(work,"node_modules/@fontsource/fraunces/files"))
    f=cand[0]
    return ("file://"+os.path.join(f,"fraunces-latin-400-normal.woff2"),
            "file://"+os.path.join(f,"fraunces-latin-400-italic.woff2"),
            "file://"+os.path.join(f,"fraunces-latin-500-normal.woff2"))

def css(fr,fi,fm):
    return f"""@font-face{{font-family:'Fr';src:url('{fr}') format('woff2');font-weight:400;font-style:normal}}
@font-face{{font-family:'Fr';src:url('{fi}') format('woff2');font-weight:400;font-style:italic}}
@font-face{{font-family:'Fr';src:url('{fm}') format('woff2');font-weight:500;font-style:normal}}
*{{margin:0;box-sizing:border-box;font-family:'Fr',serif}}html,body{{width:1080px;height:1920px}}"""

def lines_html(lines, inline_em=True):
    out=[]
    for ln in lines:
        t=ln["t"]
        if ln.get("em"):
            t=f"<span class=em>{t}</span>"
        out.append(t)
    sep="" if (lines and lines[0].get("inline")) else "<br>"
    return sep.join(out)

def overlay_html(C, lines, cue=None):
    cueh=f'<div class=cue>{cue}</div>' if cue else ''
    return f"""<!doctype html><html><head><meta charset=utf-8><style>{C}
body{{background:transparent}}
.scrim{{position:absolute;inset:0;background:linear-gradient(to bottom,rgba(10,8,6,0) 38%,rgba(10,8,6,.55) 72%,rgba(10,8,6,.80) 100%)}}
.wm{{position:absolute;top:120px;left:0;right:0;text-align:center;color:#F6EEDD;font-size:40px;font-style:italic;font-weight:500;text-shadow:0 2px 14px rgba(0,0,0,.5)}}
.wm i{{display:inline-block;width:10px;height:10px;border-radius:50%;background:{ACC};margin-left:12px}}
.tx{{position:absolute;left:90px;right:90px;top:58%;text-align:center;color:#FCF7EC;font-size:72px;line-height:1.22;text-shadow:0 3px 22px rgba(0,0,0,.6)}}
.tx .em{{font-style:italic;color:#F2C9A6}}
.cue{{position:absolute;bottom:150px;left:0;right:0;text-align:center;color:#EcE0C8;font-size:30px;letter-spacing:3px;text-transform:uppercase;text-shadow:0 2px 12px rgba(0,0,0,.6)}}
</style></head><body><div class=scrim></div><div class=wm>Legacy<i></i></div>
<div class=tx>{lines_html(lines)}</div>{cueh}</body></html>"""

def appcap_html(C, cap):
    return f"""<!doctype html><html><head><meta charset=utf-8><style>{C}
body{{background:transparent}}
.wm{{position:absolute;top:150px;left:0;right:0;text-align:center;color:{INK};font-size:40px;font-style:italic;font-weight:500}}
.wm i{{display:inline-block;width:10px;height:10px;border-radius:50%;background:{ACC};margin-left:12px}}
.cap{{position:absolute;bottom:200px;left:90px;right:90px;text-align:center;color:{INK};font-size:52px;line-height:1.3}}
.cap .em{{font-style:italic;color:{ACC}}}
</style></head><body><div class=wm>Legacy<i></i></div><div class=cap>{lines_html(cap)}</div></body></html>"""

def memoir_html(C, who, q, a):
    return f"""<!doctype html><html><head><meta charset=utf-8><style>{C}
body{{background:{BG}}}
.wm{{position:absolute;top:140px;left:0;right:0;text-align:center;font-size:38px;font-style:italic;font-weight:500;color:{INK}}}
.wm i{{display:inline-block;width:10px;height:10px;border-radius:50%;background:{ACC};margin-left:12px}}
.stage{{width:1080px;height:1920px;display:flex;align-items:center;justify-content:center;padding:90px}}
.card{{width:100%;background:#FFFDF8;border:1px solid #EFE4CE;border-radius:34px;padding:66px 58px;box-shadow:0 30px 80px rgba(90,60,30,.12)}}
.cap{{font-size:28px;letter-spacing:3px;text-transform:uppercase;color:{ACC};margin-bottom:26px}}
.q{{font-size:50px;line-height:1.3;color:{INK};font-weight:500}}
.dv{{height:1px;background:#EFE4CE;margin:38px 0}}
.a{{font-size:42px;line-height:1.52;color:#4A4136;font-style:italic}}
.badge{{margin-top:38px;font-size:26px;letter-spacing:2px;text-transform:uppercase;color:#6E8B5E}}
</style></head><body><div class=wm>Legacy<i></i></div><div class=stage><div class=card>
<div class=cap>A question for {who}</div><div class=q>{q}</div><div class=dv></div>
<div class=a>&ldquo;{a}&rdquo;</div><div class=badge>&#10003;&nbsp; Saved to memoir</div></div></div></body></html>"""

def end_html(C):
    return f"""<!doctype html><html><head><meta charset=utf-8><style>{C}
body{{background:{DARK}}}
.s{{width:1080px;height:1920px;display:flex;flex-direction:column;align-items:center;justify-content:center;color:{CREAM};padding:90px}}
.ring{{width:220px;height:220px;border-radius:50%;border:2px solid {GOLD};display:flex;align-items:center;justify-content:center;margin-bottom:46px}}
.ring span{{font-size:86px;letter-spacing:4px;color:{GOLD}}}
.brand{{font-size:62px}}.tag{{margin-top:22px;font-size:27px;letter-spacing:4px;text-transform:uppercase;color:{GOLD};text-align:center}}
.er{{width:120px;height:1px;background:rgba(198,161,91,.5);margin:40px 0}}.url{{font-size:30px;letter-spacing:1px;color:{GOLD}}}
.btn{{margin-top:44px;background:{GOLD};color:#241a0e;font-size:36px;padding:26px 54px;border-radius:999px}}
</style></head><body><div class=s><div class=ring><span>LM</span></div>
<div class=brand>Legacy Memoir</div><div class=tag>Family stories, preserved forever</div>
<div class=er></div><div class=url>legacy-memoir.com</div><div class=btn>Start for free &rarr;</div></div></body></html>"""

def render_pngs(C, scenes, work):
    from playwright.sync_api import sync_playwright
    jobs=[]  # (name, html, transparent)
    for i,s in enumerate(scenes):
        t=s["type"]
        if t in ("hook","broll","closer"):
            jobs.append((f"ov_{i}.png", overlay_html(C, s["lines"], s.get("cue")), True))
        elif t=="app":
            jobs.append((f"ov_{i}.png", appcap_html(C, s["cap"]), True))
        elif t=="memoir":
            jobs.append((f"ov_{i}.png", memoir_html(C, s.get("who","Dad"), s["q"], s["a"]), False))
        elif t=="end":
            jobs.append((f"ov_{i}.png", end_html(C), False))
    with sync_playwright() as p:
        b=p.chromium.launch()
        for name,html,transp in jobs:
            ctx=b.new_context(viewport={"width":1080,"height":1920},device_scale_factor=(1 if transp else 2))
            pg=ctx.new_page(); pg.set_content(html,wait_until="load"); pg.evaluate("document.fonts.ready"); pg.wait_for_timeout(300)
            pg.screenshot(path=os.path.join(work,name), omit_background=transp); ctx.close()
        b.close()

def ff(args):
    subprocess.run(["ffmpeg","-y",*args],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)

def broll_scene(clip, png, dur, out):
    vf=(f"[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,trim=duration={dur},setpts=PTS-STARTPTS,fps=25[v];"
        f"[v][1:v]overlay=0:0:format=auto,format=yuv420p[o]")
    ff(["-i",clip,"-i",png,"-filter_complex",vf,"-map","[o]","-t",str(dur),"-c:v","libx264","-preset","medium","-crf","20","-an",out])

def still_scene(png, dur, out, zin=True):
    z="min(zoom+0.0006,1.06)" if zin else "if(lte(zoom,1.0),1.06,max(1.001,zoom-0.0006))"
    vf=(f"scale=2160:3840,zoompan=z='{z}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={int(dur*25)+4}:s=1080x1920:fps=25,"
        f"trim=duration={dur},format=yuv420p")
    ff(["-loop","1","-i",png,"-t",str(dur),"-r","25","-vf",vf,"-c:v","libx264","-preset","medium","-crf","20","-an",out])

def app_scene(clip, png, dur, out):
    j=subprocess.run(["ffprobe","-v","error","-select_streams","v:0","-show_entries","stream=width,height","-of","json",clip],capture_output=True,text=True).stdout
    st=json.loads(j)["streams"][0]; w,h=st["width"],st["height"]
    tw=860; th=int(tw*h/w)
    if th>1480: th=1480; tw=int(th*w/h)
    x=(1080-tw)//2; y=(1920-th)//2+40
    vf=(f"color=c=0x{BG[1:]}:s=1080x1920:r=25:d={dur}[bg];"
        f"[0:v]scale={tw}:{th},setsar=1,trim=duration={dur},setpts=PTS-STARTPTS[app];"
        f"[bg][app]overlay={x}:{y}[b1];[b1][1:v]overlay=0:0:format=auto,format=yuv420p[o]")
    ff(["-i",clip,"-i",png,"-filter_complex",vf,"-map","[o]","-t",str(dur),"-c:v","libx264","-preset","medium","-crf","20","-an",out])

def xfade(scenes_mp4, out):
    c=0.5; inp=[]
    for s,_ in scenes_mp4: inp+=["-i",s]
    fc=[]; prev="[0:v]"; acc=scenes_mp4[0][1]
    for i in range(1,len(scenes_mp4)):
        lab=f"[x{i}]"; fc.append(f"{prev}[{i}:v]xfade=transition=fade:duration={c}:offset={acc-c:.2f}{lab}"); prev=lab; acc+=scenes_mp4[i][1]-c
    ff([*inp,"-filter_complex",";".join(fc),"-map",prev,"-r","25","-c:v","libx264","-preset","medium","-crf","20","-pix_fmt","yuv420p",out])

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--spec",required=True); ap.add_argument("--root",default=".")
    ap.add_argument("--out",required=True); ap.add_argument("--work",default=None)
    a=ap.parse_args()
    root=os.path.abspath(a.root)
    work=a.work or os.path.join(root,"_work"); os.makedirs(work,exist_ok=True)
    spec=json.load(open(a.spec)); scenes=spec["scenes"]
    C=css(*ensure_fonts(work))
    render_pngs(C, scenes, work)
    built=[]
    for i,s in enumerate(scenes):
        t=s["type"]; dur=float(s.get("dur",3.6)); png=os.path.join(work,f"ov_{i}.png"); mp4=os.path.join(work,f"sc_{i}.mp4")
        if t in ("hook","broll","closer"):
            broll_scene(os.path.join(root,s["broll"]), png, dur, mp4)
        elif t=="app":
            app_scene(os.path.join(root,s["clip"]), png, dur, mp4)
        elif t in ("memoir","end"):
            still_scene(png, dur, mp4, zin=(t=="memoir"))
        built.append((mp4,dur))
    xfade(built, os.path.abspath(a.out))
    print("OK", a.out)

if __name__=="__main__":
    main()
