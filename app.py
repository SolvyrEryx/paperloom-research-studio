"""Paperloom by Rahul J — run with: python -m streamlit run app.py"""
from __future__ import annotations

import hashlib
import html
import os
from pathlib import Path

import streamlit as st

from studio.agents import run_task
from studio.documents import index_paper, sample_pdf
from studio.exports import export_deck, session_report

ROOT = Path(__file__).resolve().parent
st.set_page_config(page_title="Paperloom · Rahul J", page_icon="✳", layout="wide")
st.markdown(f"<style>{(ROOT / 'ui' / 'studio.css').read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)

DEFAULTS = {"paper": None, "messages": [], "viva": [], "question": "", "deck_result": None,
            "latest_result": None, "trace": [], "upload_digest": "", "upload_version": 0}
for name, default in DEFAULTS.items():
    if name not in st.session_state:
        st.session_state[name] = default


def reset_outputs():
    for name in ("messages", "viva", "trace"):
        st.session_state[name] = []
    for name in ("deck_result", "latest_result"):
        st.session_state[name] = None
    st.session_state.question = ""
    # Reset paper-specific widget values too; a prior viva answer must not leak to a new paper.
    st.session_state.pop("viva_answer", None)


def load_paper(data: bytes, name: str, mode: str):
    try:
        with st.spinner("Reading pages and building your local index…"):
            fresh = index_paper(data, name, mode)
        old = st.session_state.paper
        if old is not None:
            old.close()
        st.session_state.paper = fresh
        reset_outputs()
        st.toast("Your paper is ready.", icon=":material/check_circle:")
        return True
    except Exception as exc:
        if isinstance(exc, ValueError):
            st.error(str(exc))
        else:
            st.error("Couldn't build the local index. If the MiniLM download is unavailable, choose Offline lexical in Settings and retry.")
        return False


with st.sidebar:
    st.markdown('<div class="brand"><span class="brand-mark">✳</span><div><strong>Paperloom</strong><small>BY RAHUL J</small></div></div>', unsafe_allow_html=True)
    st.markdown('<div class="nav-label">YOUR WORKSPACE</div>', unsafe_allow_html=True)
    view = st.radio("Workspace navigation", ["Workspace", "Slides", "Viva practice", "Session report"],
                    label_visibility="collapsed", key="navigation")
    st.markdown('<div class="sidebar-rule"></div>', unsafe_allow_html=True)
    paper = st.session_state.paper
    if paper:
        st.caption("CURRENT PAPER")
        st.markdown(f"**{paper.name}**")
        st.caption(f"{len(paper.pages)} text pages · {len(paper.chunks)} passages")
        st.caption("Local semantic search" if paper.embedding_mode == "semantic" else "Offline lexical search")
        if st.button("Close paper", use_container_width=True):
            paper.close()
            st.session_state.paper = None
            st.session_state.upload_digest = ""
            st.session_state.upload_version += 1
            reset_outputs()
            st.rerun()
    else:
        st.markdown('<div class="sidebar-note">A quiet space for<br>your next big idea.</div>', unsafe_allow_html=True)
    with st.expander("Settings", expanded=False):
        api_key = st.text_input("Groq API key", type="password", help="Kept in this browser session. Never written to a project file.", key="api_key")
        has_key = bool(api_key or os.getenv("GROQ_API_KEY"))
        mode = st.selectbox("Response mode", ["Offline preview", "Live AI"], key="response_mode")
        model_name = st.text_input("Groq model", value=os.getenv("GROQ_MODEL", "openai/gpt-oss-20b"))
        embedding_choice = st.selectbox("Index for the next paper", ["Local semantic · MiniLM", "Offline lexical · no download"],
                                        help="MiniLM downloads a free local model once. Lexical mode matches words, not meaning.")
        st.caption("No paid fallback. Live AI requires your Groq key and available quota.")
    preview = mode == "Offline preview"
    embedding_mode = "offline" if embedding_choice.startswith("Offline") else "semantic"
    st.markdown('<div class="sidebar-footer"><span class="avatar">RJ</span><div>Rahul J<small>Personal research workspace</small></div></div>', unsafe_allow_html=True)

paper = st.session_state.paper


def execute(question: str, hint: str = "", slide_count: int = 6):
    if not preview and not has_key:
        st.warning("Add your Groq API key in Settings to use Live AI. Offline preview is available without one.")
        return None
    try:
        with st.status("Finding evidence and preparing your response…", expanded=False) as status:
            result = run_task(paper, question, hint=hint, history=st.session_state.messages,
                              preview=preview, key=api_key, model_name=model_name, slide_count=slide_count)
            status.update(label="Evidence ready" if preview else "Response ready", state="complete")
        st.session_state.trace = result.trace
        st.session_state.latest_result = result
        return result
    except Exception as exc:
        if isinstance(exc, ValueError):
            st.error(str(exc))
        else:
            kind = type(exc).__name__
            if "RateLimit" in kind:
                st.warning("Groq's usage limit was reached. Wait and retry, or switch to Offline preview.")
            elif "Authentication" in kind:
                st.error("Groq rejected the API key. Check Settings or your .env file.")
            else:
                st.error("The AI request couldn't finish. Check your connection, model availability and quota, then retry. Your paper is still loaded.")
        return None


def show_sources(result):
    if result is None:
        return
    with st.expander(f"Evidence & workflow · {len(result.sources)} passages", expanded=False):
        st.caption(" → ".join(result.trace))
        for doc in result.sources:
            st.markdown(f"**Page {doc.metadata['page']} · Passage {doc.metadata['chunk']}**")
            st.write(doc.page_content)


def remember(question, result):
    st.session_state.messages.extend([
        {"role": "user", "content": question},
        {"role": "assistant", "content": result.text, "result": result},
    ])
    if result.deck:
        st.session_state.deck_result = result


head_l, head_r = st.columns([4, 1])
with head_l:
    st.markdown('<div class="eyebrow">PAPERLOOM / RESEARCH STUDIO BY RAHUL J</div>', unsafe_allow_html=True)
with head_r:
    st.markdown(f'<div class="mode-pill"><span></span>{"Offline preview" if preview else "Live AI"}</div>', unsafe_allow_html=True)

if view == "Workspace":
    if paper:
        st.markdown('<div class="hero hero-compact"><h1>A clearer point of view.</h1><p>Follow the evidence. Ask the next question.</p></div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="hero"><div class="hero-star">✳</div><h1>Make room for<br>your next discovery.</h1><p>Understand the paper. Shape the story. Own the viva.</p></div>', unsafe_allow_html=True)
    upload_col, sample_col = st.columns([3, 2], vertical_alignment="center")
    with upload_col:
        uploaded = st.file_uploader("Bring your research paper", type=["pdf"], key=f"upload_{st.session_state.upload_version}",
                                    help="Text-based PDF · up to 12 MB · 150 pages")
        if uploaded:
            data = uploaded.getvalue()
            digest = hashlib.sha256(data).hexdigest()
            if digest != st.session_state.upload_digest:
                if load_paper(data, uploaded.name, embedding_mode):
                    st.session_state.upload_digest = digest
                    st.rerun()
    with sample_col:
        st.markdown('<div class="sample-note">JUST EXPLORING?<br><span>Try a three-page teaching paper.<br>No account needed for preview.</span></div>', unsafe_allow_html=True)
        if st.button("Explore sample paper  ↗", use_container_width=True):
            # No network or model download needed for the onboarding preview.
            if load_paper(sample_pdf(), "Sample · Small Context, Better Answers.pdf", "offline"):
                st.rerun()
    if paper is None:
        st.markdown('<div class="section-heading">From a dense PDF to a clear point of view.</div>', unsafe_allow_html=True)
        cards = [("01", "Understand", "A grounded summary, key contributions and explanations you can trace to the page."),
                 ("02", "Present", "A thoughtful slide structure, speaker notes and a real PowerPoint download."),
                 ("03", "Practise", "Paper-specific viva questions and feedback on what to improve next.")]
        for col, (number, title, body) in zip(st.columns(3), cards):
            with col:
                st.markdown(f'<div class="feature-card"><span>{number}</span><h3>{title}</h3><p>{body}</p></div>', unsafe_allow_html=True)
        st.markdown('<div class="bottom-note">Built for the moment understanding turns into confidence.<br><span>Local document search · Page references · Your own pace</span></div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="paper-strip"><span>↳</span><div><strong>{html.escape(paper.name)}</strong><small>{len(paper.pages)} text pages · {len(paper.chunks)} indexed passages · Ready to explore</small></div></div>', unsafe_allow_html=True)
        if paper.name.startswith("Sample ·"):
            st.caption("Teaching sample: all experimental figures in this document are synthetic.")
        if preview:
            st.caption("Preview shows retrieved excerpts and templates. Enable Live AI in Settings for generated summaries and feedback.")
        shortcuts = [("Summarize paper", "Summarize this paper's research question, method, findings and limitations.", "summary"),
                     ("Find contributions", "What are the key contributions and what is new in this paper?", "concept"),
                     ("Explain method", "Explain the proposed method and experimental setup simply.", "concept")]
        for col, (label, request, hint) in zip(st.columns(3), shortcuts):
            with col:
                if st.button(label, use_container_width=True):
                    result = execute(request, hint)
                    if result:
                        remember(request, result)
        st.markdown("#### A conversation with your paper")
        for message in st.session_state.messages:
            with st.chat_message(message["role"], avatar=":material/auto_awesome:" if message["role"] == "assistant" else ":material/person:"):
                st.markdown(message["content"])
                if message.get("result"):
                    show_sources(message["result"])
        if not st.session_state.messages:
            st.markdown('<div class="conversation-empty">What would you like to understand?<small>Try “What are the limitations?” or “Explain the main contribution.”</small></div>', unsafe_allow_html=True)
        if request := st.chat_input("Ask a question, request slides, or start a viva…"):
            result = execute(request)
            if result:
                remember(request, result)
                if result.intent == "viva":
                    st.session_state.question = result.text
                st.rerun()

elif view == "Slides":
    st.markdown('<div class="page-title"><h1>A story worth sharing.</h1><p>Turn your paper into a presentation with a clear beginning, middle and takeaway.</p></div>', unsafe_allow_html=True)
    if not paper:
        st.info("Open a paper in Workspace to prepare your slides.")
    else:
        left, right = st.columns([3, 1])
        with left:
            focus = st.text_input("Presentation focus", value="Research question, method, results and limitations")
        with right:
            count = st.selectbox("Slides", [4, 5, 6, 7, 8, 9, 10], index=2)
        if st.button("Prepare presentation  ↗", type="primary"):
            result = execute(f"Create a {count}-slide presentation. Focus: {focus}", "slides", count)
            if result:
                st.session_state.deck_result = result
        result = st.session_state.deck_result
        if result and result.deck:
            st.caption("Extractive offline preview — source excerpts, not AI synthesis." if result.preview else "AI-generated draft. Check every claim against the cited pages before presenting.")
            st.download_button("Download PowerPoint ↓", data=export_deck(result.deck, paper.name, result.preview),
                               file_name="Rahul_J_Research_Presentation.pptx",
                               mime="application/vnd.openxmlformats-officedocument.presentationml.presentation", type="primary")
            for i, slide in enumerate(result.deck.slides):
                with st.container(border=True):
                    st.caption(f"SLIDE {i + 1:02} / {len(result.deck.slides):02}")
                    st.subheader(slide.title)
                    for bullet in slide.bullets:
                        st.markdown(f"- {bullet}")
                    with st.expander("Speaker notes & references"):
                        st.write(slide.notes)
                        st.caption("Supporting pages: " + (", ".join(map(str, slide.pages)) or "Overview"))
            show_sources(result)
        else:
            st.markdown('<div class="empty-panel"><span>▤</span><h3>Your paper, presentation-ready.</h3><p>Choose your focus and slide count.<br>We’ll keep the evidence close to the story.</p></div>', unsafe_allow_html=True)

elif view == "Viva practice":
    st.markdown('<div class="page-title"><h1>Know it. Say it. Defend it.</h1><p>A little practice makes the conversation feel familiar.</p></div>', unsafe_allow_html=True)
    if not paper:
        st.info("Open a paper in Workspace before starting a viva.")
    else:
        difficulty = st.select_slider("Question depth", options=["Foundations", "Methods", "Critical review"], value="Methods")
        if st.button("Ask an examiner question  ↗", type="primary"):
            previous = "\n".join(item["question"] for item in st.session_state.viva[-3:])
            result = execute(f"Ask a {difficulty} viva question about this paper. Prior questions to avoid: {previous}", "viva")
            if result:
                st.session_state.question = result.text
                st.session_state.pop("viva_answer", None)
        if st.session_state.question:
            st.markdown('<div class="eyebrow question-label">YOUR EXAMINER ASKS</div>', unsafe_allow_html=True)
            st.markdown(st.session_state.question)
            with st.form("answer_form"):
                answer = st.text_area("Your answer", placeholder="Explain it in your own words. Point to evidence where you can.", height=160, key="viva_answer")
                submit = st.form_submit_button("Review my answer", type="primary")
            if submit:
                if not answer.strip():
                    st.warning("Write an answer first.")
                else:
                    result = execute(f"Question: {st.session_state.question}\nCandidate answer: {answer}", "evaluate")
                    if result:
                        scores = result.evaluation.model_dump(include={"correctness", "depth", "clarity"}) if result.evaluation else None
                        st.session_state.viva.append({"question": st.session_state.question, "answer": answer,
                                                      "feedback": result.text, "scores": scores, "preview": result.preview})
                        st.markdown(result.text)
                        if scores:
                            for col, (name, score) in zip(st.columns(3), scores.items()):
                                col.metric(name.title(), f"{score}/5")
                            st.caption("Advisory AI rubric scores; these are not measured ability or confidence.")
                        show_sources(result)
        else:
            st.markdown('<div class="empty-panel"><span>✳</span><h3>One good question at a time.</h3><p>Practise explaining the method, defending the results,<br>and being honest about the limitations.</p></div>', unsafe_allow_html=True)
        if st.session_state.viva:
            with st.expander(f"Practice history · {len(st.session_state.viva)} answers"):
                for item in reversed(st.session_state.viva):
                    st.markdown(f"**{item['question']}**")
                    st.write(item["answer"])
                    st.markdown(item["feedback"])

else:
    st.markdown('<div class="page-title"><h1>Keep the progress.</h1><p>Your questions, practice and next steps, all in one place.</p></div>', unsafe_allow_html=True)
    metrics = [("Paper passages", len(paper.chunks) if paper else 0),
               ("Research questions", sum(m["role"] == "user" for m in st.session_state.messages)),
               ("Viva answers", len(st.session_state.viva))]
    for col, (label, value) in zip(st.columns(3), metrics):
        col.metric(label, value)
    report = session_report(paper, st.session_state.messages, st.session_state.viva, st.session_state.trace, preview)
    st.download_button("Download session report ↓", report, file_name="Rahul_J_Research_Report.md", mime="text/markdown")
    st.markdown(report)
    if st.session_state.trace:
        with st.expander("Last workflow"):
            for step in st.session_state.trace:
                st.write(step)

st.markdown('<div class="app-footer">PAPERLOOM <span> / </span> BY RAHUL J <span>·</span> Stay curious.</div>', unsafe_allow_html=True)
