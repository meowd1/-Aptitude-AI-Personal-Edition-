# Aptitude AI — Personal Edition
### A local, single-user AI aptitude coach

> This is a personal tool, built for one user (you), running on your own machine. It is not a product. There is no auth, no multi-tenancy, no scaling concern, no analytics/telemetry, and no need for enterprise-grade abstractions. Every decision below is made to optimize for **"works reliably for me, is easy to build, is easy to modify later"** — not for handling load, other users, or production hardening.

This document is written to be handed directly to a coding agent (Antigravity) to scaffold and build the app.

---

## 1. What This App Actually Needs To Do

Strip away the product framing and this app has exactly 5 jobs:

1. Show me a daily learning session (Learn → Practice → Review → Revise).
2. Teach concepts using an LLM, grounded in some reference material so it doesn't hallucinate formulas.
3. Generate and validate practice questions.
4. Track what I'm weak at and resurface it on a spaced schedule.
5. Look and feel calm — Notion-minimal, Duolingo-paced.

Everything in the architecture exists to serve those 5 jobs. Nothing else.

---

## 2. Design Decisions (and why they're different from a "production" version)

| Concern | Production approach | Personal-use approach (this doc) | Why |
|---|---|---|---|
| Users | Auth, sessions, multi-tenant DB | None — single row, single profile | You're the only user |
| Database | Postgres, migrations, connection pooling | SQLite, single file | One writer, zero ops |
| Vector DB | Dedicated service (Chroma server, Qdrant) | ChromaDB in **embedded/local mode** (just a folder) | No server to run/maintain |
| Scraper | Scheduled service, distributed crawling, legal review of every source | A **manual, on-demand script** you run yourself when you want to top up knowledge | You said copyright isn't a concern for personal use — so we skip building a "safe sources only" compliance layer entirely. It's just a script that pulls text into a local folder for RAG. Not distributed, not exposed, not resold. |
| Question validation | Rejects anything not provably correct, needs a fallback path per category | LLM self-checks its own answer once, deterministic re-check only where cheap (arithmetic/algebra via sympy); everything else just gets a second-pass LLM review | You're the only consumer — occasional imperfect question is fine, not a liability |
| Mastery/progression logic | Bayesian Knowledge Tracing / IRT | Simple deterministic rule (rolling accuracy + recency), still **not** LLM-decided | Doesn't need to be state-of-the-art, just needs to not be random |
| Deployment | Docker, CI/CD, monitoring | `npm run dev` + `uvicorn` in two terminals, or one `start.sh` | It's your laptop |
| Backend framework | FastAPI with layered services, DI containers | FastAPI, but simple — a handful of route files and plain Python modules, no DI framework | Overkill otherwise |

The one thing kept from the original "production" thinking: **the LLM never makes the pass/fail or unlock decision.** That's not a production-only concern — non-deterministic progression would be annoying for you too (you'd see inconsistent gating day to day). Everything else is simplified hard.

---

## 3. Tech Stack (Final)

**Frontend**
- Next.js (App Router) + TypeScript
- Tailwind CSS + shadcn/ui
- No state management library needed — React state + a couple of context providers is enough for one user

**Backend**
- FastAPI (Python)
- Runs as a single process, `uvicorn main:app --reload`

**LLM**
- OmniRoute (Local AI Gateway) pointing to `qwen2.5:7b-instruct` or other providers.
- Everything talks to OmniRoute through **one thin wrapper module** (`services/llm/client.py`) using OpenAI-compatible format. This gives us auto-fallback, free-tier pooling, and token compression.

**Data**
- SQLite (single file, `data/aptitude.db`) — progress, mistakes, questions, streaks, schedule
- ChromaDB in embedded/persistent local mode (`data/chroma/`) — concept knowledge for RAG
- Plain JSON files (`content/roadmap.json`, `content/curated_questions/*.json`) for hand-authored curriculum content you seed once

**Embeddings**
- `nomic-embed-text` via Ollama (keeps everything local, no extra Python ML deps to fight with)

**Math validation**
- `sympy` for anything with a closed-form deterministic answer (arithmetic, percentages, ratios, algebra, basic geometry)

**Scheduling**
- No APScheduler / background service needed. Spaced-repetition due-dates are just a column in SQLite (`next_review_at`), checked when the app loads. If you later want the ingestion script to run nightly, a simple cron entry is enough — no in-app scheduler required.

---

## 4. High-Level Architecture

```
┌─────────────────────────────┐
│   Next.js Frontend (UI)     │
│   Home / Learn / Practice / │
│   Review / Roadmap / Progress│
└───────────────┬─────────────┘
                │ REST (localhost)
┌───────────────▼─────────────┐
│   FastAPI Backend            │
│                               │
│  routes/                     │
│   - learn.py                 │
│   - practice.py               │
│   - review.py                │
│   - progress.py               │
│   - roadmap.py                 │
│                               │
│  services/                   │
│   - learning_engine.py   (mastery, unlocks, daily plan)
│   - question_engine.py   (selection, generation, validation)
│   - revision_engine.py   (spaced repetition scheduling)
│   - llm/client.py         (OpenAI-compatible OmniRoute wrapper)
│   - rag/retriever.py      (Chroma query + prompt building)
│   - math_validator.py     (sympy checks)
└──────┬───────────┬──────────┘
       │           │
┌──────▼────┐  ┌───▼─────────┐
│  SQLite    │  │  ChromaDB   │
│ (progress, │  │ (concept    │
│  mistakes, │  │  knowledge, │
│  questions)│  │  embeddings)│
└────────────┘  └─────────────┘
       │
┌──────▼─────────────┐
│ content/ (JSON)     │
│ - roadmap.json      │
│ - curated Qs        │
└─────────────────────┘

Separately, run on-demand:
┌─────────────────────────────┐
│  scripts/ingest.py           │
│  (you run this manually)     │
│  fetch → clean → chunk →     │
│  embed → store in Chroma     │
└─────────────────────────────┘

┌───────────────────────────────┐
│  OmniRoute (AI Gateway proxy) │
│  (connects to OpenAI API      │
│  compatible models via :20128)│
└───────────────────────────────┘
┌─────────────────────────────┐
│  Ollama (for Embeddings)    │
│  nomic-embed-text             │
└─────────────────────────────┘
```

No scraper "service," no message queue, no background workers. Ingestion is a script you run when you want to add more source material — not infrastructure.

---

## 5. Folder Structure

```
aptitude-ai/
  frontend/
    app/
      page.tsx                # Home
      learn/page.tsx
      practice/page.tsx
      review/page.tsx
      roadmap/page.tsx
      progress/page.tsx
    components/
      ui/                      # shadcn components
      TodayMission.tsx
      ConceptCard.tsx
      QuestionCard.tsx
      RoadmapList.tsx
    lib/
      api.ts                   # fetch wrappers to backend

  backend/
    main.py
    routes/
      learn.py
      practice.py
      review.py
      progress.py
      roadmap.py
    services/
      learning_engine.py
      question_engine.py
      revision_engine.py
      math_validator.py
      llm/
        client.py
        prompts.py
      rag/
        retriever.py
        embed.py
    models/
      db.py                    # SQLite schema + connection
      schema.sql
    content/
      roadmap.json
      curated_questions/
        percentages.json
        ratios.json
        ...
    data/                       # gitignored — runtime state lives here
      aptitude.db
      chroma/
    scripts/
      ingest.py                 # manual knowledge ingestion
      seed_roadmap.py            # loads roadmap.json into SQLite on first run
    tests/
      test_math_validator.py
      test_learning_engine.py

  start.sh                      # starts ollama check, backend, frontend
  README.md
```

**Note on `data/`:** kept out of the repo entirely (gitignored). Source code and runtime state are cleanly separated so you can `git pull` updates without ever touching your own progress data.

---

## 6. Database Schema (SQLite)

Kept intentionally small — one user, no need for normalized multi-user tables.

```sql
-- topics: static-ish, seeded from roadmap.json
CREATE TABLE topics (
  id TEXT PRIMARY KEY,          -- e.g. "percentages"
  name TEXT NOT NULL,
  category TEXT NOT NULL,       -- Foundation / Intermediate / Advanced / Logical / ...
  prerequisites TEXT,           -- JSON array of topic ids
  order_index INTEGER
);

-- progress: one row per topic
CREATE TABLE progress (
  topic_id TEXT PRIMARY KEY REFERENCES topics(id),
  status TEXT NOT NULL DEFAULT 'locked',  -- locked / current / mastered
  mastery_score REAL DEFAULT 0,           -- 0.0–1.0, rolling accuracy
  attempts INTEGER DEFAULT 0,
  correct INTEGER DEFAULT 0,
  last_practiced_at TIMESTAMP
);

-- questions: both curated and generated end up here
CREATE TABLE questions (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  topic_id TEXT REFERENCES topics(id),
  source TEXT NOT NULL,          -- curated / generated / hybrid
  difficulty INTEGER NOT NULL,   -- 0–10 per the difficulty scale
  question_text TEXT NOT NULL,
  options TEXT,                  -- JSON array, null if not MCQ
  correct_answer TEXT NOT NULL,
  explanation TEXT,
  validated INTEGER DEFAULT 0,   -- 0/1
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- attempts: every time you answer something
CREATE TABLE attempts (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  question_id INTEGER REFERENCES questions(id),
  topic_id TEXT REFERENCES topics(id),
  was_correct INTEGER NOT NULL,
  time_taken_seconds INTEGER,
  answered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- mistakes: for the Review page, and revision scheduling
CREATE TABLE mistakes (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  question_id INTEGER REFERENCES questions(id),
  topic_id TEXT REFERENCES topics(id),
  mistake_count INTEGER DEFAULT 1,
  next_review_at TIMESTAMP,
  interval_days INTEGER DEFAULT 1,   -- grows via spaced repetition
  last_reviewed_at TIMESTAMP
);

-- daily_log: streak + daily mission tracking
CREATE TABLE daily_log (
  date TEXT PRIMARY KEY,          -- 'YYYY-MM-DD'
  learn_done INTEGER DEFAULT 0,
  practice_done INTEGER DEFAULT 0,
  review_done INTEGER DEFAULT 0,
  revision_done INTEGER DEFAULT 0
);
```

That's the whole schema. No users table, no sessions table.

---

## 7. Core Logic (deterministic, not LLM-decided)

### 7.1 Mastery / Unlock Rule

Simple and legible — you should always be able to explain to yourself why a topic unlocked:

```
mastery_score = weighted accuracy over last N attempts (N=15), 
                recent attempts weighted higher (exponential decay)

topic is "mastered" when:
  mastery_score >= 0.8  AND  attempts >= 10

next topic unlocks when:
  all prerequisites are "mastered"
```

Implemented in `services/learning_engine.py` as a pure function — no LLM call. Easy to tune later (e.g. raise the threshold to 0.85) without touching prompts.

### 7.2 Revision Scheduling (Spaced Repetition)

Fixed-interval schedule, adjusted on repeat mistakes:

```
Base intervals: 1, 3, 7, 15, 30, 90 days

On correct review:  move to next interval in the list
On wrong review:     reset to interval 1, increment mistake_count
```

This is simpler than full FSRS — appropriate here since you're not optimizing millions of review schedules, just your own. If it ever feels off, swapping in FSRS later is a contained change to `revision_engine.py` only.

### 7.3 Question Validation

Two paths, chosen by topic category:

**Deterministic topics** (arithmetic, percentages, ratios, algebra, basic geometry):
```
generate question (LLM) 
  → extract the numeric/symbolic answer 
  → verify independently with sympy 
  → accept only if they match, else regenerate (max 2 retries)
```

**Non-deterministic topics** (RC, verbal reasoning, assumptions/arguments, puzzles, seating arrangements):
```
generate question + answer + explanation (LLM)
  → ask the LLM a second time, blind (no prior answer shown), to solve it independently
  → accept if both attempts agree
  → if not, either regenerate once or fall back to a curated question instead
```

No compliance/rejection framework needed beyond this — good enough for personal use, and still meaningfully better than "trust the first LLM output blindly."

---

## 8. RAG Pipeline (simplified)

```
User opens a concept
   ↓
Query ChromaDB for top-k relevant chunks (topic + concept name)
   ↓
If relevant chunks found → include them in the prompt as grounding context
If nothing found → skip retrieval, let the LLM teach from its own knowledge
   ↓
Build prompt (system prompt + retrieved context + user's current mastery level)
   ↓
Call Ollama
   ↓
Stream response to frontend
```

No separate "ranking" or "citation" microservice — Chroma's built-in similarity search is enough at this scale (you'll have a knowledge base of maybe a few thousand chunks, not millions).

### Manual Ingestion (`scripts/ingest.py`)

Run this yourself, whenever you want to add source material:

```
Input: a list of URLs or local text/PDF files you provide
   ↓
Extract text (trafilatura for web pages, pypdf for PDFs)
   ↓
Clean + chunk (~300-500 tokens per chunk, simple sentence-aware splitter)
   ↓
Embed each chunk (nomic-embed-text via Ollama)
   ↓
Store in ChromaDB with metadata: {topic, source_url, difficulty_hint}
```

Since this is personal use, there's no source-allowlist logic, no robots.txt checker, no licensing filter built into the script — you decide what you feed it. Keep it to a simple `sources.txt` or `sources.json` file listing what to ingest, and re-run the script whenever you add more.

---

## 9. API Endpoints (minimal set)

```
GET  /home                     → today's mission, streak, day number
GET  /roadmap                  → full roadmap with per-topic status
GET  /learn/{topic_id}         → concept explanation (streamed), grounded via RAG
POST /practice/next            → next adaptive question for current topic
POST /practice/answer          → submit answer, get explanation, updates progress
GET  /review                   → mistakes grouped by topic, due-for-review count
POST /review/{mistake_id}/answer → same as practice/answer but updates revision_engine
GET  /progress                 → mastery %, weak topics, streak, questions solved
```

That's it — 8 endpoints cover the entire app. Resist the urge to add more surface area; every extra endpoint is something you have to maintain solo.

---

## 10. Prompting

Single system prompt, reused everywhere, with the retrieved context and current mastery level injected per-call:

```
You are a world-class aptitude teacher, teaching one specific student you know well.

Teach from first principles. Never assume prior knowledge unless the student's 
mastery data says otherwise.

Always explain step by step. Prefer understanding over memorization.

When teaching, use the grounding context below if provided — stay consistent with it,
but you may expand with your own reasoning and analogies.

When generating questions, think through the solution silently first, then verify it
before presenting the question — never present a question you haven't solved yourself.

Keep explanations concise but complete. No fluff, no filler encouragement, no emoji.

Student's current mastery on this topic: {mastery_score}
Grounding context: {retrieved_chunks or "none — use your own knowledge"}
```

One prompt file (`services/llm/prompts.py`), with small task-specific suffixes appended for "explain," "generate question," "generate hint," "analyze mistake." Not five different prompt architectures — one base + variations.

---

## 11. UI (unchanged in spirit from your original vision)

Keep exactly what you had — it was already right for personal use:

- **Home**: greeting, streak, day number, today's mission, one Continue button
- **Learn**: concept → explanation → example → guided question → mini quiz, one screen at a time
- **Practice**: one question, large font, keyboard shortcuts (1-4 for MCQ, Enter to submit/continue)
- **Review**: mistake list by topic, click to start revision
- **Roadmap**: vertical list, ✓ / current / locked
- **Progress**: mastery %, weak topics, questions solved, streak — nothing else

No changes needed here — this was already correctly scoped for a calm, single-user tool. Build it with shadcn's Card, Button, and Progress components; skip anything heavier.

---

## 12. Running It

`start.sh`:
```bash
#!/bin/bash
# Checks ollama is running, pulls models if missing, starts backend + frontend

ollama list | grep -q "qwen2.5:7b-instruct" || ollama pull qwen2.5:7b-instruct
ollama list | grep -q "nomic-embed-text" || ollama pull nomic-embed-text

(cd backend && uvicorn main:app --reload --port 8000) &
(cd frontend && npm run dev) &
wait
```

First-time setup also runs `scripts/seed_roadmap.py` once to populate `topics` from `content/roadmap.json`.

---

## 13. What Got Deliberately Left Out (vs. the original doc)

Cut because they add real engineering cost with no personal-use benefit — you can always add them back later if this stops being "just for me":

- Multi-source scraper service with scheduling, dedup, quality filtering pipeline → replaced with a manual ingestion script
- Recommendation Engine as a separate service from Learning Engine → merged, since the split was never clearly defined and one module is enough at this scale
- Bayesian Knowledge Tracing / IRT-based mastery → replaced with a simple, transparent rolling-accuracy rule (upgrade path stays open)
- FSRS spaced repetition → replaced with fixed-interval spaced repetition (also upgradeable later)
- Docker/CI/CD/monitoring → not needed for a machine only you run
- Source licensing/compliance filtering in the scraper → not needed since you've confirmed this is personal, non-distributed use
- Voice tutor, handwriting recognition, cross-device sync, plugin architecture (from "Future Features") → all removed from this build entirely; they imply either cloud infra or significant extra surface area that doesn't serve a single local user. Add back individually only if you actually miss one of them.

---

## 14. Build Order (suggested, for the coding agent)

1. Scaffold `backend/` — FastAPI skeleton, SQLite schema, seed roadmap from JSON
2. Scaffold `frontend/` — Next.js + Tailwind + shadcn, static Home/Roadmap pages against mock data
3. Wire up `llm/client.py` — confirm Ollama round-trip works with a trivial prompt
4. Build `learning_engine.py` — mastery scoring, unlock logic, daily plan (fully testable without LLM)
5. Build `question_engine.py` + `math_validator.py` — generation + validation for one deterministic topic (e.g. Percentages) end to end
6. Wire Practice page to real backend for that one topic
7. Build RAG: `ingest.py` for a handful of sources on that same topic, `retriever.py`, ground the Learn page
8. Extend to remaining topics once the pattern for one topic works fully
9. Build Review page + `revision_engine.py`
10. Build Progress page
11. Polish UI pass (spacing, typography, transitions) last, once everything works functionally

Get one topic (Percentages) working fully end-to-end — Learn, Practice, Review, Revision — before touching the rest of the roadmap. Everything after that is repetition of the same pattern across topics.
