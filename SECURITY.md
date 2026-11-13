# Security notes

Paperloom is designed for a local, single-user demonstration. It binds to localhost and uses embedded, in-memory Chroma. Do not treat it as a hardened multi-user service.

## Open dependency advisories

Review date: 2026-11-13. An audit of the pinned runtime reported five entries in `chromadb==1.5.9`, representing **four distinct advisories**; one entry was duplicated. No patched versions were listed, and the package index reported 1.5.9 as its latest release.

| Advisory | Reported issue |
| --- | --- |
| [CVE-2026-45829](https://github.com/advisories/GHSA-f4j7-r4q5-qw2c) | Code injection through Chroma server collection creation. |
| [CVE-2026-45833](https://github.com/advisories/GHSA-36p7-vc44-83pf) | Code injection through a Chroma server collection update. |
| [CVE-2026-45831](https://github.com/advisories/GHSA-xph7-9rjv-w5fr) | Server RBAC permission-scoping failure. |
| [CVE-2026-45830](https://github.com/advisories/GHSA-2wm9-hf6c-p5cr) | Server cross-tenant authorization failure. |

The active implementation uses `chromadb.EphemeralClient`, random internal collection names and a fixed local embedding implementation. It does not launch a Chroma HTTP server, accept user-supplied embedding code or configure Chroma server RBAC. The network/server paths described above are not exposed by this design. This scope assessment is **not** a vulnerability-free certification.

Do not expose a Chroma server or convert the app to a public multi-tenant deployment without revisiting these findings. Recheck for patched releases before hosting it publicly. Advisories have not been suppressed to obtain a green audit result.

```powershell
.\.venv\Scripts\python.exe -m pip install pip-audit
.\.venv\Scripts\python.exe -m pip_audit -r requirements-lock.txt --no-deps --disable-pip
```

The audit currently exits nonzero for these findings. The GitHub application-check workflow runs tests, dependency consistency and source hygiene; it is not represented as a passing vulnerability audit.

## Credentials and paper data

- Never commit `.env` files, Streamlit secrets or API keys. They are ignored by default.
- The source hygiene script checks several known credential patterns without printing values. It is conservative, not exhaustive.
- Settings keys live in session memory. Environment keys stay in your local `.env`.
- PDFs and vector collections are session-local in process memory. Closing/replacing a paper clears the associated state; abrupt disconnects can leave data in memory until the process stops.
- Live requests send your prompt, recent context and retrieved paper excerpts to Groq. Only use content you are authorised to send there.
- Paper text is untrusted evidence in prompts. Prompt instructions reduce injection risk but are not a formal isolation boundary.

## Source boundaries

This clean repository includes only the newly written application and original visual assets, licensed under MIT. It excludes the unlicensed upstream reference code, recordings, data and history. See NOTICE.md. Dependency/model licences remain separate.
