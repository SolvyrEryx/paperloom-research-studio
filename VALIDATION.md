# Verification record

Date: 2026-11-13 · Windows · Python 3.11.9

## Application checks

- The implementation's 27-test suite covers PDF validation, blank-page numbering, encrypted/page-limited inputs, actual Chroma retrieval, isolated collections, intent routing, explicit-task overrides, LCEL contracts, invalid-citation rejection, structured slides/evaluation, PPTX structure, missing-key behavior and the offline Streamlit journey.
- A prior clean-source snapshot was installed into a fresh virtual environment from the pinned lock file: all 27 tests passed; dependency consistency and repository hygiene passed.
- A real MiniLM model was downloaded and used to index a PDF; a limitations query retrieved the expected supporting page.
- Browser verification covered PDF upload, semantic indexing and a real six-slide PowerPoint download. The downloaded file was inspected with python-pptx.
- Desktop layout was inspected at 1440 × 1000; mobile layout at 390 × 844 showed no horizontal overflow.
- Standalone Paperloom release: installed its own isolated environment from `requirements-lock.txt`; **27 tests passed** in 26.24 seconds; `pip check` passed; source hygiene passed. The new Paperloom branding was visually inspected in the running app and captured in `docs/workspace.jpg`.
- The original cover was visually inspected. The original workflow GIF contains 64 frames; a static alternative is included. Neither is represented as a live product recording.

## Boundaries of verification

**Live Groq:** no API key was configured during development. Deterministic model fixtures verify the code contract but not external provider availability or model-answer quality. Before a live college demonstration, supply your key and test a summary, slide generation and viva evaluation on a paper you understand.

**PowerPoint rendering:** slide structure, text, author branding and notes are tested; a native PowerPoint/LibreOffice visual render is not part of the automated checks.

**Dependencies:** consistency passes, but a separate audit reports four distinct Chroma server advisories. Read SECURITY.md for the local embedded-client assessment. Do not describe the vulnerability audit as clean.

**Illustrations:** the custom cover and GIF are original explanatory graphics. The GIF is not a recorded live agent run. The built-in sample paper and its numbers are synthetic teaching material.

**GitHub CI:** the [first published source run](https://github.com/SolvyrEryx/paperloom-research-studio/actions/runs/43436696643) completed successfully on Linux/Python 3.11. Installation from the lock file, dependency consistency, all application tests and repository hygiene passed. The README includes the live workflow-status badge; use it to inspect later revisions.

## Public repository

[SolvyrEryx/paperloom-research-studio](https://github.com/SolvyrEryx/paperloom-research-studio) is public and GitHub recognises the MIT licence. Browser inspection confirmed the rendered README, original cover, actual app screenshot and animated workflow load correctly. The standalone repository begins with a new root commit and excludes the upstream code/history, recordings, runtime paper context, environments and API credentials.
