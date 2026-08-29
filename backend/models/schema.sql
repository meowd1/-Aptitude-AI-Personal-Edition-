-- topics
CREATE TABLE IF NOT EXISTS topics (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  category TEXT NOT NULL
);

-- progress
CREATE TABLE IF NOT EXISTS progress (
  topic_id TEXT PRIMARY KEY REFERENCES topics(id),
  mastery_score REAL DEFAULT 0.0,
  status TEXT DEFAULT 'locked'
);

-- reasoning_ratings: per-topic and overall Elo-style rating
CREATE TABLE IF NOT EXISTS reasoning_ratings (
  topic_id TEXT,                  -- NULL row = overall rating
  rating INTEGER NOT NULL DEFAULT 1000,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (topic_id)
);

-- book_sources: which book/chapter a question or explanation was grounded in
CREATE TABLE IF NOT EXISTS book_sources (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  book TEXT NOT NULL,             -- 'aptitude_math' | 'puzzles'
  chapter TEXT,
  page_number INTEGER,
  topic_id TEXT REFERENCES topics(id)
);

-- questions table
CREATE TABLE IF NOT EXISTS questions (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  topic_id TEXT NOT NULL REFERENCES topics(id),
  difficulty INTEGER NOT NULL,
  question_text TEXT NOT NULL,
  options TEXT NOT NULL, -- JSON array
  correct_answer TEXT NOT NULL,
  explanation TEXT NOT NULL,
  book_source_id INTEGER REFERENCES book_sources(id)
);

-- lesson_sessions: for LangGraph checkpoint cross-reference / daily summary
CREATE TABLE IF NOT EXISTS lesson_sessions (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  date TEXT NOT NULL,
  stage TEXT NOT NULL,
  completed INTEGER DEFAULT 0,
  rating_delta INTEGER DEFAULT 0,
  started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  ended_at TIMESTAMP
);

-- attempts table
CREATE TABLE IF NOT EXISTS attempts (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  question_id INTEGER NOT NULL REFERENCES questions(id),
  is_correct BOOLEAN NOT NULL,
  time_taken_ms INTEGER NOT NULL,
  used_hint BOOLEAN NOT NULL DEFAULT 0,
  timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- mistakes table
CREATE TABLE IF NOT EXISTS mistakes (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  question_id INTEGER NOT NULL REFERENCES questions(id),
  user_answer TEXT NOT NULL,
  mistake_category TEXT,
  resolved BOOLEAN DEFAULT 0,
  timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- daily_log
CREATE TABLE IF NOT EXISTS daily_log (
  date TEXT PRIMARY KEY,
  questions_solved INTEGER DEFAULT 0,
  streak_active BOOLEAN DEFAULT 0
);
