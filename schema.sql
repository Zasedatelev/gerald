-- ═══════════════════════════════════════════════
--  Quiz TMA — схема базы данных PostgreSQL
-- ═══════════════════════════════════════════════

-- Направления тестов
CREATE TABLE IF NOT EXISTS directions (
    id      SERIAL PRIMARY KEY,
    slug    VARCHAR(64) UNIQUE NOT NULL,   -- 'legal', 'political', 'fire', 'tactical'
    title   VARCHAR(256) NOT NULL
);

-- Билеты (10 на направление)
CREATE TABLE IF NOT EXISTS tickets (
    id           SERIAL PRIMARY KEY,
    direction_id INTEGER NOT NULL REFERENCES directions(id) ON DELETE CASCADE,
    number       SMALLINT NOT NULL,        -- 1..10
    UNIQUE (direction_id, number)
);

-- Вопросы (5 на билет)
CREATE TABLE IF NOT EXISTS questions (
    id        SERIAL PRIMARY KEY,
    ticket_id INTEGER NOT NULL REFERENCES tickets(id) ON DELETE CASCADE,
    position  SMALLINT NOT NULL,           -- 1..5
    text      TEXT NOT NULL,
    UNIQUE (ticket_id, position)
);

-- Варианты ответов (4 на вопрос, один правильный)
CREATE TABLE IF NOT EXISTS answers (
    id          SERIAL PRIMARY KEY,
    question_id INTEGER NOT NULL REFERENCES questions(id) ON DELETE CASCADE,
    text        TEXT NOT NULL,
    is_correct  BOOLEAN NOT NULL DEFAULT FALSE
);

-- Пользователи (авторизация по telegram_id + пароль)
CREATE TABLE IF NOT EXISTS users (
    id          SERIAL PRIMARY KEY,
    telegram_id BIGINT UNIQUE NOT NULL,
    password    VARCHAR(256) NOT NULL,    -- bcrypt hash
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Результаты тестирования
CREATE TABLE IF NOT EXISTS results (
    id           SERIAL PRIMARY KEY,
    user_id      INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    direction_id INTEGER REFERENCES directions(id) ON DELETE SET NULL,  -- NULL = экзамен
    ticket_id    INTEGER REFERENCES tickets(id) ON DELETE SET NULL,     -- NULL = экзамен или «все»
    mode         VARCHAR(32) NOT NULL,  -- 'ticket' | 'all' | 'exam'
    correct      SMALLINT NOT NULL,
    total        SMALLINT NOT NULL,
    finished_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_results_user ON results(user_id);
CREATE INDEX IF NOT EXISTS idx_results_user_dir ON results(user_id, direction_id);
