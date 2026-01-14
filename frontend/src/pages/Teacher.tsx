
import { useEffect, useMemo, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { teachers } from "../data/teachers";
import Modal from "../components/Modal";
import Panel from "../components/Panel";
import TeacherSidebar from "../components/TeacherSidebar";
import { addTopic, getTopics } from "../data/materialsStorage";
import {
  getTeacherData,
  getTeacherStudents,
} from "../api/teacher";
import type { TeacherClassItem, TeacherStudentItem } from "../api/teacher";
import { classIdToLabel, classLabelToId } from "../data/classUtils";
import { toNumericId } from "../api/idUtils";

const subjectSlugMap: Record<string, string> = {
  Алгебра: "algebra",
  Геометрія: "geometry",
  "Українська мова": "ukr-lang",
  "Історія України": "history",
};
const subjectLabelMap: Record<string, string> = {
  algebra: "Алгебра",
  geometry: "Геометрія",
  "ukr-lang": "Українська мова",
  history: "Історія України",
};

const buildCourseId = (subject: string, grade: number) => {
  const slug =
    subjectSlugMap[subject] ??
    subject.toLowerCase().replace(/\s+/g, "-");
  return `${slug}-${grade}`;
};

const subjectFromCourseId = (courseId: string) => {
  const parts = courseId.split("-");
  const slug = parts.slice(0, -1).join("-");
  return subjectLabelMap[slug] ?? courseId;
};

const fallbackCourses = [
  {
    grade: "8 клас",
    items: [
      { id: "algebra-8", name: "Алгебра" },
      { id: "history-8", name: "Історія України" },
      { id: "ukr-lang-8", name: "Українська мова" },
    ],
  },
  {
    grade: "9 клас",
    items: [
      { id: "algebra-9", name: "Алгебра" },
      { id: "history-9", name: "Історія України" },
      { id: "ukr-lang-9", name: "Українська мова" },
    ],
  },
];

const fallbackClassesByCourse: Record<
  string,
  { id: number; label: string }[]
> = {
  "algebra-8": ["8"].map((label) => ({
    id: classLabelToId(label) ?? 0,
    label,
  })),
  "history-8": ["8"].map((label) => ({
    id: classLabelToId(label) ?? 0,
    label,
  })),
  "ukr-lang-8": ["8"].map((label) => ({
    id: classLabelToId(label) ?? 0,
    label,
  })),
  "algebra-9": ["9"].map((label) => ({
    id: classLabelToId(label) ?? 0,
    label,
  })),
  "history-9": ["9"].map((label) => ({
    id: classLabelToId(label) ?? 0,
    label,
  })),
  "ukr-lang-9": ["9"].map((label) => ({
    id: classLabelToId(label) ?? 0,
    label,
  })),
};

const Teacher = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const teacher = useMemo(
    () => teachers.find((item) => item.id === id),
    [id]
  );
  const apiTeacherId = teacher?.apiId ?? toNumericId(id) ?? 0;
  const [teacherClasses, setTeacherClasses] = useState<TeacherClassItem[]>([]);
  const [teacherStudents, setTeacherStudents] = useState<TeacherStudentItem[]>([]);

  useEffect(() => {
    if (!apiTeacherId) {
      return;
    }
    getTeacherData(apiTeacherId)
      .then((response) => {
        setTeacherClasses(response.classes);
      })
      .catch((error) => {
        console.error(error);
        setTeacherClasses([]);
      });
  }, [apiTeacherId]);

  const { courses, classesByCourse, courseSubjectMap } = useMemo(() => {
    if (!teacherClasses.length) {
      return {
        courses: fallbackCourses,
        classesByCourse: fallbackClassesByCourse,
        courseSubjectMap: {} as Record<string, string>,
      };
    }

    const courseGroups = new Map<
      string,
      { grade: string; items: { id: string; name: string }[] }
    >();
    const classMap: Record<string, { id: number; label: string }[]> = {};
    const subjectMap: Record<string, string> = {};

    teacherClasses.forEach((entry) => {
      const courseId = buildCourseId(entry.subject, entry.class_number);
      const gradeLabel = `${entry.class_number} клас`;
      if (!courseGroups.has(gradeLabel)) {
        courseGroups.set(gradeLabel, { grade: gradeLabel, items: [] });
      }
      const group = courseGroups.get(gradeLabel);
      if (group && !group.items.find((item) => item.id === courseId)) {
        group.items.push({ id: courseId, name: entry.subject });
      }
      subjectMap[courseId] = entry.subject;
      if (!classMap[courseId]) {
        classMap[courseId] = [];
      }
      classMap[courseId].push({
        id: entry.class_id,
        label: classIdToLabel(entry.class_number, entry.class_id),
      });
    });

    return {
      courses: Array.from(courseGroups.values()),
      classesByCourse: classMap,
      courseSubjectMap: subjectMap,
    };
  }, [teacherClasses]);

  // Filter courses based on teacher's allowed subjects
  const filteredCourses = useMemo(() => {
    if (!teacher || !teacher.subjectIds) return courses;

    return courses
      .map((gradeGroup) => ({
        ...gradeGroup,
        items: gradeGroup.items.filter((item) =>
          teacher.subjectIds?.some((subjectId) => item.id.startsWith(subjectId))
        ),
      }))
      .filter((group) => group.items.length > 0);
  }, [teacher, courses]);


  const initialCourseId = filteredCourses[0]?.items[0]?.id ?? "";

  useEffect(() => {
    if (filteredCourses[0]?.items[0]?.id) {
      setSelectedCourseId(filteredCourses[0].items[0].id);
      const firstCourseId = filteredCourses[0].items[0].id;
      const classes = classesByCourse[firstCourseId] ?? [];
      setSelectedClassId(classes[0]?.id ?? null);
    }
  }, [teacher, filteredCourses, classesByCourse]);

  const [selectedCourseId, setSelectedCourseId] = useState(initialCourseId);
  const currentClasses = classesByCourse[selectedCourseId] ?? [];
  const [selectedClassId, setSelectedClassId] = useState<number | null>(
    currentClasses[0]?.id ?? null
  );
  const selectedClassLabel =
    currentClasses.find((item) => item.id === selectedClassId)?.label ?? "";
  const [topicsByClass, setTopicsByClass] = useState<
    Record<string, string[]>
  >({});
  const currentTopics = topicsByClass[selectedClassLabel] ?? [];
  const [isTopicModalOpen, setIsTopicModalOpen] = useState(false);
  const [newTopic, setNewTopic] = useState("");

  const handleCourseSelect = (courseId: string) => {
    setSelectedCourseId(courseId);
    const nextClasses = classesByCourse[courseId] ?? [];
    setSelectedClassId(nextClasses[0]?.id ?? null);
  };

  useEffect(() => {
    const storedTopics = getTopics({
      teacherId: id,
      courseId: selectedCourseId,
    });
    const nextTopicsByClass = storedTopics.reduce<Record<string, string[]>>(
      (acc, item) => {
        const classKey = item.className ?? "";
        if (!classKey) {
          return acc;
        }
        if (!acc[classKey]) {
          acc[classKey] = [];
        }
        acc[classKey].push(item.title);
        return acc;
      },
      {}
    );
    setTopicsByClass(nextTopicsByClass);
  }, [id, selectedCourseId]);

  useEffect(() => {
    if (!apiTeacherId || !selectedClassId) {
      return;
    }
    const subject =
      courseSubjectMap[selectedCourseId] ?? subjectFromCourseId(selectedCourseId);
    getTeacherStudents({
      class_id: selectedClassId,
      teacher_id: apiTeacherId,
      subject,
    })
      .then((response) => {
        setTeacherStudents(response.students);
      })
      .catch((error) => {
        console.error(error);
        setTeacherStudents([]);
      });
  }, [apiTeacherId, selectedClassId, selectedCourseId, courseSubjectMap]);

  const handleAddTopic = () => {
    const trimmedTopic = newTopic.trim();
    if (!trimmedTopic || !selectedClassLabel) {
      return;
    }

    const created = addTopic({
      title: trimmedTopic,
      teacherId: id,
      courseId: selectedCourseId,
      className: selectedClassLabel,
    });
    setTopicsByClass((prev) => {
      const existing = prev[selectedClassLabel] ?? [];
      if (existing.includes(created.title)) {
        return prev;
      }

      return {
        ...prev,
        [selectedClassLabel]: [...existing, created.title],
      };
    });
    setIsTopicModalOpen(false);
    setNewTopic("");
  };

  const handleTopicOpen = (topic: string) => {
    if (!id) {
      return;
    }

    if (!selectedClassId) {
      return;
    }
    const encodedCourse = encodeURIComponent(selectedCourseId);
    const encodedClass = encodeURIComponent(String(selectedClassId));
    const encodedTopic = encodeURIComponent(topic);
    navigate(
      `/teacher/${id}/topic/${encodedCourse}/${encodedClass}/${encodedTopic}`
    );
  };

  return (
    <div className="min-h-screen bg-[#1E73F7] text-slate-900">
      <div className="flex min-h-screen">
        <TeacherSidebar
          teacherName={
            teacher ? `${teacher.firstName} ${teacher.lastName}` : "Вчитель"
          }
          activeItem="materials"
        />
        <main className="flex-1 px-8 py-10">
          <div className="relative min-h-[calc(100vh-5rem)]">
            <div className="grid gap-6 lg:grid-cols-[1.1fr_1fr]">
              <Panel title="Курси">
                <div className="space-y-6">
                  {filteredCourses.map((group) => (
                    <div key={group.grade}>
                      <div className="text-sm font-semibold text-slate-700">
                        {group.grade}
                      </div>
                      <div className="mt-3 space-y-3">
                        {group.items.map((course) => (
                          <button
                            key={course.id}
                            type="button"
                            onClick={() => handleCourseSelect(course.id)}
                            className={`flex w-full items-center justify-between rounded-2xl border px-4 py-3 text-left text-sm font-medium transition ${
                              selectedCourseId === course.id
                                ? "border-[#BFD6FF] bg-[#E9F1FF] text-slate-900"
                                : "border-slate-200 bg-white text-slate-800 hover:border-slate-300"
                            } cursor-pointer`}
                          >
                            <span>{course.name}</span>
                            <span className="text-lg text-slate-500">›</span>
                          </button>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              </Panel>
              <Panel title="Теми">
                <div className="space-y-3">
                  {currentTopics.map((topic) => (
                    <button
                      key={topic}
                      type="button"
                      onClick={() => handleTopicOpen(topic)}
                      className="flex w-full items-center justify-between rounded-2xl border border-slate-200 px-4 py-3 text-left text-sm font-medium text-slate-800 transition hover:border-slate-300 hover:bg-slate-50 cursor-pointer"
                    >
                      <span>{topic}</span>
                      <span className="text-lg text-slate-400">›</span>
                    </button>
                  ))}
                </div>
              </Panel>
            </div>
            <button
              type="button"
              className="absolute bottom-0 right-0 flex items-center gap-2 rounded-full bg-white px-6 py-3 text-sm font-semibold text-[#1E73F7] shadow-lg transition hover:-translate-y-0.5 hover:bg-blue-50 hover:shadow-xl cursor-pointer"
              onClick={() => setIsTopicModalOpen(true)}
            >
              <span className="text-lg">＋</span>
              Додати тему
            </button>
          </div>
        </main>
      </div>
      <Modal
        isOpen={isTopicModalOpen}
        onClose={() => setIsTopicModalOpen(false)}
        title="Додайте тему"
        size="lg"
      >
        <div className="flex flex-col items-center gap-6">
          <input
            type="text"
            value={newTopic}
            onChange={(event) => setNewTopic(event.target.value)}
            onKeyDown={(e) => {
                if (e.key === 'Enter') {
                    handleAddTopic();
                }
            }}
            placeholder="Введіть тему"
            className="w-full rounded-full bg-[#E9F1FF] px-8 py-5 text-lg font-medium text-slate-700 placeholder-slate-500 outline-none transition focus:bg-white focus:ring-2 focus:ring-[#BFD6FF]"
          />
          <button
            type="button"
            className="ml-auto rounded-full bg-[#1E73F7] px-8 py-4 text-lg font-semibold text-white shadow transition hover:-translate-y-0.5 hover:bg-[#1A63D6] hover:shadow-lg cursor-pointer"
            onClick={handleAddTopic}
          >
            Додати
          </button>
        </div>
      </Modal>
    </div>
  );
};

export default Teacher;
