import { useEffect, useState, useMemo } from "react";
import { useParams, useNavigate } from "react-router-dom";
import BackButton from "../components/BackButton";
import Breadcrumbs from "../components/Breadcrumbs";
import Panel from "../components/Panel";
import TeacherSidebar from "../components/TeacherSidebar";
import { getTeacherStudents } from "../api/teacher";
import type { TeacherStudentItem } from "../api/teacher";
import { classIdToLabel } from "../data/classUtils";
import { toNumericId } from "../api/idUtils";
import { getRecommendation } from "../data/recommendationsStorage";

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

const levelColors: Record<string, { bg: string; dot: string }> = {
  strong: { bg: "bg-green-100", dot: "bg-green-500" },
  medium: { bg: "bg-yellow-100", dot: "bg-yellow-500" },
  weak: { bg: "bg-pink-100", dot: "bg-pink-500" },
};

const TeacherClass = () => {
  const { id, courseId, classId } = useParams();
  const navigate = useNavigate();
  const apiTeacherId = toNumericId(id) ?? 0;
  const decodedCourseId = courseId ? decodeURIComponent(courseId) : "";
  const decodedClassId = classId ? Number(decodeURIComponent(classId)) : null;

  const [students, setStudents] = useState<TeacherStudentItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);

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

  const statistics = useMemo(() => {
    const counts = { strong: 0, medium: 0, weak: 0 };
    students.forEach((student) => {
      if (student.subject_level in counts) {
        counts[student.subject_level as keyof typeof counts]++;
      }
    });
    return counts;
  }, [students]);

  const [recommendationText, setRecommendationText] = useState("");

  useEffect(() => {
    if (!id || !decodedClassId || !decodedCourseId || !subjectName) {
      return;
    }
    const stored = getRecommendation({
      teacherId: id,
      classId: decodedClassId,
      courseId: decodedCourseId,
      subject: subjectName,
    });
    if (stored) {
      setRecommendationText(stored.text);
    }
  }, [id, decodedClassId, decodedCourseId, subjectName]);

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

          <div className="grid gap-6 lg:grid-cols-2 flex-1">
            <Panel title="Учні класу" className="flex flex-col">
              <div className="space-y-3 flex-1 overflow-y-auto max-h-[calc(100vh-16rem)]">
                {isLoading && (
                  <div className="rounded-2xl border border-dashed border-slate-200 bg-slate-50 px-4 py-4 text-sm text-slate-600">
                    Завантаження...
                  </div>
                )}
                {!isLoading && students.length === 0 && (
                  <div className="rounded-2xl border border-dashed border-slate-200 bg-slate-50 px-4 py-4 text-sm text-slate-600">
                    Немає учнів у цьому класі.
                  </div>
                )}
                {!isLoading &&
                  students.map((student) => (
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
            <Panel title="Статистика" className="flex flex-col">
              <div className="space-y-4 flex-1">
                {(["strong", "medium", "weak"] as const).map((level) => (
                  <div
                    key={level}
                    className={`flex items-center justify-between rounded-2xl px-4 py-3 ${levelColors[level].bg}`}
                  >
                    <div className="flex items-center gap-3">
                      <span className={`h-3 w-3 rounded-full ${levelColors[level].dot}`} />
                      <span className="text-sm font-medium text-slate-800">
                        {levelLabels[level]} рівень
                      </span>
                    </div>
                    <span className="text-sm font-semibold text-slate-700">
                      {statistics[level]} учнів
                    </span>
                  </div>
                ))}
                <div className="mt-6 rounded-2xl bg-[#E9F1FF] p-4">
                  <h3 className="text-sm font-semibold text-slate-900 mb-2">Рекомендації</h3>
                  <p className="text-sm text-slate-600">
                    {recommendationText ||
                      "Рекомендації для цього класу ще не сформовані."}
                  </p>
                </div>
              </div>
            </Panel>
          </div>
        </main>
      </div>
    </div>
  );
};

export default TeacherClass;
