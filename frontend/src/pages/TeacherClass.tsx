import { useEffect, useMemo, useRef, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import BackButton from "../components/BackButton";
import Breadcrumbs from "../components/Breadcrumbs";
import Panel from "../components/Panel";
import TeacherSidebar from "../components/TeacherSidebar";
import { getTeacherStudents } from "../api/teacher";
import type { TeacherStudentItem } from "../api/teacher";
import { classIdToLabel } from "../data/classUtils";
import { toNumericId } from "../api/idUtils";

const subjectLabelMap: Record<string, string> = {
  algebra: "Алгебра",
  geometry: "Геометрія",
  "ukr-lang": "Українська мова",
  history: "Історія України",
};

const levelLabels: Record<string, string> = {
  weak: "Початковий",
  medium: "Середній",
  strong: "Високий",
};

const TeacherClass = () => {
  const { id, courseId, classId } = useParams();
  const navigate = useNavigate();
  const apiTeacherId = toNumericId(id) ?? 0;
  const decodedCourseId = courseId ? decodeURIComponent(courseId) : "";
  const decodedClassId = classId ? Number(decodeURIComponent(classId)) : null;

  const [students, setStudents] = useState<TeacherStudentItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const createDefaultFilters = () => ({
    strong: true,
    medium: true,
    weak: true,
  });
  const [levelFilters, setLevelFilters] = useState(createDefaultFilters);
  const [pendingLevelFilters, setPendingLevelFilters] = useState(createDefaultFilters);
  const [isFilterOpen, setIsFilterOpen] = useState(false);
  const filterRef = useRef<HTMLDivElement | null>(null);

  const subjectSlug = decodedCourseId.split("-").slice(0, -1).join("-");
  const gradeMatch = decodedCourseId.match(/-(\d+)$/);
  const grade = gradeMatch ? Number(gradeMatch[1]) : null;
  const subjectName = subjectLabelMap[subjectSlug] ?? subjectSlug;
  const classLabel =
    grade && decodedClassId ? classIdToLabel(grade, decodedClassId) : "";

  useEffect(() => {
    if (!apiTeacherId || !decodedClassId || !subjectName) {
      setIsLoading(false);
      return;
    }
    setIsLoading(true);
    getTeacherStudents({
      class_id: decodedClassId,
      teacher_id: apiTeacherId,
      subject: subjectName,
    })
      .then((response) => {
        setStudents(response.students);
      })
      .catch((error) => {
        console.error(error);
        setStudents([]);
      })
      .finally(() => {
        setIsLoading(false);
      });
  }, [apiTeacherId, decodedClassId, subjectName]);

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

  const backToStudentsHref = id ? `/teacher/${id}?view=students` : "/";
  const backToMaterialsHref = id ? `/teacher/${id}` : "/";

  return (
    <div className="min-h-screen bg-[#1E73F7] text-slate-900">
      <div className="flex min-h-screen">
        <TeacherSidebar
          teacherName={id ? `Вчитель ${id}` : "Вчитель"}
          activeItem="students"
          onMaterialsClick={() => navigate(backToMaterialsHref)}
          onStudentsClick={() => navigate(backToStudentsHref)}
        />
        <main className="flex-1 px-8 py-10 overflow-y-auto">
          <div className="flex items-center gap-4 mb-6">
            <BackButton fallbackPath={backToStudentsHref} />
            <Breadcrumbs
              items={[
                { label: "Учні", href: backToStudentsHref },
                { label: subjectName || "Предмет", href: backToStudentsHref },
                { label: classLabel || "Клас" },
              ]}
            />
          </div>

          <h1 className="text-2xl font-bold text-white mb-6">
            {classLabel} — {subjectName}
          </h1>

          <div className="flex flex-col gap-6 flex-1">
            <Panel title="Учні класу" className="flex flex-col">
              <div className="flex items-center justify-end mb-4" ref={filterRef}>
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
              <div className="space-y-3 flex-1 overflow-y-auto max-h-[calc(100vh-16rem)]">
                {isLoading && (
                  <div className="rounded-2xl border border-dashed border-slate-200 bg-slate-50 px-4 py-4 text-sm text-slate-600">
                    Завантаження...
                  </div>
                )}
                {!isLoading && filteredStudents.length === 0 && (
                  <div className="rounded-2xl border border-dashed border-slate-200 bg-slate-50 px-4 py-4 text-sm text-slate-600">
                    Немає учнів у цьому класі.
                  </div>
                )}
                {!isLoading &&
                  filteredStudents.map((student) => (
                    <button
                      key={student.student_id}
                      type="button"
                      onClick={() =>
                        navigate(
                          `/teacher/${id}/class/${courseId}/${classId}/student/${student.student_id}`
                        )
                      }
                      className="flex w-full items-center justify-between rounded-2xl border border-slate-200 bg-white px-4 py-3 text-left text-sm font-medium text-slate-800 transition hover:border-slate-300 hover:bg-slate-50 cursor-pointer"
                    >
                      <div className="flex items-center gap-3">
                        <div className="flex h-10 w-10 items-center justify-center rounded-full bg-[#E9F1FF] text-sm font-semibold text-[#1E73F7]">
                          {student.student_id}
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
        </main>
      </div>
    </div>
  );
};

export default TeacherClass;
