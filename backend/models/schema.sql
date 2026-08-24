-- topics: static-ish, seeded from roadmap.json
CREATE TABLE IF NOT EXISTS topics (
  id TEXT PRIMARY KEY,          -- e.g. "percentages"
  name TEXT NOT NULL,
  category TEXT NOT NULL,       -- Foundation / Intermediate / Advanced / Logical / ...
  prerequisites TEXT,           -- JSON array of topic ids
  order_index INTEGER
);

-- progress: one row per topic
CREATE TABLE IF NOT EXISTS progress (
  topic_id TEXT PRIMARY KEY REFERENCES topics(id),
  status TEXT NOT NULL DEFAULT 'locked',  -- locked / current / mastered
  mastery_score REAL DEFAULT 0,           -- 0.0–1.0, rolling accuracy
  attempts INTEGER DEFAULT 0,
  correct INTEGER DEFAULT 0,
  last_practiced_at TIMESTAMP
);

-- questions: both curated and generated end up here
CREATE TABLE IF NOT EXISTS questions (
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
CREATE TABLE IF NOT EXISTS attempts (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  question_id INTEGER REFERENCES questions(id),
  topic_id TEXT REFERENCES topics(id),
  was_correct INTEGER NOT NULL,
  time_taken_seconds INTEGER,
  answered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- mistakes: for the Review page, and revision scheduling
CREATE TABLE IF NOT EXISTS mistakes (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  question_id INTEGER REFERENCES questions(id),
  topic_id TEXT REFERENCES topics(id),
  mistake_count INTEGER DEFAULT 1,
  next_review_at TIMESTAMP,
  interval_days INTEGER DEFAULT 1,   -- grows via spaced repetition
  last_reviewed_at TIMESTAMP
);

-- daily_log: streak + daily mission tracking
CREATE TABLE IF NOT EXISTS daily_log (
  date TEXT PRIMARY KEY,          -- 'YYYY-MM-DD'
  learn_done INTEGER DEFAULT 0,
  practice_done INTEGER DEFAULT 0,
  review_done INTEGER DEFAULT 0,
  revision_done INTEGER DEFAULT 0
);
