# API Contracts Documentation

This document provides complete endpoint contracts with request/response schemas and JSON examples.

**Base URL:** `/api/v1`

---

## Table of Contents

- [Teacher Endpoints](#teacher-endpoints)
  - [EP1: Get Teacher Classes](#ep1-get-teacher-classes)
  - [EP2: Get Student List](#ep2-get-student-list)
  - [EP3.1: Generate Notes by Level](#ep31-generate-notes-by-level)
  - [EP3.2: Generate Notes Individual](#ep32-generate-notes-individual)
  - [EP4: Generate Test](#ep4-generate-test)
  - [EP5: Get Student Details](#ep5-get-student-details)
  - [EP6: Get Student Recommendation](#ep6-get-student-recommendation)
- [Student Endpoints](#student-endpoints)
  - [EP8: Get Student Info](#ep8-get-student-info)
  - [EP9: Check Open Answer](#ep9-check-open-answer)
  - [EP10: Get Test Feedback](#ep10-get-test-feedback)
- [Health Endpoints](#health-endpoints)
- [Enums Reference](#enums-reference)

---

## Teacher Endpoints

### EP1: Get Teacher Classes

Retrieves all classes and subjects taught by a teacher.

**Endpoint:** `GET /teacher/{teacher_id}`

**Path Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| teacher_id | integer | Yes | Teacher's unique identifier |

**Response:** `TeacherClassesResponse`

```json
{
  "classes": [
    {
      "class_id": 101,
      "class_number": 8,
      "subject": "Алгебра"
    },
    {
      "class_id": 102,
      "class_number": 9,
      "subject": "Українська мова"
    }
  ]
}
```

**Error Responses:**
- `404`: Teacher not found

---

### EP2: Get Student List

Retrieves students in a class with their performance levels.

**Endpoint:** `POST /teacher/students`

**Request Body:** `GetStudentListRequest`

```json
{
  "class_id": 101,
  "teacher_id": 1,
  "subject": "Алгебра"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| class_id | integer | Yes | Class identifier |
| teacher_id | integer | Yes | Teacher identifier |
| subject | string | Yes | Subject name in Ukrainian |

**Response:** `StudentListResponse`

```json
{
  "students": [
    {
      "student_id": 1001,
      "subject_level": "strong",
      "average_subject_grade": 10.5
    },
    {
      "student_id": 1002,
      "subject_level": "medium",
      "average_subject_grade": 7.8
    },
    {
      "student_id": 1003,
      "subject_level": "weak",
      "average_subject_grade": 4.2
    }
  ]
}
```

**Error Responses:**
- `404`: No students found for this class/subject combination

---

### EP3.1: Generate Notes by Level

Generates lesson notes adapted to student ability levels with prerequisite-aware recap.

The flow internally:
1. Analyzes students to compute performance level and knowledge gaps
2. Uses LLM to filter which gaps are prerequisites for the topic
3. Retrieves RAG context for both the main topic and prerequisites
4. Generates notes with optional recap section for missed prerequisites

**Endpoint:** `POST /teacher/notes/by-level`

**Request Body:** `GenerateLevelNotesRequest`

```json
{
  "class_id": 101,
  "teacher_id": 1,
  "subject": "Алгебра",
  "level_list": ["weak", "medium"],
  "topic_definition": "Квадратні рівняння та їх розв'язання"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| class_id | integer | Yes | Class identifier |
| teacher_id | integer | Yes | Teacher identifier |
| subject | string | Yes | Subject name in Ukrainian |
| level_list | array[Level] | Yes | Target levels: "weak", "medium", "strong" |
| topic_definition | string | Yes | Topic description |

**Response:** `NotesResponse`

```json
{
  "title": "Квадратні рівняння: основи та методи розв'язання",
  "contents": "## Що таке квадратне рівняння?\n\nКвадратне рівняння — це рівняння виду ax² + bx + c = 0...\n\n## Формула дискримінанта\n\nD = b² - 4ac\n\n...",
  "teacher_notes": "Зверніть увагу: 3 учні пропустили тему 'Дискримінант'. Рекомендується повторити формулу на початку уроку.",
  "sources": [
    "Істер, Розділ 3, с. 45",
    "Істер, Розділ 3, с. 47"
  ],
  "statistics": {
    "total_students": 8,
    "weak_topics": [
      {
        "topic": "Дискримінант",
        "count": 4,
        "avg_score": 4.5
      }
    ],
    "skipped_topics": [
      {
        "topic": "Формули коренів",
        "count": 2
      }
    ]
  }
}
```

---

### EP3.2: Generate Notes Individual

Generates personalized notes for specific students with prerequisite-aware recap.

Uses the same internal flow as EP3.1, but targets specific students instead of level groups.

**Endpoint:** `POST /teacher/notes/individual`

**Request Body:** `GenerateIndividualNotesRequest`

```json
{
  "class_id": 101,
  "teacher_id": 1,
  "subject": "Алгебра",
  "student_list": [1001, 1003, 1005],
  "topic_definition": "Квадратні рівняння та їх розв'язання"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| class_id | integer | Yes | Class identifier |
| teacher_id | integer | Yes | Teacher identifier |
| subject | string | Yes | Subject name in Ukrainian |
| student_list | array[integer] | Yes | Student IDs to generate for |
| topic_definition | string | Yes | Topic description |

**Response:** `NotesResponse` (same structure as EP3.1)

**Error Responses:**
- `400`: student_list cannot be empty
- `404`: Class not found / No valid students found in class

---

### EP4: Generate Test

Generates validated test questions using a planning-based parallel architecture. The flow first plans the test structure, then generates and validates questions in parallel with automatic retry for failed questions.

**Endpoint:** `POST /teacher/generate-test`

**Request Body:** `GenerateTestRequest`

```json
{
  "class_id": 101,
  "teacher_id": 1,
  "subject": "Алгебра",
  "topic_definition": "Квадратні рівняння",
  "easy_count": 3,
  "medium_count": 4,
  "hard_count": 3
}
```

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| class_id | integer | Yes | - | Class identifier |
| teacher_id | integer | Yes | - | Teacher identifier |
| subject | string | Yes | - | Subject name in Ukrainian |
| topic_definition | string | Yes | - | Topic description |
| easy_count | integer | No | 1 | Number of easy questions (0-20) |
| medium_count | integer | No | 1 | Number of medium questions (0-20) |
| hard_count | integer | No | 1 | Number of hard questions (0-20) |

**Response:** `TestResponse`

```json
{
  "success": true,
  "message": "Generated 10 questions",
  "questions": [
    {
      "question": "Яке значення дискримінанта рівняння x² - 4x + 4 = 0?",
      "type": "single_choice",
      "difficulty": "easy",
      "options": ["0", "4", "8", "-4"],
      "correct_answer_index": 0,
      "explanation": "D = b² - 4ac = (-4)² - 4(1)(4) = 16 - 16 = 0",
      "topic": "Дискримінант"
    },
    {
      "question": "Які корені має рівняння x² - 5x + 6 = 0?",
      "type": "multiple_choice",
      "difficulty": "medium",
      "options": ["x = 2", "x = 3", "x = 4", "x = 6"],
      "correct_answer_indices": [0, 1],
      "explanation": "D = 25 - 24 = 1. x₁ = 3, x₂ = 2",
      "topic": "Квадратні рівняння"
    },
    {
      "question": "Розв'яжіть рівняння: x² - 7x + 12 = 0",
      "type": "open",
      "difficulty": "medium",
      "correct_answer": "x = 3 або x = 4",
      "explanation": "D = 49 - 48 = 1. x₁ = (7+1)/2 = 4, x₂ = (7-1)/2 = 3",
      "topic": "Квадратні рівняння"
    }
  ],
  "stats": {
    "total_questions": 10,
    "easy_count": 3,
    "medium_count": 4,
    "hard_count": 3,
    "single_choice_count": 5,
    "multiple_choice_count": 3,
    "open_count": 2,
    "llm_calls": 21
  }
}
```

**Question Types:**

| Type | Fields | Description |
|------|--------|-------------|
| single_choice | options (4), correct_answer_index | Exactly one correct answer |
| multiple_choice | options (4), correct_answer_indices | One or more correct answers |
| open | correct_answer | Free-text answer expected |

**Error Responses:**
- `400`: At least one question count must be > 0
- `404`: Class not found

---

### EP5: Get Student Details

Retrieves detailed performance data for a specific student.

**Endpoint:** `POST /teacher/student/details`

**Request Body:** `StudentDetailsRequest`

```json
{
  "class_id": 101,
  "subject": "Алгебра",
  "teacher_id": 1,
  "student_id": 1001
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| class_id | integer | Yes | Class identifier |
| subject | string | Yes | Subject name in Ukrainian |
| teacher_id | integer | Yes | Teacher identifier |
| student_id | integer | Yes | Student identifier |

**Response:** `StudentDetailsResponse`

```json
{
  "average_subject_grade": 7.5,
  "level": "medium",
  "skipped_lessons": [
    {
      "date": "2025-09-15",
      "topic": "Дискримінант"
    },
    {
      "date": "2025-09-22",
      "topic": "Теорема Вієта"
    }
  ],
  "problematic_topics": [
    {
      "topic": "Квадратні нерівності",
      "average_score": 4.5
    },
    {
      "topic": "Системи рівнянь",
      "average_score": 5.0
    }
  ]
}
```

**Error Responses:**
- `404`: Student not found in this class/subject

---

### EP6: Get Student Recommendation

Generates AI-powered recommendation for a student. Uses LangGraph flow with concise, factual output style (no greetings, no addressing teacher directly).

**Endpoint:** `POST /teacher/student/recommendation`

**Request Body:** `StudentRecommendationRequest`

```json
{
  "student_id": 1001,
  "subject": "Алгебра"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| student_id | integer | Yes | Student identifier |
| subject | string | Yes | Subject name in Ukrainian |

**Response:** `RecommendationResponse`

```json
{
  "feedback": "Середній бал 7.5 (рівень: середній).\n\nСильні теми: Лінійні рівняння, Графіки функцій.\n\nПроблемні теми: Квадратні нерівності (4.5), Системи рівнянь (5.0).\n\nРекомендації:\n1. Індивідуальна робота над квадратними нерівностями\n2. Повторення пропущеного матеріалу: Дискримінант, Теорема Вієта\n3. Додаткові завдання на системи рівнянь"
}
```

**Output Style:**
- Concise and factual (Ukrainian language)
- No greetings, no addressing teacher ("Шановний вчителю"), no goodbyes
- Maximum 2-3 short paragraphs
- Concrete recommendations based on student data

**Error Responses:**
- `404`: Student not found or does not have this subject

---

## Student Endpoints

### EP8: Get Student Info

Retrieves student's class and subjects with performance levels.

**Endpoint:** `GET /student/{student_id}`

**Path Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| student_id | integer | Yes | Student's unique identifier |

**Response:** `StudentDataResponse`

```json
{
  "class_id": 101,
  "class_number": 9,
  "subjects": [
    {
      "subject": "Алгебра",
      "level": "medium"
    },
    {
      "subject": "Українська мова",
      "level": "strong"
    },
    {
      "subject": "Історія України",
      "level": "weak"
    }
  ]
}
```

**SubjectLevelResponse Schema:**
| Field | Type | Description |
|-------|------|-------------|
| subject | string | Subject name in Ukrainian |
| level | string | Performance level: "weak", "medium", or "strong" |

**Error Responses:**
- `404`: Student not found

---

### EP9: Check Open Answer

Evaluates a student's open-ended answer using LangGraph flow with RAG-grounded evaluation.

**Endpoint:** `POST /student/check-open`

**Request Body:** `CheckOpenQuestionRequest`

```json
{
  "student_id": 1001,
  "subject": "Українська мова",
  "topic": "Дієприкметники",
  "subtopics": ["Дієприкметниковий зворот"],
  "question": "Що таке дієприкметниковий зворот?",
  "answer": "Дієприкметниковий зворот — це дієприкметник з залежними словами"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| student_id | integer | Yes | Student identifier |
| subject | string | Yes | Subject name in Ukrainian |
| topic | string | Yes | Main topic |
| subtopics | array[string] | No | Specific subtopics |
| question | string | Yes | Question text |
| answer | string | Yes | Student's answer |

**Response:** `OpenQuestionResultResponse`

```json
{
  "correct": true,
  "feedback": "Правильно! Ваша відповідь точна. Дієприкметниковий зворот — це дієприкметник разом із залежними від нього словами. Наприклад: 'виконане учнем завдання', де 'виконане' — дієприкметник, а 'учнем' — залежне слово."
}
```

**Internal Flow:**
1. Builds RAG query from topic + question
2. Retrieves reference content from textbooks (top_k=4)
3. LLM evaluates answer against retrieved context
4. Returns correctness and constructive feedback

---

### EP10: Get Test Feedback

Generates feedback after completing a test using LangGraph flow. Output is concise and factual, written FOR the student but without excessive emotion or greetings.

**Endpoint:** `POST /student/test-feedback`

**Request Body:** `TestFeedbackRequest`

```json
{
  "student_id": 1001,
  "subject": "Алгебра",
  "questions": [
    {
      "question": "Чому дорівнює D для x² - 4x + 4 = 0?",
      "correct": true,
      "topic": "Дискримінант",
      "subtopics": []
    },
    {
      "question": "Розв'яжіть: x² - 5x + 6 = 0",
      "correct": false,
      "topic": "Квадратні рівняння",
      "subtopics": ["Формули коренів"]
    },
    {
      "question": "Скільки коренів має рівняння якщо D < 0?",
      "correct": true,
      "topic": "Дискримінант",
      "subtopics": []
    }
  ]
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| student_id | integer | Yes | Student identifier |
| subject | string | Yes | Subject name in Ukrainian |
| questions | array[QuestionResult] | Yes | List of answered questions |

**QuestionResult Schema:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| question | string | Yes | Question text |
| correct | boolean | Yes | Whether answer was correct |
| topic | string | Yes | Question topic |
| subtopics | array[string] | No | Question subtopics |

**Response:** `TestFeedbackResponse`

```json
{
  "feedback": "Результат: 2/3 (67%) — добрий результат.\n\nУспішні теми: Дискримінант (2 правильних).\n\nПроблемні теми: Квадратні рівняння > Формули коренів (1 помилка).\n\nРекомендації:\n1. Повторити формули коренів квадратного рівняння\n2. Перевіряти відповіді підстановкою в початкове рівняння"
}
```

**Output Style:**
- Concise and factual (Ukrainian language)
- Written FOR the student (they will read it), but without excessive emotion
- No greetings ("Привіт"), no motivational phrases ("Вірю в тебе", "Успіхів")
- Maximum 2-3 short paragraphs
- Concrete recommendations based on test results

**Internal Flow:**
1. Aggregates questions by topic (correct/incorrect)
2. Calculates score percentage and performance level
3. LLM generates concise feedback with specific recommendations

---

## Health Endpoints

### Health Check

**Endpoint:** `GET /health`

**Response:**
```json
{
  "status": "healthy",
  "version": "0.1.0"
}
```

### Liveness Probe

**Endpoint:** `GET /health/live`

**Response:**
```json
{
  "status": "alive"
}
```

### Readiness Probe

**Endpoint:** `GET /health/ready`

**Response (healthy):**
```json
{
  "status": "ready",
  "checks": {
    "data_files": true,
    "llm_config": true,
    "redis": true
  }
}
```

**Response (not ready):**
```json
{
  "status": "not_ready",
  "checks": {
    "data_files": true,
    "llm_config": false,
    "redis": true
  }
}
```

---

## Enums Reference

### Level
```
"weak" | "medium" | "strong"
```

### Difficulty
```
"easy" | "medium" | "difficult"
```

### QuestionType
```
"single_choice" | "multiple_choice" | "open"
```

---

## Error Response Format

All error responses follow this structure:

```json
{
  "error": "not_found",
  "message": "Student not found in this class/subject"
}
```

**Common HTTP Status Codes:**
- `400` - Bad Request (invalid input)
- `404` - Not Found (resource doesn't exist)
- `500` - Internal Server Error
