import { apiGet, apiPost } from "./client";

export interface TeacherClassItem {
  class_id: number;
  class_number: number;
  subject: string;
}

export interface TeacherDataResponse {
  teacher_id: number;
  full_name: string;
  classes: TeacherClassItem[];
}

export interface TeacherStudentsRequest {
  class_id: number;
  teacher_id: number;
  subject: string;
}

export interface TeacherStudentItem {
  student_id: number;
  subject_level: "weak" | "medium" | "strong";
  average_subject_grade: number;
}

export interface TeacherStudentsResponse {
  students: TeacherStudentItem[];
}

export interface GenerateNotesByLevelRequest {
  class_id: number;
  teacher_id: number;
  subject: string;
  level_list: ("weak" | "medium" | "strong")[];
  topic_definition: string;
}

export interface GenerateNotesByStudentRequest {
  class_id: number;
  teacher_id: number;
  subject: string;
  student_list: number[];
  topic_definition: string;
}

export interface GeneratedNotesResponse {
  title: string;
  contents: string;
  teacher_notes: string;
}

export interface GenerateTestRequest {
  class_id: number;
  teacher_id: number;
  subject: string;
  topic_definition: string;
}

export interface TestAnswerOption {
  answer: string;
  correct: boolean;
}

export interface GeneratedQuestion {
  question: string;
  type: "single_choice" | "multiple_choice" | "open";
  difficulty: "easy" | "medium" | "difficult";
  answer_options: TestAnswerOption[] | null;
  explanation: string;
  topic: string;
  subtopics: string[];
}

export interface GeneratedTestResponse {
  title: string;
  questions: GeneratedQuestion[];
}


export interface StudentDetailsRequest {
  class_id: number;
  subject: string;
  teacher_id: number;
  student_id: number;
}

export interface StudentDetailsResponse {
  average_subject_grade: number;
  level: "weak" | "medium" | "strong";
  skipped_lessons: { date: string; topic: string }[];
  problematic_topics: { topic: string; average_score: number }[];
}

export interface StudentRecommendationRequest {
  student_id: number;
}

export interface StudentRecommendationResponse {
  feedback: string;
}

export interface SolverRequest {
  questions: string[];
}

export interface SolverResponse {
  solutions: { question: string; answer_explained: string }[];
}

export const getTeacherData = (teacherId: number) =>
  apiGet<TeacherDataResponse>(`/teacher/${teacherId}`);

export const getTeacherStudents = (payload: TeacherStudentsRequest) =>
  apiPost<TeacherStudentsResponse, TeacherStudentsRequest>("/teacher/students", payload);

export const generateNotesByLevel = (payload: GenerateNotesByLevelRequest) =>
  apiPost<GeneratedNotesResponse, GenerateNotesByLevelRequest>(
    "/teacher/notes/by-level",
    payload
  );

export const generateNotesIndividual = (payload: GenerateNotesByStudentRequest) =>
  apiPost<GeneratedNotesResponse, GenerateNotesByStudentRequest>(
    "/teacher/notes/individual",
    payload
  );

export const generateTest = (payload: GenerateTestRequest) =>
  apiPost<GeneratedTestResponse, GenerateTestRequest>(
    "/teacher/test/generate",
    payload
  );

export const getStudentDetails = (payload: StudentDetailsRequest) =>
  apiPost<StudentDetailsResponse, StudentDetailsRequest>(
    "/teacher/student/details",
    payload
  );

export const getStudentRecommendation = (payload: StudentRecommendationRequest) =>
  apiPost<StudentRecommendationResponse, StudentRecommendationRequest>(
    "/teacher/student/recommendation",
    payload
  );

export const solveQuestions = (payload: SolverRequest) =>
  apiPost<SolverResponse, SolverRequest>("/solver", payload);
