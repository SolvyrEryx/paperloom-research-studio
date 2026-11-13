"""Render original Paperloom diagrams, not mock screenshots or benchmark evidence.

Optional maintainer dependency: Pillow. Outputs are committed; app users do not need it separately.
"""
from pathlib import Path
import math
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "assets"
OUT.mkdir(parents=True, exist_ok=True)
PAPER, INK, MUTED, ACCENT, LINE = "#f8f6f1", "#302d29", "#80766a", "#b76448", "#dfd7cb"


def font(size, serif=False, italic=False):
    windows = Path("C:/Windows/Fonts")
    paths = ([windows / ("georgiai.ttf" if italic else "georgia.ttf"), Path("/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf")]
             if serif else [windows / "segoeui.ttf", Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf")])
    for path in paths:
        if path.exists():
            return ImageFont.truetype(str(path), size)
    return ImageFont.load_default(size=size)


def spark(d, cx, cy, radius, fill=ACCENT, width=3):
    for i in range(8):
        angle = i * math.pi / 4
        d.line((cx+math.cos(angle)*radius*.3, cy+math.sin(angle)*radius*.3,
                cx+math.cos(angle)*radius, cy+math.sin(angle)*radius), fill=fill, width=width)


def hero():
    im = Image.new("RGB", (1600, 650), PAPER)
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((1, 1, 1598, 648), radius=28, outline=LINE, width=2)
    d.text((85, 57), "PAPERLOOM  /  BY RAHUL J", font=font(17), fill=ACCENT)
    d.text((80, 134), "A clearer", font=font(92, True), fill=INK)
    d.text((80, 239), "point of view.", font=font(92, True, True), fill=INK)
    d.text((85, 389), "Understand the paper. Shape the story. Own the viva.", font=font(24), fill=MUTED)
    d.line((85, 474, 720, 474), fill=LINE, width=2)
    d.text((85, 504), "PAGE-CITED RESEARCH  /  REAL SLIDE EXPORT  /  VIVA PRACTICE", font=font(14), fill=MUTED)
    # Original editorial illustration: paper → evidence cards → a presentation.
    d.ellipse((868, 74, 1492, 589), fill="#f0eae0")
    d.rounded_rectangle((1018, 86, 1320, 440), radius=12, fill="#d9cdbd")
    d.rounded_rectangle((996, 70, 1298, 424), radius=12, fill="#fffdf8", outline=LINE, width=2)
    d.text((1023, 99), "THE RESEARCH PAPER", font=font(13), fill=ACCENT)
    d.text((1023, 141), "From questions", font=font(27, True), fill=INK)
    d.text((1023, 178), "to understanding.", font=font(27, True), fill=INK)
    for y, length in [(242,217),(263,196),(284,225),(305,155),(351,207),(372,185)]:
        d.rounded_rectangle((1023,y,1023+length,y+5),radius=2,fill=LINE)
    d.rounded_rectangle((925, 343, 1157, 456), radius=10, fill="#302d29")
    d.text((947, 364), "EVIDENCE, NOT GUESSWORK", font=font(11), fill="#d4b299")
    d.text((947, 396), "[p. 2]  [p. 3]", font=font(25, True), fill="#fffaf0")
    d.rounded_rectangle((1190, 441, 1460, 584), radius=12, fill="#fffdf8", outline=LINE, width=2)
    d.text((1210, 459), "YOUR NEXT PRESENTATION", font=font(11), fill=ACCENT)
    for i, h in enumerate([22, 35, 52, 68]):
        d.rounded_rectangle((1212+i*37, 561-h, 1233+i*37, 561), radius=3, fill=["#d4b299","#c88c6e","#b76448","#855643"][i])
    spark(d, 1425, 220, 41, width=3)
    d.text((919, 610), "AN ORIGINAL WORKFLOW ILLUSTRATION", font=font(10), fill=MUTED)
    im.save(OUT / "paperloom-cover.png", optimize=True)


def workflow():
    width, height = 1400, 420
    stages = [("01", "Read", "Bring a research paper.", "Local PDF extraction"),
              ("02", "Ground", "Keep the evidence close.", "Page-aware retrieval"),
              ("03", "Present", "Give the ideas a shape.", "PowerPoint + notes"),
              ("04", "Defend", "Practise the next question.", "Viva + feedback")]
    frames = []
    for n in range(64):
        im=Image.new("RGB",(width,height),PAPER)
        d=ImageDraw.Draw(im)
        d.text((42,25),"FROM A DENSE PDF TO A CLEAR POINT OF VIEW",font=font(15),fill=INK)
        d.text((42,383),"PAPERLOOM  /  WORKFLOW ILLUSTRATION — NOT A LIVE RECORDING",font=font(11),fill=MUTED)
        phase=n/64*4
        active=int(phase)%4
        for i,(number,title,subtitle,detail) in enumerate(stages):
            x=42+i*337
            d.rounded_rectangle((x,90,x+301,339),radius=15,fill="#fffdf8" if i!=active else "#f1e6d9",outline=ACCENT if i==active else LINE,width=2)
            d.text((x+25,110),number,font=font(14),fill=ACCENT)
            if i==0:
                d.rectangle((x+26,155,x+63,203),outline=ACCENT,width=2)
                for yy in [168,178,188]: d.line((x+34,yy,x+54,yy),fill=ACCENT,width=2)
            elif i==1:
                for dx,dy in [(0,14),(34,0),(67,14)]:
                    d.ellipse((x+26+dx,160+dy,x+38+dx,172+dy),fill=ACCENT)
                d.line((x+32,180,x+66,166,x+99,180),fill=ACCENT,width=2)
            elif i==2:
                d.rounded_rectangle((x+26,158,x+92,201),radius=4,outline=ACCENT,width=2)
                d.line((x+39,174,x+78,174),fill=ACCENT,width=2)
                d.line((x+39,184,x+67,184),fill=ACCENT,width=2)
            else: spark(d,x+53,181,27,width=2)
            d.text((x+24,220),title,font=font(34,True),fill=INK)
            d.text((x+25,275),subtitle,font=font(16),fill=MUTED)
            d.text((x+25,306),detail,font=font(12),fill=ACCENT)
            if i<3:
                y=212; start=x+306; end=x+332
                d.line((start,y,end,y),fill=LINE,width=2)
                if active==i:
                    progress=(phase-i)
                    px=start+(end-start)*progress
                    d.ellipse((px-4,y-4,px+4,y+4),fill=ACCENT)
        d.line((42,365,1355,365),fill=LINE,width=2)
        d.line((42,365,42+1313*n/63,365),fill=ACCENT,width=3)
        frames.append(im.quantize(colors=96,method=Image.Quantize.MEDIANCUT))
    frames[0].save(OUT/"paperloom-workflow.gif",save_all=True,append_images=frames[1:],duration=85,loop=0,optimize=True,disposal=2)
    frames[0].convert("RGB").save(OUT/"paperloom-workflow-static.png",optimize=True)


if __name__ == "__main__":
    hero()
    workflow()
    print("Rendered Paperloom cover, animated workflow and static alternative.")
