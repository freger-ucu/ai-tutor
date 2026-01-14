
import { useEffect, useMemo, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import Modal from "../components/Modal";
import Panel from "../components/Panel";
import TeacherSidebar from "../components/TeacherSidebar";
import { addTopic, getTopics } from "../data/materialsStorage";
import {
  getTeacherData,
  getTeacherStudents,
} from "../api/teacher";
import type { TeacherClassItem, TeacherStudentItem } from "../api/teacher";
import { classIdToLabel } from "../data/classUtils";
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

const Teacher = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const apiTeacherId = toNumericId(id) ?? 0;
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
        courses: [],
        classesByCourse: {},
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

  const filteredCourses = courses;
  const initialCourseId = courses[0]?.items[0]?.id ?? "";

  useEffect(() => {
    if (courses[0]?.items[0]?.id) {
      setSelectedCourseId(courses[0].items[0].id);
      const firstCourseId = courses[0].items[0].id;
      const classes = classesByCourse[firstCourseId] ?? [];
      setSelectedClassId(classes[0]?.id ?? null);
    }
  }, [courses, classesByCourse]);

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
    const subject =
      courseSubjectMap[selectedCourseId] ?? subjectFromCourseId(selectedCourseId);
    const storedTopics = getTopics({
      teacherId: id,
      courseId: selectedCourseId,
      subject,
      classId: selectedClassId ?? undefined,
      className: selectedClassLabel,
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
  }, [id, selectedCourseId, selectedClassId, selectedClassLabel, courseSubjectMap]);

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

    const subject =
      courseSubjectMap[selectedCourseId] ?? subjectFromCourseId(selectedCourseId);
    const created = addTopic({
      title: trimmedTopic,
      teacherId: id,
      courseId: selectedCourseId,
      subject,
      classId: selectedClassId ?? undefined,
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
            id ? `Вчитель ${id}` : "Вчитель"
          }
          activeItem="materials"
        />
        <main className="flex-1 px-8 py-10">
          <div className="relative min-h-[calc(100vh-5rem)]">
            <div className="grid gap-6 lg:grid-cols-[1.1fr_1fr]">
              <Panel title="Курси">
                <div className="space-y-6">
                  {filteredCourses.length === 0 && (
                    <div className="rounded-2xl border border-dashed border-slate-200 bg-slate-50 px-4 py-4 text-sm text-slate-600">
                      Немає доступних курсів. Перевірте ID вчителя або дані в
                      бекенді.
                    </div>
                  )}
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
                  {currentClasses.length > 0 && (
                    <div className="border-t border-slate-200 pt-4">
                      <div className="text-sm font-semibold text-slate-700">
                        Клас
                      </div>
                      <div className="mt-3 grid gap-3 sm:grid-cols-2">
                        {currentClasses.map((item) => (
                          <button
                            key={item.id}
                            type="button"
                            onClick={() => setSelectedClassId(item.id)}
                            className={`flex w-full items-center justify-between rounded-2xl border px-4 py-3 text-left text-sm font-medium transition ${
                              selectedClassId === item.id
                                ? "border-[#BFD6FF] bg-[#E9F1FF] text-slate-900"
                                : "border-slate-200 bg-white text-slate-800 hover:border-slate-300"
                            } cursor-pointer`}
                          >
                            <span>{item.label}</span>
                            <span className="text-xs text-slate-500">
                              ID {item.id}
                            </span>
                          </button>
                        ))}
                      </div>
                    </div>
                  )}
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
              disabled={!selectedClassId}
              className="absolute bottom-0 right-0 flex items-center gap-2 rounded-full bg-white px-6 py-3 text-sm font-semibold text-[#1E73F7] shadow-lg transition hover:-translate-y-0.5 hover:bg-blue-50 hover:shadow-xl disabled:cursor-not-allowed disabled:opacity-60"
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
