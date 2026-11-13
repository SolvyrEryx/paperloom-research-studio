from io import BytesIO
import json

import pymupdf as fitz
import pytest
from langchain_core.messages import AIMessage
from langchain_core.runnables import RunnableLambda
from pptx import Presentation

from studio.agents import Deck, Slide, make_model, route_offline, run_task
from studio.documents import index_paper, read_pdf, sample_pdf
from studio.exports import export_deck, session_report


@pytest.fixture
def paper():
    value = index_paper(sample_pdf(), "sample.pdf", "offline")
    yield value
    value.close()


def test_ingestion_metadata_and_real_chroma_retrieval(paper):
    assert len(paper.pages) == 3
    assert all(d.metadata["page"] in {1, 2, 3} for d in paper.chunks)
    docs = paper.retrieve("limitations equations tables image-only", k=1)
    assert docs[0].metadata["page"] == 3
    assert paper.store._collection.count() == len(paper.chunks)


def test_rejects_invalid_and_image_only_pdfs():
    with pytest.raises(ValueError, match="PDF"):
        read_pdf(b"broken", "bad.pdf")
    with fitz.open() as doc:
        doc.new_page()
        empty = doc.tobytes()
    with pytest.raises(ValueError, match="No usable text"):
        read_pdf(empty, "scan.pdf")
    with pytest.raises(ValueError, match="12 MB"):
        read_pdf(b"x" * (12 * 1024 * 1024 + 1), "big.pdf")


@pytest.mark.parametrize("question,intent", [("hello", "general"), ("summarize the paper", "summary"),
    ("make slides", "slides"), ("start viva", "viva"), ("explain the method", "concept")])
def test_preview_intent_router(question, intent):
    route = route_offline(question)
    assert route.intent == intent
    assert route.retrieve == (intent != "general")


def test_agent_skips_retrieval_for_greeting():
    result = run_task(None, "hello", preview=True)
    assert result.sources == []
    assert any("skipped" in t for t in result.trace)


def test_preview_does_not_fake_evaluation(paper):
    result = run_task(paper, "My answer: it uses retrieval.", hint="evaluate", preview=True)
    assert result.evaluation is None
    assert "does not grade" in result.text


def test_pptx_export_has_real_slides_notes_and_brand(paper):
    result = run_task(paper, "create slides", hint="slides", preview=True, slide_count=6)
    payload = export_deck(result.deck, paper.name, True)
    prs = Presentation(BytesIO(payload))
    assert len(prs.slides) == 6
    assert prs.core_properties.author == "Rahul J"
    assert "preview" in prs.slides[0].notes_slide.notes_text_frame.text.lower()
    assert any("EXTRACTIVE PREVIEW" in s.text for s in prs.slides[1].shapes if s.has_text_frame)


def fake_model(responses):
    outputs = iter(responses)
    return RunnableLambda(lambda prompt: AIMessage(content=next(outputs)))


def test_live_lcel_router_and_grounded_specialist(paper):
    model = fake_model([json.dumps({"intent": "concept", "retrieve": True, "query": "limitations", "reason": "Needs paper evidence"}),
                        "The sample cannot establish generalization [p. 3]."])
    result = run_task(paper, "What are the limits?", model=model)
    assert result.sources and "[p. 3]" in result.text
    assert "LCEL" in result.trace[-1]
    assert not result.preview


def test_live_router_skips_retrieval_and_no_paper_needed():
    model = fake_model([json.dumps({"intent": "general", "retrieve": False, "query": "hello", "reason": "Greeting"}), "Hello!"])
    result = run_task(None, "hello", model=model)
    assert result.text == "Hello!" and not result.sources


def test_invalid_page_citation_is_rejected(paper):
    model = fake_model([json.dumps({"intent": "concept", "retrieve": True, "query": "method", "reason": "Paper question"}),
                        "A claim [p. 999]."])
    with pytest.raises(ValueError, match="unavailable page"):
        run_task(paper, "Explain method", model=model)


def test_lcel_structured_slide_output(paper):
    deck = Deck(title="Research", slides=[Slide(title=f"Slide {i}", bullets=["Source-based point"], notes="Explain the method.", pages=[2]) for i in range(4)])
    model = fake_model([json.dumps({"intent": "slides", "retrieve": True, "query": "method results", "reason": "Build presentation"}), deck.model_dump_json()])
    result = run_task(paper, "Make 4 slides", slide_count=4, model=model)
    assert len(result.deck.slides) == 4


def test_live_viva_evaluation_preserves_rubric_and_sources(paper):
    evaluation = {"correctness": 4, "depth": 3, "clarity": 4, "feedback": "Discuss limitations [p. 3].",
                  "model_answer": "The method keeps page metadata [p. 2].", "pages": [2, 3]}
    model = fake_model([json.dumps({"intent": "evaluate", "retrieve": True, "query": "method limitations", "reason": "Evaluate against paper"}), json.dumps(evaluation)])
    result = run_task(paper, "Question: explain method. Answer: retrieve text.", hint="evaluate", model=model)
    assert result.evaluation.correctness == 4
    assert len(result.sources) > 0


def test_wrong_live_slide_count_is_rejected(paper):
    deck = Deck(title="Research", slides=[Slide(title="Method", bullets=["A point"], notes="Notes", pages=[2]) for _ in range(3)])
    model = fake_model([json.dumps({"intent": "slides", "retrieve": True, "query": "method", "reason": "Presentation"}), deck.model_dump_json()])
    with pytest.raises(ValueError, match="wrong slide count"):
        run_task(paper, "Make 6 slides", slide_count=6, model=model)


def test_session_report_has_no_invented_readiness_score(paper):
    report = session_report(paper, [], [], [], True)
    assert "Viva answers submitted: 0" in report
    assert "readiness score" not in report.lower()
    assert "no live LLM" in report


def test_missing_key_does_not_require_api_at_import(monkeypatch):
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    with pytest.raises(ValueError, match="API key"):
        make_model()


def test_document_collections_are_isolated(paper):
    other = index_paper(sample_pdf(), "other.pdf", "offline")
    try:
        assert other.store._collection.name != paper.store._collection.name
        other.close()
        assert paper.retrieve("method")
    finally:
        # Already closed above; don't delete twice.
        pass


def test_password_protected_pdf_is_rejected():
    with fitz.open(stream=sample_pdf(), filetype="pdf") as doc:
        protected = doc.tobytes(encryption=fitz.PDF_ENCRYPT_AES_256,
                                owner_pw="owner-test-only", user_pw="user-test-only")
    with pytest.raises(ValueError, match="password-protected"):
        read_pdf(protected, "locked.pdf")


def test_original_page_numbers_survive_blank_pages():
    with fitz.open(stream=sample_pdf(), filetype="pdf") as doc:
        doc.new_page(pno=0)
        data = doc.tobytes()
    pages = read_pdf(data, "blank-first-page.pdf")
    assert [p.metadata["page"] for p in pages] == [2, 3, 4]


def test_page_limit_is_enforced():
    with fitz.open() as doc:
        for _ in range(151):
            doc.new_page()
        data = doc.tobytes()
    with pytest.raises(ValueError, match="150 pages"):
        read_pdf(data, "too-many-pages.pdf")


def test_explicit_ui_task_overrides_incorrect_model_routing(paper):
    model = fake_model([json.dumps({"intent": "general", "retrieve": False, "query": "hello", "reason": "Wrong route"}),
                        "A summary supported by the method [p. 2]."])
    result = run_task(paper, "Summarize this paper", hint="summary", model=model)
    assert result.intent == "summary" and result.sources


def test_hidden_invalid_citation_in_structured_evaluation_is_rejected(paper):
    evaluation = {"correctness": 4, "depth": 3, "clarity": 4, "feedback": "Unsupported claim [p. 999].",
                  "model_answer": "The method keeps metadata [p. 2].", "pages": [2]}
    model = fake_model([json.dumps({"intent": "evaluate", "retrieve": True, "query": "method", "reason": "Evaluate"}), json.dumps(evaluation)])
    with pytest.raises(ValueError, match="unavailable page"):
        run_task(paper, "Evaluate this answer", hint="evaluate", model=model)
