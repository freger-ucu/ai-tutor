# Опис полів бенчмарків і датасетів Мрії

## Загальна інформація

- **Класи:** тільки 8 і 9
- **Предмети:** Українська мова (id=131), Алгебра (id=72), Історія України (id=107)
- **Навчальні роки:** 2024-2025, 2025-2026
- **Семестри:** 1, 2

---

## lms_questions_dev.parquet

**Кількість записів:** 141

- `question_id` (string): унікальний ідентифікатор питання
- `question_text` (string): текст питання
- `test_type` (string): тип питання (завжди `single_choice` у цьому датасеті)
- `description` (null): резервне поле, завжди порожнє
- `model` (string): джерело/метод формування питання (завжди `manual` у цьому датасеті)
- `source` (string): походження питання (завжди `imported_from_lms` у цьому датасеті)
- `global_discipline_name` (string): предмет (Українська мова, Алгебра або Історія України)
- `grade` (int64): клас (8 або 9)
- `answers` (list): варіанти відповіді у порядку A, B, C, D
- `correct_answer_indices` (list): індекси правильних відповідей (індексація з 0)

---

## toc_for_hackathon_with_subtopics.parquet

**Кількість записів:** 237 тем

- `book_id` (string): унікальний id підручника
- `book_filename` (string): ім'я файлу підручника
- `book_name` (string): назва підручника
- `grade` (int64): клас (8 або 9)
- `book_part` (float/nullable): частина підручника (завжди null у цьому датасеті)
- `section_title` (string): назва розділу
- `topic_title` (string): назва теми
- `topic_type` (string): тип теми (`theoretical` або `practical`)
- `topic_summary` (string): короткий зміст теми
- `subtopics` (list): список виділених підтем
- `topic_text` (string): текст теми
- `section_start_page` (int64): початкова сторінка розділу
- `section_end_page` (int64): кінцева сторінка розділу
- `topic_start_page` (float/nullable): початкова сторінка теми
- `topic_end_page` (float/nullable): кінцева сторінка теми
- `global_discipline_id` (int64): id предмету (72-Алгебра, 107-Історія України, 131-Українська мова)
- `global_discipline_name` (string): назва предмету (Українська мова, Алгебра або Історія України)
- `section_embedding` (list): ембедінг розділу
- `topic_embedding` (list): ембедінг теми
- `section_topic_embedding` (list): комбінований ембедінг
- `book_section_id` (string): id розділу в підручнику
- `book_topic_id` (string): id теми в підручнику
- `subtopics_with_text` (list): список виділених підтем з їх текстами `{name: string, text: string}`

---

## pages_for_hackathon.parquet

**Кількість записів:** 1,318 сторінок

- `book_id` (string): унікальний id підручника
- `book_filename` (string): ім'я файлу підручника
- `book_name` (string): назва підручника
- `grade` (int64): клас (8 або 9)
- `book_part` (float/nullable): частина підручника (завжди null у цьому датасеті)
- `page_filename` (string): ім'я файлу сторінки
- `page_number` (float): номер сторінки (внутрішній)
- `book_page_number` (int64): номер сторінки у книзі
- `section_title` (string): назва розділу
- `topic_title` (string): назва теми
- `page_text` (string): виділений текст сторінки (в маркдауні)

- `page_metadata` (struct): додаткові дані сторінки з 7 полів:
  - `book_page_number` (int64): номер сторінки у книзі
  - `contains_theory` (bool): чи містить сторінка теоретичний матеріал
  - `exercises` (numpy.ndarray): вправи на сторінці з текстами `{number: int, text: string}`
  - `exercises_count` (float): кількість вправ на сторінці
  - `images_count` (float): кількість зображень на сторінці
  - `is_table_of_contents` (bool): чи є сторінка змістом книги
  - `tables_count` (float): кількість таблиць на сторінці

- `global_discipline_id` (int64): id предмету (72-Алгебра, 107-Історія України, 131-Українська мова)
- `global_discipline_name` (string): назва предмету (Українська мова, Алгебра або Історія України)
- `page_text_embedding` (list): ембедінг сторінки
- `book_section_id` (string): id розділу
- `book_topic_id` (string): id теми

---

## benchmark_scores.parquet

**Кількість записів:** 1,030,823 оцінок

- `school_id` (int64): id школи
- `academic_year` (string): навчальний рік (`2024-2025` або `2025-2026`)
- `semester` (int64): семестр (1 або 2)
- `class_id` (int64): id класу
- `grade` (int64): клас (8 або 9)
- `discipline_name` (string): предмет
- `teacher_id` (int64): id вчителя
- `lesson_date` (string): дата уроку у форматі YYYY-MM-DD
- `score_text` (string): оцінка в текстовому вигляді
  - Значення: 1-12, Не оцінено, Зараховано, Не атестовано, Звільнено, Не зараховано
- `score_numeric` (int64): числова оцінка (0-12, де 0 відповідає нечисловим оцінкам - можна не враховувати)
- `is_final_score` (int64): 1 якщо підсумкова оцінка, 0 якщо поточна
- `topic_name` (string): тема уроку
- `lesson_number` (int64): номер уроку
- `student_id` (int64): id учня

---

## benchmark_absences.parquet

**Кількість записів:** 297,991 пропусків

- `school_id` (int64): id школи
- `academic_year` (string): навчальний рік (`2024-2025` або `2025-2026`)
- `semester` (int64): семестр (1 або 2)
- `class_id` (int64): id класу
- `grade` (int64): клас (8 або 9)
- `discipline_name` (string): предмет
- `teacher_id` (int64): id вчителя
- `lesson_date` (string): дата уроку у форматі YYYY-MM-DD
- `absence_reason` (string): причина пропуску. Через хворобу, Поважна причина, Не було на уроці
- `topic_name` (string): тема уроку
- `lesson_number` (int64): номер уроку
- `student_id` (int64): id учня
