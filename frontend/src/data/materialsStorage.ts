export type MaterialType = "note" | "test";

export interface MaterialItem {
  id: string;
  type: MaterialType;
  title: string;
  teacherId?: string;
  courseId?: string;
  className?: string;
  topicName?: string;
  createdAt: string;
}

export interface TopicItem {
  id: string;
  title: string;
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
    return Array.isArray(parsed) ? parsed : [];
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
    if (filters.courseId && item.courseId !== filters.courseId) {
      return false;
    }
    if (filters.className && item.className !== filters.className) {
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

export const getTopics = (filters?: {
  teacherId?: string;
  courseId?: string;
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
    if (filters.courseId && item.courseId !== filters.courseId) {
      return false;
    }
    if (filters.className && item.className !== filters.className) {
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
