from pathlib import Path
from streamlit.testing.v1 import AppTest

APP = Path(__file__).resolve().parents[1] / "app.py"


def button(at, label):
    return next(b for b in at.button if b.label == label)


def test_user_journey_without_key():
    at = AppTest.from_file(str(APP), default_timeout=45).run()
    assert not at.exception
    button(at, "Explore sample paper  ↗").click().run()
    assert not at.exception
    assert at.session_state.paper is not None
    button(at, "Summarize paper").click().run()
    assert not at.exception
    assert len(at.session_state.messages) == 2
    at.radio(key="navigation").set_value("Slides").run()
    button(at, "Prepare presentation  ↗").click().run()
    assert not at.exception
    assert len(at.session_state.deck_result.deck.slides) == 6
    at.radio(key="navigation").set_value("Viva practice").run()
    button(at, "Ask an examiner question  ↗").click().run()
    at.text_area(key="viva_answer").set_value("The method retrieves relevant chunks and retains page metadata.")
    button(at, "Review my answer").click().run()
    assert not at.exception
    assert len(at.session_state.viva) == 1
    assert at.session_state.viva[0]["scores"] is None
    at.radio(key="navigation").set_value("Session report").run()
    assert not at.exception
    assert any("Viva answers submitted: 1" in m.value for m in at.markdown)
    button(at, "Close paper").click().run()
    assert not at.exception
    assert at.session_state.paper is None
    assert not at.session_state.messages and not at.session_state.viva


def test_live_without_key_shows_actionable_message(monkeypatch):
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    at = AppTest.from_file(str(APP), default_timeout=45).run()
    button(at, "Explore sample paper  ↗").click().run()
    at.selectbox(key="response_mode").set_value("Live AI").run()
    button(at, "Summarize paper").click().run()
    assert not at.exception
    assert any("Add your Groq API key" in w.value for w in at.warning)


def test_replacing_paper_clears_existing_work():
    at = AppTest.from_file(str(APP), default_timeout=45).run()
    button(at, "Explore sample paper  ↗").click().run()
    button(at, "Summarize paper").click().run()
    previous_collection = at.session_state.paper.store._collection.name
    assert at.session_state.messages
    button(at, "Explore sample paper  ↗").click().run()
    assert not at.exception
    assert not at.session_state.messages
    assert at.session_state.deck_result is None
    assert at.session_state.paper.store._collection.name != previous_collection
