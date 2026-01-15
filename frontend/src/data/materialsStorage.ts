import { fixLatexEscapes } from "../api/client";

export type MaterialType = "note" | "test";

export type AssignmentScope = "class" | "levels" | "students";

export interface MaterialItem {
  id: string;
  type: MaterialType;
  title: string;
  content?: string;
  teacherNotes?: string;
  questions?: unknown;
  classId?: number;
  subject?: string;
  teacherId?: string;
  courseId?: string;
  className?: string;
  topicName?: string;
  createdAt: string;
  // Assignment targeting - exactly ONE scope per material
  assignmentScope?: AssignmentScope;
  assignedLevels?: ("weak" | "medium" | "strong")[];
  assignedStudents?: number[];
}

export interface TopicItem {
  id: string;
  title: string;
  classId?: number;
  subject?: string;
  teacherId?: string;
  courseId?: string;
  className?: string;
  createdAt: string;
}

const STORAGE_KEY_MATERIALS = "teacher_materials_v1";
const STORAGE_KEY_TOPICS = "teacher_topics_v1";

const createId = () => {
  if (typeof crypto !== "undefined" && crypto.randomUUID) {
    return crypto.randomUUID();
  }
  return `mat_${Date.now()}_${Math.random().toString(16).slice(2)}`;
};

const readMaterials = (): MaterialItem[] => {
  if (typeof window === "undefined") {
    return [];
  }

  const raw = window.localStorage.getItem(STORAGE_KEY_MATERIALS);
  if (!raw) {
    return [];
  }

  try {
    const parsed = JSON.parse(raw);
    const items = Array.isArray(parsed) ? parsed : [];
    // Fix any corrupted LaTeX escape sequences in stored content
    return items.map((item) => fixLatexEscapes(item) as MaterialItem);
  } catch {
    return [];
  }
};

const writeMaterials = (items: MaterialItem[]) => {
  if (typeof window === "undefined") {
    return;
  }
  window.localStorage.setItem(STORAGE_KEY_MATERIALS, JSON.stringify(items));
};

const readTopics = (): TopicItem[] => {
  if (typeof window === "undefined") {
    return [];
  }

  const raw = window.localStorage.getItem(STORAGE_KEY_TOPICS);
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

const writeTopics = (items: TopicItem[]) => {
  if (typeof window === "undefined") {
    return;
  }
  window.localStorage.setItem(STORAGE_KEY_TOPICS, JSON.stringify(items));
};

export const getMaterials = (filters?: {
  teacherId?: string;
  courseId?: string;
  subject?: string;
  classId?: number;
  className?: string;
  topicName?: string;
  type?: MaterialType;
}) => {
  const items = readMaterials();
  if (!filters) {
    return items;
  }

  return items.filter((item) => {
    if (filters.teacherId && item.teacherId !== filters.teacherId) {
      return false;
    }
    if (filters.subject) {
      if (item.subject && item.subject !== filters.subject) {
        return false;
      }
      if (!item.subject && filters.courseId && item.courseId !== filters.courseId) {
        return false;
      }
    } else if (filters.courseId && item.courseId !== filters.courseId) {
      return false;
    }
    if (typeof filters.classId === "number") {
      if (typeof item.classId === "number" && item.classId !== filters.classId) {
        return false;
      }
      if (
        typeof item.classId !== "number" &&
        filters.className &&
        item.className !== filters.className
      ) {
        return false;
      }
    } else if (filters.className && item.className !== filters.className) {
      return false;
    }
    if (filters.topicName && item.topicName !== filters.topicName) {
      return false;
    }
    if (filters.type && item.type !== filters.type) {
      return false;
    }
    return true;
  });
};

export const addMaterial = (input: Omit<MaterialItem, "id" | "createdAt">) => {
  const nextItem: MaterialItem = {
    ...input,
    id: createId(),
    createdAt: new Date().toISOString(),
  };
  const items = readMaterials();
  const updated = [...items, nextItem];
  writeMaterials(updated);
  return nextItem;
};

export const updateMaterial = (
  id: string,
  updates: Partial<Omit<MaterialItem, "id" | "createdAt">>
) => {
  const items = readMaterials();
  const index = items.findIndex((item) => item.id === id);
  if (index === -1) {
    return null;
  }
  const updated = { ...items[index], ...updates };
  items[index] = updated;
  writeMaterials(items);
  return updated;
};

export const deleteMaterial = (id: string): boolean => {
  const items = readMaterials();
  const index = items.findIndex((item) => item.id === id);
  if (index === -1) {
    return false;
  }
  items.splice(index, 1);
  writeMaterials(items);
  return true;
};

export const getTopics = (filters?: {
  teacherId?: string;
  courseId?: string;
  subject?: string;
  classId?: number;
  className?: string;
}) => {
  const items = readTopics();
  if (!filters) {
    return items;
  }

  return items.filter((item) => {
    if (filters.teacherId && item.teacherId !== filters.teacherId) {
      return false;
    }
    if (filters.subject) {
      if (item.subject && item.subject !== filters.subject) {
        return false;
      }
      if (!item.subject && filters.courseId && item.courseId !== filters.courseId) {
        return false;
      }
    } else if (filters.courseId && item.courseId !== filters.courseId) {
      return false;
    }
    if (typeof filters.classId === "number") {
      if (typeof item.classId === "number" && item.classId !== filters.classId) {
        return false;
      }
      if (
        typeof item.classId !== "number" &&
        filters.className &&
        item.className !== filters.className
      ) {
        return false;
      }
    } else if (filters.className && item.className !== filters.className) {
      return false;
    }
    return true;
  });
};

export const addTopic = (input: Omit<TopicItem, "id" | "createdAt">) => {
  const nextItem: TopicItem = {
    ...input,
    id: createId(),
    createdAt: new Date().toISOString(),
  };
  const items = readTopics();
  const updated = [...items, nextItem];
  writeTopics(updated);
  return nextItem;
};

/**
 * Check if a student should see a material based on assignment scope.
 * Implements strict visibility rules:
 * - assignmentScope="class" → ALL students see it
 * - assignmentScope="students" → ONLY listed students see it
 * - assignmentScope="levels" → students in those levels see it (requires level lookup)
 * - No assignmentScope (legacy) → treat as "class" (all see it)
 */
export const isVisibleToStudent = (
  material: MaterialItem,
  studentId: number,
  studentLevel?: "weak" | "medium" | "strong"
): boolean => {
  // Legacy materials without scope → visible to all (class default)
  if (!material.assignmentScope) {
    return true;
  }

  switch (material.assignmentScope) {
    case "class":
      // Entire class → everyone sees it
      return true;

    case "students":
      // Individual assignment → ONLY listed students
      if (!material.assignedStudents || material.assignedStudents.length === 0) {
        // Edge case: scope is "students" but no students listed → no one sees it
        return false;
      }
      return material.assignedStudents.includes(studentId);

    case "levels":
      // Level assignment → students matching the level
      if (!material.assignedLevels || material.assignedLevels.length === 0) {
        // Edge case: scope is "levels" but no levels listed → no one sees it
        return false;
      }
      // If student level is unknown, they cannot match
      if (!studentLevel) {
        return false;
      }
      return material.assignedLevels.includes(studentLevel);

    default:
      // Unknown scope → default to visible (fail-open for legacy)
      return true;
  }
};
