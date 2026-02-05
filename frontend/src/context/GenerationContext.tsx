import {
  createContext,
  useContext,
  useState,
  useCallback,
  useRef,
  type ReactNode,
} from "react";
import { addMaterial } from "../data/materialsStorage";
import {
  generateNotesByLevel,
  generateNotesIndividual,
  generateTest,
} from "../api/teacher";
import { buildFallbackNotes, buildFallbackTest } from "../data/fallbackContent";

interface GeneratingItem {
  tempId: string;
  type: "note" | "test";
  title: string;
  courseId: string;
  topicName: string;
  classId?: number;
  className?: string;
}

interface CompletedItem {
  tempId: string;
  realId: string;
  title: string;
  type: "note" | "test";
  courseId: string;
  topicName: string;
}

interface GenerationContextType {
  generatingItems: GeneratingItem[];
  completedItems: CompletedItem[];
  startNoteGeneration: (params: {
    tempId: string;
    title: string;
    topicDefinition: string;
    teacherId: string;
    apiTeacherId: number;
    apiClassId: number;
    subjectName: string;
    courseId: string;
    classLabel: string;
    topicName: string;
    audienceSelection: {
      levels: ("weak" | "medium" | "strong")[];
      students: number[];
    } | null;
  }) => void;
  startTestGeneration: (params: {
    tempId: string;
    title: string;
    topicDefinition: string;
    teacherId: string;
    apiTeacherId: number;
    apiClassId: number;
    subjectName: string;
    courseId: string;
    classLabel: string;
    topicName: string;
    audienceSelection: {
      levels: ("weak" | "medium" | "strong")[];
      students: number[];
    } | null;
  }) => void;
  clearCompletedItem: (tempId: string) => void;
  getGeneratingItemsForTopic: (
    courseId: string,
    topicName: string,
  ) => GeneratingItem[];
  getCompletedItemsForTopic: (
    courseId: string,
    topicName: string,
  ) => CompletedItem[];
}

const GenerationContext = createContext<GenerationContextType | null>(null);

export const useGeneration = () => {
  const context = useContext(GenerationContext);
  if (!context) {
    throw new Error("useGeneration must be used within GenerationProvider");
  }
  return context;
};

export const GenerationProvider = ({ children }: { children: ReactNode }) => {
  const [generatingItems, setGeneratingItems] = useState<GeneratingItem[]>([]);
  const [completedItems, setCompletedItems] = useState<CompletedItem[]>([]);

  // Use refs to track active generations and avoid duplicate calls
  const activeGenerations = useRef<Set<string>>(new Set());

  const startNoteGeneration = useCallback(
    async (params: {
      tempId: string;
      title: string;
      topicDefinition: string;
      teacherId: string;
      apiTeacherId: number;
      apiClassId: number;
      subjectName: string;
      courseId: string;
      classLabel: string;
      topicName: string;
      audienceSelection: {
        levels: ("weak" | "medium" | "strong")[];
        students: number[];
      } | null;
    }) => {
      // Prevent duplicate generations
      if (activeGenerations.current.has(params.tempId)) {
        return;
      }
      activeGenerations.current.add(params.tempId);

      // Add to generating list
      setGeneratingItems((prev) => [
        ...prev,
        {
          tempId: params.tempId,
          type: "note",
          title: params.title,
          courseId: params.courseId,
          topicName: params.topicName,
          classId: params.apiClassId,
          className: params.classLabel,
        },
      ]);

      const hasLevels =
        params.audienceSelection?.levels &&
        params.audienceSelection.levels.length > 0;
      const hasStudents =
        params.audienceSelection?.students &&
        params.audienceSelection.students.length > 0;

      let assignmentScope: "class" | "levels" | "students";
      let assignedLevels: ("weak" | "medium" | "strong")[] | undefined;
      let assignedStudents: number[] | undefined;

      if (hasLevels) {
        assignmentScope = "levels";
        assignedLevels = params.audienceSelection!.levels;
        assignedStudents = undefined;
      } else if (hasStudents) {
        assignmentScope = "students";
        assignedLevels = undefined;
        assignedStudents = params.audienceSelection!.students;
      } else {
        assignmentScope = "class";
        assignedLevels = undefined;
        assignedStudents = undefined;
      }

      try {
        let response;

        if (hasLevels) {
          response = await generateNotesByLevel({
            class_id: params.apiClassId,
            teacher_id: params.apiTeacherId,
            subject: params.subjectName,
            level_list: params.audienceSelection!.levels,
            topic_definition: params.topicDefinition,
          });
        } else if (hasStudents) {
          response = await generateNotesIndividual({
            class_id: params.apiClassId,
            teacher_id: params.apiTeacherId,
            subject: params.subjectName,
            student_list: params.audienceSelection!.students,
            topic_definition: params.topicDefinition,
          });
        } else {
          response = await generateNotesByLevel({
            class_id: params.apiClassId,
            teacher_id: params.apiTeacherId,
            subject: params.subjectName,
            level_list: ["weak", "medium", "strong"],
            topic_definition: params.topicDefinition,
          });
        }

        if (!response?.title || !response?.contents) {
          throw new Error("Invalid notes response");
        }

        const created = addMaterial({
          type: "note",
          title: response.title,
          content: response.contents,
          teacherNotes: response.teacher_notes,
          sources: response.sources,
          teacherId: params.teacherId,
          courseId: params.courseId,
          subject: params.subjectName,
          classId: params.apiClassId || undefined,
          className: params.classLabel,
          topicName: params.topicName,
          assignmentScope,
          assignedLevels,
          assignedStudents,
        });

        // Move from generating to completed
        setGeneratingItems((prev) =>
          prev.filter((item) => item.tempId !== params.tempId),
        );
        setCompletedItems((prev) => [
          ...prev,
          {
            tempId: params.tempId,
            realId: created.id,
            title: created.title,
            type: "note",
            courseId: params.courseId,
            topicName: params.topicName,
          },
        ]);
      } catch (error) {
        console.error("Note generation failed:", error);
        // On error, use fallback content to continue UI testing
        try {
          const fallback = buildFallbackNotes(
            params.topicDefinition,
            params.topicName,
          );
          const created = addMaterial({
            type: "note",
            title: fallback.title,
            content: fallback.contents,
            teacherNotes: fallback.teacher_notes,
            sources: fallback.sources,
            teacherId: params.teacherId,
            courseId: params.courseId,
            subject: params.subjectName,
            classId: params.apiClassId || undefined,
            className: params.classLabel,
            topicName: params.topicName,
            assignmentScope,
            assignedLevels,
            assignedStudents,
          });

          setGeneratingItems((prev) =>
            prev.filter((item) => item.tempId !== params.tempId),
          );
          setCompletedItems((prev) => [
            ...prev,
            {
              tempId: params.tempId,
              realId: created.id,
              title: created.title,
              type: "note",
              courseId: params.courseId,
              topicName: params.topicName,
            },
          ]);
        } catch (fallbackError) {
          // Complete failure - log and remove from generating
          console.error("Fallback note creation also failed:", fallbackError);
          setGeneratingItems((prev) =>
            prev.filter((item) => item.tempId !== params.tempId),
          );
        }
      } finally {
        activeGenerations.current.delete(params.tempId);
      }
    },
    [],
  );

  const startTestGeneration = useCallback(
    async (params: {
      tempId: string;
      title: string;
      topicDefinition: string;
      teacherId: string;
      apiTeacherId: number;
      apiClassId: number;
      subjectName: string;
      courseId: string;
      classLabel: string;
      topicName: string;
      audienceSelection: {
        levels: ("weak" | "medium" | "strong")[];
        students: number[];
      } | null;
    }) => {
      // Prevent duplicate generations
      if (activeGenerations.current.has(params.tempId)) {
        return;
      }
      activeGenerations.current.add(params.tempId);

      // Add to generating list
      setGeneratingItems((prev) => [
        ...prev,
        {
          tempId: params.tempId,
          type: "test",
          title: params.title,
          courseId: params.courseId,
          topicName: params.topicName,
          classId: params.apiClassId,
          className: params.classLabel,
        },
      ]);

      const hasLevels =
        params.audienceSelection?.levels &&
        params.audienceSelection.levels.length > 0;
      const hasStudents =
        params.audienceSelection?.students &&
        params.audienceSelection.students.length > 0;

      let assignmentScope: "class" | "levels" | "students";
      let assignedLevels: ("weak" | "medium" | "strong")[] | undefined;
      let assignedStudents: number[] | undefined;

      if (hasLevels) {
        assignmentScope = "levels";
        assignedLevels = params.audienceSelection!.levels;
        assignedStudents = undefined;
      } else if (hasStudents) {
        assignmentScope = "students";
        assignedLevels = undefined;
        assignedStudents = params.audienceSelection!.students;
      } else {
        assignmentScope = "class";
        assignedLevels = undefined;
        assignedStudents = undefined;
      }

      try {
        const response = await generateTest({
          class_id: params.apiClassId,
          teacher_id: params.apiTeacherId,
          subject: params.subjectName,
          topic_definition: params.topicDefinition,
          level_list: assignedLevels ?? [],
          student_list: assignedStudents ?? [],
        });

        const payload = response?.title
          ? response
          : buildFallbackTest(params.topicDefinition, params.topicName);

        const created = addMaterial({
          type: "test",
          title: payload.title,
          questions: payload.questions,
          teacherId: params.teacherId,
          courseId: params.courseId,
          subject: params.subjectName,
          classId: params.apiClassId || undefined,
          className: params.classLabel,
          topicName: params.topicName,
          assignmentScope,
          assignedLevels,
          assignedStudents,
        });

        // Move from generating to completed
        setGeneratingItems((prev) =>
          prev.filter((item) => item.tempId !== params.tempId),
        );
        setCompletedItems((prev) => [
          ...prev,
          {
            tempId: params.tempId,
            realId: created.id,
            title: created.title,
            type: "test",
            courseId: params.courseId,
            topicName: params.topicName,
          },
        ]);
      } catch (error) {
        console.error("Test generation failed:", error);
        // On error, still try to create a fallback
        try {
          const fallback = buildFallbackTest(
            params.topicDefinition,
            params.topicName,
          );
          const created = addMaterial({
            type: "test",
            title: fallback.title,
            questions: fallback.questions,
            teacherId: params.teacherId,
            courseId: params.courseId,
            subject: params.subjectName,
            classId: params.apiClassId || undefined,
            className: params.classLabel,
            topicName: params.topicName,
            assignmentScope,
            assignedLevels,
            assignedStudents,
          });

          setGeneratingItems((prev) =>
            prev.filter((item) => item.tempId !== params.tempId),
          );
          setCompletedItems((prev) => [
            ...prev,
            {
              tempId: params.tempId,
              realId: created.id,
              title: created.title,
              type: "test",
              courseId: params.courseId,
              topicName: params.topicName,
            },
          ]);
        } catch (fallbackError) {
          // Complete failure - log and remove from generating
          console.error("Fallback test creation also failed:", fallbackError);
          setGeneratingItems((prev) =>
            prev.filter((item) => item.tempId !== params.tempId),
          );
        }
      } finally {
        activeGenerations.current.delete(params.tempId);
      }
    },
    [],
  );

  const clearCompletedItem = useCallback((tempId: string) => {
    setCompletedItems((prev) => prev.filter((item) => item.tempId !== tempId));
  }, []);

  const getGeneratingItemsForTopic = useCallback(
    (courseId: string, topicName: string) => {
      return generatingItems.filter(
        (item) => item.courseId === courseId && item.topicName === topicName,
      );
    },
    [generatingItems],
  );

  const getCompletedItemsForTopic = useCallback(
    (courseId: string, topicName: string) => {
      return completedItems.filter(
        (item) => item.courseId === courseId && item.topicName === topicName,
      );
    },
    [completedItems],
  );

  return (
    <GenerationContext.Provider
      value={{
        generatingItems,
        completedItems,
        startNoteGeneration,
        startTestGeneration,
        clearCompletedItem,
        getGeneratingItemsForTopic,
        getCompletedItemsForTopic,
      }}
    >
      {children}
    </GenerationContext.Provider>
  );
};
