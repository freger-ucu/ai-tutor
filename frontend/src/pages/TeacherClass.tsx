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
  const [levelFilters, setLevelFilters] = useState({
    strong: true,
    medium: true,
    weak: true,
  });
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
      return "All levels (3)";
    }
    if (active.length === 2) {
      return "2 levels selected";
    }
    if (active.length === 1) {
      const single = active[0];
      return single === "strong"
        ? "High level (1)"
        : single === "medium"
        ? "Medium level (1)"
        : "Low level (1)";
    }
    return "No levels selected";
  }, [levelFilters]);

  const toggleFilter = (level: "strong" | "medium" | "weak") => {
    setLevelFilters((prev) => ({ ...prev, [level]: !prev[level] }));
    setIsFilterOpen(false);
  };

  const clearFilters = () => {
    setLevelFilters({ strong: true, medium: true, weak: true });
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
                    onClick={() => setIsFilterOpen((open) => !open)}
                    className="inline-flex items-center gap-2 rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 shadow-sm transition hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
                  >
                    {filterButtonLabel}
                    <span className="text-slate-400">▾</span>
                  </button>
                  {isFilterOpen && (
                    <div className="absolute top-full left-0 z-50 mt-1 max-h-60 w-full overflow-auto rounded-lg border border-gray-200 bg-white py-1 shadow-xl">
                      <label className="group flex cursor-pointer items-center rounded-lg p-3 transition-all duration-200 hover:bg-gray-50">
                        <input
                          type="checkbox"
                          checked={levelFilters.strong}
                          onChange={() => toggleFilter("strong")}
                          className="mr-3 h-4 w-4 rounded border-gray-300 accent-blue-600 text-blue-600 focus:ring-blue-500"
                        />
                        <span className="text-sm font-medium text-gray-900 group-hover:text-gray-900">
                          Високий рівень
                        </span>
                      </label>
                      <label className="group flex cursor-pointer items-center rounded-lg p-3 transition-all duration-200 hover:bg-gray-50">
                        <input
                          type="checkbox"
                          checked={levelFilters.medium}
                          onChange={() => toggleFilter("medium")}
                          className="mr-3 h-4 w-4 rounded border-gray-300 accent-blue-600 text-blue-600 focus:ring-blue-500"
                        />
                        <span className="text-sm font-medium text-gray-900 group-hover:text-gray-900">
                          Середній рівень
                        </span>
                      </label>
                      <label className="group flex cursor-pointer items-center rounded-lg p-3 transition-all duration-200 hover:bg-gray-50">
                        <input
                          type="checkbox"
                          checked={levelFilters.weak}
                          onChange={() => toggleFilter("weak")}
                          className="mr-3 h-4 w-4 rounded border-gray-300 accent-blue-600 text-blue-600 focus:ring-blue-500"
                        />
                        <span className="text-sm font-medium text-gray-900 group-hover:text-gray-900">
                          Низький рівень
                        </span>
                      </label>
                      <button
                        type="button"
                        onClick={clearFilters}
                        className="mx-3 mb-2 mt-2 w-[calc(100%-1.5rem)] rounded-md border border-gray-300 bg-white px-3 py-2 text-xs font-semibold text-gray-600 transition hover:bg-gray-50"
                      >
                        Clear filters
                      </button>
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
                              : "bg-red-100 text-red-700"
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
