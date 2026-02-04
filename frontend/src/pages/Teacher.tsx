import { useEffect, useMemo, useRef, useState } from "react";
import { useNavigate, useParams, useSearchParams } from "react-router-dom";
import Modal from "../components/Modal";
import Panel from "../components/Panel";
import TeacherSidebar from "../components/TeacherSidebar";
import { addTopic, getTopics } from "../data/materialsStorage";
import { getTeacherData, getTeacherStudents } from "../api/teacher";
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
const levelLabels: Record<string, string> = {
  strong: "Високий",
  medium: "Середній",
  weak: "Початковий",
};

const buildCourseId = (subject: string, grade: number) => {
  const slug =
    subjectSlugMap[subject] ?? subject.toLowerCase().replace(/\s+/g, "-");
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
  const [searchParams, setSearchParams] = useSearchParams();
  const apiTeacherId = toNumericId(id) ?? 0;
  const [teacherClasses, setTeacherClasses] = useState<TeacherClassItem[]>([]);
  const [students, setStudents] = useState<TeacherStudentItem[]>([]);
  const [isStudentsLoading, setIsStudentsLoading] = useState(false);
  const createDefaultFilters = () => ({
    strong: true,
    medium: true,
    weak: true,
  });
  const [levelFilters, setLevelFilters] = useState(createDefaultFilters);
  const [pendingLevelFilters, setPendingLevelFilters] =
    useState(createDefaultFilters);
  const [isFilterOpen, setIsFilterOpen] = useState(false);
  const filterRef = useRef<HTMLDivElement | null>(null);

  const viewParam = searchParams.get("view");
  const activeView: "materials" | "students" =
    viewParam === "students" ? "students" : "materials";

  const setActiveView = (view: "materials" | "students") => {
    if (view === "students") {
      setSearchParams({ view: "students" });
    } else {
      setSearchParams({});
    }
  };

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

  const courseGroups = useMemo(() => {
    return courses.flatMap((group) => {
      const gradeNumber = Number(group.grade.split(" ")[0]);
      if (gradeNumber !== 8 && gradeNumber !== 9) {
        return [];
      }
      return group.items.map((course) => ({
        key: `${group.grade}-${course.id}`,
        title: `${group.grade} ${course.name}`,
        courseId: course.id,
        classes: classesByCourse[course.id] ?? [],
      }));
    });
  }, [courses, classesByCourse]);
  const initialCourseId = courseGroups[0]?.courseId ?? "";

  useEffect(() => {
    const firstGroup = courseGroups[0];
    if (firstGroup) {
      setSelectedCourseId(firstGroup.courseId);
      setSelectedClassId(firstGroup.classes[0]?.id ?? null);
    }
  }, [courseGroups]);

  const [selectedCourseId, setSelectedCourseId] = useState(initialCourseId);
  const currentClasses = classesByCourse[selectedCourseId] ?? [];
  const [selectedClassId, setSelectedClassId] = useState<number | null>(
    currentClasses[0]?.id ?? null,
  );
  const selectedClassLabel =
    currentClasses.find((item) => item.id === selectedClassId)?.label ?? "";
  const [topicsByClass, setTopicsByClass] = useState<Record<string, string[]>>(
    {},
  );
  const currentTopics = topicsByClass[selectedClassLabel] ?? [];
  const [isTopicModalOpen, setIsTopicModalOpen] = useState(false);
  const [newTopic, setNewTopic] = useState("");

  const handleCourseSelect = (courseId: string, classId?: number | null) => {
    setSelectedCourseId(courseId);
    const nextClasses = classesByCourse[courseId] ?? [];
    const nextClassId = classId ?? nextClasses[0]?.id ?? null;
    setSelectedClassId(nextClassId);
  };

  useEffect(() => {
    // Don't filter by teacherId - topics should be visible regardless of which teacher created them
    // This matches how students see topics (without teacherId filter)
    const storedTopics = getTopics({
      courseId: selectedCourseId,
      classId: selectedClassId ?? undefined,
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
      {},
    );
    setTopicsByClass(nextTopicsByClass);
  }, [selectedCourseId, selectedClassId]);

  useEffect(() => {
    if (activeView !== "students") {
      return;
    }
    if (!apiTeacherId || !selectedClassId || !selectedCourseId) {
      setStudents([]);
      return;
    }
    const subject =
      courseSubjectMap[selectedCourseId] ??
      subjectFromCourseId(selectedCourseId);
    setIsStudentsLoading(true);
    getTeacherStudents({
      class_id: selectedClassId,
      teacher_id: apiTeacherId,
      subject,
    })
      .then((response) => {
        setStudents(response.students);
      })
      .catch((error) => {
        console.error(error);
        setStudents([]);
      })
      .finally(() => {
        setIsStudentsLoading(false);
      });
  }, [
    activeView,
    apiTeacherId,
    selectedClassId,
    selectedCourseId,
    courseSubjectMap,
  ]);

  useEffect(() => {
    const handleOutsideClick = (event: MouseEvent) => {
      if (
        filterRef.current &&
        !filterRef.current.contains(event.target as Node)
      ) {
        setIsFilterOpen(false);
      }
    };
    document.addEventListener("mousedown", handleOutsideClick);
    return () => document.removeEventListener("mousedown", handleOutsideClick);
  }, []);

  const filteredStudents = useMemo(() => {
    return students.filter((student) => {
      if (student.subject_level === "strong") {
        return levelFilters.strong;
      }
      if (student.subject_level === "medium") {
        return levelFilters.medium;
      }
      return levelFilters.weak;
    });
  }, [students, levelFilters]);

  const filterButtonLabel = useMemo(() => {
    const active = [
      levelFilters.strong ? "strong" : null,
      levelFilters.medium ? "medium" : null,
      levelFilters.weak ? "weak" : null,
    ].filter(Boolean) as Array<"strong" | "medium" | "weak">;
    if (active.length === 3) {
      return "Всі рівні (3)";
    }
    if (active.length === 2) {
      return "Обрано 2 рівні";
    }
    if (active.length === 1) {
      const single = active[0];
      return single === "strong"
        ? "Високий рівень"
        : single === "medium"
          ? "Середній рівень"
          : "Початковий рівень";
    }
    return "Рівні не обрано";
  }, [levelFilters]);

  const toggleFilter = (level: "strong" | "medium" | "weak") => {
    setPendingLevelFilters((prev) => ({ ...prev, [level]: !prev[level] }));
  };

  const applyFilters = () => {
    setLevelFilters({ ...pendingLevelFilters });
    setIsFilterOpen(false);
  };

  const handleAddTopic = () => {
    const trimmedTopic = newTopic.trim();
    if (!trimmedTopic || !selectedClassLabel) {
      return;
    }

    const subject =
      courseSubjectMap[selectedCourseId] ??
      subjectFromCourseId(selectedCourseId);
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
      `/teacher/${id}/topic/${encodedCourse}/${encodedClass}/${encodedTopic}`,
    );
  };

  return (
    <div className="min-h-screen bg-[#1E73F7] text-slate-900">
      <div className="flex min-h-screen">
        <div className="hidden lg:flex">
          <TeacherSidebar
            teacherName={id ? `Вчитель ${id}` : "Вчитель"}
            activeItem={activeView}
            onMaterialsClick={() => setActiveView("materials")}
            onStudentsClick={() => setActiveView("students")}
          />
        </div>
        <main
          className="flex-1 px-8 py-10 overflow-y-auto lg:overflow-visible"
          data-scroll-root="mobile"
        >
          <div className="mb-6 rounded-2xl bg-white/95 px-4 py-3 shadow-md lg:hidden">
            <div className="flex items-center justify-between gap-3">
              <div className="flex items-center gap-3">
                <div
                  className="h-10 w-10 overflow-hidden rounded-full bg-slate-200"
                  style={{
                    backgroundImage:
                      "url('https://i1.poltava.to/uploads/2017/09/2017-09-19/best.jpg')",
                    backgroundSize: "cover",
                    backgroundPosition: "center",
                  }}
                />
                <div className="text-sm font-semibold text-slate-700">
                  {id ? `Вчитель ${id}` : "Вчитель"}
                </div>
              </div>
              <button
                type="button"
                onClick={() => navigate("/")}
                className="rounded-full border border-rose-200 bg-rose-50 px-3 py-1 text-xs font-semibold text-rose-600 transition hover:border-rose-300 hover:text-rose-700"
              >
                Вийти
              </button>
            </div>
            <div className="mt-3 flex items-center gap-2">
              <button
                type="button"
                onClick={() => setActiveView("materials")}
                className={`flex-1 rounded-full px-4 py-2 text-sm font-semibold transition ${
                  activeView === "materials"
                    ? "bg-[#1E73F7] text-white"
                    : "bg-slate-100 text-slate-700"
                }`}
              >
                Матеріали
              </button>
              <button
                type="button"
                onClick={() => setActiveView("students")}
                className={`flex-1 rounded-full px-4 py-2 text-sm font-semibold transition ${
                  activeView === "students"
                    ? "bg-[#1E73F7] text-white"
                    : "bg-slate-100 text-slate-700"
                }`}
              >
                Учні
              </button>
            </div>
          </div>
          <div
            className={`relative ${
              activeView === "students"
                ? "lg:h-[calc(100vh-5rem)] lg:overflow-hidden"
                : "lg:min-h-[calc(100vh-5rem)]"
            }`}
          >
            {activeView === "materials" ? (
              <>
                <div className="grid gap-6 lg:grid-cols-2">
                  <Panel title="Курси">
                    <div className="space-y-6">
                      {courseGroups.length === 0 && (
                        <div className="rounded-2xl border border-dashed border-slate-200 bg-slate-50 px-4 py-4 text-sm text-slate-600">
                          Немає доступних курсів. Перевірте ID вчителя або дані
                          в бекенді.
                        </div>
                      )}
                      {courseGroups.map((group) => {
                        const gradeNumber = group.title.split(" ")[0];
                        const subjectName =
                          courseSubjectMap[group.courseId] ??
                          subjectFromCourseId(group.courseId);
                        return (
                          <div key={group.key}>
                            <div className="text-sm font-semibold text-slate-700">
                              {gradeNumber} клас
                            </div>
                            <div className="mt-3 space-y-3">
                              {group.classes.map((item) => (
                                <button
                                  key={item.id}
                                  type="button"
                                  onClick={() =>
                                    handleCourseSelect(group.courseId, item.id)
                                  }
                                  className={`flex w-full items-center justify-between rounded-2xl border px-4 py-3 text-left text-sm font-medium transition ${
                                    selectedCourseId === group.courseId &&
                                    selectedClassId === item.id
                                      ? "border-[#BFD6FF] bg-[#E9F1FF] text-slate-900"
                                      : "border-slate-200 bg-white text-slate-800 hover:border-slate-300"
                                  } cursor-pointer`}
                                >
                                  <span>{subjectName}</span>
                                  <span className="text-xs text-slate-500">
                                    ID {item.id}
                                  </span>
                                </button>
                              ))}
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </Panel>
                  <Panel>
                    <div className="flex items-center gap-3">
                      <h2 className="text-lg font-semibold text-slate-900 lg:text-xl">
                        Теми
                      </h2>
                      <button
                        type="button"
                        onClick={() => setIsTopicModalOpen(true)}
                        className="ml-auto mr-1 rounded-full bg-[#1E73F7] px-3 py-2 text-xs font-semibold text-white shadow-sm transition hover:bg-[#1A63D6] lg:hidden"
                      >
                        + Додати тему
                      </button>
                    </div>
                    <div className="mt-4 space-y-3 lg:mt-6">
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
                  className="absolute bottom-0 right-0 hidden items-center gap-2 rounded-full bg-white px-6 py-3 text-sm font-semibold text-[#1E73F7] shadow-lg transition hover:-translate-y-0.5 hover:bg-blue-50 hover:shadow-xl disabled:cursor-not-allowed disabled:opacity-60 lg:flex"
                  onClick={() => setIsTopicModalOpen(true)}
                >
                  <span className="text-lg">＋</span>
                  Додати тему
                </button>
              </>
            ) : (
              <>
                <div className="grid h-full grid-cols-1 gap-6 lg:grid-cols-2">
                  <Panel
                    className="flex h-full flex-col overflow-hidden"
                    contentClassName="flex flex-col flex-1 min-h-0"
                  >
                    <div className="flex items-center justify-between shrink-0">
                      <h2 className="text-xl font-semibold text-slate-900">
                        Курси
                      </h2>
                    </div>
                    <div className="mt-6 flex-1 min-h-0 overflow-y-auto space-y-6 pr-1 scroll-smooth">
                      {courseGroups.length === 0 && (
                        <div className="rounded-2xl border border-dashed border-slate-200 bg-slate-50 px-4 py-4 text-sm text-slate-600">
                          Немає доступних курсів. Перевірте ID вчителя або дані
                          в бекенді.
                        </div>
                      )}
                      {courseGroups.map((group) => {
                        const gradeNumber = group.title.split(" ")[0];
                        const subjectName =
                          courseSubjectMap[group.courseId] ??
                          subjectFromCourseId(group.courseId);
                        return (
                          <div key={group.key}>
                            <div className="text-sm font-semibold text-slate-700">
                              {gradeNumber} клас
                            </div>
                            <div className="mt-3 space-y-3">
                              {group.classes.map((item) => (
                                <button
                                  key={item.id}
                                  type="button"
                                  onClick={() =>
                                    handleCourseSelect(group.courseId, item.id)
                                  }
                                  className={`flex w-full items-center justify-between rounded-2xl border px-4 py-3 text-left text-sm font-medium transition ${
                                    selectedCourseId === group.courseId &&
                                    selectedClassId === item.id
                                      ? "border-2 border-blue-500 bg-blue-100 text-slate-900"
                                      : "border-slate-200 bg-white text-slate-800 hover:border-slate-300"
                                  } cursor-pointer`}
                                >
                                  <span>{subjectName}</span>
                                  <span className="text-xs text-slate-500">
                                    ID {item.id}
                                  </span>
                                </button>
                              ))}
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </Panel>
                  <Panel
                    className="flex h-full flex-col overflow-hidden"
                    contentClassName="flex flex-col flex-1 min-h-0"
                  >
                    <div
                      className="flex items-center justify-between shrink-0"
                      ref={filterRef}
                    >
                      <h2 className="text-xl font-semibold text-slate-900">
                        Учні класу
                      </h2>
                      <div className="relative">
                        <button
                          type="button"
                          onClick={() => {
                            if (!isFilterOpen) {
                              setPendingLevelFilters({ ...levelFilters });
                            }
                            setIsFilterOpen((open) => !open);
                          }}
                          className="inline-flex items-center gap-2 rounded-2xl border border-slate-200 bg-white px-4 py-2 text-sm font-semibold text-slate-700 shadow-sm transition hover:border-[#1E73F7] hover:text-slate-900 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
                        >
                          {filterButtonLabel}
                          <span className="text-slate-400">▾</span>
                        </button>
                        {isFilterOpen && (
                          <div className="absolute right-0 top-full z-50 mt-2 w-72 rounded-2xl border border-slate-200 bg-white p-3 shadow-xl">
                            <div className="space-y-2">
                              <label className="flex cursor-pointer items-center gap-3 rounded-xl bg-green-100 px-3 py-2 text-sm font-semibold text-green-700 transition hover:brightness-95">
                                <input
                                  type="checkbox"
                                  checked={pendingLevelFilters.strong}
                                  onChange={() => toggleFilter("strong")}
                                  className="h-4 w-4 rounded border-slate-300 accent-blue-600 text-blue-600 focus:ring-blue-500"
                                />
                                Високий рівень
                              </label>
                              <label className="flex cursor-pointer items-center gap-3 rounded-xl bg-yellow-100 px-3 py-2 text-sm font-semibold text-yellow-700 transition hover:brightness-95">
                                <input
                                  type="checkbox"
                                  checked={pendingLevelFilters.medium}
                                  onChange={() => toggleFilter("medium")}
                                  className="h-4 w-4 rounded border-slate-300 accent-blue-600 text-blue-600 focus:ring-blue-500"
                                />
                                Середній рівень
                              </label>
                              <label className="flex cursor-pointer items-center gap-3 rounded-xl bg-pink-100 px-3 py-2 text-sm font-semibold text-pink-700 transition hover:brightness-95">
                                <input
                                  type="checkbox"
                                  checked={pendingLevelFilters.weak}
                                  onChange={() => toggleFilter("weak")}
                                  className="h-4 w-4 rounded border-slate-300 accent-blue-600 text-blue-600 focus:ring-blue-500"
                                />
                                Початковий рівень
                              </label>
                            </div>
                            <div className="mt-4 grid gap-2">
                              <button
                                type="button"
                                onClick={applyFilters}
                                className="w-full rounded-xl bg-[#1E73F7] px-3 py-2 text-xs font-semibold text-white shadow-sm transition hover:bg-[#1A63D6]"
                              >
                                Застосувати фільтр
                              </button>
                            </div>
                          </div>
                        )}
                      </div>
                    </div>
                    <div className="mt-6 space-y-3 flex-1 min-h-0 overflow-y-auto pr-1 scroll-smooth">
                      {!selectedClassId && (
                        <div className="rounded-2xl border border-dashed border-slate-200 bg-slate-50 px-4 py-4 text-sm text-slate-600">
                          Оберіть клас, щоб побачити учнів.
                        </div>
                      )}
                      {selectedClassId && isStudentsLoading && (
                        <div className="rounded-2xl border border-dashed border-slate-200 bg-slate-50 px-4 py-4 text-sm text-slate-600">
                          Завантаження...
                        </div>
                      )}
                      {selectedClassId &&
                        !isStudentsLoading &&
                        filteredStudents.length === 0 && (
                          <div className="rounded-2xl border border-dashed border-slate-200 bg-slate-50 px-4 py-4 text-sm text-slate-600">
                            Немає учнів у цьому класі.
                          </div>
                        )}
                      {selectedClassId &&
                        !isStudentsLoading &&
                        filteredStudents.map((student) => (
                          <button
                            key={student.student_id}
                            type="button"
                            onClick={() => {
                              if (!id || !selectedCourseId) {
                                return;
                              }
                              const encodedCourse =
                                encodeURIComponent(selectedCourseId);
                              const encodedClass = encodeURIComponent(
                                String(selectedClassId),
                              );
                              navigate(
                                `/teacher/${id}/class/${encodedCourse}/${encodedClass}/student/${student.student_id}`,
                              );
                            }}
                            className="flex w-full items-center justify-between rounded-2xl border border-slate-200 bg-white px-4 py-3 text-left text-sm font-medium text-slate-800 transition hover:border-slate-300 hover:bg-slate-50 cursor-pointer"
                          >
                            <div className="flex items-center gap-3">
                              <div className="h-10 w-10 overflow-hidden rounded-full bg-slate-200">
                                <img
                                  src={`https://api.dicebear.com/7.x/avataaars/svg?seed=${student.student_id}`}
                                  alt={`Учень ${student.student_id}`}
                                  className="h-full w-full object-cover"
                                />
                              </div>
                              <span>Учень {student.student_id}</span>
                            </div>
                            <div className="flex items-center gap-3">
                              <span
                                className={`rounded-full px-3 py-1 text-xs font-medium ${
                                  student.subject_level === "strong"
                                    ? "bg-green-100 text-green-700"
                                    : student.subject_level === "medium"
                                      ? "bg-yellow-100 text-yellow-700"
                                      : "bg-pink-100 text-pink-700"
                                }`}
                              >
                                {levelLabels[student.subject_level] ??
                                  student.subject_level}
                              </span>
                              <span className="text-sm text-slate-600 font-semibold">
                                {student.average_subject_grade.toFixed(1)}
                              </span>
                            </div>
                          </button>
                        ))}
                    </div>
                  </Panel>
                </div>
              </>
            )}
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
              if (e.key === "Enter") {
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
