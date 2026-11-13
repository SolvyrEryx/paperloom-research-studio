"""Session-local, page-aware PDF indexing. No paid embedding API."""
from __future__ import annotations

import hashlib
import uuid
from dataclasses import dataclass

import chromadb
import pymupdf as fitz
from chromadb.config import Settings
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter


class LocalEmbeddings(Embeddings):
    """Local MiniLM ONNX by default; explicit offline lexical preview option."""

    def __init__(self, mode: str = "semantic"):
        self.mode = mode
        if mode == "semantic":
            from chromadb.utils.embedding_functions import ONNXMiniLM_L6_V2
            self.encoder = ONNXMiniLM_L6_V2()
        elif mode == "offline":
            from sklearn.feature_extraction.text import HashingVectorizer
            self.encoder = HashingVectorizer(n_features=768, alternate_sign=False, norm="l2")
        else:
            raise ValueError("Unknown embedding mode.")

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        if self.mode == "offline":
            return self.encoder.transform(texts).toarray().tolist()
        return [v.tolist() for v in self.encoder(input=texts)]

    def embed_query(self, text: str) -> list[float]:
        return self.embed_documents([text])[0]


@dataclass
class Paper:
    name: str
    fingerprint: str
    pages: list[Document]
    chunks: list[Document]
    store: Chroma
    embedding_mode: str

    def retrieve(self, query: str, k: int = 6) -> list[Document]:
        return self.store.similarity_search(query, k=min(k, len(self.chunks)))

    def close(self):
        self.store.delete_collection()


def read_pdf(data: bytes, name: str) -> list[Document]:
    if not data or len(data) > 12 * 1024 * 1024:
        raise ValueError("Choose a non-empty PDF smaller than 12 MB.")
    try:
        with fitz.open(stream=data, filetype="pdf") as pdf:
            if pdf.needs_pass:
                raise ValueError("This PDF is password-protected. Upload an unlocked copy.")
            if len(pdf) > 150:
                raise ValueError("Please use a paper with 150 pages or fewer.")
            pages = [Document(page_content=p.get_text().strip(),
                              metadata={"source": name, "page": i + 1})
                     for i, p in enumerate(pdf)]
    except ValueError:
        raise
    except Exception as exc:
        raise ValueError("This file could not be read as a PDF.") from exc
    pages = [p for p in pages if p.page_content]
    if sum(len(p.page_content) for p in pages) < 100:
        raise ValueError("No usable text found. Scanned PDFs need OCR before uploading.")
    if sum(len(p.page_content) for p in pages) > 1_000_000:
        raise ValueError("This document contains too much text. Use a shorter paper.")
    return pages


def index_paper(data: bytes, name: str, mode: str = "semantic") -> Paper:
    pages = read_pdf(data, name)
    splitter = RecursiveCharacterTextSplitter(chunk_size=1100, chunk_overlap=150)
    chunks = splitter.split_documents(pages)
    for i, chunk in enumerate(chunks):
        chunk.metadata["chunk"] = i + 1
    client = chromadb.EphemeralClient(Settings(anonymized_telemetry=False))
    store = Chroma(client=client, collection_name="paper-" + uuid.uuid4().hex,
                   embedding_function=LocalEmbeddings(mode),
                   collection_metadata={"hnsw:space": "cosine"})
    try:
        store.add_documents(chunks, ids=[str(i) for i in range(len(chunks))])
    except Exception:
        store.delete_collection()
        raise
    return Paper(name, hashlib.sha256(data).hexdigest(), pages, chunks, store, mode)


def source_context(docs: list[Document]) -> str:
    return "\n\n".join(f"[p. {d.metadata['page']}, chunk {d.metadata['chunk']}]\n{d.page_content}"
                        for d in docs)


def sample_pdf() -> bytes:
    """Original synthetic fixture, not a real published paper or empirical result."""
    sections = [
        ("Small Context, Better Answers", "A synthetic research paper for exploring Rahul J Research Studio.\n\n"
         "ABSTRACT\nThis illustrative study investigates retrieval-augmented generation for student research assistants. "
         "We compare a baseline that receives the first section of a document against a page-aware retriever. "
         "The aim is to make evidence easy to inspect while limiting the context sent to a language model.\n\n"
         "CONTRIBUTION\nThe proposed workflow keeps page metadata, routes requests by task, and combines local vector search "
         "with grounded generation. This is a teaching example, not a published or peer-reviewed study."),
        ("Method & Experimental Setup", "METHOD\nDocuments are split into overlapping passages of 1,100 characters. "
         "A local MiniLM encoder maps each passage into a semantic vector. Chroma retrieves relevant passages using cosine similarity. "
         "The assistant chooses whether a question needs paper evidence before retrieving. Summary, concept, slides and viva tasks use distinct prompts.\n\n"
         "EXPERIMENTAL SETUP\nA hypothetical evaluation uses 30 questions from three short papers. We measure exact citation matches "
         "and answer relevance. The first-section baseline receives the opening 2,000 characters. The retrieval condition receives six passages. "
         "The same model and prompt constraints are used in both conditions. All counts and outcomes in this sample are invented for UI demonstration."),
        ("Results, Limits & Next Steps", "ILLUSTRATIVE RESULTS\nThe synthetic baseline cites a supporting page on 12 of 30 questions; "
         "the hypothetical retrieval workflow cites a supporting page on 24 of 30 questions. These are made-up teaching numbers, not measured findings.\n\n"
         "LIMITATIONS\nA small sample cannot establish generalization. Citation presence does not guarantee factual correctness. "
         "Retrieval may miss equations, tables and image-only content. Chunk size, embedding choice and prompt wording affect the outcome.\n\n"
         "FUTURE WORK\nEvaluate on a larger, public benchmark; measure retrieval recall; compare chunk sizes; and ask independent reviewers "
         "to score answer support. The main takeaway is to separate evidence retrieval from generation and make both inspectable.")]
    with fitz.open() as pdf:
        for title, body in sections:
            page = pdf.new_page(width=595, height=842)
            page.insert_textbox(fitz.Rect(48, 48, 548, 110), title, fontsize=22, fontname="hebo")
            page.insert_textbox(fitz.Rect(48, 125, 548, 770), body, fontsize=12, lineheight=1.5)
        return pdf.tobytes()
