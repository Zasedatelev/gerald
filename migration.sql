-- ═══════════════════════════════════════════════════════════════
--  Quiz TMA — единая миграция: схема + начальные данные
--  psql quiz_tma < migration.sql
-- ═══════════════════════════════════════════════════════════════

-- ── СХЕМА ──────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS directions (
    id    SERIAL PRIMARY KEY,
    slug  VARCHAR(64)  UNIQUE NOT NULL,
    title VARCHAR(256) NOT NULL
);

CREATE TABLE IF NOT EXISTS tickets (
    id           SERIAL PRIMARY KEY,
    direction_id INTEGER  NOT NULL REFERENCES directions(id) ON DELETE CASCADE,
    number       SMALLINT NOT NULL,
    UNIQUE (direction_id, number)
);

CREATE TABLE IF NOT EXISTS questions (
    id        SERIAL PRIMARY KEY,
    ticket_id INTEGER  NOT NULL REFERENCES tickets(id) ON DELETE CASCADE,
    position  SMALLINT NOT NULL,
    text      TEXT     NOT NULL,
    UNIQUE (ticket_id, position)
);

CREATE TABLE IF NOT EXISTS answers (
    id          SERIAL  PRIMARY KEY,
    question_id INTEGER NOT NULL REFERENCES questions(id) ON DELETE CASCADE,
    text        TEXT    NOT NULL,
    is_correct  BOOLEAN NOT NULL DEFAULT FALSE
);

-- Гарантируем: от 2 до 5 вариантов на вопрос (проверяется триггером)
CREATE OR REPLACE FUNCTION check_answer_count() RETURNS TRIGGER AS $$
DECLARE cnt INTEGER;
BEGIN
  SELECT COUNT(*) INTO cnt FROM answers WHERE question_id = COALESCE(NEW.question_id, OLD.question_id);
  IF cnt < 2 OR cnt > 5 THEN
    RAISE EXCEPTION 'Вопрос % должен иметь от 2 до 5 вариантов ответа (сейчас %)',
      COALESCE(NEW.question_id, OLD.question_id), cnt;
  END IF;
  RETURN NULL;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_answer_count ON answers;
CREATE CONSTRAINT TRIGGER trg_answer_count
  AFTER INSERT OR UPDATE OR DELETE ON answers
  DEFERRABLE INITIALLY DEFERRED
  FOR EACH ROW EXECUTE FUNCTION check_answer_count();

CREATE TABLE IF NOT EXISTS users (
    id          SERIAL  PRIMARY KEY,
    telegram_id BIGINT  UNIQUE NOT NULL,
    password    VARCHAR(256) NOT NULL,   -- bcrypt hash
    created_at  TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS results (
    id           SERIAL  PRIMARY KEY,
    user_id      INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    direction_id INTEGER REFERENCES directions(id) ON DELETE SET NULL,
    ticket_id    INTEGER REFERENCES tickets(id)    ON DELETE SET NULL,
    mode         VARCHAR(32) NOT NULL,   -- 'ticket' | 'all' | 'exam'
    correct      SMALLINT    NOT NULL,
    total        SMALLINT    NOT NULL,
    finished_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_results_user     ON results(user_id);
CREATE INDEX IF NOT EXISTS idx_results_user_dir ON results(user_id, direction_id);

-- ── НАПРАВЛЕНИЯ ────────────────────────────────────────────────

INSERT INTO directions (slug, title) VALUES
  ('legal',     'Правовая подготовка'),
  ('political', 'Политическая подготовка'),
  ('fire',      'Огневая подготовка'),
  ('tactical',  'Тактико-специальная подготовка')
ON CONFLICT (slug) DO UPDATE SET title = EXCLUDED.title;

-- ── ВСПОМОГАТЕЛЬНАЯ ФУНКЦИЯ для вставки вопросов ───────────────
-- Используем DO-блок: создаём билеты 1-10 для каждого направления
-- и вставляем по 5 вопросов в каждый.
-- ⚠️  ЗАМЕНИТЕ тексты вопросов и ответов на реальные!

DO $$
DECLARE
  v_dir  INTEGER;
  v_tkt  INTEGER;
  v_q    INTEGER;
BEGIN

-- ══════════════════════════════════════════════════════════════
-- ПРАВОВАЯ ПОДГОТОВКА
-- ══════════════════════════════════════════════════════════════
SELECT id INTO v_dir FROM directions WHERE slug='legal';

-- Билет 1
INSERT INTO tickets (direction_id,number) VALUES (v_dir,1)
  ON CONFLICT (direction_id,number) DO UPDATE SET number=EXCLUDED.number RETURNING id INTO v_tkt;

INSERT INTO questions (ticket_id,position,text) VALUES (v_tkt,1,'Какой документ является основным законом Российской Федерации?') RETURNING id INTO v_q;
INSERT INTO answers (question_id,text,is_correct) VALUES (v_q,'Гражданский кодекс РФ',false),(v_q,'Конституция РФ',true),(v_q,'Уголовный кодекс РФ',false),(v_q,'Трудовой кодекс РФ',false);

INSERT INTO questions (ticket_id,position,text) VALUES (v_tkt,2,'С какого возраста наступает уголовная ответственность в общем порядке?') RETURNING id INTO v_q;
INSERT INTO answers (question_id,text,is_correct) VALUES (v_q,'14 лет',false),(v_q,'16 лет',true),(v_q,'18 лет',false),(v_q,'21 год',false);

INSERT INTO questions (ticket_id,position,text) VALUES (v_tkt,3,'Что такое презумпция невиновности?') RETURNING id INTO v_q;
INSERT INTO answers (question_id,text,is_correct) VALUES (v_q,'Право на адвоката',false),(v_q,'Обвиняемый считается невиновным до вступления приговора в законную силу',true),(v_q,'Запрет повторного привлечения к суду',false),(v_q,'Право хранить молчание',false);

INSERT INTO questions (ticket_id,position,text) VALUES (v_tkt,4,'На сколько лет избирается Президент РФ?') RETURNING id INTO v_q;
INSERT INTO answers (question_id,text,is_correct) VALUES (v_q,'4 года',false),(v_q,'5 лет',false),(v_q,'6 лет',true),(v_q,'7 лет',false);

INSERT INTO questions (ticket_id,position,text) VALUES (v_tkt,5,'Кто является высшим должностным лицом субъекта РФ?') RETURNING id INTO v_q;
INSERT INTO answers (question_id,text,is_correct) VALUES (v_q,'Мэр',false),(v_q,'Губернатор (Глава региона)',true),(v_q,'Спикер Законодательного собрания',false),(v_q,'Прокурор субъекта',false);

-- Билет 2
INSERT INTO tickets (direction_id,number) VALUES (v_dir,2)
  ON CONFLICT (direction_id,number) DO UPDATE SET number=EXCLUDED.number RETURNING id INTO v_tkt;

INSERT INTO questions (ticket_id,position,text) VALUES (v_tkt,1,'Какой орган осуществляет конституционный контроль в России?') RETURNING id INTO v_q;
INSERT INTO answers (question_id,text,is_correct) VALUES (v_q,'Верховный суд',false),(v_q,'Конституционный суд',true),(v_q,'Генеральная прокуратура',false),(v_q,'Совет Федерации',false);

INSERT INTO questions (ticket_id,position,text) VALUES (v_tkt,2,'Что такое правоспособность?') RETURNING id INTO v_q;
INSERT INTO answers (question_id,text,is_correct) VALUES (v_q,'Способность нести юридическую ответственность',false),(v_q,'Способность иметь права и обязанности',true),(v_q,'Способность самостоятельно осуществлять права',false),(v_q,'Способность заключать договоры',false);

INSERT INTO questions (ticket_id,position,text) VALUES (v_tkt,3,'Сколько глав в Конституции РФ?') RETURNING id INTO v_q;
INSERT INTO answers (question_id,text,is_correct) VALUES (v_q,'7',false),(v_q,'9',true),(v_q,'11',false),(v_q,'12',false);

INSERT INTO questions (ticket_id,position,text) VALUES (v_tkt,4,'Какой срок исковой давности установлен по общему правилу?') RETURNING id INTO v_q;
INSERT INTO answers (question_id,text,is_correct) VALUES (v_q,'1 год',false),(v_q,'2 года',false),(v_q,'3 года',true),(v_q,'5 лет',false);

INSERT INTO questions (ticket_id,position,text) VALUES (v_tkt,5,'Что такое дееспособность?') RETURNING id INTO v_q;
INSERT INTO answers (question_id,text,is_correct) VALUES (v_q,'Право иметь имущество',false),(v_q,'Способность иметь права',false),(v_q,'Способность своими действиями приобретать и осуществлять права',true),(v_q,'Способность быть истцом в суде',false);

-- Билеты 3-10 правовой подготовки
-- ⚠️  ВСТАВЬТЕ РЕАЛЬНЫЕ ВОПРОСЫ — ниже заглушки

DO_BLOCK_LEGAL_STUBS:
FOR i IN 3..10 LOOP
  INSERT INTO tickets (direction_id,number) VALUES (v_dir,i)
    ON CONFLICT (direction_id,number) DO UPDATE SET number=EXCLUDED.number RETURNING id INTO v_tkt;
  FOR j IN 1..5 LOOP
    INSERT INTO questions (ticket_id,position,text) VALUES (v_tkt,j,
      FORMAT('[ПРАВОВАЯ] Билет %s, вопрос %s — замените реальным вопросом', i, j)) RETURNING id INTO v_q;
    INSERT INTO answers (question_id,text,is_correct) VALUES
      (v_q,'Вариант А',false),(v_q,'Вариант Б — правильный',true),(v_q,'Вариант В',false),(v_q,'Вариант Г',false);
  END LOOP;
END LOOP DO_BLOCK_LEGAL_STUBS;

-- ══════════════════════════════════════════════════════════════
-- ПОЛИТИЧЕСКАЯ ПОДГОТОВКА
-- ══════════════════════════════════════════════════════════════
SELECT id INTO v_dir FROM directions WHERE slug='political';

-- Билет 1
INSERT INTO tickets (direction_id,number) VALUES (v_dir,1)
  ON CONFLICT (direction_id,number) DO UPDATE SET number=EXCLUDED.number RETURNING id INTO v_tkt;

INSERT INTO questions (ticket_id,position,text) VALUES (v_tkt,1,'Какая форма правления установлена в России?') RETURNING id INTO v_q;
INSERT INTO answers (question_id,text,is_correct) VALUES (v_q,'Парламентская республика',false),(v_q,'Президентская республика',false),(v_q,'Конституционная монархия',false),(v_q,'Смешанная (президентско-парламентская) республика',true);

INSERT INTO questions (ticket_id,position,text) VALUES (v_tkt,2,'Что такое государственный суверенитет?') RETURNING id INTO v_q;
INSERT INTO answers (question_id,text,is_correct) VALUES (v_q,'Независимость и верховенство государственной власти',true),(v_q,'Право граждан на самоуправление',false),(v_q,'Система органов власти',false),(v_q,'Форма правления',false);

INSERT INTO questions (ticket_id,position,text) VALUES (v_tkt,3,'Что означает принцип разделения властей?') RETURNING id INTO v_q;
INSERT INTO answers (question_id,text,is_correct) VALUES (v_q,'Деление страны на субъекты',false),(v_q,'Разграничение полномочий между законодательной, исполнительной и судебной ветвями',true),(v_q,'Федеративное устройство',false),(v_q,'Местное самоуправление',false);

INSERT INTO questions (ticket_id,position,text) VALUES (v_tkt,4,'Какой орган является высшим исполнительным органом РФ?') RETURNING id INTO v_q;
INSERT INTO answers (question_id,text,is_correct) VALUES (v_q,'Администрация Президента',false),(v_q,'Государственная Дума',false),(v_q,'Правительство Российской Федерации',true),(v_q,'Совет Безопасности',false);

INSERT INTO questions (ticket_id,position,text) VALUES (v_tkt,5,'Что такое политическая партия?') RETURNING id INTO v_q;
INSERT INTO answers (question_id,text,is_correct) VALUES (v_q,'Государственный орган',false),(v_q,'Объединение граждан для участия в политической жизни',true),(v_q,'Профессиональный союз',false),(v_q,'Религиозная организация',false);

-- Билеты 2-10 политической подготовки (заглушки)
FOR i IN 2..10 LOOP
  INSERT INTO tickets (direction_id,number) VALUES (v_dir,i)
    ON CONFLICT (direction_id,number) DO UPDATE SET number=EXCLUDED.number RETURNING id INTO v_tkt;
  FOR j IN 1..5 LOOP
    INSERT INTO questions (ticket_id,position,text) VALUES (v_tkt,j,
      FORMAT('[ПОЛИТИКА] Билет %s, вопрос %s — замените реальным вопросом', i, j)) RETURNING id INTO v_q;
    INSERT INTO answers (question_id,text,is_correct) VALUES
      (v_q,'Вариант А',false),(v_q,'Вариант Б — правильный',true),(v_q,'Вариант В',false),(v_q,'Вариант Г',false);
  END LOOP;
END LOOP;

-- ══════════════════════════════════════════════════════════════
-- ОГНЕВАЯ ПОДГОТОВКА
-- ══════════════════════════════════════════════════════════════
SELECT id INTO v_dir FROM directions WHERE slug='fire';

-- Билет 1
INSERT INTO tickets (direction_id,number) VALUES (v_dir,1)
  ON CONFLICT (direction_id,number) DO UPDATE SET number=EXCLUDED.number RETURNING id INTO v_tkt;

INSERT INTO questions (ticket_id,position,text) VALUES (v_tkt,1,'Что необходимо сделать перед началом стрельбы в первую очередь?') RETURNING id INTO v_q;
INSERT INTO answers (question_id,text,is_correct) VALUES (v_q,'Зарядить оружие',false),(v_q,'Убедиться в исправности оружия и безопасности направления стрельбы',true),(v_q,'Снять с предохранителя',false),(v_q,'Принять изготовку',false);

INSERT INTO questions (ticket_id,position,text) VALUES (v_tkt,2,'Что такое прицельная линия?') RETURNING id INTO v_q;
INSERT INTO answers (question_id,text,is_correct) VALUES (v_q,'Направление ствола оружия',false),(v_q,'Линия, проходящая через прорезь прицела и вершину мушки',true),(v_q,'Линия от глаза стрелка до цели',false),(v_q,'Ось канала ствола',false);

INSERT INTO questions (ticket_id,position,text) VALUES (v_tkt,3,'Что называется настильностью траектории?') RETURNING id INTO v_q;
INSERT INTO answers (question_id,text,is_correct) VALUES (v_q,'Дальность полёта пули',false),(v_q,'Степень пологости траектории пули',true),(v_q,'Начальная скорость пули',false),(v_q,'Угол возвышения ствола',false);

INSERT INTO questions (ticket_id,position,text) VALUES (v_tkt,4,'Какое действие выполняется при осечке?') RETURNING id INTO v_q;
INSERT INTO answers (question_id,text,is_correct) VALUES (v_q,'Немедленно разрядить оружие',false),(v_q,'Выждать 15 секунд, затем извлечь патрон',true),(v_q,'Перезарядить оружие',false),(v_q,'Повторно нажать на спуск',false);

INSERT INTO questions (ticket_id,position,text) VALUES (v_tkt,5,'Что такое боевая скорострельность?') RETURNING id INTO v_q;
INSERT INTO answers (question_id,text,is_correct) VALUES (v_q,'Максимальное количество выстрелов в минуту',false),(v_q,'Количество выстрелов в минуту с учётом прицеливания и смены магазина',true),(v_q,'Начальная скорость пули',false),(v_q,'Темп автоматической стрельбы',false);

-- Билеты 2-10 огневой подготовки (заглушки)
FOR i IN 2..10 LOOP
  INSERT INTO tickets (direction_id,number) VALUES (v_dir,i)
    ON CONFLICT (direction_id,number) DO UPDATE SET number=EXCLUDED.number RETURNING id INTO v_tkt;
  FOR j IN 1..5 LOOP
    INSERT INTO questions (ticket_id,position,text) VALUES (v_tkt,j,
      FORMAT('[ОГНЕВАЯ] Билет %s, вопрос %s — замените реальным вопросом', i, j)) RETURNING id INTO v_q;
    INSERT INTO answers (question_id,text,is_correct) VALUES
      (v_q,'Вариант А',false),(v_q,'Вариант Б — правильный',true),(v_q,'Вариант В',false),(v_q,'Вариант Г',false);
  END LOOP;
END LOOP;

-- ══════════════════════════════════════════════════════════════
-- ТАКТИКО-СПЕЦИАЛЬНАЯ ПОДГОТОВКА
-- ══════════════════════════════════════════════════════════════
SELECT id INTO v_dir FROM directions WHERE slug='tactical';

-- Билет 1
INSERT INTO tickets (direction_id,number) VALUES (v_dir,1)
  ON CONFLICT (direction_id,number) DO UPDATE SET number=EXCLUDED.number RETURNING id INTO v_tkt;

INSERT INTO questions (ticket_id,position,text) VALUES (v_tkt,1,'Что такое боевой порядок?') RETURNING id INTO v_q;
INSERT INTO answers (question_id,text,is_correct) VALUES (v_q,'Список личного состава',false),(v_q,'Построение подразделения для выполнения боевой задачи',true),(v_q,'Приказ командира',false),(v_q,'Маршрут движения',false);

INSERT INTO questions (ticket_id,position,text) VALUES (v_tkt,2,'Что понимается под маскировкой?') RETURNING id INTO v_q;
INSERT INTO answers (question_id,text,is_correct) VALUES (v_q,'Смена позиции',false),(v_q,'Комплекс мероприятий по скрытию от противника',true),(v_q,'Только дымовая завеса',false),(v_q,'Передвижение ночью',false);

INSERT INTO questions (ticket_id,position,text) VALUES (v_tkt,3,'Что такое огневая позиция?') RETURNING id INTO v_q;
INSERT INTO answers (question_id,text,is_correct) VALUES (v_q,'Место хранения боеприпасов',false),(v_q,'Место, занимаемое для ведения огня',true),(v_q,'Позиция командира',false),(v_q,'Место отдыха личного состава',false);

INSERT INTO questions (ticket_id,position,text) VALUES (v_tkt,4,'Что означает термин «фланг» применительно к подразделению?') RETURNING id INTO v_q;
INSERT INTO answers (question_id,text,is_correct) VALUES (v_q,'Тыловая часть подразделения',false),(v_q,'Правая или левая оконечность боевого порядка',true),(v_q,'Авангард подразделения',false),(v_q,'Командный пункт',false);

INSERT INTO questions (ticket_id,position,text) VALUES (v_tkt,5,'Что такое дозор в тактике?') RETURNING id INTO v_q;
INSERT INTO answers (question_id,text,is_correct) VALUES (v_q,'Группа обеспечения тыла',false),(v_q,'Небольшое подразделение для разведки и охранения',true),(v_q,'Резерв командира',false),(v_q,'Огневая группа',false);

-- Билеты 2-10 тактической подготовки (заглушки)
FOR i IN 2..10 LOOP
  INSERT INTO tickets (direction_id,number) VALUES (v_dir,i)
    ON CONFLICT (direction_id,number) DO UPDATE SET number=EXCLUDED.number RETURNING id INTO v_tkt;
  FOR j IN 1..5 LOOP
    INSERT INTO questions (ticket_id,position,text) VALUES (v_tkt,j,
      FORMAT('[ТАКТИКА] Билет %s, вопрос %s — замените реальным вопросом', i, j)) RETURNING id INTO v_q;
    INSERT INTO answers (question_id,text,is_correct) VALUES
      (v_q,'Вариант А',false),(v_q,'Вариант Б — правильный',true),(v_q,'Вариант В',false),(v_q,'Вариант Г',false);
  END LOOP;
END LOOP;

END $$;
