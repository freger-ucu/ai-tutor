export interface StudentTestCompletion {
  studentId: string;
  testId: string;
  completedAt: string;
  correctAnswers: number;
  totalQuestions: number;
  percent: number;
}

const STORAGE_KEY = "student_test_completions_v1";

const readCompletions = (): StudentTestCompletion[] => {
  if (typeof window === "undefined") {
    return [];
  }

  const raw = window.localStorage.getItem(STORAGE_KEY);
  if (!raw) {
    return [];
  }

  try {
    const parsed = JSON.parse(raw);
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
};

const writeCompletions = (items: StudentTestCompletion[]) => {
  if (typeof window === "undefined") {
    return;
  }
  window.localStorage.setItem(STORAGE_KEY, JSON.stringify(items));
};

export const getStudentTestCompletions = (studentId?: string) => {
  const items = readCompletions();
  if (!studentId) {
    return items;
  }
  return items.filter((item) => item.studentId === studentId);
};

export const markStudentTestCompleted = (input: {
  studentId: string;
  testId: string;
  correctAnswers: number;
  totalQuestions: number;
}) => {
  const items = readCompletions();
  const existingIndex = items.findIndex(
    (item) => item.studentId === input.studentId && item.testId === input.testId
  );

  if (existingIndex !== -1) {
    const existing = items[existingIndex];
    const percent =
      input.totalQuestions > 0
        ? Math.round((input.correctAnswers / input.totalQuestions) * 100)
        : 0;
    const updatedItem: StudentTestCompletion = {
      ...existing,
      completedAt: new Date().toISOString(),
      correctAnswers: input.correctAnswers,
      totalQuestions: input.totalQuestions,
      percent,
    };
    const nextItems = [...items];
    nextItems[existingIndex] = updatedItem;
    writeCompletions(nextItems);
    return updatedItem;
  }

  const percent =
    input.totalQuestions > 0
      ? Math.round((input.correctAnswers / input.totalQuestions) * 100)
      : 0;
  const nextItem: StudentTestCompletion = {
    studentId: input.studentId,
    testId: input.testId,
    completedAt: new Date().toISOString(),
    correctAnswers: input.correctAnswers,
    totalQuestions: input.totalQuestions,
    percent,
  };
  const updated = [...items, nextItem];
  writeCompletions(updated);
  return nextItem;
};

export const getStudentCompletedTestIds = (studentId?: string) => {
  const items = getStudentTestCompletions(studentId);
  return new Set(items.map((item) => item.testId));
};

export const getStudentTestCompletionMap = (studentId?: string) => {
  const items = getStudentTestCompletions(studentId);
  return new Map(items.map((item) => [item.testId, item]));
};
