import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import BackButton from "../components/BackButton";
import Breadcrumbs from "../components/Breadcrumbs";
import Panel from "../components/Panel";
import TeacherSidebar from "../components/TeacherSidebar";
import MarkdownContent from "../components/MarkdownContent";
import { getStudentDetails, getStudentRecommendation } from "../api/teacher";
import type { StudentDetailsResponse } from "../api/teacher";
import { classIdToLabel } from "../data/classUtils";
import { toNumericId } from "../api/idUtils";

const subjectLabelMap: Record<string, string> = {
  algebra: "Алгебра",
  geometry: "Геометрія",
  "ukr-lang": "Українська мова",
  history: "Історія України",
};

const levelLabels: Record<string, string> = {
  weak: "Початковий рівень",
  medium: "Середній рівень",
  strong: "Високий рівень",
};

const levelColors: Record<string, string> = {
  strong: "bg-green-100 text-green-700",
  medium: "bg-yellow-100 text-yellow-700",
  weak: "bg-pink-100 text-pink-700",
};

const TeacherStudentDetail = () => {
  const { id, courseId, classId, studentId } = useParams();
  const navigate = useNavigate();
  const apiTeacherId = toNumericId(id);
  const apiStudentId = toNumericId(studentId);
  const decodedCourseId = courseId ? decodeURIComponent(courseId) : "";
  const decodedClassId = classId ? Number(decodeURIComponent(classId)) : null;

  const [studentDetails, setStudentDetails] =
    useState<StudentDetailsResponse | null>(null);
  const [recommendation, setRecommendation] = useState("");
  const [recommendationError, setRecommendationError] = useState<string | null>(null);
  const [isRecommendationLoading, setIsRecommendationLoading] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [fetchError, setFetchError] = useState<string | null>(null);

  const subjectSlug = decodedCourseId.split("-").slice(0, -1).join("-");
  const gradeMatch = decodedCourseId.match(/-(\d+)$/);
  const grade = gradeMatch ? Number(gradeMatch[1]) : null;
  const subjectName = subjectLabelMap[subjectSlug] ?? subjectSlug;
  const classLabel =
    grade && decodedClassId ? classIdToLabel(grade, decodedClassId) : "";

  useEffect(() => {
    if (
      apiTeacherId === null ||
      decodedClassId === null ||
      !subjectName ||
      apiStudentId === null
    ) {
      setIsLoading(false);
      setFetchError("Невірні параметри запиту");
      return;
    }
    setIsLoading(true);
    setFetchError(null);

    setIsRecommendationLoading(true);
    setRecommendationError(null);
    setRecommendation("");

    getStudentDetails({
      class_id: decodedClassId,
      subject: subjectName,
      teacher_id: apiTeacherId,
      student_id: apiStudentId,
    })
      .then((details) => {
        setStudentDetails(details);
        setFetchError(null);
      })
      .catch((error) => {
        console.error(error);
        setStudentDetails(null);
        if (error instanceof Error && error.message.includes("404")) {
          setFetchError("Учня не знайдено");
        } else {
          setFetchError("Помилка завантаження даних");
        }
      })
      .finally(() => {
        setIsLoading(false);
      });

    getStudentRecommendation({ student_id: apiStudentId, subject: subjectName })
      .then((rec) => {
        setRecommendation(rec.feedback ?? "");
        setRecommendationError(null);
      })
      .catch((error) => {
        console.error(error);
        setRecommendation("");
        setRecommendationError("Рекомендації недоступні.");
      })
      .finally(() => {
        setIsRecommendationLoading(false);
      });
  }, [apiTeacherId, decodedClassId, subjectName, apiStudentId]);

  const backToStudentsHref = id ? `/teacher/${id}?view=students` : "/";
  const backToMaterialsHref = id ? `/teacher/${id}` : "/";
  const backToClassHref =
    id && courseId && classId
      ? `/teacher/${id}/class/${courseId}/${classId}`
      : backToStudentsHref;

  if (isLoading) {
    return (
      <div className="min-h-screen bg-[#1E73F7] text-slate-900">
        <div className="flex min-h-screen">
          <TeacherSidebar
            teacherName={id ? `Вчитель ${id}` : "Вчитель"}
            activeItem="students"
            onMaterialsClick={() => navigate(backToMaterialsHref)}
            onStudentsClick={() => navigate(backToStudentsHref)}
          />
          <main className="flex-1 px-8 py-10 flex items-center justify-center">
            <div className="text-xl text-white">Завантаження...</div>
          </main>
        </div>
      </div>
    );
  }

  if (fetchError || !studentDetails) {
    return (
      <div className="min-h-screen bg-[#1E73F7] text-slate-900">
        <div className="flex min-h-screen">
          <TeacherSidebar
            teacherName={id ? `Вчитель ${id}` : "Вчитель"}
            activeItem="students"
            onMaterialsClick={() => navigate(backToMaterialsHref)}
            onStudentsClick={() => navigate(backToStudentsHref)}
          />
          <main className="flex-1 px-8 py-10 flex items-center justify-center">
            <div className="text-xl text-white">
              {fetchError ?? "Учня не знайдено"}
            </div>
          </main>
        </div>
      </div>
    );
  }

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
            <BackButton fallbackPath={backToClassHref} />
            <Breadcrumbs
              items={[
                { label: "Учні", href: backToStudentsHref },
                { label: subjectName || "Предмет", href: backToStudentsHref },
                { label: classLabel || "Клас", href: backToClassHref },
                { label: `Учень ${apiStudentId ?? studentId}` },
              ]}
            />
          </div>

          <div className="flex items-center gap-4 mb-6">
            <div className="flex h-14 w-14 items-center justify-center rounded-full bg-white text-lg font-semibold text-[#1E73F7]">
              {apiStudentId ?? studentId}
            </div>
            <div>
              <h1 className="text-2xl font-bold text-white">
                Учень {apiStudentId ?? studentId}
              </h1>
              <p className="text-white/70 text-sm">
                {subjectName} — {classLabel}
              </p>
            </div>
            <div className="ml-auto" />
          </div>

          <div className="grid gap-6 lg:grid-cols-2 items-stretch">
            <div className="flex flex-col gap-6 lg:h-[760px] min-h-0">
              <div
                className={`rounded-[22px] px-6 py-5 text-slate-900 shadow-sm ${
                  studentDetails.level === "strong"
                    ? "bg-green-100"
                    : studentDetails.level === "medium"
                      ? "bg-yellow-100"
                      : "bg-pink-100"
                }`}
              >
                <div className="text-sm font-semibold text-slate-700">
                  {levelLabels[studentDetails.level] ?? studentDetails.level}
                </div>
                <div className="mt-2 text-2xl font-bold">
                  {studentDetails.average_subject_grade.toFixed(1)} бал з предмету
                </div>
              </div>

              <Panel
                title="Рекомендації"
                className="flex-1 min-h-0 overflow-hidden"
                contentClassName="flex flex-col flex-1 min-h-0"
              >
                <div className="flex-1 min-h-0 overflow-y-auto pr-1">
                  {isRecommendationLoading ? (
                    <p className="text-sm text-slate-500">Завантаження рекомендацій...</p>
                  ) : recommendation ? (
                    <MarkdownContent content={recommendation} className="text-sm text-slate-600" />
                  ) : (
                    <p className="text-sm text-slate-600 leading-relaxed">
                      Рекомендації для цього учня ще не сформовані.
                    </p>
                  )}
                  {recommendationError && (
                    <p className="mt-3 text-xs text-rose-500">
                      {recommendationError}
                    </p>
                  )}
                </div>
              </Panel>
            </div>

            <div className="flex flex-col gap-6 lg:h-[760px] min-h-0">
              <Panel
                title="Проблемні теми"
                className="h-[360px] flex flex-col min-h-0 overflow-hidden"
                contentClassName="flex flex-col flex-1 min-h-0"
              >
                <div className="flex-1 min-h-0 overflow-y-auto pr-1">
                  {studentDetails.problematic_topics.length === 0 ? (
                    <div className="rounded-2xl border border-dashed border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-600">
                      Немає проблемних тем.
                    </div>
                  ) : (
                    <div className="space-y-2">
                      {studentDetails.problematic_topics.map((topic, index) => (
                        <div
                          key={index}
                          className="grid grid-cols-[1fr_auto] items-center gap-3 rounded-2xl border border-slate-200 bg-white px-4 py-3"
                        >
                          <span className="text-sm font-medium text-slate-800">
                            {topic.topic}
                          </span>
                          <span className="text-xs font-semibold text-slate-600 whitespace-nowrap">
                            {topic.average_score.toFixed(1)} балів
                          </span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </Panel>

              <Panel
                title="Пропущені теми"
                className="h-[360px] flex flex-col min-h-0 overflow-hidden"
                contentClassName="flex flex-col flex-1 min-h-0"
              >
                <div className="flex-1 min-h-0 overflow-y-auto pr-1">
                  {studentDetails.skipped_lessons.length === 0 ? (
                    <div className="rounded-2xl border border-dashed border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-600">
                      Немає пропущених тем.
                    </div>
                  ) : (
                    <div className="space-y-2">
                      {studentDetails.skipped_lessons.map((lesson, index) => (
                        <div
                          key={index}
                          className="grid grid-cols-[1fr_auto] items-center gap-3 rounded-2xl border border-slate-200 bg-white px-4 py-3"
                        >
                          <span className="text-sm font-medium text-slate-800">
                            {lesson.topic}
                          </span>
                          <span className="text-xs text-slate-500 text-right whitespace-nowrap">
                            {lesson.date}
                          </span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </Panel>
            </div>
          </div>
        </main>
      </div>
    </div>
  );
};

export default TeacherStudentDetail;
