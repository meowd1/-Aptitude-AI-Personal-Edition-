# Aptitude AI v2 — Architecture
### Book-grounded, LangGraph-orchestrated, portable personal aptitude coach

> This supersedes the v1 architecture doc. Core change in direction: the curriculum and RAG knowledge are now grounded in **two specific books you own**, orchestration moves to **LangChain + LangGraph** instead of hand-rolled service calls, the app is designed to **run on any computer** (not just a 16GB+ machine), and each lesson now produces a **Reasoning Rating** — a speed/accuracy performance score, not a real IQ measurement.

---

## 1. What Changed From v1, and Why

| Area | v1 | v2 | Why |
|---|---|---|---|
| Knowledge source | Generic scraped web sources (NCERT, Khan Academy, blogs) | **Two specific books you feed it**, chunked and embedded | Curriculum should match what you're actually studying from, not generic web content |
| Orchestration | Hand-written Python service functions calling Ollama directly | **LangChain** for retrieval/loading, **LangGraph** for the daily-lesson workflow as a stateful graph | You explicitly want LangChain/LangGraph; also genuinely fits better once the flow has branches (regenerate on invalid question, resume mid-session, etc.) |
| Hardware target | Assumed 16GB RAM, local 7B model always | **Tiered**: auto-detects hardware, picks the right model size, falls back to a cloud API key you provide if the machine can't run any local model well | "Run on any computer" — a 4GB laptop and a 32GB desktop both need to work |
| Performance tracking | Mastery % only | Mastery % **plus a per-lesson Reasoning Rating** (Elo-style, inspired by Matiks) | You asked for lesson-wise "IQ improvement" tracking — implemented honestly as a relative performance rating |
| UI reference | Notion/Linear/calm minimal | **Matiks-inspired**: dark, competitive, timed, rating-driven | Explicit request to copy Matiks' design direction (see companion UI doc) |

Everything else that worked in v1 — SQLite for structured data, deterministic (non-LLM) mastery/unlock logic, sympy validation for math — carries forward unchanged. Those decisions were sound regardless of orchestration framework.

---

## 2. The Two Books

You're feeding the system two sources, and they serve different roles in the curriculum:

**Book 1 — the aptitude & mathematics book** (your primary curriculum source)
Used to ground the Foundation → Intermediate → Advanced roadmap. Its chapter structure effectively *becomes* the roadmap: chapter/section titles are extracted and mapped to your existing topic list (Numbers, Fractions, Percentages, Ratio, Algebra, etc.) rather than you hand-authoring topic order from scratch.

**Book 2 — "My Best Mathematical and Logic Puzzles"** (Kordemski)
Used specifically for the **Logical** and **Critical Thinking** categories, and for the **Daily Challenge** feature — puzzle-style questions are pulled and adapted from here rather than generated cold by the LLM, since a curated puzzle book is a much better source of genuinely clever, non-formulaic problems than an LLM inventing puzzles from scratch.

Both books live in Chroma as **separate collections** (`book_aptitude_math`, `book_puzzles`) with shared metadata fields (`topic`, `chapter`, `difficulty_hint`, `page_number`) so retrieval can be filtered by book, topic, or both. This is a personal, offline, non-distributed tool built from books you own — the ingestion pipeline treats this as a normal personal RAG use case, not something requiring a licensing/compliance layer.

---

## 3. Book Ingestion Pipeline

Run once per book (re-run if you replace a book edition):

```
PDF (book file)
   ↓
LangChain PyPDFLoader / UnstructuredPDFLoader
   (falls back to OCR via pytesseract if the PDF is scanned images)
   ↓
Chapter/Section Detection
   (regex + heading-style heuristics on font size/bold runs;
    for Book 1, this produces the raw topic list — see §4)
   ↓
LangChain RecursiveCharacterTextSplitter
   (chunk size ~500 tokens, 50 token overlap, split on paragraph/sentence boundaries)
   ↓
Per-chunk metadata tagging
   {book, chapter, topic (see §4 mapping), page_number, content_type: "explanation" | "solved_example" | "puzzle"}
   ↓
Embedding (nomic-embed-text via Ollama, or a lighter model — see §6 for tiering)
   ↓
Chroma collection (persisted locally in data/chroma/)
```

Implemented as `scripts/ingest_book.py --book aptitude_math --path books/aptitude_math.pdf` and the same for puzzles. This is a manual, on-demand script — no scheduler, no background service, matching the v1 philosophy of "infrastructure only where it earns its keep."

### 4. Topic Mapping (book chapters → roadmap topics)

Since the roadmap should now reflect what Book 1 actually teaches, mapping is semi-automatic:

```
Extract all chapter/section headings from Book 1
   ↓
Embed each heading
   ↓
Compare against the existing topic taxonomy (Numbers, Fractions, Percentages, ...)
   via cosine similarity
   ↓
Auto-assign headings above a similarity threshold (e.g. 0.75)
   ↓
Write remaining low-confidence matches to content/topic_mapping_review.json
   for you to manually confirm/adjust once
   ↓
Final mapping saved to content/roadmap.json (replaces the v1 hardcoded roadmap)
```

This means the actual roadmap topic list is now **generated from your book's table of contents** on first ingestion, rather than hardcoded — the taxonomy in the original PRD (Foundation/Intermediate/Advanced/...) becomes the *category* scaffolding that chapters get sorted into, not a fixed topic list.

---

## 5. Orchestration: LangChain + LangGraph

### Where LangChain is used
Purely for its retrieval/loading primitives — document loaders, text splitters, the Chroma vectorstore wrapper, and the retriever interface. Not used as a "chain of chains" for the whole app; that's LangGraph's job.

```python
# services/rag/retriever.py (conceptual)
from langchain_community.vectorstores import Chroma
from langchain_ollama import OllamaEmbeddings

embeddings = OllamaEmbeddings(model=settings.embedding_model)
book_store = Chroma(collection_name="book_aptitude_math", embedding_function=embeddings, persist_directory="data/chroma")
puzzle_store = Chroma(collection_name="book_puzzles", embedding_function=embeddings, persist_directory="data/chroma")

def retrieve(topic: str, k: int = 4, source: str = "book_aptitude_math"):
    store = book_store if source == "book_aptitude_math" else puzzle_store
    return store.similarity_search(topic, k=k, filter={"topic": topic})
```

### Where LangGraph is used
The **daily lesson flow** (Learn → Guided Practice → Independent Practice → Mistake Analysis → Revision → Daily Challenge) is modeled as an explicit **stateful graph**, not a linear function call chain. This is the right tool here because the flow genuinely branches and needs to resume:

```
                ┌──────────────┐
                │   START      │
                └──────┬───────┘
                       ▼
              ┌─────────────────┐
              │  retrieve_node   │  (pulls grounding chunks from the
              └────────┬─────────┘   right book collection for current topic)
                       ▼
              ┌─────────────────┐
              │   teach_node     │  (LLM explains concept, grounded)
              └────────┬─────────┘
                       ▼
              ┌─────────────────┐
              │ generate_q_node  │  (LLM drafts a question)
              └────────┬─────────┘
                       ▼
              ┌─────────────────┐
         ┌────┤  validate_node   │
         │    └────────┬─────────┘
         │ invalid     │ valid
         ▼             ▼
   (loop back,   ┌─────────────────┐
    max 2 retries)│  present_node   │  (send to frontend, wait for answer)
                  └────────┬─────────┘
                           ▼
                  ┌─────────────────┐
                  │  score_node      │  (update mastery, Reasoning Rating,
                  └────────┬─────────┘   log mistake if wrong)
                           ▼
                  ┌─────────────────┐
                  │ next_or_end_node │  (more questions in this step? loop;
                  └────────┬─────────┘   else advance to next daily-flow stage)
                           ▼
                        [ END ]
```

Concretely, each daily-flow stage (Learn, Guided Practice, Independent Practice, Mistake Analysis, Revision, Daily Challenge) is its own small graph reusing the same node types (`retrieve → generate → validate → present → score`), and a top-level graph sequences the six stages. LangGraph's **checkpointer** (SQLite-backed, `SqliteSaver`) persists graph state after every node — meaning if you close the app mid-session, reopening resumes exactly where you left off, including which questions were already validated and shown. This solves a real gap in the v1 design, which had no defined resume behavior.

```python
# services/graph/daily_flow.py (conceptual)
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.sqlite import SqliteSaver

class LessonState(TypedDict):
    topic_id: str
    stage: str              # learn / guided / independent / mistakes / revision / challenge
    retrieved_chunks: list
    current_question: dict | None
    attempts_this_stage: int
    mastery_score: float
    reasoning_rating: int

graph = StateGraph(LessonState)
graph.add_node("retrieve", retrieve_node)
graph.add_node("teach", teach_node)
graph.add_node("generate_q", generate_question_node)
graph.add_node("validate", validate_node)
graph.add_node("present", present_node)
graph.add_node("score", score_node)

graph.add_conditional_edges("validate", lambda s: "generate_q" if not s["valid"] else "present")
graph.add_conditional_edges("score", lambda s: "generate_q" if s["stage_incomplete"] else END)

checkpointer = SqliteSaver.from_conn_string("data/lesson_state.db")
compiled = graph.compile(checkpointer=checkpointer)
```

### Memory
Two distinct kinds, kept separate rather than conflated into one "memory" system:

- **Session/working memory** — the LangGraph checkpointer above; short-lived, per-lesson, resumable.
- **Long-term learner memory** — stays in SQLite as in v1 (mastery, mistakes, attempts, streak). LangGraph state reads from and writes to this on stage transitions, but SQLite remains the durable source of truth, not the graph checkpoints. This avoids the common mistake of treating an agent framework's session state as your actual database.

---

## 6. Running on Any Computer

The single biggest architectural addition in v2. Three tiers, auto-detected on first launch:

```
Detect available RAM + whether a GPU is present
   ↓
┌─────────────────────────────────────────────────────────┐
│ Tier A — Capable local machine (16GB+ RAM, or any GPU)    │
│   → Ollama, qwen2.5:7b-instruct, full local RAG            │
├─────────────────────────────────────────────────────────┤
│ Tier B — Modest local machine (8–16GB RAM, CPU only)       │
│   → Ollama, qwen2.5:3b-instruct or phi3:mini, same RAG      │
│     pipeline, slightly shorter context window               │
├─────────────────────────────────────────────────────────┤
│ Tier C — Low-spec machine (<8GB RAM) or no Ollama installed │
│   → Local retrieval (Chroma) stays local and free;           │
│     generation/teaching calls a cloud API instead            │
│     (Anthropic API or OpenAI — you supply your own key)      │
│     Embeddings fall back to a small ONNX model              │
│     (e.g. bge-small) run via fastembed, not Ollama            │
└─────────────────────────────────────────────────────────┘
```

Implementation: `services/llm/client.py` becomes a small factory that reads a detected-or-configured `tier` from a local `config.yaml`, and returns the same interface (`.generate()`, `.stream()`) regardless of whether it's backed by Ollama or a cloud API. **Nothing above the client abstraction — LangGraph nodes, the retriever, the routes — knows or cares which tier is active.** This was already a stated principle in v1 ("never directly couple the UI with Ollama"); v2 just extends the same abstraction to cover cloud fallback too.

Practically: retrieval, embeddings-at-rest, SQLite, and the whole frontend always run 100% locally regardless of tier — the *only* thing that ever leaves the machine on Tier C is the prompt sent to a cloud LLM for generation, and only if you've explicitly configured an API key. Tiers A and B remain fully offline.

`config.yaml` (created on first run, editable anytime):
```yaml
tier: auto        # auto | A | B | C
cloud_provider: null   # anthropic | openai, only used if tier is C or forced
cloud_api_key: null    # read from env var if not set here
embedding_backend: auto  # auto | ollama | fastembed
```

---

## 7. Reasoning Rating (the "lesson-wise IQ improvement" feature)

Framed honestly: this is **not** a clinical or psychometrically validated IQ score. It's a relative, self-referential performance rating — same category as a chess Elo rating or Matiks' internal skill rating — that goes up when you solve faster and more accurately than your recent baseline, and down when you don't. It's useful for *you tracking your own trend over time*, not for any claim about general intelligence.

### Computation
An Elo-style rating, updated after every question, not just every lesson:

```
Each question has an implicit difficulty rating (0–2400 scale, derived from
its labeled difficulty level 0–10, e.g. difficulty 3 ≈ rating 1200).

Your Reasoning Rating starts at 1000.

After each answer:
  expected_score = 1 / (1 + 10^((question_rating - your_rating) / 400))
  actual_score    = 1 if correct else 0
                    (scaled down slightly if you used a hint, since a hinted
                     correct answer isn't the same signal as an unaided one)
  time_factor     = bonus/penalty of up to ±10% of the rating delta based on
                    solve time vs. the rolling median solve time for that
                    difficulty level (faster = small bonus, much slower = small penalty)

  your_rating += K * (actual_score - expected_score) * time_factor
  (K = 24, same magnitude chess uses for a developing player)
```

- Stored per-topic **and** as an overall rating, both in SQLite (`reasoning_ratings` table: `topic_id, rating, updated_at`).
- Shown on the Progress page as a trend line and on Home as the current number, styled per the Matiks-inspired UI (see companion UI doc) — this is the app's answer to Matiks' competitive rating display, just versus your own history instead of other players.
- Explicit UI copy always calls it "Reasoning Rating," never "IQ," to avoid making a claim the metric can't back up.

---

## 8. Updated Database Schema (additions to v1)

```sql
-- reasoning_ratings: per-topic and overall Elo-style rating
CREATE TABLE reasoning_ratings (
  topic_id TEXT,                  -- NULL row = overall rating
  rating INTEGER NOT NULL DEFAULT 1000,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (topic_id)
);

-- book_sources: which book/chapter a question or explanation was grounded in
CREATE TABLE book_sources (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  book TEXT NOT NULL,             -- 'aptitude_math' | 'puzzles'
  chapter TEXT,
  page_number INTEGER,
  topic_id TEXT
);

-- questions table (v1) gains a nullable FK
ALTER TABLE questions ADD COLUMN book_source_id INTEGER REFERENCES book_sources(id);

-- lesson_sessions: for LangGraph checkpoint cross-reference / daily summary
CREATE TABLE lesson_sessions (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  date TEXT NOT NULL,
  stage TEXT NOT NULL,
  completed INTEGER DEFAULT 0,
  rating_delta INTEGER DEFAULT 0,
  started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  ended_at TIMESTAMP
);
```

Everything else from the v1 schema (`topics`, `progress`, `attempts`, `mistakes`, `daily_log`) carries forward unchanged.

---

## 9. Updated Folder Structure

```
aptitude-ai/
  frontend/                        # unchanged structure from v1, Matiks-styled (see UI doc)

  backend/
    main.py
    routes/                        # same as v1: learn, practice, review, progress, roadmap
    services/
      graph/
        daily_flow.py               # LangGraph top-level graph
        nodes.py                    # retrieve / teach / generate_q / validate / present / score
        state.py                    # LessonState TypedDict
      rag/
        retriever.py                # LangChain Chroma wrappers, per-book
        topic_mapper.py             # chapter-heading → topic similarity mapping
      llm/
        client.py                   # tiered factory: Ollama (A/B) or cloud API (C)
        prompts.py
      learning_engine.py            # unchanged from v1 — deterministic mastery/unlocks
      revision_engine.py            # unchanged from v1 — spaced repetition
      rating_engine.py               # NEW — Elo-style Reasoning Rating computation
      math_validator.py             # unchanged from v1 — sympy checks
    models/
      db.py
      schema.sql
    content/
      roadmap.json                  # now generated from Book 1's TOC, not hand-authored
      topic_mapping_review.json     # low-confidence chapter→topic matches for manual review
    data/                            # gitignored
      aptitude.db
      lesson_state.db                # LangGraph checkpoints
      chroma/
    books/                            # gitignored — you place the 2 PDFs here yourself
      aptitude_math.pdf
      puzzles.pdf
    scripts/
      ingest_book.py
      seed_roadmap.py
    config.yaml                       # tier selection, cloud fallback config
    tests/

  start.sh
  README.md
```

---

## 10. Updated Tech Stack

**Frontend:** Next.js, TypeScript, Tailwind, shadcn/ui — same as v1, restyled per the companion UI doc.

**Backend:** FastAPI, Python.

**Orchestration:** LangChain (document loading, splitting, vectorstore/retriever interfaces), LangGraph (stateful lesson-flow graph, SQLite checkpointing).

**LLM:** Ollama for Tiers A/B (`qwen2.5:7b-instruct` / `qwen2.5:3b-instruct` / `phi3:mini`); Anthropic or OpenAI API for Tier C, via LangChain's chat model wrappers so the same `.invoke()`/`.stream()` interface works regardless of tier.

**Embeddings:** `nomic-embed-text` via Ollama (Tiers A/B) or `fastembed` (bge-small, ONNX, no GPU/Ollama needed) for Tier C.

**Vector DB:** ChromaDB, embedded/local mode, two collections (one per book).

**Database:** SQLite, extended schema above.

**Math validation:** sympy, unchanged.

**PDF/book ingestion:** LangChain's `PyPDFLoader`, falling back to `UnstructuredPDFLoader` + `pytesseract` OCR for scanned pages.

---

## 11. Build Order (v2)

1. Ingest Book 1 → auto-generate `roadmap.json`, manually confirm the low-confidence topic mappings once
2. Ingest Book 2 (puzzles) into its own Chroma collection
3. Build the tiered `llm/client.py` factory; confirm it works against both an Ollama model and a cloud API key, swappable via `config.yaml`
4. Build the LangGraph `daily_flow` for **one topic only**, all six stages, with checkpointing verified by closing and reopening the app mid-lesson
5. Wire `rating_engine.py`, confirm Reasoning Rating updates sensibly across a run of test answers (mix of fast-correct, slow-correct, incorrect, hinted)
6. Extend to the rest of the roadmap topics generated from Book 1
7. Wire the Daily Challenge stage specifically to Book 2 (puzzles collection)
8. Frontend build per the companion UI doc, wired to the now-working backend
9. Test the Tier C (cloud fallback) path end-to-end on a low-spec machine or a deliberately constrained VM, to confirm the "runs on any computer" claim actually holds

As before: get one topic fully working end-to-end before extending to the rest — that hasn't changed, only what "fully working" now includes (LangGraph resumability, book grounding, rating updates).
