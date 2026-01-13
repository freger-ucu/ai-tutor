# AI Tutor Backend - Architecture Document

> **Source of Truth** - This document defines the architecture based on analysis of actual data and API contracts.

---

## Table of Contents

1. [Overview](#overview)
2. [Phase 1: Data Layer](#phase-1-data-layer)
   - [Data Sources](#data-sources)
   - [Data Schemas](#data-schemas)
   - [Entity Relationship Model](#entity-relationship-model)
   - [Required Filters](#required-filters)
   - [Edge Cases](#edge-cases)
   - [Endpoint Data Requirements](#endpoint-data-requirements)
3. [Phase 2: LLM Abstraction Layer](#phase-2-llm-abstraction-layer)
4. [Phase 3: RAG Layer](#phase-3-rag-layer)
5. [Phase 4: Service Layer](#phase-4-service-layer)
6. [Phase 5: Workflow Layer](#phase-5-workflow-layer)
7. [Phase 6: API Implementation Mapping](#phase-6-api-implementation-mapping)

---

## Overview

AI Tutor is an educational tutoring system for Ukrainian schools (grades 8-9). It supports:
- **3 subjects**: Алгебра, Українська мова, Історія України
- **Teacher flow**: Class analysis, lesson generation, test creation, reports
- **Student flow**: Test taking, answer checking, feedback

**Key Constraints:**
- MVP scoped to 3 subjects (have textbook content for RAG)
- No caching for MVP (skip Redis)
- Embeddings pre-computed (4096 dimensions)
- All LLM prompts and responses in Ukrainian
- Unknown IDs return 404 (not empty results)

---

## Phase 1: Data Layer

### Data Sources

| File | Records | Purpose |
|------|---------|---------|
| `data/benchmark_scores.parquet` | 139,382* | Student grades per topic |
| `data/benchmark_absences.parquet` | 42,977* | Student absences |
| `data/lms_questions_dev.parquet` | 141 | Pre-made question bank |
| `data/embeddings/toc_for_hackathon_with_subtopics.parquet` | 237 | Topics + summaries + embeddings |
| `data/embeddings/pages_for_hackathon.parquet` | 1,318 | Textbook pages + embeddings |

*After applying required filters

---

### Data Schemas

**Terminology Note:** The parquet files use `grade` (8 or 9) to indicate school year level. The API contracts use `class_number` as the field name in responses. **These are the same thing** - just different naming conventions between internal data and external API.

#### benchmark_scores.parquet

| Column | Type | Description |
|--------|------|-------------|
| `school_id` | int64 | School identifier |
| `academic_year` | string | "2024-2025" or "2025-2026" |
| `semester` | int64 | 1 or 2 |
| `class_id` | int64 | Class identifier (globally unique) |
| `grade` | int64 | School grade: 8 or 9 (exposed as `class_number` in API) |
| `discipline_name` | string | Subject in Ukrainian |
| `teacher_id` | int64 | Teacher identifier (globally unique) |
| `lesson_date` | date | Lesson date |
| `score_text` | string | Score as text |
| `score_numeric` | int64 | Score 0-12 (Ukrainian scale) |
| `is_final_score` | int64 | 0 or 1 (IGNORE - unclear meaning) |
| `topic_name` | string | Lesson topic (free text, may be NULL) |
| `lesson_number` | int64 | Lesson sequence number |
| `student_id` | int64 | Student identifier (globally unique) |

#### benchmark_absences.parquet

| Column | Type | Description |
|--------|------|-------------|
| `school_id` | int64 | School identifier |
| `academic_year` | string | Academic year |
| `semester` | int64 | Semester number |
| `class_id` | int64 | Class identifier |
| `grade` | int64 | School grade |
| `discipline_name` | string | Subject in Ukrainian |
| `teacher_id` | int64 | Teacher identifier |
| `lesson_date` | date | Lesson date |
| `absence_reason` | string | "Поважна причина", "Через хворобу", "Не було на уроці" |
| `topic_name` | string | Topic missed |
| `lesson_number` | int64 | Lesson number |
| `student_id` | int64 | Student identifier |

#### lms_questions_dev.parquet

| Column | Type | Description |
|--------|------|-------------|
| `question_id` | string | UUID |
| `question_text` | string | Question text (may contain LaTeX) |
| `test_type` | string | Always "single_choice" |
| `description` | string | Optional description |
| `model` | string | "manual" |
| `source` | string | "imported_from_lms" |
| `global_discipline_name` | string | Subject name |
| `grade` | int64 | 8 or 9 |
| `answers` | array[string] | Answer options |
| `correct_answer_indices` | array[int] | Indices of correct answers |

**Question distribution:**
- Алгебра: 46 questions
- Українська мова: 59 questions
- Історія України: 36 questions

#### toc_for_hackathon_with_subtopics.parquet

| Column | Type | Description |
|--------|------|-------------|
| `book_id` | string | Book identifier |
| `book_name` | string | Full book title |
| `grade` | int64 | 8 or 9 |
| `section_title` | string | Section name |
| `topic_title` | string | Topic name (e.g., "§ 5. Непряма мова...") |
| `topic_type` | string | "theoretical" |
| `topic_summary` | string | AI-generated summary |
| `subtopics` | array[string] | List of subtopic names |
| `subtopics_with_text` | array[object] | `[{name: str, text: str}, ...]` |
| `topic_text` | string | Full topic text from textbook |
| `topic_start_page` | float | Page number |
| `global_discipline_name` | string | Subject name |
| `section_embedding` | array[float] | 4096-dim embedding |
| `topic_embedding` | array[float] | 4096-dim embedding |
| `section_topic_embedding` | array[float] | 4096-dim embedding |

**Topic distribution:**
- Алгебра: 53 topics
- Українська мова: 105 topics
- Історія України: 79 topics

#### pages_for_hackathon.parquet

| Column | Type | Description |
|--------|------|-------------|
| `book_id` | string | Book identifier |
| `book_name` | string | Full book title |
| `grade` | int64 | 8 or 9 |
| `page_number` | float | Page number |
| `section_title` | string | Section name |
| `topic_title` | string | Topic name |
| `page_text` | string | Full page text |
| `page_metadata` | object | Contains exercises, images count, etc. |
| `global_discipline_name` | string | Subject name |
| `page_text_embedding` | array[float] | 4096-dim embedding |

**Page distribution:**
- Алгебра: 418 pages
- Українська мова: 429 pages
- Історія України: 471 pages

---

### Entity Relationship Model

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         ENTITY RELATIONSHIP MODEL                            │
└─────────────────────────────────────────────────────────────────────────────┘

  SCHOOL (13)
     │
     ├──1:N──► TEACHER (146)         [globally unique ID]
     │              │
     │              ├── teaches 1-3 SUBJECTS (of the 3 supported)
     │              └── teaches 1-11 CLASSES per subject
     │
     └──1:N──► CLASS (134)           [globally unique ID]
                    │
                    ├── belongs to 1 GRADE (8 or 9)
                    ├── has 1-2 TEACHERS per subject (co-teaching)
                    └── has 1-35 STUDENTS (avg 23)
                              │
                              └── STUDENT (3,064) [globally unique ID]
                                       ├── in exactly 1 CLASS (use latest)
                                       ├── has 1-3 SUBJECTS
                                       ├── has N SCORES
                                       └── has N ABSENCES
```

**Cardinality Rules:**

| Relationship | Cardinality | Notes |
|--------------|-------------|-------|
| Teacher → School | 1:1 | Each teacher in exactly 1 school |
| Teacher → Subjects | 1:N | Teacher can teach 1-3 subjects |
| Teacher → Classes | 1:N | Teacher can teach 1-11 classes per subject |
| Class → Grade | 1:1 | Each class has exactly 1 grade (8 or 9) |
| Class → Teachers (per subject) | 1:1 or 1:2 | Co-teaching exists (47 pairs) |
| Student → Class | 1:1* | Use latest class for 22 exceptions |
| Student → Subjects | 1:N | Most have all 3 subjects |

**Authorization Model:**

Frontend is trusted for authorization. Backend does NOT validate that a teacher actually teaches a given class/subject combination. The `teacher_id` parameter in requests is used for **attribution and logging only**, not access control.

---

### Required Filters

**Always apply these filters when loading benchmark data:**

```python
# Filter 1: Current academic year only
df = df[df['academic_year'] == '2025-2026']

# Filter 2: Supported subjects only
SUPPORTED_SUBJECTS = ['Алгебра', 'Українська мова', 'Історія України']
df = df[df['discipline_name'].isin(SUPPORTED_SUBJECTS)]

# Filter 3: For multi-class students, use latest class
# (22 students have records in 2 classes due to transfers)
# Implementation: When querying student's class, use most recent lesson_date
```

**Why these filters:**
1. **2025-2026 only**: Old year data shows students in different grades (8→9 progression), causing confusion
2. **3 subjects only**: Only these have textbook content for RAG
3. **Latest class**: 22 students transferred mid-year, using latest avoids duplicates

---

### Edge Cases

#### 1. Multi-Class Students (22 students)

**Problem:** 22 students appear in 2 classes (0.7% of total).

**Analysis:**
- 12 are clear transfers (sequential dates, no overlap)
- 10 have overlapping periods (transition)
- Only 11 actual conflict records (same subject, same day, different classes)

**Solution:** For each student, use their **latest class** only (based on most recent `lesson_date`).

```python
def get_student_class(student_id: int, df: pd.DataFrame) -> int:
    student_df = df[df['student_id'] == student_id]
    latest = student_df.sort_values('lesson_date', ascending=False).iloc[0]
    return latest['class_id']
```

#### 2. Co-Teaching (47 class-subject pairs)

**Problem:** 47 class-subject combinations have 2 teachers.

**Analysis:**
- Both teachers teach all students in the class
- They teach concurrently throughout the year
- This is valid co-teaching, not data error

**Solution:** Both teachers see the class when they log in. No special handling needed.

#### 3. NULL topic_name (2,766 records)

**Problem:** Some records have NULL topic_name.

**Analysis:** All NULL topic_name records have `is_final_score=1`. These are semester summary grades.

**Solution:**
- For topic analysis: Exclude NULL topic_name records
- For grade averages: Include all records (they're still valid grades)

#### 4. is_final_score Column

**Problem:** 99.96% of records have `is_final_score=1`, making it useless for filtering.

**Solution:** IGNORE this column entirely.

#### 5. Topic Name Data Quality

**Problem:** Topics in `benchmark_scores` (~29,620 unique) and `benchmark_absences` (~27,938 unique) are free-text with quality issues.

**Analysis of both scores and absences:**
- Free-text entered by teachers with spelling variations, whitespace issues, punctuation inconsistencies
- Unicode apostrophe variants (8+ different characters for apostrophe)
- Same topic with/without trailing period: "Підсумковий урок" vs "Підсумковий урок."
- Leading/trailing whitespace: 6.98% of absences have trailing spaces
- Multiple consecutive spaces: 12.02% of absences
- Pipe delimiters in absences (2.01%): "Topic A | Topic B" format
- Lesson prefixes: "Тема 5.", "Урок 12.", "§5." etc.
- Parenthetical suffixes: "(повторення)", "(продовження)"
- Only 2 direct matches with TOC topics (237 structured)

**Solution:** Apply **enhanced normalization** before using `topic_name`:

```python
import re
import unicodedata

def normalize_topic_name(topic: str) -> str | None:
    """
    Normalize topic_name for consistent grouping.
    Used by EP3, EP5, EP6 for gap analysis and display.
    """
    if not topic:
        return None

    # Strip whitespace
    topic = topic.strip()
    if not topic:
        return None

    # Lowercase for consistent grouping
    topic = topic.lower()

    # Normalize unicode (NFKC form)
    topic = unicodedata.normalize('NFKC', topic)

    # Normalize apostrophes to standard '
    topic = re.sub(r"[''ʼ`´*]", "'", topic)

    # Remove lesson/topic prefixes: "Тема 5.", "Урок 12.", "§5."
    topic = re.sub(r'^(тема|урок|§|параграф)\s*\d*\.?\s*', '', topic)

    # Remove parenthetical suffixes: "(повторення)", "(продовження)"
    topic = re.sub(r'\s*\([^)]*\)\s*$', '', topic)

    # Remove trailing punctuation
    topic = topic.rstrip(".,;:!?")

    # Collapse multiple spaces
    topic = " ".join(topic.split())

    return topic if topic else None
```

**Usage contexts:**
- **EP3 gap analysis**: Normalize before grouping weak topics
- **EP5 problematic_topics**: Normalize, aggregate, then `.title()` for display
- **EP5 skipped_lessons**: Normalize + handle pipes + truncate long topics
- **EP6 recommendation**: Normalize for topic mentions in LLM prompt

For gap analysis (EP3, EP6), use normalized `topic_name` for grouping. RAG retrieval uses `topic_definition` (from frontend), not score topic names.

---

### Endpoint Data Requirements

| EP | Endpoint | Data Sources | Computed Fields |
|----|----------|--------------|-----------------|
| 1 | GET /teacher/{id} | scores | GROUP BY class_id, grade, discipline_name |
| 2 | POST /teacher/students | scores | AVG(score), quartile-based levels |
| 3.1 | POST /teacher/notes/by-level | scores, absences | Filter by level, get context |
| 3.2 | POST /teacher/notes/individual | scores, absences | Filter by student_ids |
| 4 | POST /teacher/test/generate | questions, toc, pages | RAG search + LLM |
| 5 | POST /teacher/student/details | scores, absences | AVG, level, skipped, problematic topics |
| 6 | POST /teacher/student/rec. | scores, absences | LLM generates text |
| 7 | POST /solver | (none) | LLM solves questions |
| 8 | GET /student/{id} | scores | class_id, grade, subjects |
| 9 | POST /student/check-open | toc, pages | RAG + LLM evaluation |
| 10 | POST /student/test-feedback | scores | LLM generates feedback |

**Level Computation (for EP2, EP5):**

```python
def compute_level(student_avg: float, q1: float, q3: float) -> str:
    """Quartile-based level assignment."""
    if student_avg < q1:
        return "weak"
    elif student_avg > q3:
        return "strong"
    else:
        return "medium"

# Q1 = 25th percentile, Q3 = 75th percentile
# IMPORTANT: Computed per class PER SUBJECT (not across all subjects)
# Example: For EP2 with class_id=4, subject="Алгебра":
#   - Filter scores to class_id=4 AND discipline_name="Алгебра"
#   - Compute student averages within that filtered set
#   - Q1/Q3 are percentiles of those averages
```

### Two Grading Systems

The architecture uses **two different systems** for different purposes:

#### 1. Quartile-Based Levels (Relative)

Used for: **Student classification** (EP2, EP5)

```python
# Relative to class performance
Q1 = 25th percentile of class
Q3 = 75th percentile of class

if student_avg < Q1: "weak"      # Bottom 25%
elif student_avg > Q3: "strong"  # Top 25%
else: "medium"                    # Middle 50%
```

**Why:** A student with 7.5 average might be "strong" in a struggling class but "weak" in a high-performing class. Relative comparison is fair.

#### 2. Absolute Grade Thresholds (Fixed)

Used for: **Gap analysis** (EP3, EP6 - finding problematic topics)

```python
GRADE_BAD = 6       # score < 6 = bad grade
GRADE_AVERAGE = 9   # 6-9 = average
GRADE_GOOD = 10     # score >= 10 = good grade
```

**Why:** When identifying topics where students struggle, we need absolute standards. A score of 4 is objectively bad regardless of class performance.

#### Summary

| System | Used For | Logic |
|--------|----------|-------|
| Quartile | EP2, EP5 (student classification) | Relative to class |
| Absolute | EP3, EP6 (gap analysis) | Fixed thresholds |

---

## Phase 2: LLM Abstraction Layer

### Source

Existing implementation in `Archive better ukr 2/scripts/agentic_rag_solution/utils/llm_client.py`

### LLM Provider

- **Model**: `mamay` (Ukrainian LLM)
- **Embedding Model**: `text-embedding-qwen`
- **API**: OpenAI-compatible (AsyncOpenAI)
- **Base URL**: `http://146.59.127.106:4000`

### LLMClient Interface

```python
class LLMClient:
    """OpenAI-compatible client for mamay LLM."""

    async def generate(
        self,
        prompt: str,
        temperature: float = 0.0,
        max_tokens: int = 500,
        json_mode: bool = False
    ) -> str:
        """Generate text completion."""

    async def generate_json(
        self,
        prompt: str,
        temperature: float = 0.0,
        max_tokens: int = 500,
    ) -> Dict[str, Any]:
        """Generate JSON with robust parsing (fallbacks for malformed JSON)."""

    async def embed(self, text: str) -> List[float]:
        """Generate embedding vector (4096 dims)."""
```

### JSON Parsing Strategy

The LLM client has robust JSON parsing with multiple fallbacks:
1. Direct parse
2. Clean text and parse (remove escape sequences)
3. Extract from code blocks
4. Regex extraction for common patterns

### Configuration

```python
class Settings(BaseSettings):
    api_key: str = ""
    api_base_url: str = "http://146.59.127.106:4000"
    model: str = "mamay"
    embedding_model: str = "text-embedding-qwen"

    # Generation
    generation_temperature: float = 0.0
    max_tokens: int = 500
```

### Integration Strategy

**Minimal changes approach:**
1. Copy `llm_client.py` to `backend/app/rag/utils/`
2. Update imports to use backend's config
3. Expose via `get_llm_client()` singleton

---

## Phase 3: RAG Layer

### Source

Existing implementation in `Archive better ukr 2/scripts/agentic_rag_solution/`

### Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              RAG PIPELINE                                    │
└─────────────────────────────────────────────────────────────────────────────┘

  Query (question_text, subject, grade)
       │
       ▼
  ┌─────────────────┐
  │ HybridRetriever │
  │                 │
  │ ┌─────────────┐ │
  │ │   BM25      │ │──────► Keyword matching (Ukrainian lemmatization)
  │ └─────────────┘ │
  │        +        │
  │ ┌─────────────┐ │
  │ │   Vector    │ │──────► Semantic search (query embedded at runtime)
  │ └─────────────┘ │
  │        +        │
  │ ┌─────────────┐ │
  │ │ RRF Fusion  │ │──────► Combine rankings
  │ └─────────────┘ │
  └────────┬────────┘
           │
           ▼
  Retrieved Documents (top_k pages)
           │
           ▼
  ┌─────────────────┐
  │ format_context  │──────► Build prompt context string
  └────────┬────────┘
           │
           ▼
  ┌─────────────────┐
  │ Expert Prompt   │──────► Subject-specific prompt template
  └────────┬────────┘
           │
           ▼
  ┌─────────────────┐
  │   LLM Call      │──────► mamay model (JSON response)
  └────────┬────────┘
           │
           ▼
  Answer + Reasoning + References
```

### Embedding Strategy

**Pre-computed (loaded from parquet at startup):**
- Page embeddings (`page_text_embedding` in `pages_for_hackathon.parquet`)
- Topic embeddings (`topic_embedding` in `toc_for_hackathon.parquet`)
- Dimension: 4096 (text-embedding-qwen model)

**Computed at runtime (API calls):**
- **Query embeddings**: Every search query is embedded via `llm_client.embed(query)`
- Called in 2 places:
  1. `HybridRetriever._vector_search()` - embeds the search query
  2. `TopicRetriever.find_relevant_topics()` - embeds the question for TOC matching

**Similarity computation:**
- Both query and document vectors are L2-normalized
- Cosine similarity: `np.dot(normalized_docs, normalized_query)`

**Zero-LLM retrieval philosophy:**
- Retrieval uses ONLY embedding API calls, no LLM generation calls
- LLM is called only AFTER retrieval, for answer generation

### Key Components

#### 1. HybridRetriever (`hybrid_retriever.py`)

**Features:**
- BM25 keyword search (rank_bm25)
- Vector semantic search (cosine similarity on pre-computed embeddings)
- RRF fusion for combining results
- Ukrainian lemmatization (pymorphy2)
- Dual-field BM25 for Ukrainian (surface + lemma tokens)

**Subject-Specific Settings:**
```python
SUBJECT_CONFIGS = {
    "Українська мова": SubjectConfig(
        retrieval_top_k=40,
        use_dual_field_bm25=True,
        rrf_bm25_weight=1.2,  # BM25 more important for grammar
    ),
    "Алгебра": SubjectConfig(
        retrieval_top_k=4,
        # Full page content (no truncation) for worked examples
    ),
    "Історія України": SubjectConfig(
        retrieval_top_k=4,
        retrieval_boost=1.2,
    ),
}
```

#### 2. DataLoader (`data_loader.py`)

```python
class DataLoader:
    def load_textbook_pages() -> pd.DataFrame  # With embeddings
    def load_toc() -> pd.DataFrame              # Topics with summaries
    def get_pages_for_subject_grade(subject, grade) -> pd.DataFrame
    def get_topics_for_subject_grade(subject, grade) -> pd.DataFrame
```

**Theory-Only Filtering:** By default, filters to pages where `page_metadata.contains_theory=True`

#### 3. Expert Prompts (`unified_generate.py`)

Each subject has specialized expert prompts:

**Ukrainian Language:**
```
Ти — експерт з української мови.

КЛЮЧОВІ ПРАВИЛА:
• Безособове речення: немає і НЕ МОЖЕ бути підмета
• Узагальнено-особове: дія для ВСІХ, 2 ос. одн.
...
```

**Algebra:**
```
Ти — експерт з математики.

ФОРМУЛИ:
• Геометрична прогресія: q = b₂/b₁
• Парабола: a>0 вгору, a<0 вниз
...
```

**History:**
```
Знайди в контексті факти, дати, події що стосуються питання.
Порівняй кожен варіант з інформацією в контексті.
```

### LangGraph Workflow

```python
# graph.py - Simple 2-node pipeline
def build_v4_graph() -> StateGraph:
    graph = StateGraph(AgenticRAGState)

    graph.add_node("smart_retrieve", smart_retrieve_node)
    graph.add_node("generate_answer", generate_answer_node)

    graph.set_entry_point("smart_retrieve")
    graph.add_edge("smart_retrieve", "generate_answer")
    graph.add_edge("generate_answer", END)

    return graph.compile()
```

**State Definition:**
```python
class AgenticRAGState(TypedDict, total=False):
    # Input
    question_id: str
    question_text: str
    subject: str
    grade: int
    answers: List[str]

    # Retrieval
    retrieved_docs: List[Dict]
    retrieval_score: float
    topic_match: Optional[Dict]

    # Generation
    context_text: str
    final_answer_index: int
    final_confidence: float
    final_reasoning: str
    references: List[Dict]

    # Metadata
    llm_calls_count: int
```

### Main Entry Point

```python
async def solve_question(question: Dict[str, Any]) -> SolverResult:
    """
    Solve a single question using RAG pipeline.

    Args:
        question: Dict with keys:
            - question_id
            - question_text
            - global_discipline_name (subject)
            - grade
            - answers

    Returns:
        SolverResult with answer_index, confidence, reasoning, references
    """
```

### Integration Strategy

**Copy existing files with minimal changes:**

```
Archive better ukr 2/scripts/agentic_rag_solution/
    └── Copy to → backend/app/rag/

Changes needed:
1. Update imports (..config → app.config)
2. Update data paths (use backend's data/ folder)
3. Expose main functions via __init__.py:
   - solve_question()
   - get_retriever()
   - get_llm_client()
```

### Complete File Inventory

**Core Files:**

| Source | Purpose | Lines |
|--------|---------|-------|
| `config.py` | Settings, SubjectConfig, paths | ~180 |
| `state.py` | AgenticRAGState TypedDict, SolverResult | ~140 |
| `graph.py` | LangGraph build, solve_question() entry point | ~150 |

**Utils (app/rag/utils/):**

| Source | Purpose | Key Classes/Functions |
|--------|---------|----------------------|
| `llm_client.py` | OpenAI-compatible client | `LLMClient`, `generate_json_safe()` |
| `data_loader.py` | Parquet loading, caching | `DataLoader`, `get_data_loader()` |
| `hybrid_retriever.py` | BM25 + Vector + RRF | `HybridRetriever`, `format_context()` |
| `topic_retriever.py` | Two-stage TOC→Pages retrieval | `TopicRetriever`, `format_context_with_topics()` |
| `passage_extractor.py` | V8 paragraph extraction | `PassageExtractor`, `PassageConfig` |
| `reranker.py` | Cross-encoder reranking | `Reranker` (BGE-reranker-v2-m3) |

**Nodes (app/rag/nodes/):**

| Source | Purpose | Notes |
|--------|---------|-------|
| `smart_retrieve.py` | Main retrieval node | Special Ukrainian pipeline |
| `unified_generate.py` | Answer generation | Expert prompts per subject |
| `agent_decision.py` | Agent decision (not used) | For future retry logic |

**Prompts (app/rag/prompts/):**

| Source | Purpose | Content |
|--------|---------|---------|
| `ukrainian_rules.py` | Ukrainian grammar rules | Punctuation, syntax, morphology |
| `algebra_rules.py` | Math formulas | Equations, progressions, functions |
| `history_rules.py` | History methodology | Dates, cause-effect, documents |

### Advanced Features

#### 1. Ukrainian-Specific Retrieval Pipeline

```
Question → HybridRetriever (BM25+Vector, 40 candidates)
       → TopicRetriever (TOC embedding match)
       → Topic Boosting (mark matched topic pages)
       → Cross-Encoder Reranking (BGE-v2-m3, top 10)
       → PassageExtractor (BM25 on paragraphs)
       → Final Context (focused passages)
```

#### 2. Cross-Encoder Reranking (`reranker.py`)

- Model: `BAAI/bge-reranker-v2-m3` (multilingual)
- Option-aware reranking: considers question + answer options
- Score combination: 70% question score + 30% best option score

#### 3. Passage Extraction (`passage_extractor.py`)

For Ukrainian grammar questions:
- Split pages into paragraphs (50-800 chars)
- BM25 ranking with query + answer options
- Select top-5 passages with page diversity (max 3 pages)
- Expected +5-15% accuracy improvement

#### 4. Mega-Prompts with Embedded Rules

Each subject has comprehensive rules embedded in the prompt:
- **Ukrainian**: Punctuation, sentence types, parts of speech
- **Algebra**: Quadratic equations, progressions, functions
- **History**: Chronological reasoning, fact verification

### Dependencies (from requirements.txt)

**Required:**
```
openai>=1.10.0        # LLM client
pandas>=2.1.0         # Data processing
pyarrow>=14.0.0       # Parquet
numpy>=1.24.0         # Numerical
langgraph>=0.2.0      # Workflow
langchain-core>=0.3.0 # LLM framework
rank-bm25>=0.2.2      # BM25 search
```

**Optional (for advanced features):**
```
sentence-transformers  # Cross-encoder reranking
pymorphy2             # Ukrainian lemmatization
```

### Files to Copy

| Source | Destination | Changes |
|--------|-------------|---------|
| `config.py` | `app/rag/config.py` | Merge with app/config.py |
| `state.py` | `app/rag/state.py` | None |
| `graph.py` | `app/rag/graph.py` | Update imports |
| `utils/llm_client.py` | `app/rag/utils/llm_client.py` | Update config import |
| `utils/data_loader.py` | `app/rag/utils/data_loader.py` | Update paths |
| `utils/hybrid_retriever.py` | `app/rag/utils/hybrid_retriever.py` | Update imports |
| `utils/topic_retriever.py` | `app/rag/utils/topic_retriever.py` | Update imports |
| `utils/passage_extractor.py` | `app/rag/utils/passage_extractor.py` | Update imports |
| `utils/reranker.py` | `app/rag/utils/reranker.py` | None |
| `nodes/smart_retrieve.py` | `app/rag/nodes/smart_retrieve.py` | Update imports |
| `nodes/unified_generate.py` | `app/rag/nodes/unified_generate.py` | Update imports |
| `prompts/ukrainian_rules.py` | `app/rag/prompts/ukrainian_rules.py` | None |
| `prompts/algebra_rules.py` | `app/rag/prompts/algebra_rules.py` | None |
| `prompts/history_rules.py` | `app/rag/prompts/history_rules.py` | None |

### Archive Data Folder

The archive contains its own data copy with **two embedding types**:

```
Archive better ukr 2/Lapathon2026 Mriia public files/
├── benchmark_absences.parquet      (6.5MB)
├── benchmark_scores.parquet        (15MB)
├── lms_questions_dev.parquet       (44KB)
├── mriia_fields.md                 (field documentation)
├── gemini-embedding-001/           # Google Gemini embeddings
│   ├── pages_for_hackathon.parquet     (33MB)
│   └── toc_for_hackathon_with_subtopics.parquet (17MB)
└── text-embedding-qwen/            # Qwen embeddings (USED BY CODE)
    ├── pages_for_hackathon.parquet     (27MB)
    └── toc_for_hackathon_with_subtopics.parquet (14MB)
```

**Note:** The code uses `text-embedding-qwen` embeddings. Gemini embeddings are alternative.

### Benchmark & Testing Scripts

| Script | Purpose |
|--------|---------|
| `run_agentic_benchmark.py` | Full benchmark runner with per-subject/grade metrics |
| `compare_models.py` | Compare different LLM models (mamay vs GPT) |

**Benchmark usage:**
```bash
# Full benchmark
python scripts/agentic_rag_solution/run_agentic_benchmark.py

# Test single question
python scripts/agentic_rag_solution/run_agentic_benchmark.py --test --question-idx 0

# Filter by subject
python scripts/agentic_rag_solution/run_agentic_benchmark.py --subject "Українська мова"
```

### Public API Exports

**Main package (`__init__.py`):**
```python
from .graph import solve_question, build_agentic_graph
from .state import AgenticRAGState, SolverResult

__all__ = ["solve_question", "build_agentic_graph", "AgenticRAGState", "SolverResult"]
```

**Utils:**
```python
__all__ = ["HybridRetriever", "LLMClient", "generate_json_safe", "DataLoader"]
```

**Nodes:**
```python
__all__ = ["smart_retrieve_node", "agent_decision_node", "unified_generate_node"]
```

**Prompts:**
```python
__all__ = [
    "UKRAINIAN_RULES", "get_ukrainian_mega_prompt",
    "ALGEBRA_RULES", "get_algebra_mega_prompt",
    "HISTORY_RULES", "get_history_mega_prompt",
]
```

### API Credentials (from code)

```python
API_KEY = "sk-VbzOVVk7InXaN-9t9BM60g"  # In compare_models.py
BASE_URL = "http://146.59.127.106:4000"
MODEL = "mamay"
EMBEDDING_MODEL = "text-embedding-qwen"
```

### Documentation Found

- `mriia_fields.md` - Complete field descriptions for all parquet files (matches our Phase 1 analysis)

---

### Verification Results

#### 1. Data Compatibility ✅

| Check | Backend | Archive | Match |
|-------|---------|---------|-------|
| Pages shape | (1318, 17) | (1318, 17) | ✅ |
| Pages columns | 17 | 17 | ✅ |
| TOC shape | (237, 23) | (237, 23) | ✅ |
| TOC columns | 23 | 23 | ✅ |
| Embedding dims | 4096 | 4096 | ✅ |

**Conclusion:** Backend and archive data are **identical**. No migration needed.

#### 2. Dependency Comparison

**Missing in backend (MUST ADD):**
```
openai>=1.10.0        # Required for LLM client
pyarrow>=14.0.0       # Required for parquet reading
rank-bm25>=0.2.2      # Required for BM25 search
tqdm>=4.66.0          # Progress bars
```

**Version updates needed:**
```
langgraph>=0.2.0      # Backend has >=0.0.20
langchain-core>=0.3.0 # Backend has langchain>=0.1.0
```

**Optional (for advanced features):**
```
sentence-transformers  # Cross-encoder reranking
pymorphy2             # Ukrainian lemmatization
```

#### 3. Hardcoded Paths to Update

| File | Path | Change to |
|------|------|-----------|
| `config.py` | `data_dir: str = "Lapathon2026 Mriia public files"` | `data_dir: str = "data"` |

#### 4. Integration Checklist

- [ ] Copy RAG files to `backend/app/rag/`
- [ ] Update `requirements.txt` with missing deps
- [ ] Update `config.py` data paths
- [ ] Update all relative imports
- [ ] Add `__init__.py` exports
- [ ] Test `solve_question()` works

---

## Phase 4: Service Layer

### Overview

The archive RAG is a **benchmark solver** (multiple-choice questions). The API needs broader capabilities. This phase defines how to bridge the gap.

### Endpoint Classification

| EP | Name | Type | RAG? | Student Data? |
|----|------|------|------|---------------|
| EP1 | Get Teacher Data | Data only | No | Query |
| EP2 | Get Student List | Data only | No | Query + compute levels |
| EP3 | Generate Notes | RAG + LLM | Yes | Analyze gaps |
| EP4 | Generate Test | RAG + LLM | Yes | No |
| EP5 | Get Student Details | Data only | No | Query + aggregate |
| EP6 | Get Recommendation | LLM only | No | Full analysis |
| EP7 | Solver | RAG + LLM | Yes | No |
| EP8 | Get Student Data | Data only | No | Query |
| EP9 | Check Open Question | RAG + LLM | Yes | Grade lookup |
| EP10 | Test Feedback | LLM only | No | Provided in request |

### Grade Thresholds

```python
# For student analysis (EP3, EP5, EP6)
GRADE_BAD = 6      # score < 6 = bad
GRADE_GOOD = 10    # score >= 10 = good
# 6-9 = average
```

---

### Data-Only Endpoints (EP1, EP2, EP5, EP8)

Pure pandas operations on parquet files.

#### EP5: Get Student Details (with Topic Normalization)

Returns detailed info about a specific student including processed topic data.

**Input:** `class_id`, `subject`, `teacher_id`, `student_id`

**Output:**
```typescript
{
  "average_subject_grade": number,
  "level": "weak" | "medium" | "strong",
  "skipped_lessons": SkippedLesson[],
  "problematic_topics": ProblematicTopic[]
}
```

**Implementation for `problematic_topics`:**

```python
def get_problematic_topics(self, student_id: int, subject: str) -> List[ProblematicTopic]:
    """Get topics where student has low grades, with normalization."""
    scores = self.data_loader.load_scores()
    student_scores = scores[
        (scores['student_id'] == student_id) &
        (scores['discipline_name'] == subject) &
        (scores['score_numeric'] < GRADE_BAD)  # < 6
    ].copy()

    # Skip if no low scores
    if len(student_scores) == 0:
        return []

    # Normalize topic names for grouping
    student_scores['normalized_topic'] = student_scores['topic_name'].apply(normalize_topic_name)

    # Filter out None/empty topics
    student_scores = student_scores[student_scores['normalized_topic'].notna()]

    # Group by normalized topic and compute average
    grouped = student_scores.groupby('normalized_topic').agg({
        'score_numeric': 'mean'
    }).reset_index()

    # Sort by average score (worst first)
    grouped = grouped.sort_values('score_numeric')

    return [
        ProblematicTopic(
            topic=row['normalized_topic'].title(),  # Capitalize for display
            average_score=round(row['score_numeric'], 1)
        )
        for _, row in grouped.iterrows()
    ]
```

**Implementation for `skipped_lessons`:**

```python
def get_skipped_lessons(self, student_id: int, subject: str) -> List[SkippedLesson]:
    """Get lessons student missed, with topic normalization."""
    absences = self.data_loader.load_absences()
    student_absences = absences[
        (absences['student_id'] == student_id) &
        (absences['discipline_name'] == subject)
    ]

    skipped = []
    for _, row in student_absences.iterrows():
        topic = normalize_topic_name(row['topic_name'])

        # Handle null/empty topics
        if not topic:
            topic = "тема невідома"

        # Handle pipe-delimited combined topics - take first part
        if '|' in topic:
            topic = topic.split('|')[0].strip()

        # Truncate very long topics (>100 chars) for display
        if len(topic) > 100:
            topic = topic[:97] + "..."

        skipped.append(SkippedLesson(
            date=row['lesson_date'].strftime('%Y-%m-%d'),
            topic=topic.title()  # Capitalize for display
        ))

    # Sort by date (most recent first)
    skipped.sort(key=lambda x: x.date, reverse=True)

    return skipped
```

**Key differences:**
- `problematic_topics`: **Aggregated** by normalized topic with average score
- `skipped_lessons`: **Individual entries** with date, not aggregated (teacher needs to see each absence)

---

### LLM-Only Endpoints (EP6, EP10)

#### EP6: Get Student Recommendation

**Reuses EP5 data** - EP6 internally calls EP5's data methods to avoid duplicate queries.

```
Input: student_id, subject

Flow:
1. Call EP5's data methods to get:
   - average_subject_grade (from EP5)
   - level (from EP5)
   - problematic_topics (from EP5) → becomes "bad topics"
   - skipped_lessons (from EP5) → becomes "missed topics"
2. Additionally query good topics (score ≥ 10) - not in EP5
   └── This is the ONLY additional query EP6 makes

LLM Prompt includes:
- Subject name
- Average grade in subject (from EP5)
- Level in subject (from EP5)
- Topics with good grades (additional query)
- Topics with bad grades (from EP5 problematic_topics)
- Missed topics (from EP5 skipped_lessons)

Output: feedback (balanced recommendation in Ukrainian)
- Praise good performance
- Flag problem areas
- Actionable recommendations
```

**Implementation note:** The `StudentAnalysisService` should expose the EP5 data computation as reusable internal methods that both EP5 endpoint and EP6 can call.

#### EP10: Get Test Feedback

```
Input: student_id, subject, questions[] (with correctness provided by frontend)

Flow:
1. Group incorrect answers by topic/subtopics
2. Count correct vs total

LLM Prompt includes:
- Score (e.g., 7/10)
- Topics/subtopics of incorrect answers
- Topics/subtopics of correct answers

Output: feedback
- Overall result
- What student did well
- What needs more study
```

**Note:** No RAG needed - frontend provides all question data including correctness.

---

### RAG + LLM Endpoints

#### Shared Retrieval Pattern

All RAG endpoints use the same retrieval pipeline from archive:

```
Query (question or topic_definition)
    │
    ▼
HybridRetriever (BM25 + Vector + RRF)
    │
    ▼
format_context() → context string
    │
    ▼
LLM with subject-specific prompt
```

#### EP7: Solver (Single Question)

Solves one question at a time with RAG-grounded explanation.

| Aspect | Value |
|--------|-------|
| Input | subject, grade, question (single string) |
| RAG query | question text |
| LLM task | Solve + explain step by step |
| Output | question, answer_explained |

**Flow:**
```
Request (subject, grade, question)
    │
    ▼
┌─────────────────┐
│ RAG Retrieve    │──► Textbook context for subject/grade
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ LLM Generate    │──► Solve with SUBJECT_RULES + context
└────────┬────────┘
         │
         ▼
Response { question, answer_explained }
```

**Shared components with EP9:**
- HybridRetriever
- format_context()
- SUBJECT_RULES constants (UKRAINIAN_RULES, ALGEBRA_RULES, HISTORY_RULES)

**Prompt template:**
- "Solve this question step by step, explain the answer using the textbook context"

**Important:** EP7 does NOT support batch processing. To solve multiple questions, call this endpoint multiple times. The full-pipeline integration test does exactly this - loops through ~30 generated questions.

---

#### EP9: Check Open Question

Evaluates student's answer to an open-ended question.

| Aspect | Value |
|--------|-------|
| Input | student_id, subject, topic, subtopics, question, answer |
| RAG query | question text |
| Grade | lookup from student_id (default: 8) |
| LLM task | Evaluate correctness, provide feedback |
| Output | correct (bool), feedback |

**Prompt template:**
- "Evaluate if student's answer is correct, provide constructive feedback"

**Note on archive prompts:** The existing `get_*_mega_prompt()` functions are MC-specific (analyze options 0-3, return answer_index). We reuse `SUBJECT_RULES` constants but need new prompt templates for solving/evaluating.

#### EP3: Generate Notes

```
Input: class_id, teacher_id, subject, topic_definition
     + level_list (EP3.1) OR student_list (EP3.2)

Flow:
1. GET TARGET STUDENTS
   ├── EP3.1: filter by level_list
   └── EP3.2: use student_list directly

2. COMPUTE EFFECTIVE LEVEL (for content adaptation)
   └── Weighted average of student grades → map to level

   ```python
   def get_effective_level(student_ids: List[int], subject: str) -> str:
       """Compute effective level from student group using weighted average."""
       # Get average grades for each student in subject
       student_avgs = [get_student_avg(sid, subject) for sid in student_ids]
       # Weighted average (could weight by recency, but simple avg for MVP)
       group_avg = sum(student_avgs) / len(student_avgs)

       # Map to level using absolute thresholds
       if group_avg < 5:
           return "weak"
       elif group_avg > 8:
           return "strong"
       else:
           return "medium"
   ```

   For mixed levels (e.g., level_list=["weak", "strong"]):
   → Generate middle ground content (not lowest level)

3. ANALYZE GAPS (for teacher_notes) - ONLY RELATED TOPICS
   a. Get all weak topics for target students:
      ├── scores WHERE student_id IN (...) AND score < 6
      │   → GROUP BY normalized(topic_name) → counts
      └── absences WHERE student_id IN (...)
          → GROUP BY normalized(topic_name) → counts

   b. FILTER to topics related to topic_definition using SEMANTIC SEARCH:
      ```python
      # Embed topic_definition
      topic_embedding = await llm_client.embed(topic_definition)

      # For each unique weak topic_name, compute similarity
      related_topics = []
      for topic_name in weak_topics:
          topic_emb = await llm_client.embed(topic_name)
          similarity = cosine_similarity(topic_embedding, topic_emb)
          if similarity > 0.6:  # threshold
              related_topics.append(topic_name)
      ```

   Note: Apply normalize_topic_name() before grouping

4. RAG RETRIEVE (for contents)
   └── topic_definition → textbook content

5. LLM GENERATE (with level-adapted prompt)
   Prompt includes:
   - LEVEL INSTRUCTION (see below)
   - Gap data: "X students had bad grades in 'topic_name'" (only related topics)
   - Gap data: "Y students missed 'topic_name'" (only related topics)
   - Textbook context for topic_definition
   - Student levels summary

Output:
├── title: lesson title
├── teacher_notes:
│   - Gap warnings: "12 учнів мали низькі оцінки з 'Дискримінант'"
│   - Teaching tips: "Рекомендуємо повторити..."
└── contents: lesson material adapted to effective level
```

**Level-Adapted Content Generation:**

```python
LEVEL_INSTRUCTIONS = {
    "weak": """
ІНСТРУКЦІЇ ДЛЯ СЛАБКОГО РІВНЯ:
- Пиши ДУЖЕ простою мовою
- Пояснюй кожен крок детально, ніби учень бачить це вперше
- Використовуй найпростіші приклади з числами 1, 2, 3
- Уникай складних термінів або одразу пояснюй їх
- Додавай підказки типу "Пам'ятай, що...", "Зверни увагу..."
- Повторюй ключові формули кілька разів
""",
    "medium": """
ІНСТРУКЦІЇ ДЛЯ СЕРЕДНЬОГО РІВНЯ:
- Пиши зрозумілою мовою зі стандартними поясненнями
- Наводь 2-3 приклади різної складності
- Терміни можна використовувати з коротким поясненням
- Баланс між теорією та практикою
""",
    "strong": """
ІНСТРУКЦІЇ ДЛЯ СИЛЬНОГО РІВНЯ:
- Пиши стисло, без зайвих пояснень очевидних речей
- Фокусуйся на нюансах, винятках, складних випадках
- Наводь нестандартні приклади
- Можна згадувати зв'язки з іншими темами
- Учні вже знають базу - не повторюй її
"""
}
```

**Key decisions:**
1. teacher_notes warns about weak topics but contents only covers topic_definition
2. Gap analysis filtered to topics RELATED to topic_definition via semantic search
3. Content complexity adapts to effective level (weighted average, middle ground for mixed)

**Edge case: No related topics found**

If semantic search finds NO topics with similarity > 0.6:
- `teacher_notes` should include: "Немає даних про проблемні теми, пов'язані з цією темою."
- Don't fall back to unrelated topics - that would confuse the teacher
- The lesson content (`contents`) is still generated normally from RAG retrieval

#### EP4: Generate Test Pool (Chunked Generation)

Generates ~30 questions by difficulty level in 3 separate LLM calls for reliability.

**Why chunked?** Asking LLM to generate 30 structured questions in one call is unreliable:
- LLMs can't count accurately
- Large JSON output increases malformed response risk
- Single failure = entire request fails
- Token limits may truncate output

**Flow:**
```
Request (class_id, teacher_id, subject, topic_definition)
    │
    ▼
┌─────────────────┐
│ RAG Retrieve    │──► Textbook context (done ONCE, shared)
└────────┬────────┘
         │
         ├──────────────────┬──────────────────┐
         ▼                  ▼                  ▼
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│ Generate EASY   │ │ Generate MEDIUM │ │ Generate HARD   │
│ (~10 questions) │ │ (~10 questions) │ │ (~10 questions) │
└────────┬────────┘ └────────┬────────┘ └────────┬────────┘
         │                   │                   │
         │    (can run in parallel)              │
         │                   │                   │
         └───────────────────┼───────────────────┘
                             │
                             ▼
                  ┌─────────────────┐
                  │ Validate + Merge│
                  └────────┬────────┘
                           │
                           ▼
                  Response (~30 questions)
```

**Implementation:**
```python
async def generate_test(self, class_id, teacher_id, subject, topic_definition) -> TestResponse:
    # 1. Derive grade from class_id
    grade = self.get_grade_for_class(class_id)

    # 2. RAG retrieve once (shared context)
    context = await self.retriever.retrieve(topic_definition, subject, grade)

    # 3. Generate in 3 batches (can parallelize)
    difficulties = ["easy", "medium", "hard"]
    tasks = [
        self._generate_batch(context, subject, difficulty, count=10, topic_definition)
        for difficulty in difficulties
    ]
    batches = await asyncio.gather(*tasks)

    # 4. Merge and validate
    all_questions = []
    for batch in batches:
        all_questions.extend(batch)

    return TestResponse(title=f"Тест: {topic_definition}", questions=all_questions)

async def _generate_batch(self, context, subject, difficulty, count, topic_definition) -> List[Question]:
    prompt = f"""
Згенеруй {count} питань рівня "{difficulty}" з теми "{topic_definition}".

Контекст з підручника:
{context}

Вимоги:
- Рівень складності: {difficulty}
- Мінімум 1 відкрите питання в цій групі
- Решта: single_choice або multiple_choice
- Формат: JSON масив
"""
    response = await self.llm.generate_json(prompt)
    questions = self._parse_and_validate(response, difficulty)
    return questions

def _is_valid_question(self, q: dict) -> bool:
    """Validate question structure."""
    required = ["question", "type", "difficulty", "explanation", "topic"]
    if not all(k in q for k in required):
        return False

    if q["type"] in ["single_choice", "multiple_choice"]:
        if not q.get("answer_options") or len(q["answer_options"]) < 2:
            return False
        if not any(opt.get("correct") for opt in q["answer_options"]):
            return False

    return True
```

**Output per question:**
```
├── question: text
├── type: single_choice | multiple_choice | open (LLM decides)
├── difficulty: easy | medium | hard (from batch)
├── answer_options: [{answer, correct}] or null for open
├── explanation: why correct answer is correct
├── topic: the main topic_definition
└── subtopics: specific subtopics covered (LLM extracts from content)
```

**Benefits of chunked approach:**
- Smaller JSON outputs = more reliable parsing
- Partial success possible (if one batch fails, others may succeed)
- Can parallelize the 3 batches for speed
- Clearer prompts (one difficulty at a time)
- Validation per batch catches errors early

**Tolerance:** Accept 8-12 questions per batch (not strictly 10). Total should be 24-36 questions.

**Handling Vague topic_definition:**

When topic_definition is broad (e.g., "Квадратні рівняння"), the LLM should:
1. Identify subtopics from retrieved textbook content
2. Distribute questions across subtopics within each difficulty batch
3. Return subtopics in each question's response

**Frontend responsibility:**
- Receives pool of ~30 questions with difficulties
- Groups questions into student tests by level
- Weak students: more easy questions
- Medium students: balanced mix
- Strong students: more difficult questions

---

### What to Reuse vs Create

#### Reuse from Archive (as-is)

| Component | Location | Use For |
|-----------|----------|---------|
| `HybridRetriever` | utils/hybrid_retriever.py | All RAG retrieval |
| `TopicRetriever` | utils/topic_retriever.py | Ukrainian language |
| `PassageExtractor` | utils/passage_extractor.py | Ukrainian passages |
| `Reranker` | utils/reranker.py | Cross-encoder |
| `DataLoader` | utils/data_loader.py | Load parquets |
| `LLMClient` | utils/llm_client.py | All LLM calls |
| `format_context()` | utils/hybrid_retriever.py | Context formatting |
| `UKRAINIAN_RULES` | prompts/ukrainian_rules.py | EP7, EP9 prompts |
| `ALGEBRA_RULES` | prompts/algebra_rules.py | EP7, EP9 prompts |
| `HISTORY_RULES` | prompts/history_rules.py | EP7, EP9 prompts |

#### Create New

| Component | Purpose |
|-----------|---------|
| `SolverPrompt` | EP7 - solve and explain (not MC) |
| `EvaluatorPrompt` | EP9 - evaluate student answer |
| `NotesGeneratorPrompt` | EP3 - generate lesson with gap warnings |
| `TestGeneratorPrompt` | EP4 - generate 30 questions pool |
| `RecommendationPrompt` | EP6 - student recommendation |
| `FeedbackPrompt` | EP10 - test feedback |
| `StudentGapAnalyzer` | EP3, EP6 - query and aggregate student gaps |

---

### Data Derivation

Some endpoints need data that isn't in the request but can be derived:

#### Grade Derivation

RAG retrieval needs `grade` to filter textbooks (grade 8 vs 9). Several endpoints have `class_id` but not `grade`.

```python
def get_grade_for_class(class_id: int, data_loader: DataLoader) -> int:
    """Derive grade from class_id by querying benchmark_scores."""
    scores = data_loader.load_scores()
    class_scores = scores[scores['class_id'] == class_id]
    if len(class_scores) == 0:
        raise ValueError(f"No data for class_id {class_id}")
    return int(class_scores['grade'].iloc[0])
```

| Endpoint | Has | Needs | Derivation |
|----------|-----|-------|------------|
| EP3, EP4 | class_id | grade | Query scores by class_id |
| EP9 | student_id | grade | Query scores by student_id → get grade |

---

### Key Design Decisions

1. **Retrieval unchanged** - Archive retrieval pipeline is well-optimized, reuse as-is

2. **New prompts for generation** - Archive prompts are MC-specific, create new for:
   - Open question solving (EP7)
   - Answer evaluation (EP9)
   - Content generation (EP3, EP4)
   - Feedback generation (EP6, EP10)

3. **SUBJECT_RULES reused** - The rule constants are valuable subject knowledge, include in EP7/EP9 prompts

4. **No topic matching needed** - Use raw `topic_name` from scores/absences for gap analysis, no need to match to TOC

5. **EP3 warns but doesn't include** - teacher_notes warns about weak topics, but contents only covers topic_definition

6. **EP4 generates pool** - Backend generates 30 questions, frontend distributes by student level

---

## Phase 5: Full Pipeline (Integration Test)

### Purpose

Single API endpoint that exercises multiple components for smoke testing. Tests Data + RAG + LLM integration in one request.

**⚠️ TESTING ONLY** - This endpoint is NOT for production use. It should be:
- Excluded from production deployment OR
- Protected behind admin authentication OR
- Removed before release

### Endpoint

```
POST /api/v1/internal/full-pipeline  # Note: /internal/ prefix

Input:
{
  "class_id": number,
  "teacher_id": number,
  "subject": string,
  "topic_definition": string
}
```

### Flow

```
1. DATA: Get ALL students in class
       └── Query benchmark_scores for class

2. DATA: Analyze gaps for all students
       ├── scores: GROUP BY topic_name WHERE score < 6 → counts
       └── absences: GROUP BY topic_name → counts

3. RAG: Retrieve content for topic_definition
       └── HybridRetriever → format_context()

4. LLM: Generate notes (EP3 logic)
       └── Include gap warnings for whole class

5. LLM: Generate test pool (EP4 logic)
       └── 30 questions: 10 easy, 10 medium, 10 hard

6. LLM: Solve each generated question (EP7 logic, called N times)
       └── Loop: call EP7 for each question → build answer key
       └── Note: EP7 handles ONE question at a time, so this loops ~30 times
```

### Output

```typescript
{
  "notes": {
    "title": string,
    "contents": string,
    "teacher_notes": string  // includes gap analysis for all students
  },
  "test": {
    "title": string,
    "questions": Question[]  // 30 questions
  },
  "answer_key": {
    "solutions": Solution[]  // solved versions of all 30 questions
  }
}
```

### Components Tested

| Component | What's Tested |
|-----------|---------------|
| Data Layer | Student queries, gap aggregation |
| RAG Retrieval | HybridRetriever, format_context |
| EP3 Logic | Notes generation with gap analysis |
| EP4 Logic | Test pool generation (30 questions) |
| EP7 Logic | Solving questions (single-question API called ~30 times) |
| LLM Client | Multiple LLM calls |

This endpoint serves as a comprehensive integration test for the core teacher workflow.

---

## Phase 6: API Implementation Mapping

### File Structure

```
backend/app/
├── api/
│   ├── __init__.py
│   ├── deps.py                # FastAPI dependencies (DI)
│   ├── teacher_routes.py      # EP1, EP2, EP3, EP4, EP5, EP6, EP7
│   ├── student_routes.py      # EP8, EP9, EP10
│   └── internal_routes.py     # Testing-only endpoints (full-pipeline)
│
├── services/
│   ├── __init__.py
│   ├── benchmark_data.py      # BenchmarkDataLoader (scores, absences)
│   ├── teacher_service.py     # EP1, EP2 (data)
│   ├── student_service.py     # EP8 (data)
│   ├── student_analysis.py    # EP5, EP6 (data + LLM)
│   ├── notes_generator.py     # EP3 (RAG + LLM)
│   ├── test_generator.py      # EP4 (RAG + LLM)
│   ├── solver.py              # EP7 (RAG + LLM)
│   ├── open_checker.py        # EP9 (RAG + LLM)
│   ├── test_feedback.py       # EP10 (LLM)
│   └── full_pipeline.py       # Integration test endpoint
│
├── prompts/
│   ├── __init__.py
│   ├── solver.py              # EP7 prompt
│   ├── evaluator.py           # EP9 prompt
│   ├── notes_generator.py     # EP3 prompt
│   ├── test_generator.py      # EP4 prompt
│   ├── recommendation.py      # EP6 prompt
│   └── feedback.py            # EP10 prompt
│
├── rag/                       # Copied from archive (minimal changes)
│   ├── __init__.py
│   ├── config.py
│   ├── utils/
│   │   ├── llm_client.py
│   │   ├── rag_data_loader.py # RAGDataLoader (textbooks, TOC, embeddings)
│   │   ├── hybrid_retriever.py
│   │   └── ...
│   └── prompts/
│       ├── ukrainian_rules.py  # SUBJECT_RULES constants
│       ├── algebra_rules.py
│       └── history_rules.py
│
├── schemas/
│   ├── __init__.py
│   ├── teacher.py             # Request/Response models for teacher endpoints
│   └── student.py             # Request/Response models for student endpoints
│
└── core/
    ├── __init__.py
    └── config.py              # App settings
```

### Two DataLoaders (Separate Concerns)

| DataLoader | Location | Purpose | Data |
|------------|----------|---------|------|
| `BenchmarkDataLoader` | `services/benchmark_data.py` | Student metrics | `benchmark_scores.parquet`, `benchmark_absences.parquet` |
| `RAGDataLoader` | `rag/utils/rag_data_loader.py` | Textbook content | `pages_for_hackathon.parquet`, `toc_for_hackathon.parquet` |

These are **intentionally separate**:
- Different data domains (metrics vs content)
- Different query patterns (by student/teacher vs by subject/grade)
- Different lifecycles (operational vs curriculum)

### Dependency Injection

Use FastAPI's dependency injection for clean service instantiation:

```python
# app/api/deps.py
from functools import lru_cache
from app.services.benchmark_data import BenchmarkDataLoader
from app.rag.utils.rag_data_loader import RAGDataLoader
from app.rag.utils.llm_client import LLMClient
from app.rag.utils.hybrid_retriever import HybridRetriever

@lru_cache()
def get_benchmark_data() -> BenchmarkDataLoader:
    """Singleton: loads parquets once, reused across requests."""
    return BenchmarkDataLoader()

@lru_cache()
def get_rag_data() -> RAGDataLoader:
    """Singleton: loads textbook pages once."""
    return RAGDataLoader()

@lru_cache()
def get_llm_client() -> LLMClient:
    """Singleton: reuse client connection."""
    return LLMClient()

@lru_cache()
def get_retriever() -> HybridRetriever:
    """Singleton: pre-built BM25 indexes."""
    return HybridRetriever(get_rag_data())

# Service factories (created per-request but use singleton deps)
def get_teacher_service(
    data: BenchmarkDataLoader = Depends(get_benchmark_data)
) -> TeacherService:
    return TeacherService(data)

def get_solver_service(
    retriever: HybridRetriever = Depends(get_retriever),
    llm: LLMClient = Depends(get_llm_client)
) -> SolverService:
    return SolverService(retriever, llm)
```

**Usage in routes:**
```python
# app/api/teacher_routes.py
from fastapi import APIRouter, Depends, HTTPException
from app.api.deps import get_teacher_service

router = APIRouter()

@router.get("/teacher/{teacher_id}")
def get_teacher(
    teacher_id: int,
    service: TeacherService = Depends(get_teacher_service)
):
    classes = service.get_teacher_classes(teacher_id)
    if not classes:
        raise HTTPException(status_code=404, detail="Teacher not found")
    return {"classes": classes}
```

**Key patterns:**
- **Singletons via `@lru_cache()`** - Data loaders, LLM client, retriever (expensive to create)
- **Per-request services** - Services are cheap, use fresh instances
- **Depends()** - FastAPI handles injection automatically

---

### Endpoint → File Mapping

| EP | Endpoint | Router | Service | Prompt |
|----|----------|--------|---------|--------|
| EP1 | GET /teacher/{id} | teacher_routes.py | teacher_service.py | - |
| EP2 | POST /teacher/students | teacher_routes.py | teacher_service.py | - |
| EP3.1 | POST /teacher/notes/by-level | teacher_routes.py | notes_generator.py | notes_generator.py |
| EP3.2 | POST /teacher/notes/individual | teacher_routes.py | notes_generator.py | notes_generator.py |
| EP4 | POST /teacher/test/generate | teacher_routes.py | test_generator.py | test_generator.py |
| EP5 | POST /teacher/student/details | teacher_routes.py | student_analysis.py | - |
| EP6 | POST /teacher/student/recommendation | teacher_routes.py | student_analysis.py | recommendation.py |
| EP7 | POST /solver | teacher_routes.py | solver.py | solver.py |
| EP8 | GET /student/{id} | student_routes.py | student_service.py | - |
| EP9 | POST /student/check-open | student_routes.py | open_checker.py | evaluator.py |
| EP10 | POST /student/test-feedback | student_routes.py | test_feedback.py | feedback.py |
| - | POST /internal/full-pipeline | internal_routes.py | full_pipeline.py | (uses EP3,4,7) |

**Note on full-pipeline route:** This is a testing-only endpoint under `/api/v1/internal/`. Create a separate `internal_routes.py` to keep test endpoints isolated from production routes.

---

### Implementation Order & Checklist

#### Stage 1: Foundation
- [ ] Copy RAG files from archive to `app/rag/`
- [ ] Update imports in RAG files (relative → absolute)
- [ ] Update `config.py` data paths
- [ ] Create `app/core/config.py` (app settings)
- [ ] Create `app/core/data.py` (parquet loading with filters)
- [ ] Create `app/schemas/teacher.py` and `app/schemas/student.py`
- [ ] Verify LLM client connects to mamay

#### Stage 2: Data Endpoints (no LLM)
- [ ] EP1: `teacher_service.get_teacher_classes()`
- [ ] EP2: `teacher_service.get_students_with_levels()`
- [ ] EP5: `student_analysis.get_student_details()`
- [ ] EP8: `student_service.get_student_data()`
- [ ] Create `teacher_routes.py` with EP1, EP2, EP5
- [ ] Create `student_routes.py` with EP8
- [ ] Test all data endpoints

#### Stage 3: LLM-Only Endpoints
- [ ] Create `prompts/recommendation.py`
- [ ] EP6: `student_analysis.generate_recommendation()`
- [ ] Create `prompts/feedback.py`
- [ ] EP10: `test_feedback.generate_feedback()`
- [ ] Add EP6 to teacher_routes.py
- [ ] Add EP10 to student_routes.py
- [ ] Test LLM endpoints

#### Stage 4: RAG + LLM Endpoints
- [ ] Create `prompts/solver.py` (with SUBJECT_RULES)
- [ ] EP7: `solver.solve_question()`
- [ ] Create `prompts/evaluator.py` (with SUBJECT_RULES)
- [ ] EP9: `open_checker.check_answer()`
- [ ] Create `prompts/notes_generator.py`
- [ ] EP3: `notes_generator.generate_notes()`
- [ ] Create `prompts/test_generator.py`
- [ ] EP4: `test_generator.generate_test()`
- [ ] Add EP7, EP3, EP4 to teacher_routes.py
- [ ] Add EP9 to student_routes.py
- [ ] Test RAG endpoints

#### Stage 5: Full Pipeline
- [ ] Create `full_pipeline.py` (combines EP3 + EP4 + EP7)
- [ ] Add full-pipeline endpoint to teacher_routes.py
- [ ] Integration test

---

### Service Signatures

#### teacher_service.py (Data only)
```python
class TeacherService:
    def __init__(self, data_loader: DataLoader): ...

    def get_teacher_classes(self, teacher_id: int) -> List[ClassInfo]: ...

    def get_students_with_levels(
        self, class_id: int, teacher_id: int, subject: str
    ) -> List[StudentSummary]: ...
```

#### student_service.py (Data only)
```python
class StudentService:
    def __init__(self, data_loader: DataLoader): ...

    def get_student_data(self, student_id: int) -> StudentData: ...
```

#### student_analysis.py (Data + LLM)
```python
class StudentAnalysisService:
    def __init__(self, data_loader: DataLoader, llm_client: LLMClient): ...

    def get_student_details(
        self, class_id: int, subject: str, teacher_id: int, student_id: int
    ) -> StudentDetails: ...

    async def generate_recommendation(self, student_id: int, subject: str) -> str:
        """Generate recommendation for student in specific subject."""
        ...

    def get_gap_analysis(
        self, student_ids: List[int], subject: str, topic_definition: str
    ) -> GapData:
        """Get gaps filtered to topics related to topic_definition via semantic search."""
        ...
```

#### solver.py (RAG + LLM)
```python
class SolverService:
    def __init__(self, retriever: HybridRetriever, llm_client: LLMClient): ...

    async def solve_question(
        self, subject: str, grade: int, question: str
    ) -> Solution:
        """Solve a single question with RAG-grounded explanation."""
        ...
```

#### open_checker.py (RAG + LLM)
```python
class OpenCheckerService:
    def __init__(
        self, retriever: HybridRetriever, llm_client: LLMClient,
        student_service: StudentService
    ): ...

    async def check_answer(
        self, student_id: int, subject: str, topic: str,
        subtopics: List[str], question: str, answer: str
    ) -> OpenQuestionResult: ...
```

#### notes_generator.py (RAG + LLM)
```python
class NotesGeneratorService:
    def __init__(
        self, retriever: HybridRetriever, llm_client: LLMClient,
        teacher_service: TeacherService, analysis_service: StudentAnalysisService
    ): ...

    async def generate_notes_by_level(
        self, class_id: int, teacher_id: int, subject: str,
        topic_definition: str, level_list: List[str]
    ) -> NotesResponse: ...

    async def generate_notes_individual(
        self, class_id: int, teacher_id: int, subject: str,
        topic_definition: str, student_list: List[int]
    ) -> NotesResponse: ...
```

#### test_generator.py (RAG + LLM)
```python
class TestGeneratorService:
    def __init__(self, retriever: HybridRetriever, llm_client: LLMClient): ...

    async def generate_test(
        self, class_id: int, teacher_id: int, subject: str, topic_definition: str
    ) -> TestResponse: ...
```

#### test_feedback.py (LLM only)
```python
class TestFeedbackService:
    def __init__(self, llm_client: LLMClient): ...

    async def generate_feedback(
        self, student_id: int, teacher_id: int, subject: str,
        questions: List[QuestionResult]
    ) -> str: ...
```

#### full_pipeline.py (Integration)
```python
class FullPipelineService:
    def __init__(
        self, notes_service: NotesGeneratorService,
        test_service: TestGeneratorService,
        solver_service: SolverService
    ): ...

    async def execute(
        self, class_id: int, teacher_id: int, subject: str, topic_definition: str
    ) -> FullPipelineResponse: ...
```

---

### Testing

#### Test Framework
- pytest + pytest-asyncio
- Real LLM calls (no mocking)
- Real parquet data

#### Test Structure

```
backend/tests/
├── conftest.py                    # Shared fixtures, data loaders
├── test_api/
│   ├── test_teacher_routes.py     # EP1-7 endpoint tests
│   └── test_student_routes.py     # EP8-10 endpoint tests
├── test_services/
│   ├── test_teacher_service.py    # Data service unit tests
│   ├── test_student_service.py    # Data service unit tests
│   ├── test_student_analysis.py   # Gap analysis tests
│   ├── test_notes_generator.py    # RAG + LLM tests
│   ├── test_test_generator.py     # RAG + LLM tests
│   ├── test_solver.py             # RAG + LLM tests
│   ├── test_open_checker.py       # RAG + LLM tests
│   └── test_full_pipeline.py      # Integration test
├── test_rag/
│   ├── test_retriever.py          # RAG retrieval quality
│   └── test_llm_client.py         # LLM connectivity
└── test_data/
    └── test_data_loader.py        # Parquet loading, filtering
```

#### Coverage Targets

| Priority | Component | Target | Why |
|----------|-----------|--------|-----|
| Critical | Data layer | 100% | Core logic, fast, deterministic |
| Critical | RAG retrieval | 100% | Must return relevant content |
| Critical | LLM connectivity | Exists | Catch config/network issues |
| High | API contracts | 90%+ | Ensure endpoints match spec |
| High | Service business logic | 80%+ | Gap analysis, level computation |
| Medium | Error handling | 70%+ | Graceful failures |
| Low | Edge cases | As needed | Empty data, missing students |

#### Key Fixtures (conftest.py)

```python
import pytest
from app.rag.utils.llm_client import LLMClient
from app.rag.utils.data_loader import DataLoader
from app.rag.utils.hybrid_retriever import HybridRetriever

@pytest.fixture
def data_loader():
    """Real data loader with actual parquets."""
    return DataLoader()

@pytest.fixture
def llm_client():
    """Real LLM client connected to mamay."""
    return LLMClient()

@pytest.fixture
def retriever(data_loader):
    """Real HybridRetriever."""
    return HybridRetriever(data_loader)

@pytest.fixture
def sample_class_id(data_loader):
    """Return a valid class_id from real data."""
    scores = data_loader.load_scores()
    return scores['class_id'].iloc[0]

@pytest.fixture
def sample_teacher_id(data_loader):
    """Return a valid teacher_id from real data."""
    scores = data_loader.load_scores()
    return scores['teacher_id'].iloc[0]

@pytest.fixture
def sample_student_id(data_loader):
    """Return a valid student_id from real data."""
    scores = data_loader.load_scores()
    return scores['student_id'].iloc[0]
```

#### Test Markers

```python
# Mark slow tests (LLM calls)
@pytest.mark.slow
async def test_solver_generates_solution(solver_service):
    ...

# Run without slow tests
# pytest -m "not slow"

# Run only slow tests
# pytest -m slow
```

#### Sample Test Cases

**Data Service Test:**
```python
def test_get_teacher_classes_returns_list(teacher_service, sample_teacher_id):
    classes = teacher_service.get_teacher_classes(sample_teacher_id)

    assert isinstance(classes, list)
    assert len(classes) > 0
    assert all(hasattr(c, 'class_id') for c in classes)
    assert all(hasattr(c, 'subject') for c in classes)

def test_get_teacher_classes_unknown_teacher_raises(teacher_service):
    # Service returns empty list, but route handler converts to 404
    with pytest.raises(TeacherNotFoundError):
        teacher_service.get_teacher_classes(999999)
```

**RAG Service Test:**
```python
@pytest.mark.slow
async def test_solver_returns_explained_answer(solver_service):
    solution = await solver_service.solve_question(
        subject="Алгебра",
        grade=8,
        question="Розв'яжіть рівняння: x² - 4 = 0"
    )

    assert solution.question == "Розв'яжіть рівняння: x² - 4 = 0"
    assert "x = 2" in solution.answer_explained or "x = -2" in solution.answer_explained

@pytest.mark.slow
async def test_solver_uses_textbook_context(solver_service):
    """Solver should ground answer in retrieved textbook content."""
    solution = await solver_service.solve_question(
        subject="Українська мова",
        grade=8,
        question="Що таке складнопідрядне речення?"
    )

    # Should mention key terms from textbook
    answer = solution.answer_explained.lower()
    assert "підрядне" in answer or "головне" in answer
```

**API Endpoint Test:**
```python
def test_get_teacher_endpoint(client, sample_teacher_id):
    response = client.get(f"/api/v1/teacher/{sample_teacher_id}")

    assert response.status_code == 200
    data = response.json()
    assert "classes" in data
    assert isinstance(data["classes"], list)

def test_get_teacher_not_found(client):
    response = client.get("/api/v1/teacher/999999")

    assert response.status_code == 404
```

---

## Error Handling

### HTTP Status Codes

| Scenario | Status | Response |
|----------|--------|----------|
| Unknown teacher_id | 404 | `{"detail": "Teacher not found"}` |
| Unknown student_id | 404 | `{"detail": "Student not found"}` |
| Unknown class_id | 404 | `{"detail": "Class not found"}` |
| Student has no scores | 200 | `{"problematic_topics": [], "skipped_lessons": [], ...}` |
| Invalid subject | 400 | `{"detail": "Unsupported subject"}` |
| LLM error | 503 | `{"detail": "LLM service unavailable"}` |

**Key rule:** Unknown IDs → 404. Empty data for valid IDs → 200 with empty arrays/nulls.

### ID Existence Check

An ID is considered "unknown" if it doesn't appear in **filtered** benchmark data (current year, supported subjects). We only work with filtered data.

```python
def check_teacher_exists(teacher_id: int, scores_df: pd.DataFrame) -> bool:
    """Check if teacher exists in filtered data."""
    # scores_df is already filtered by academic_year='2025-2026' and supported subjects
    return teacher_id in scores_df['teacher_id'].unique()

def check_student_exists(student_id: int, scores_df: pd.DataFrame) -> bool:
    """Check if student exists in filtered data."""
    return student_id in scores_df['student_id'].unique()

def check_class_exists(class_id: int, scores_df: pd.DataFrame) -> bool:
    """Check if class exists in filtered data."""
    return class_id in scores_df['class_id'].unique()
```

**Important:** A teacher/student/class that exists in old data (2024-2025) but not in current year will return 404. This is intentional - we only serve current academic year data.

### Grade Derivation Edge Cases

```python
def get_grade_for_student(student_id: int) -> int | None:
    """Get grade for student from scores."""
    scores = data_loader.load_scores()
    student_scores = scores[scores['student_id'] == student_id]
    if len(student_scores) == 0:
        return None  # No scores → return None, let caller decide
    return int(student_scores['grade'].iloc[0])
```

For EP9 (check-open), if student has no scores:
- Default to grade 8 (most common case, safe fallback for RAG retrieval)

---

## Appendix: Quick Reference

### Supported Subjects
```python
SUPPORTED_SUBJECTS = ['Алгебра', 'Українська мова', 'Історія України']
```

### Ukrainian Grading Scale
- 0-12 points
- Typical distribution peaks at 7-8

### Absence Reasons
```python
ABSENCE_REASONS = ['Поважна причина', 'Через хворобу', 'Не було на уроці']
```

### Embedding Dimensions
- All embeddings: 4096 dimensions
- Pre-computed, no embedding service needed

### Entity Counts (after filters)
| Entity | Count |
|--------|-------|
| Schools | 13 |
| Teachers | 146 |
| Classes | 134 |
| Students | 3,064 |
| Score Records | 139,382 |
| Absence Records | 42,977 |
| Questions | 141 |
| TOC Topics | 237 |
| Textbook Pages | 1,318 |
