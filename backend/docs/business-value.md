# Business Value Documentation

This document describes what each endpoint does in terms of **business value** — the problems it solves and the user needs it addresses.

---

## Overview

The AI Tutor backend serves two primary user personas:

| Persona | Needs |
|---------|-------|
| **Teacher** | View classes, monitor student performance, generate personalized materials, create tests, get AI recommendations |
| **Student** | View enrolled subjects, complete tests, get instant feedback on answers |

---

## Teacher Endpoints

### EP1: Get Teacher Classes
**`GET /api/v1/teacher/{teacher_id}`**

**Problem Solved:** Teachers need to see which classes they teach and in which subjects.

**Business Value:**
- Entry point for teacher dashboard
- Shows all class-subject combinations assigned to a teacher
- Enables navigation to specific class management

**User Story:** *"As a teacher, I want to see all my classes so I can select one to manage."*

---

### EP2: Get Student List
**`POST /api/v1/teacher/students`**

**Problem Solved:** Teachers need to see all students in a class with their performance levels.

**Business Value:**
- Displays student roster with performance indicators
- Uses quartile-based clustering (weak/medium/strong) based on grades
- Enables teachers to identify struggling students at a glance
- Supports differentiated instruction planning

**User Story:** *"As a teacher, I want to see my students' performance levels so I can identify who needs extra attention."*

**Level Assignment Logic:**
- **Weak:** Score < Q1 (25th percentile)
- **Medium:** Q1 ≤ Score ≤ Q3
- **Strong:** Score > Q3 (75th percentile)

---

### EP3.1: Generate Notes by Level
**`POST /api/v1/teacher/notes/by-level`**

**Problem Solved:** Teachers need lesson materials adapted to different student ability levels.

**Business Value:**
- Generates level-appropriate lesson notes (simplified for weak, challenging for strong)
- Aggregates common weak topics and missed lessons across the level group
- Includes teacher tips based on group-wide gaps
- Saves hours of manual differentiation work
- Grounded in official textbook content via RAG

**User Story:** *"As a teacher, I want to generate lesson notes for my weak students that address their common gaps."*

---

### EP3.2: Generate Notes for Individuals
**`POST /api/v1/teacher/notes/individual`**

**Problem Solved:** Teachers need personalized materials for specific students.

**Business Value:**
- Generates notes targeting specific student weaknesses
- Aggregates gaps across selected students
- Includes prerequisite recap sections when needed
- Useful for catch-up sessions or tutoring

**User Story:** *"As a teacher, I want to create personalized study materials for three students who missed last week's classes."*

---

### EP4: Generate Test Pool
**`POST /api/v1/teacher/test/generate`**

**Problem Solved:** Creating quality tests is time-consuming and error-prone.

**Business Value:**
- Generates 30 validated questions (10 easy, 10 medium, 10 hard)
- Each question is validated for correctness using a solver
- Questions are grounded in textbook content
- Saves teachers hours of test creation work
- Ensures fair difficulty distribution

**User Story:** *"As a teacher, I want to quickly generate a test on quadratic equations with questions at different difficulty levels."*

**Quality Assurance:**
- CPU validation: format, structure, duplicates
- LLM validation: 3 random questions per batch verified by solver
- Auto-retry failed batches up to 2 times

---

### EP5: Get Student Details
**`POST /api/v1/teacher/student/details`**

**Problem Solved:** Teachers need deep insight into individual student performance.

**Business Value:**
- Shows average grade, performance level
- Lists missed lessons with dates and topics
- Identifies problematic topics (score < 6)
- Enables targeted intervention planning

**User Story:** *"As a teacher, I want to understand why a student is struggling by seeing their attendance and weak topics."*

---

### EP6: Get Student Recommendation
**`POST /api/v1/teacher/student/recommendation`**

**Problem Solved:** Teachers need AI-powered insights for student improvement.

**Business Value:**
- Generates actionable, professional recommendations
- Considers strong topics (what's working)
- Addresses weak topics (what needs work)
- Accounts for missed lessons
- Written in teacher-appropriate language

**User Story:** *"As a teacher, I want AI-generated advice on how to help a specific student improve."*

---

### EP7: Solve Question
**`POST /api/v1/solver`**

**Problem Solved:** Teachers need help preparing answer keys or understanding complex problems.

**Business Value:**
- Solves any question using textbook knowledge
- Provides step-by-step explanations
- Cites relevant textbook pages
- Useful for answer key preparation
- Subject-specific reasoning (Algebra vs Ukrainian vs History)

**User Story:** *"As a teacher, I want to see the correct solution and explanation for a difficult problem."*

---

## Student Endpoints

### EP8: Get Student Info
**`GET /api/v1/student/{student_id}`**

**Problem Solved:** Students need to see their class and enrolled subjects.

**Business Value:**
- Entry point for student dashboard
- Shows class assignment and available subjects
- Enables navigation to subject-specific activities

**User Story:** *"As a student, I want to see which subjects I'm enrolled in."*

---

### EP9: Check Open Answer
**`POST /api/v1/student/check-open`**

**Problem Solved:** Open-ended questions can't be auto-graded without AI.

**Business Value:**
- Instant feedback on free-text answers
- Uses RAG to ground evaluation in textbook content
- Provides constructive feedback, not just right/wrong
- Enables self-study without teacher availability
- Supports partial credit recognition

**User Story:** *"As a student, I want to know if my answer to an open question is correct and get feedback on how to improve."*

---

### EP10: Get Test Feedback
**`POST /api/v1/student/test-feedback`**

**Problem Solved:** After a test, students need constructive feedback, not just a score.

**Business Value:**
- Analyzes performance by topic
- Highlights strengths and weaknesses
- Provides motivating, constructive feedback
- Helps students understand where to focus study efforts
- Written in student-appropriate, encouraging language

**User Story:** *"As a student, I want to understand what topics I need to study more after completing a test."*

---

## Health Endpoints

### Health Check
**`GET /api/v1/health`**

**Problem Solved:** Operations team needs to monitor service health.

**Business Value:**
- Quick status check
- Returns version information
- Used by monitoring systems

### Liveness Probe
**`GET /api/v1/health/live`**

**Problem Solved:** Kubernetes needs to know if the service is running.

**Business Value:**
- Simple alive check
- Used by container orchestration

### Readiness Probe
**`GET /api/v1/health/ready`**

**Problem Solved:** Traffic shouldn't be routed until the service is fully initialized.

**Business Value:**
- Checks data files are loaded
- Verifies LLM configuration
- Confirms Redis connectivity
- Ensures RAG system is ready

---

## Summary: Value Delivered

| Area | Value |
|------|-------|
| **Time Savings** | Teachers save hours on test creation, notes generation, and student analysis |
| **Personalization** | AI-powered differentiation for different student levels |
| **Quality** | Content grounded in official textbooks via RAG |
| **Instant Feedback** | Students get immediate evaluation without waiting for teacher |
| **Data-Driven** | Recommendations based on actual performance data |
| **Scalability** | One teacher can effectively support more students |
