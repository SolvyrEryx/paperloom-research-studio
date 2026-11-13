# A five-minute Paperloom demonstration

**Presenter:** Rahul J<br>
**Project:** Paperloom — Paper-to-Presentation & Viva Agent

## Before presenting

1. Install the pinned environment and run the tests as described in README.
2. Start the app with `run.cmd` or `python -m streamlit run app.py`.
3. Add a valid Groq key privately in Settings. Select a model available to your account and Live AI.
4. Use a public research paper that you have actually read and are authorised to send to Groq.
5. Complete a summary, slide generation and viva evaluation beforehand. Check generated claims against the original paper. The repository's offline tests do not replace this step.
6. Keep a downloaded deck and report as a backup. Explain if you switch to offline preview.

## Demonstration sequence

| Time | Show | Explain |
| --- | --- | --- |
| 0:00–0:40 | Upload a paper | Original page numbers survive extraction; local embeddings populate Chroma. |
| 0:40–1:35 | Ask for contributions or a method explanation | Intent routing chooses the specialist and whether retrieval is needed. Expand Evidence & workflow and inspect a cited passage. |
| 1:35–2:00 | Send a greeting in chat | The live router can skip document retrieval for a request that does not need evidence. |
| 2:00–3:00 | Generate four slides and download PowerPoint | Structured output is validated; the file contains actual slides, speaker notes and page references. |
| 3:00–4:15 | Request a viva question and submit an answer | The evaluator uses paper evidence; rubric scores are advisory, not measured ability. |
| 4:15–5:00 | Download the session report and show architecture | Point to explicit LCEL chains and explain the limitations. |

## Questions you should be able to answer

- Why is agent-selected retrieval different from always retrieving for every message?
- Where are the system and user prompts? What does the LCEL pipe compose?
- How does the application preserve page metadata and isolate document collections?
- Why can a correctly formatted citation still support an incorrect answer?
- What changes between local semantic indexing and lexical preview indexing?
- Which work is local, and which data is sent to Groq?
- What does offline preview demonstrate, and why does it not satisfy LLM integration by itself?

## Disclose accurately

This project uses separately prompted task specialists selected by a router. It does not run an autonomous debate between agents. The sample paper is synthetic. Camera/voice analysis is not included. Live AI is subject to provider quota and has to be verified with a real key. Follow your institution's rules on AI-assisted development and attribution; see NOTICE.md.
