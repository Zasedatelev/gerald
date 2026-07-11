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

-- ── СРЕЗЫ ─────────────────────────────────────

-- Сам срез
CREATE TABLE IF NOT EXISTS slices (
    id            SERIAL PRIMARY KEY,
    admin_id      INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    direction_id  INTEGER REFERENCES directions(id) ON DELETE SET NULL,
    title         VARCHAR(256) NOT NULL,
    password      VARCHAR(256) NOT NULL,       -- пароль для участия
    pass_percent  SMALLINT NOT NULL DEFAULT 60, -- проходной балл %
    duration_min  SMALLINT NOT NULL DEFAULT 30, -- длительность в минутах
    starts_at     TIMESTAMPTZ,                  -- NULL = старт сразу при создании
    ends_at       TIMESTAMPTZ NOT NULL,
    slice_type    VARCHAR(32) NOT NULL DEFAULT 'single', -- 'single'|'heraldry'|'coming_soon'
    created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Участники среза
CREATE TABLE IF NOT EXISTS slice_participants (
    id         SERIAL PRIMARY KEY,
    slice_id   INTEGER NOT NULL REFERENCES slices(id) ON DELETE CASCADE,
    user_id    INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    ticket_id  INTEGER REFERENCES tickets(id) ON DELETE SET NULL, -- выданный билет
    started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    finished_at TIMESTAMPTZ,                   -- NULL = ещё не завершил
    correct    SMALLINT,
    total      SMALLINT,
    tickets_json TEXT,                   -- JSON со списком билетов (для геральдики)
    UNIQUE (slice_id, user_id)
);

-- Ответы участников в срезе (для детального разбора)
CREATE TABLE IF NOT EXISTS slice_answers (
    id             SERIAL PRIMARY KEY,
    participant_id INTEGER NOT NULL REFERENCES slice_participants(id) ON DELETE CASCADE,
    question_id    INTEGER NOT NULL REFERENCES questions(id) ON DELETE CASCADE,
    answer_id      INTEGER REFERENCES answers(id) ON DELETE SET NULL, -- NULL = не ответил
    is_correct     BOOLEAN NOT NULL DEFAULT FALSE,
    answered_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_slices_admin    ON slices(admin_id);
CREATE INDEX IF NOT EXISTS idx_slice_parts     ON slice_participants(slice_id);
CREATE INDEX IF NOT EXISTS idx_slice_answers   ON slice_answers(participant_id);