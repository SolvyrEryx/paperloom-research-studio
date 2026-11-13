"""Portable PowerPoint and Markdown exports."""
from __future__ import annotations

from io import BytesIO

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.util import Inches, Pt

from studio.agents import Deck


def export_deck(deck: Deck, paper_name: str, preview: bool = False) -> bytes:
    prs = Presentation()
    prs.slide_width, prs.slide_height = Inches(13.333), Inches(7.5)
    prs.core_properties.title = deck.title
    prs.core_properties.author = "Rahul J"
    prs.core_properties.subject = "Research Studio · Paper-to-Presentation"
    ink, muted, accent = RGBColor(48, 45, 41), RGBColor(109, 103, 95), RGBColor(183, 100, 72)

    def text(slide, x, y, w, h, content, size, color, font="Aptos", bold=False):
        frame = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h)).text_frame
        frame.word_wrap = True
        for i, line in enumerate(content.split("\n")):
            p = frame.paragraphs[0] if i == 0 else frame.add_paragraph()
            p.text, p.font.size, p.font.name = line, Pt(size), font
            p.font.color.rgb, p.font.bold = color, bold
        return frame

    for i, item in enumerate(deck.slides):
        slide = prs.slides.add_slide(prs.slide_layouts[6])
        slide.background.fill.solid()
        slide.background.fill.fore_color.rgb = RGBColor(248, 246, 241)
        text(slide, .65, .4, 12, .4, "RAHUL J  /  RESEARCH STUDIO", 11, accent, bold=True)
        text(slide, .65, 1.1, 11.8, 1.1, item.title[:90], 32, ink, "Georgia")
        bullets = [b[:240] for b in item.bullets[:5]]
        text(slide, .85, 2.55, 11.4, 3.7, "\n\n".join("• " + b for b in bullets), 19, ink)
        pages = ", ".join(str(p) for p in item.pages) or "Overview"
        footer = f"{paper_name[:70]}  ·  Pages: {pages}"
        if preview:
            footer += "  ·  EXTRACTIVE PREVIEW"
        text(slide, .65, 6.85, 11.5, .35, footer, 10, muted)
        text(slide, 12, 6.85, .6, .35, f"{i + 1:02}", 10, accent)
        slide.notes_slide.notes_text_frame.text = item.notes + "\nSupporting pages: " + pages
    buffer = BytesIO()
    prs.save(buffer)
    return buffer.getvalue()


def session_report(paper, messages: list, viva: list, trace: list, preview: bool) -> str:
    lines = ["# Rahul J · Research Studio", "", "## Session report", "",
             f"Paper: {paper.name if paper else 'None'}",
             f"Current response mode: {'Offline preview — no live LLM evaluation' if preview else 'Live AI (individual outputs are labelled below)'}",
             f"Extractable pages: {len(paper.pages) if paper else 0}",
             f"Indexed passages: {len(paper.chunks) if paper else 0}",
             f"Conversation turns: {len([m for m in messages if m['role'] == 'user'])}",
             f"Viva answers submitted: {len(viva)}", "", "## Research conversation", ""]
    for message in messages:
        lines.extend([f"### {message['role'].title()}", message["content"], ""])
        result = message.get("result")
        if result:
            lines.extend([f"Output mode: {'Offline preview' if result.preview else 'Live AI'}", ""])
    lines.extend(["## Viva practice", ""])
    for item in viva:
        lines.extend([f"### Question\n{item['question']}", f"Answer: {item['answer']}", item["feedback"], ""])
        lines.append(f"Feedback mode: {'Offline preview' if item.get('preview') else 'Live AI'}")
        if item.get("scores"):
            lines.append("Advisory model scores (0–5): " + str(item["scores"]))
    lines.extend(["## Last workflow trace", *[f"- {t}" for t in trace], "",
                  "Model scores are advisory judgments, not measured ability. Verify generated claims against the original paper."])
    return "\n".join(lines)
