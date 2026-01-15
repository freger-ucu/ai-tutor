export interface ClassRecommendation {
  id: string;
  teacherId: string;
  classId: number;
  courseId: string;
  subject: string;
  text: string;
  generatedAt: string;
  editedAt?: string;
}

const STORAGE_KEY = "class_recommendations_v1";

const createId = () => {
  if (typeof crypto !== "undefined" && crypto.randomUUID) {
    return crypto.randomUUID();
  }
  return `rec_${Date.now()}_${Math.random().toString(16).slice(2)}`;
};

const readRecommendations = (): ClassRecommendation[] => {
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

const writeRecommendations = (items: ClassRecommendation[]) => {
  if (typeof window === "undefined") {
    return;
  }
  window.localStorage.setItem(STORAGE_KEY, JSON.stringify(items));
};

export const getRecommendation = (filters: {
  teacherId: string;
  classId: number;
  courseId: string;
  subject: string;
}): ClassRecommendation | null => {
  const items = readRecommendations();
  return (
    items.find(
      (item) =>
        item.teacherId === filters.teacherId &&
        item.classId === filters.classId &&
        item.courseId === filters.courseId &&
        item.subject === filters.subject
    ) ?? null
  );
};

export const saveRecommendation = (input: {
  teacherId: string;
  classId: number;
  courseId: string;
  subject: string;
  text: string;
  isEdit?: boolean;
}): ClassRecommendation => {
  const items = readRecommendations();
  const existingIndex = items.findIndex(
    (item) =>
      item.teacherId === input.teacherId &&
      item.classId === input.classId &&
      item.courseId === input.courseId &&
      item.subject === input.subject
  );

  const now = new Date().toISOString();

  if (existingIndex !== -1) {
    const existing = items[existingIndex];
    const updated: ClassRecommendation = {
      ...existing,
      text: input.text,
      editedAt: input.isEdit ? now : existing.editedAt,
      generatedAt: input.isEdit ? existing.generatedAt : now,
    };
    items[existingIndex] = updated;
    writeRecommendations(items);
    return updated;
  }

  const newItem: ClassRecommendation = {
    id: createId(),
    teacherId: input.teacherId,
    classId: input.classId,
    courseId: input.courseId,
    subject: input.subject,
    text: input.text,
    generatedAt: now,
  };
  items.push(newItem);
  writeRecommendations(items);
  return newItem;
};

export const deleteRecommendation = (filters: {
  teacherId: string;
  classId: number;
  courseId: string;
  subject: string;
}): boolean => {
  const items = readRecommendations();
  const index = items.findIndex(
    (item) =>
      item.teacherId === filters.teacherId &&
      item.classId === filters.classId &&
      item.courseId === filters.courseId &&
      item.subject === filters.subject
  );
  if (index === -1) {
    return false;
  }
  items.splice(index, 1);
  writeRecommendations(items);
  return true;
};
