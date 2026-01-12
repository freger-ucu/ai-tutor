# Data Schema & Preprocessing

## Raw Data Structure

### benchmark_scores.csv

| Column | Type | Example | Description |
|--------|------|---------|-------------|
| `school_id` | `int` | `1` | School identifier |
| `academic_year` | `str` | `"2024-2025"` | Academic year |
| `semester` | `int` | `1`, `2` | Semester number |
| `class_id` | `int` | `1`, `2`, `3`, `4` | Class identifier (NOT "8-A" format!) |
| `grade` | `int` | `8`, `9` | School grade level |
| `discipline_name` | `str` | `"Алгебра"`, `"Українська мова"` | Subject in Ukrainian |
| `teacher_id` | `int` | `1`, `4`, `13` | Teacher identifier |
| `lesson_date` | `str` | `"2024-09-03"` | ISO date format |
| `score_text` | `str` | `"10"` | Score as text (same as numeric) |
| `score_numeric` | `int` | `0-12` | Score on Ukrainian scale |
| `is_final_score` | `int` | `0`, `1` | Boolean: is this a final grade |
| `topic_name` | `str` | `"Квадратні рівняння..."` | Lesson topic |
| `lesson_number` | `int` | `1`, `2`, `3` | Lesson sequence number |
| `student_id` | `int` | `1`, `22`, `102` | Student identifier |
| `_rescued_data` | `null` | `null` | Ignore |

### benchmark_absences.csv

| Column | Type | Example | Description |
|--------|------|---------|-------------|
| `school_id` | `int` | `1` | School identifier |
| `academic_year` | `str` | `"2024-2025"` | Academic year |
| `semester` | `int` | `1`, `2` | Semester number |
| `class_id` | `int` | `1`, `2`, `3`, `4` | Class identifier |
| `grade` | `int` | `8`, `9` | School grade level |
| `discipline_name` | `str` | `"Алгебра"` | Subject in Ukrainian |
| `teacher_id` | `int` | `1`, `13` | Teacher identifier |
| `lesson_date` | `str` | `"2024-09-03"` | ISO date format |
| `absence_reason` | `str` | `"Поважна причина"`, `"Через хворобу"` | Absence reason |
| `topic_name` | `str` | `"..."` | Topic missed |
| `lesson_number` | `int` | `1`, `2`, `3` | Lesson number |
| `student_id` | `int` | `91`, `102` | Student identifier |
| `_rescued_data` | `null` | `null` | Ignore |

---

## Key Observations

### IDs Are Integers!
```python
# WRONG (current models)
teacher_id: str
student_id: str
class_id: str

# CORRECT
teacher_id: int
student_id: int
class_id: int
```

### No Names in Data
- No `teacher_name` - only `teacher_id`
- No `student_name` - only `student_id`
- **Solution:** Generate fake names or use ID as display (e.g., "Учень #102")

### Class Structure
- `class_id` = unique class identifier (int)
- `grade` = school grade level (8 or 9)
- **No `class_letter`** - not in the data!
- **Solution:** Either derive letter from class_id or skip it

### Discipline Mapping
```python
DISCIPLINE_MAP = {
    "Алгебра": "algebra",
    "Геометрія": "geometry",          # NOT in our Subject enum!
    "Українська мова": "ukrainian",
    "Українська література": "ukrainian",
    "Зарубіжна література": "literature",  # NOT in our Subject enum!
    "Іноземна мова": "foreign_lang",       # NOT in our Subject enum!
    "Всесвітня історія": "history",
    "Історія України": "history",
    "Біологія": "biology",                 # NOT in our Subject enum!
    "Географія": "geography",              # NOT in our Subject enum!
    "Фізика і астрономія": "physics",      # NOT in our Subject enum!
    "Хімія": "chemistry",                  # NOT in our Subject enum!
    "Фізична культура": "pe",              # NOT in our Subject enum!
}
```

**Problem:** Current `Subject` enum only has `algebra`, `ukrainian`, `history`.
Data has many more subjects!

---

## Preprocessing Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         DATA PREPROCESSING FLOW                              │
└─────────────────────────────────────────────────────────────────────────────┘

    RAW DATA (CSV/Parquet)
    ├── benchmark_scores.csv
    └── benchmark_absences.csv
              │
              ▼
    ┌─────────────────────┐
    │  1. LOAD & PARSE    │
    │  - Read CSV/Parquet │
    │  - Parse dates      │
    │  - Cast types       │
    └──────────┬──────────┘
               │
               ▼
    ┌─────────────────────┐
    │  2. EXTRACT ENTITIES│
    │  - Unique teachers  │
    │  - Unique students  │
    │  - Unique classes   │
    │  - Subjects list    │
    └──────────┬──────────┘
               │
               ▼
    ┌─────────────────────┐
    │ 3. BUILD RELATIONS  │
    │ - Teacher → Classes │
    │ - Class → Students  │
    │ - Teacher → Subjects│
    └──────────┬──────────┘
               │
               ▼
    ┌─────────────────────┐
    │ 4. COMPUTE METRICS  │
    │ - Avg grade/student │
    │ - Student levels    │
    │ - Absence counts    │
    └──────────┬──────────┘
               │
               ▼
    ┌─────────────────────┐
    │ 5. BUILD INDEXES    │
    │ - by teacher_id     │
    │ - by class_id       │
    │ - by student_id     │
    └──────────┬──────────┘
               │
               ▼
    PREPROCESSED DATA (in memory / Redis cache)
```

---

## Preprocessing Steps Detail

### Step 1: Load & Parse
```python
import pandas as pd

scores_df = pd.read_csv("benchmark_scores.csv", parse_dates=["lesson_date"])
absences_df = pd.read_csv("benchmark_absences.csv", parse_dates=["lesson_date"])

# Ensure correct types
scores_df["teacher_id"] = scores_df["teacher_id"].astype(int)
scores_df["student_id"] = scores_df["student_id"].astype(int)
scores_df["class_id"] = scores_df["class_id"].astype(int)
scores_df["score_numeric"] = scores_df["score_numeric"].astype(int)
```

### Step 2: Extract Unique Entities
```python
# Unique teachers with their classes and subjects
teachers = scores_df.groupby("teacher_id").agg({
    "class_id": lambda x: list(x.unique()),
    "discipline_name": lambda x: list(x.unique()),
    "grade": lambda x: list(x.unique())
}).reset_index()

# Unique students with their class
students = scores_df.groupby("student_id").agg({
    "class_id": "first",  # assume student belongs to one class
    "grade": "first"
}).reset_index()

# Unique classes
classes = scores_df.groupby("class_id").agg({
    "grade": "first",
    "school_id": "first"
}).reset_index()
```

### Step 3: Build Relations
```python
# Teacher → Classes mapping
teacher_classes = {}
for _, row in scores_df.groupby(["teacher_id", "class_id", "discipline_name"]).size().reset_index().iterrows():
    tid = row["teacher_id"]
    if tid not in teacher_classes:
        teacher_classes[tid] = []
    teacher_classes[tid].append({
        "class_id": row["class_id"],
        "discipline_name": row["discipline_name"]
    })

# Class → Students mapping
class_students = scores_df.groupby("class_id")["student_id"].unique().to_dict()
```

### Step 4: Compute Metrics
```python
# Average grade per student per subject
student_avgs = scores_df.groupby(["student_id", "discipline_name"])["score_numeric"].mean()

# Student level based on percentiles within class
def compute_level(avg_score, q1, q3):
    if avg_score < q1:
        return "weak"
    elif avg_score > q3:
        return "strong"
    else:
        return "medium"

# Absence count per student
absence_counts = absences_df.groupby("student_id").size()
```

### Step 5: Build Indexes
```python
# Fast lookup structures
class DataIndex:
    def __init__(self):
        self.teachers = {}        # teacher_id -> TeacherData
        self.students = {}        # student_id -> StudentData
        self.classes = {}         # class_id -> ClassData

        self.teacher_classes = {} # teacher_id -> [class_ids]
        self.class_students = {}  # class_id -> [student_ids]

    def get_teacher(self, teacher_id: int) -> dict: ...
    def get_students_in_class(self, class_id: int, discipline: str) -> list: ...
    def get_student_average(self, student_id: int, discipline: str) -> float: ...
```

---

## Corrected Type Definitions

```typescript
// All IDs are INTEGERS, not strings!

interface TeacherData {
  teacher_id: number              // int, not string
  full_name: string               // generated or "Вчитель #1"
  classes: ClassInfo[]
}

interface ClassInfo {
  class_id: number                // int, not string
  grade: number                   // 8 or 9
  discipline_name: string         // Ukrainian name from data
  // NO class_letter - not in data!
}

interface StudentSummary {
  student_id: number              // int, not string
  full_name: string               // generated or "Учень #102"
  class_id: number                // int
  discipline_name: string         // Ukrainian name
  subject_level: "weak" | "medium" | "strong"
  average_subject_grade: number   // 0-12 float
}

interface StudentDetails {
  student_id: number
  full_name: string
  class_id: number
  grade: number                   // school grade (8, 9)
  average_subject_grade: number
  level: "weak" | "medium" | "strong"
  skipped_lessons: SkippedLesson[]
  problematic_topics: ProblematicTopic[]
}

interface SkippedLesson {
  date: string                    // ISO date
  topic_name: string
  discipline_name: string
  absence_reason: string          // "Поважна причина" | "Через хворобу"
}

interface ProblematicTopic {
  topic_name: string
  discipline_name: string
  average_score: number
  lesson_count: number
}
```

---

## Questions for Team

1. **Subject enum:** Should we expand to include all disciplines from data (Геометрія, Біологія, Фізика, etc.)?
   - Or filter only 3 subjects for hackathon?

2. **Names:** How to handle missing names?
   - Generate fake Ukrainian names?
   - Use "Вчитель #1", "Учень #102" format?

3. **Class letter:** Data doesn't have it. Options:
   - Skip it (just use class_id + grade)
   - Derive from class_id (class_id=1 → "А", class_id=2 → "Б")

4. **Multi-class students:** Can a student be in multiple classes?
   - Data suggests no (same student_id appears with same class_id)
