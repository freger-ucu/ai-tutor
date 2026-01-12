# AI Tutor - API Flow & Contracts

> **Source of Truth** - Based on `endpoints_all.md`

---

## Table of Contents

1. [Data Foundation](#data-foundation)
2. [Teacher Flow](#teacher-flow)
3. [Student Flow](#student-flow)
4. [Flow Diagram](#flow-diagram)
5. [API Contracts](#api-contracts)
   - [Teacher Endpoints](#teacher-endpoints-1-7)
   - [Student Endpoints](#student-endpoints-8-10)
6. [Type Definitions](#type-definitions)

---

## Data Foundation

### Data Sources

| Source | Format | Contains |
|--------|--------|----------|
| `benchmark_scores.parquet` | Parquet | Grades, teacher→class→subject→student relationships |
| `benchmark_absences.parquet` | Parquet | Student absences per lesson |
| **Frontend** | Runtime | Topics (created by Ostap, sent as `topic_definition`) |

### Key Data Relationships

```
Teacher (teacher_id)
    └── teaches Classes (class_id, class_number)
            └── for Subject (discipline_name)
                    └── has Students (student_id)
                            ├── grades history
                            ├── absences
                            └── computed: subject_level, average_grade
```

### ID Types (from actual CSV data)

| Field | Type | Example |
|-------|------|---------|
| `teacher_id` | `int` | `1`, `4`, `13` |
| `student_id` | `int` | `5`, `102`, `89` |
| `class_id` | `int` | `1`, `2`, `3`, `4` |
| `class_number` | `int` | `8`, `9` (school grade) |
| `subject` | `string` | `"Алгебра"`, `"Українська мова"` |

---

## Teacher Flow

### Step 1: Teacher Login → Get Teacher Data (Endpoint 1)

Teacher opens the app and authenticates with their `teacher_id`.

**What happens:**
- Backend looks up teacher in preprocessed data
- Returns list of classes this teacher teaches
- Each class has: `class_id`, `class_number`, `subject`

**Example:** Teacher #4 logs in → sees they teach Алгебра to class 8 (id=4) and Геометрія to class 8 (id=3).

---

### Step 2: Select Class → View Students (Endpoint 2)

Teacher selects one of their classes to work with.

**What happens:**
- Backend filters students in that class for that subject
- Computes `subject_level` (weak/medium/strong) from percentiles
- Returns student list with levels and average grades

**Example:** Teacher selects class_id=4, subject="Алгебра" → sees 25 students with their levels.

---

### Step 3: Generate Lesson Notes (Endpoints 3.1 & 3.2)

Teacher prepares lesson materials. **Two options:**

#### Option A: By Level (Endpoint 3.1)
- Teacher selects levels: `["weak", "medium"]`
- Provides `topic_definition` (from frontend)
- Backend generates notes for those levels

#### Option B: By Student Set (Endpoint 3.2)
- Teacher selects specific students: `[5, 12, 18]`
- Provides `topic_definition`
- Backend generates notes for that group

**Both return:**
- `title` - lesson title
- `contents` - lesson content (markdown)
- `teacher_notes` - tips for the teacher

**Frontend constructs two versions:**
| Version | Contains | Goes To |
|---------|----------|---------|
| Teacher | `teacher_notes` + `contents` | Teacher only |
| Student | `contents` only | Selected students |

---

### Step 4: Generate Test Pool (Endpoint 4)

Teacher creates a test for the class.

**What happens:**
- Teacher provides `topic_definition`
- Backend generates pool of questions (varying difficulty)
- Returns questions with: text, type, difficulty, answers, explanation

**Frontend responsibilities:**
- Distributes tests to students (not backend)
- Checks single/multiple choice answers locally
- Sends open questions to backend for checking (Endpoint 9)

---

### Step 5: View Student Details (Endpoint 5)

Teacher views detailed info about a specific student.

**Returns:**
- Average subject grade
- Level (weak/medium/strong)
- List of skipped lessons
- List of problematic topics

---

### Step 6: Get Student Recommendation (Endpoint 6)

Teacher requests AI advice for a student.

**What happens:**
- Backend analyzes student's history
- Returns text feedback with recommendations

---

### Step 7: Solver Tool (Endpoint 7)

Teacher has questions they want solved.

**What happens:**
- Teacher enters questions in text fields
- Backend solves each question
- Returns: question + explained answer

**Use case:** Preparing answer keys, verifying problems.

---

## Student Flow

### Step 8: Student Login → Get Student Data (Endpoint 8)

Student authenticates with their `student_id`.

**Returns:**
- `class_id` - their class
- `class_number` - grade level (8, 9)
- `subjects` - list of subjects they study

---

### Step 9: Check Open Question (Endpoint 9)

Student answers an open-ended question during test.

**Why needed:** Frontend can check single/multiple choice (has answers). Open questions need LLM evaluation.

**What happens:**
- Student submits: question, their answer, topic context
- Backend (LLM) evaluates correctness
- Returns: `correct` (bool) + `feedback` (explanation)

---

### Step 10: Get Test Feedback (Endpoint 10)

Student finishes test and wants overall feedback.

**What happens:**
- Frontend sends all questions with answers and correctness
- Backend analyzes mistake patterns
- Returns comprehensive feedback and recommendations

---

## Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              TEACHER FLOW                                    │
└─────────────────────────────────────────────────────────────────────────────┘

  [Login]
     │
     ▼
  ┌──────────────────────┐
  │ EP1: Get Teacher Data │──────▶ Returns: classes[]
  └──────────────────────┘
              │
              ▼
  ┌──────────────────────┐
  │ EP2: Get Student List │──────▶ Returns: students[] with levels
  └──────────────────────┘
              │
              ├─────────────────────┬─────────────────────┐
              ▼                     ▼                     ▼
  ┌───────────────────┐  ┌───────────────────┐  ┌─────────────────┐
  │ EP3.1: Level Notes │  │EP3.2: Student Notes│  │ EP4: Gen Test   │
  └───────────────────┘  └───────────────────┘  └─────────────────┘
              │                     │                     │
              └──────────┬──────────┘                     │
                         ▼                                ▼
              ┌─────────────────────┐          ┌─────────────────────┐
              │  Frontend splits:   │          │  Frontend distributes│
              │  • Teacher version  │          │  test to students   │
              │  • Student version  │          └─────────────────────┘
              └─────────────────────┘

  [View Student]
     │
     ▼
  ┌──────────────────────┐         ┌────────────────────────┐
  │ EP5: Student Details  │────────▶│ EP6: Get Recommendation │
  └──────────────────────┘         └────────────────────────┘

  [Solver Page]
     │
     ▼
  ┌──────────────────────┐
  │ EP7: Solve Questions  │──────▶ Returns: answers + explanations
  └──────────────────────┘


┌─────────────────────────────────────────────────────────────────────────────┐
│                              STUDENT FLOW                                    │
└─────────────────────────────────────────────────────────────────────────────┘

  [Login]
     │
     ▼
  ┌──────────────────────┐
  │ EP8: Get Student Data │──────▶ Returns: class_id, subjects[]
  └──────────────────────┘
              │
              ▼
  ┌──────────────────────┐
  │  Receive Test from   │
  │      Frontend        │
  └──────────────────────┘
              │
              ├─────────────────────────────────┐
              ▼                                 ▼
  ┌─────────────────────┐            ┌─────────────────────┐
  │  Single/Multiple    │            │   Open Questions    │
  │  Choice (local)     │            │                     │
  └─────────────────────┘            └─────────────────────┘
              │                                 │
              │                                 ▼
              │                      ┌─────────────────────┐
              │                      │EP9: Check Open Q    │
              │                      └─────────────────────┘
              │                                 │
              └─────────────────┬───────────────┘
                                ▼
                    ┌─────────────────────┐
                    │   Test Complete     │
                    └─────────────────────┘
                                │
                                ▼
                    ┌─────────────────────┐
                    │EP10: Get Feedback   │──────▶ Returns: feedback, recommendations
                    └─────────────────────┘
```

---

## API Contracts

### Teacher Endpoints (1-7)

---

#### Endpoint 1: Get Teacher Data

Get teacher's classes and subjects on login.

**Request:**
```http
GET /api/v1/teacher/{teacher_id}
```

| Param | Type | Location | Description |
|-------|------|----------|-------------|
| `teacher_id` | `int` | path | Teacher identifier |

**Response:**
```typescript
{
  "classes": [
    {
      "class_id": number,
      "class_number": number,
      "subject": string
    }
  ]
}
```

**Example:**
```json
{
  "classes": [
    { "class_id": 4, "class_number": 8, "subject": "Алгебра" },
    { "class_id": 3, "class_number": 8, "subject": "Геометрія" }
  ]
}
```

---

#### Endpoint 2: Get Student List

Get students in a class with their performance levels.

**Request:**
```http
POST /api/v1/teacher/students
```

```typescript
{
  "class_id": number,
  "teacher_id": number,
  "subject": string
}
```

**Response:**
```typescript
{
  "students": [
    {
      "student_id": number,
      "subject_level": "weak" | "medium" | "strong",
      "average_subject_grade": number
    }
  ]
}
```

**Example:**
```json
{
  "students": [
    { "student_id": 5, "subject_level": "strong", "average_subject_grade": 10.5 },
    { "student_id": 12, "subject_level": "medium", "average_subject_grade": 7.8 },
    { "student_id": 22, "subject_level": "weak", "average_subject_grade": 4.2 }
  ]
}
```

---

#### Endpoint 3.1: Generate Level Notes

Generate notes for students by level.

**Request:**
```http
POST /api/v1/teacher/notes/by-level
```

```typescript
{
  "class_id": number,
  "teacher_id": number,
  "subject": string,
  "level_list": ("weak" | "medium" | "strong")[],
  "topic_definition": string      // topic description text
}
```

**Response:**
```typescript
{
  "title": string,
  "contents": string,
  "teacher_notes": string
}
```

**Example:**
```json
{
  "title": "Квадратні рівняння",
  "contents": "## Основні поняття\n\nКвадратне рівняння має вигляд ax² + bx + c = 0...",
  "teacher_notes": "Зверніть увагу: 3 учні пропустили тему дискримінанта. Почніть з повторення."
}
```

---

#### Endpoint 3.2: Generate Individual Notes

Generate notes for specific students.

**Request:**
```http
POST /api/v1/teacher/notes/individual
```

```typescript
{
  "class_id": number,
  "teacher_id": number,
  "subject": string,
  "student_list": number[],
  "topic_definition": string      // topic description text
}
```

**Response:**
```typescript
{
  "title": string,
  "contents": string,
  "teacher_notes": string
}
```

---

#### Endpoint 4: Generate Test

Generate a pool of test questions.

**Request:**
```http
POST /api/v1/teacher/test/generate
```

```typescript
{
  "class_id": number,
  "teacher_id": number,
  "subject": string,
  "topic_definition": string      // topic description text
}
```

**Response:**
```typescript
{
  "title": string,
  "questions": [
    {
      "question": string,
      "type": "single_choice" | "multiple_choice" | "open",
      "difficulty": "easy" | "medium" | "difficult",
      "answer_options": [
        {
          "answer": string,
          "correct": boolean
        }
      ] | null,
      "explanation": string,
      "topic": string,
      "subtopics": string[]
    }
  ]
}
```

**Example:**
```json
{
  "title": "Тест: Квадратні рівняння",
  "questions": [
    {
      "question": "Розв'яжіть рівняння: x² - 5x + 6 = 0",
      "type": "single_choice",
      "difficulty": "easy",
      "answer_options": [
        { "answer": "x = 2, x = 3", "correct": true },
        { "answer": "x = 1, x = 6", "correct": false },
        { "answer": "x = -2, x = -3", "correct": false },
        { "answer": "x = 2, x = -3", "correct": false }
      ],
      "explanation": "D = 25 - 24 = 1, x = (5 ± 1) / 2",
      "topic": "Квадратні рівняння",
      "subtopics": ["дискримінант", "корені"]
    },
    {
      "question": "Поясніть, коли квадратне рівняння не має дійсних розв'язків",
      "type": "open",
      "difficulty": "medium",
      "answer_options": null,
      "explanation": "Коли дискримінант D < 0",
      "topic": "Квадратні рівняння",
      "subtopics": ["дискримінант"]
    }
  ]
}
```

---

#### Endpoint 5: Get Student Data

Get detailed info about a specific student.

**Request:**
```http
POST /api/v1/teacher/student/details
```

```typescript
{
  "class_id": number,
  "subject": string,
  "teacher_id": number,
  "student_id": number
}
```

**Response:**
```typescript
{
  "average_subject_grade": number,
  "level": "weak" | "medium" | "strong",
  "skipped_lessons": [
    {
      "date": string,
      "topic": string
    }
  ],
  "problematic_topics": [
    {
      "topic": string,
      "average_score": number
    }
  ]
}
```

**Example:**
```json
{
  "average_subject_grade": 6.5,
  "level": "medium",
  "skipped_lessons": [
    { "date": "2024-09-15", "topic": "Дискримінант" },
    { "date": "2024-09-22", "topic": "Теорема Вієта" }
  ],
  "problematic_topics": [
    { "topic": "Дискримінант", "average_score": 4.5 },
    { "topic": "Квадратні нерівності", "average_score": 5.0 }
  ]
}
```

---

#### Endpoint 6: Get Student Recommendation

Get AI recommendation for a student.

**Request:**
```http
POST /api/v1/teacher/student/recommendation
```

```typescript
{
  "student_id": number
}
```

**Response:**
```typescript
{
  "feedback": string
}
```

**Example:**
```json
{
  "feedback": "Учень має прогалини в темі 'Дискримінант' через пропуски занять. Рекомендую: 1) Провести додаткове пояснення формули D = b² - 4ac, 2) Дати 3-4 прості приклади для закріплення, 3) Перевірити розуміння через усне опитування."
}
```

---

#### Endpoint 7: Solver

Solve questions and provide explanations.

**Request:**
```http
POST /api/v1/solver
```

```typescript
{
  "questions": string[]
}
```

**Response:**
```typescript
{
  "solutions": [
    {
      "question": string,
      "answer_explained": string
    }
  ]
}
```

**Example:**
```json
{
  "solutions": [
    {
      "question": "Розв'яжіть: 2x² + 3x - 2 = 0",
      "answer_explained": "Використаємо формулу дискримінанта:\nD = 9 + 16 = 25\nx = (-3 ± 5) / 4\nx₁ = 0.5, x₂ = -2\n\nВідповідь: x = 0.5 або x = -2"
    }
  ]
}
```

---

### Student Endpoints (8-10)

---

#### Endpoint 8: Get Student Data

Get student's class and subjects on login.

**Request:**
```http
GET /api/v1/student/{student_id}
```

| Param | Type | Location | Description |
|-------|------|----------|-------------|
| `student_id` | `int` | path | Student identifier |

**Response:**
```typescript
{
  "class_id": number,
  "class_number": number,
  "subjects": string[]
}
```

**Example:**
```json
{
  "class_id": 4,
  "class_number": 8,
  "subjects": ["Алгебра", "Геометрія", "Українська мова", "Фізика"]
}
```

---

#### Endpoint 9: Check Open Question

Check correctness of open-ended answer.

**Request:**
```http
POST /api/v1/student/check-open
```

```typescript
{
  "student_id": number,
  "subject": string,
  "topic": string,
  "subtopics": string[],
  "question": string,
  "answer": string
}
```

**Response:**
```typescript
{
  "correct": boolean,
  "feedback": string
}
```

**Example:**
```json
{
  "correct": true,
  "feedback": "Правильно! Ви вірно пояснили, що рівняння не має дійсних коренів коли D < 0."
}
```

---

#### Endpoint 10: Get Test Feedback

Get overall feedback after completing test.

**Request:**
```http
POST /api/v1/student/test-feedback
```

```typescript
{
  "student_id": number,
  "teacher_id": number,
  "subject": string,
  "questions": [
    {
      "question": string,
      "answer": string,
      "correct": boolean,
      "topic": string,
      "subtopics": string[]
    }
  ]
}
```

**Response:**
```typescript
{
  "feedback": string
}
```

**Example:**
```json
{
  "feedback": "Результат: 7/10 правильних відповідей.\n\nСильні сторони:\n• Добре розумієте базові формули\n• Правильно застосовуєте дискримінант\n\nНад чим попрацювати:\n• Теорема Вієта - 2 помилки\n• Уважніше з від'ємними числами\n\nРекомендація: Повторіть зв'язок коренів та коефіцієнтів рівняння."
}
```

---

## Type Definitions

### Common Types

```typescript
// =============================================================================
// IDs are INTEGERS (from CSV data)
// =============================================================================

type Level = "weak" | "medium" | "strong"
type Difficulty = "easy" | "medium" | "difficult"
type QuestionType = "single_choice" | "multiple_choice" | "open"

// Subjects are Ukrainian strings from data:
// "Алгебра", "Геометрія", "Українська мова", "Українська література",
// "Зарубіжна література", "Іноземна мова", "Історія України",
// "Всесвітня історія", "Біологія", "Географія", "Фізика", "Хімія"
```

### Request Types

```typescript
// topic_definition is just a string (topic description text)

interface GetStudentListRequest {
  class_id: number
  teacher_id: number
  subject: string
}

interface GenerateNotesRequest {
  class_id: number
  teacher_id: number
  subject: string
  level_list?: Level[]        // for 3.1
  student_list?: number[]     // for 3.2
  topic_definition: string
}

interface GenerateTestRequest {
  class_id: number
  teacher_id: number
  subject: string
  topic_definition: string
}

interface StudentDetailsRequest {
  class_id: number
  subject: string
  teacher_id: number
  student_id: number
}

interface CheckOpenQuestionRequest {
  student_id: number
  subject: string
  topic: string
  subtopics: string[]
  question: string
  answer: string
}

interface TestFeedbackRequest {
  student_id: number
  teacher_id: number
  subject: string
  questions: QuestionResult[]
}

interface QuestionResult {
  question: string
  answer: string
  correct: boolean
  topic: string
  subtopics: string[]
}
```

### Response Types

```typescript
interface ClassInfo {
  class_id: number
  class_number: number
  subject: string
}

interface StudentSummary {
  student_id: number
  subject_level: Level
  average_subject_grade: number
}

interface NotesResponse {
  title: string
  contents: string
  teacher_notes: string
}

interface AnswerOption {
  answer: string
  correct: boolean
}

interface Question {
  question: string
  type: QuestionType
  difficulty: Difficulty
  answer_options: AnswerOption[] | null
  explanation: string
  topic: string
  subtopics: string[]
}

interface TestResponse {
  title: string
  questions: Question[]
}

interface SkippedLesson {
  date: string
  topic: string
}

interface ProblematicTopic {
  topic: string
  average_score: number
}

interface StudentDetails {
  average_subject_grade: number
  level: Level
  skipped_lessons: SkippedLesson[]
  problematic_topics: ProblematicTopic[]
}

interface Solution {
  question: string
  answer_explained: string
}

interface StudentData {
  class_id: number
  class_number: number
  subjects: string[]
}

interface OpenQuestionResult {
  correct: boolean
  feedback: string
}
```
