# Teacher Flow - Contracts & Process Description

## Overview

This document describes the complete teacher workflow based on frontend requirements.

### Data Sources
- `benchmark_scores.parquet` - Student grades, contains teacher-class-subject-student relationships
- `benchmark_absences.parquet` - Student absences
- **Frontend** - Topics are created and stored by Ostap on frontend

---

## Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           TEACHER FLOW                                       │
└─────────────────────────────────────────────────────────────────────────────┘

    ┌──────────────┐
    │   Teacher    │
    │   Logs In    │
    └──────┬───────┘
           │
           ▼
    ┌──────────────┐      GET /teacher/{teacher_id}
    │  Endpoint 1  │ ───► Returns: classes, subjects
    │  Get Teacher │
    │     Data     │
    └──────┬───────┘
           │
           ▼
    ┌──────────────┐      POST /teacher/students
    │  Endpoint 2  │ ───► Returns: student list with levels
    │  Get Student │
    │     List     │
    └──────┬───────┘
           │
           ├─────────────────────┬─────────────────────┐
           │                     │                     │
           ▼                     ▼                     ▼
    ┌──────────────┐      ┌──────────────┐      ┌──────────────┐
    │ Endpoint 3.1 │      │ Endpoint 3.2 │      │  Endpoint 4  │
    │  Gen Level   │      │ Gen Individual│      │  Gen Test    │
    │    Notes     │      │    Notes     │      │    Pool      │
    └──────────────┘      └──────────────┘      └──────┬───────┘
                                                       │
                                                       ▼
                                                ┌──────────────┐
                                                │   Frontend   │
                                                │ Sends Tests  │
                                                │ to Students  │
                                                └──────────────┘

    ┌──────────────┐      GET /teacher/student/{student_id}
    │  Endpoint 5  │ ───► Returns: student details, problems
    │  Get Student │
    │    Data      │
    └──────────────┘

    ┌──────────────┐      GET /teacher/student/{student_id}/recommendation
    │  Endpoint 6  │ ───► Returns: AI feedback
    │  Get Student │
    │   Recommend  │
    └──────────────┘

    ┌──────────────┐      POST /solver
    │  Endpoint 7  │ ───► Returns: solved tests with answers
    │    Solver    │
    └──────────────┘
```

---

## Endpoint Contracts (JSON + Types)

### Endpoint 1: Get Teacher Data

**Purpose:** Get teacher's classes and subjects when they log in.

**Request:**
```json
{
  "method": "GET",
  "path": "/api/v1/teacher/{teacher_id}",
  "params": {
    "teacher_id": "int (path param)"
  }
}
```

**Response:**
```typescript
{
  "teacher_id": number,             // int from data
  "full_name": string,              // generated or "Вчитель #1"
  "classes": [
    {
      "class_id": number,           // int from data
      "grade": number,              // 8 or 9 (school grade)
      "discipline_name": string     // Ukrainian: "Алгебра", "Українська мова", etc.
    }
  ]
}
```

**Example Response:**
```json
{
  "teacher_id": 4,
  "full_name": "Вчитель #4",
  "classes": [
    {
      "class_id": 4,
      "grade": 8,
      "discipline_name": "Алгебра"
    },
    {
      "class_id": 3,
      "grade": 8,
      "discipline_name": "Геометрія"
    }
  ]
}
```

---

### Endpoint 2: Get Student List

**Purpose:** Get all students in a class with their performance levels.

**Request:**
```typescript
{
  "method": "POST",
  "path": "/api/v1/teacher/students",
  "body": {
    "class_id": number,             // int
    "teacher_id": number,           // int
    "discipline_name": string       // Ukrainian: "Алгебра", etc.
  }
}
```

**Response:**
```typescript
{
  "students": [
    {
      "student_id": number,         // int from data
      "full_name": string,          // generated or "Учень #102"
      "subject_level": "weak" | "medium" | "strong",
      "average_subject_grade": number  // 0-12 scale, float
    }
  ]
}
```

**Example Response:**
```json
{
  "students": [
    {
      "student_id": 5,
      "full_name": "Учень #5",
      "subject_level": "strong",
      "average_subject_grade": 10.5
    },
    {
      "student_id": 12,
      "full_name": "Учень #12",
      "subject_level": "medium",
      "average_subject_grade": 7.8
    }
  ]
}
```

---

### Endpoint 3.1: Generate Level Notes

**Purpose:** Generate lesson notes for students grouped by level (weak/medium/strong).

**Request:**
```typescript
{
  "method": "POST",
  "path": "/api/v1/teacher/notes/by-level",
  "body": {
    "class_id": number,
    "teacher_id": number,
    "discipline_name": string,          // "Алгебра", etc.
    "level_list": ("weak" | "medium" | "strong")[],  // which levels to generate for
    "topic_definition": {
      "title": string,
      "description": string,
      "subtopics": string[]
    }
  }
}
```

**Response:**
```typescript
{
  "notes": [
    {
      "level": "weak" | "medium" | "strong",
      "title": string,
      "contents": string,        // markdown content
      "key_points": string[]     // summary bullets
    }
  ]
}
```

**Example Response:**
```json
{
  "notes": [
    {
      "level": "weak",
      "title": "Квадратні рівняння - Базовий рівень",
      "contents": "## Що таке квадратне рівняння?\n\nКвадратне рівняння...",
      "key_points": [
        "Формула: ax² + bx + c = 0",
        "Дискримінант: D = b² - 4ac"
      ]
    },
    {
      "level": "strong",
      "title": "Квадратні рівняння - Поглиблений рівень",
      "contents": "## Теорема Вієта\n\nДля рівняння ax² + bx + c = 0...",
      "key_points": [
        "x₁ + x₂ = -b/a",
        "x₁ · x₂ = c/a"
      ]
    }
  ]
}
```

---

### Endpoint 3.2: Generate Individual Notes

**Purpose:** Generate personalized notes for specific students.

**Request:**
```typescript
{
  "method": "POST",
  "path": "/api/v1/teacher/notes/individual",
  "body": {
    "class_id": number,
    "teacher_id": number,
    "discipline_name": string,          // "Алгебра", etc.
    "student_ids": number[],            // student IDs
    "topic_definition": {
      "title": string,
      "description": string,
      "subtopics": string[]
    }
  }
}
```

**Response:**
```typescript
{
  "notes": [
    {
      "student_id": number,
      "student_name": string,
      "title": string,
      "contents": string,
      "personalized_tips": string[]  // based on student's weak areas
    }
  ]
}

---

### Endpoint 4: Generate Test Pool

**Purpose:** Generate a pool of test questions. Frontend will distribute to students.

**Request:**
```typescript
{
  "method": "POST",
  "path": "/api/v1/teacher/test/generate",
  "body": {
    "class_id": string,
    "teacher_id": string,
    "subject": "algebra" | "ukrainian" | "history",
    "topic_definition": {
      "title": string,
      "description": string,
      "subtopics": string[]
    }
  }
}
```

**Response:**
```typescript
{
  "title": string,
  "questions": [
    {
      "question_id": string,
      "question": string,
      "type": "single_choice" | "multiple_choice" | "open",
      "difficulty": "easy" | "medium" | "difficult",
      "answer_options": [
        {
          "answer": string,
          "correct": boolean
        }
      ] | null,  // null for open questions
      "explanation": string,
      "topic": string,
      "subtopics": string[]
    }
  ]
}
```

**Example Response:**
```json
{
  "title": "Тест: Квадратні рівняння",
  "questions": [
    {
      "question_id": "q_001",
      "question": "Розв'яжіть рівняння: x² - 5x + 6 = 0",
      "type": "single_choice",
      "difficulty": "easy",
      "answer_options": [
        {"answer": "x = 2, x = 3", "correct": true},
        {"answer": "x = 1, x = 6", "correct": false},
        {"answer": "x = -2, x = -3", "correct": false},
        {"answer": "x = 2, x = -3", "correct": false}
      ],
      "explanation": "Використовуємо формулу дискримінанта...",
      "topic": "Квадратні рівняння",
      "subtopics": ["дискримінант", "корені рівняння"]
    },
    {
      "question_id": "q_002",
      "question": "Поясніть, коли квадратне рівняння не має розв'язків",
      "type": "open",
      "difficulty": "medium",
      "answer_options": null,
      "explanation": "Коли D < 0, рівняння не має дійсних коренів",
      "topic": "Квадратні рівняння",
      "subtopics": ["дискримінант"]
    }
  ]
}
```

**Note from Ostap:** Frontend handles sending tests to students. This is a general pool - frontend will pull from it based on student levels.

---

### Endpoint 5: Get Student Data

**Purpose:** Get detailed data for a specific student.

**Request:**
```typescript
{
  "method": "POST",
  "path": "/api/v1/teacher/student/details",
  "body": {
    "class_id": string,
    "subject": "algebra" | "ukrainian" | "history",
    "teacher_id": string,
    "student_id": string
  }
}
```

**Response:**
```typescript
{
  "full_name": string,
  "average_subject_grade": number,    // 0-12
  "level": "weak" | "medium" | "strong",
  "skipped_lessons": [
    {
      "date": string,        // ISO date
      "topic": string | null
    }
  ],
  "problematic_topics": [
    {
      "topic": string,
      "average_score": number,
      "attempts": number
    }
  ]
}
```

**Note:** Level is calculated from average grade in database (not manually set).

---

### Endpoint 6: Get Student Recommendation

**Purpose:** Get AI-generated recommendation for a student.

**Request:**
```typescript
{
  "method": "GET",
  "path": "/api/v1/teacher/student/{student_id}/recommendation"
}
```

**Response:**
```typescript
{
  "student_id": string,
  "feedback": string    // AI-generated text
}
```

---

### Endpoint 7: Solver (TBD)

**Purpose:** Solve/validate test questions.

**Request:**
```typescript
{
  "method": "POST",
  "path": "/api/v1/solver",
  "body": {
    "tests": string[]   // question texts to solve
  }
}
```

**Response:**
```typescript
{
  "tests": [
    {
      "title": string,
      "question": string,
      "answer": string,
      "difficulty": "easy" | "medium" | "difficult",
      "explanation": string,
      "topic": string,
      "subtopics": string[]
    }
  ]
}
```

---

## Data Model Requirements

Based on these endpoints, we need:

### From Parquet Files (DataLoader)
- Teacher → Classes mapping
- Teacher → Subjects mapping
- Class → Students mapping
- Student grades history
- Student absences

### Computed
- `subject_level`: Calculate from `average_subject_grade` based on percentiles

---

## Type Definitions Summary

```typescript
// =============================================================================
// IMPORTANT: IDs are INTEGERS (from actual CSV data), not strings!
// =============================================================================

// Enums / Literals
type Level = "weak" | "medium" | "strong"
type Difficulty = "easy" | "medium" | "difficult"
type QuestionType = "single_choice" | "multiple_choice" | "open"

// discipline_name values from data (Ukrainian):
// "Алгебра", "Геометрія", "Українська мова", "Українська література",
// "Зарубіжна література", "Іноземна мова", "Всесвітня історія",
// "Історія України", "Біологія", "Географія", "Фізика і астрономія",
// "Хімія", "Фізична культура"

// Core Types
interface ClassInfo {
  class_id: number              // int! e.g., 1, 2, 3, 4
  grade: number                 // 8 or 9 (school grade)
  discipline_name: string       // Ukrainian subject name
  // NO class_letter - not in data!
}

interface StudentSummary {
  student_id: number            // int! e.g., 5, 102
  full_name: string             // generated: "Учень #102"
  subject_level: Level
  average_subject_grade: number // 0-12, float
}

interface TopicDefinition {
  title: string
  description: string
  subtopics: string[]
}

interface AnswerOption {
  answer: string
  correct: boolean
}

interface Question {
  question_id: string           // generated UUID or "q_001"
  question: string
  type: QuestionType
  difficulty: Difficulty
  answer_options: AnswerOption[] | null
  explanation: string
  topic: string
  subtopics: string[]
}

interface LevelNote {
  level: Level
  title: string
  contents: string
  key_points: string[]
}

interface SkippedLesson {
  date: string                  // ISO date "2024-09-03"
  topic_name: string
  discipline_name: string
  absence_reason: string        // "Поважна причина" | "Через хворобу"
}

interface ProblematicTopic {
  topic: string
  average_score: number
  attempts: number
}
```
