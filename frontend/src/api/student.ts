import { apiGet, apiPost } from "./client";

export interface StudentDataResponse {
  class_id: number;
  class_number: number;
  subjects: string[];
}

export interface CheckOpenRequest {
  student_id: number;
  subject: string;
  topic: string;
  subtopics: string[];
  question: string;
  answer: string;
}

export interface CheckOpenResponse {
  correct: boolean;
  feedback: string;
}

export interface TestFeedbackQuestion {
  question: string;
  answer: string;
  correct: boolean;
  topic: string;
  subtopics: string[];
  focus: string;
}

export interface TestFeedbackRequest {
  student_id: number;
  teacher_id: number;
  subject: string;
  questions: TestFeedbackQuestion[];
}

export interface TestFeedbackResponse {
  feedback: string;
}

export const getStudentData = (studentId: number) =>
  apiGet<StudentDataResponse>(`/student/${studentId}`);

export const checkOpenQuestion = (payload: CheckOpenRequest) =>
  apiPost<CheckOpenResponse, CheckOpenRequest>("/student/check-open", payload);

export const getTestFeedback = (payload: TestFeedbackRequest) =>
  apiPost<TestFeedbackResponse, TestFeedbackRequest>(
    "/student/test-feedback",
    payload
  );
