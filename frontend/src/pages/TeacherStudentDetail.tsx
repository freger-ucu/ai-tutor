import { useEffect, useRef, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import BackButton from "../components/BackButton";
import Breadcrumbs from "../components/Breadcrumbs";
import TeacherSidebar from "../components/TeacherSidebar";
import MarkdownContent from "../components/MarkdownContent";
import { getStudentDetails, getStudentRecommendation } from "../api/teacher";
import type { StudentDetailsResponse } from "../api/teacher";
import { classIdToLabel } from "../data/classUtils";
import { toNumericId } from "../api/idUtils";
import highStar from "../assets/high.png";
import midStar from "../assets/mid.png";
import lowStar from "../assets/low.png";

const subjectLabelMap: Record<string, string> = {
  algebra: "Алгебра",
  geometry: "Геометрія",
  "ukr-lang": "Українська мова",
  history: "Історія України",
};
const levelStars: Record<StudentDetailsResponse["level"], string> = {
  strong: highStar,
  medium: midStar,
  weak: lowStar,
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
  const recommendationRequestIdRef = useRef(0);
  const recommendationKeyRef = useRef<string | null>(null);

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

    const recommendationKey = `${apiStudentId}-${subjectName}`;
    const isNewRecommendation = recommendationKeyRef.current !== recommendationKey;
    recommendationKeyRef.current = recommendationKey;
    setIsRecommendationLoading(true);
    setRecommendationError(null);
    if (isNewRecommendation) {
      setRecommendation("");
    }
    recommendationRequestIdRef.current += 1;
    const currentRequestId = recommendationRequestIdRef.current;

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
        if (currentRequestId !== recommendationRequestIdRef.current) {
          return;
        }
        if (rec.feedback) {
          setRecommendation(rec.feedback);
          setRecommendationError(null);
        }
      })
      .catch((error) => {
        console.error(error);
        if (currentRequestId !== recommendationRequestIdRef.current) {
          return;
        }
        setRecommendationError("Рекомендації недоступні.");
      })
      .finally(() => {
        if (currentRequestId === recommendationRequestIdRef.current) {
          setIsRecommendationLoading(false);
        }
      });
  }, [apiTeacherId, decodedClassId, subjectName, apiStudentId]);

  const backToStudentsHref = id ? `/teacher/${id}?view=students` : "/";
  const backToMaterialsHref = id ? `/teacher/${id}` : "/";
  const backToClassHref =
    id && courseId && classId
      ? `/teacher/${id}/class/${courseId}/${classId}`
      : backToStudentsHref;
  const formatDate = (value: string) => {
    const [year, month, day] = value.split("-");
    if (!year || !month || !day) {
      return value;
    }
    return `${day}.${month}.${year}`;
  };

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
        <main className="flex-1 px-8 py-10 overflow-hidden">
          <div className="flex h-[calc(100vh-5rem)] flex-col">
            <div className="flex items-center gap-4 mb-6 shrink-0">
              <BackButton fallbackPath={backToClassHref} />
              <Breadcrumbs
                items={[
                  { label: subjectName || "Предмет", href: backToStudentsHref },
                  { label: classLabel || "Клас", href: backToClassHref },
                  { label: `Учень ${apiStudentId ?? studentId}` },
                ]}
              />
            </div>

            <div className="flex items-center gap-4 mb-8 shrink-0">
              <div className="flex h-16 w-16 items-center justify-center rounded-full bg-white text-lg font-semibold text-[#1E73F7]">
                {apiStudentId ?? studentId}
              </div>
              <div className="text-left">
                <h1 className="text-3xl font-bold text-white">
                  Учень {apiStudentId ?? studentId}
                </h1>
                <p className="text-white/70 text-sm">
                  {subjectName} — {classLabel}
                </p>
              </div>
              <div className="relative ml-4 h-20 w-20">
                <img
                  src={levelStars[studentDetails.level]}
                  alt="GPA level badge"
                  className="h-full w-full object-contain"
                />
                <span className="absolute inset-0 flex items-center justify-center text-lg font-bold text-black">
                  {studentDetails.average_subject_grade.toFixed(1)}
                </span>
              </div>
            </div>

            <div className="grid flex-1 min-h-0 gap-6 lg:grid-cols-2">
              <div className="flex h-full flex-col overflow-hidden rounded-[22px] bg-white p-6 text-slate-900 shadow-sm">
                <h2 className="text-xl font-semibold text-slate-900">Рекомендації</h2>
                <div className="mt-4 flex-1 min-h-0 overflow-y-auto pr-1 scroll-smooth">
                  {isRecommendationLoading ? (
                    <p className="text-sm text-slate-500">
                      Завантаження рекомендацій...
                    </p>
                  ) : recommendation ? (
                    <MarkdownContent content={recommendation} className="text-sm text-slate-700" />
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
              </div>

              <div className="flex h-full flex-col overflow-hidden rounded-[22px] bg-white p-6 text-slate-900 shadow-sm">
                <h2 className="text-xl font-semibold text-slate-900">Проблемні теми</h2>
                <div className="mt-4 flex-1 min-h-0 overflow-y-auto pr-1 scroll-smooth">
                  <div className="space-y-6">
                    <div>
                      <div className="mb-3 flex items-center gap-2 text-sm font-semibold text-slate-700">
                        <span className="h-2 w-2 rounded-full bg-rose-500" />
                        Низькі оцінки
                      </div>
                      {studentDetails.problematic_topics.length === 0 ? (
                        <div className="rounded-2xl border border-dashed border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-600">
                          Немає проблемних тем.
                        </div>
                      ) : (
                        <div className="space-y-2">
                          {studentDetails.problematic_topics.map((topic, index) => (
                            <div
                              key={index}
                              className="flex items-center justify-between rounded-2xl border border-rose-100 bg-rose-50 px-4 py-3 text-sm"
                            >
                              <span className="font-medium text-slate-800">
                                {topic.topic}
                              </span>
                              <span className="text-sm font-semibold text-rose-600">
                                {topic.average_score.toFixed(1)}/12
                              </span>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                    <div className="border-t border-slate-200 pt-4">
                      <div className="mb-3 flex items-center gap-2 text-sm font-semibold text-slate-700">
                        <span className="h-2 w-2 rounded-full bg-slate-400" />
                        Пропущені теми
                      </div>
                      {studentDetails.skipped_lessons.length === 0 ? (
                        <div className="rounded-2xl border border-dashed border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-600">
                          Немає пропущених тем.
                        </div>
                      ) : (
                        <div className="space-y-2">
                          {studentDetails.skipped_lessons.map((lesson, index) => (
                            <div
                              key={index}
                              className="flex items-center justify-between rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm"
                            >
                              <span className="font-medium text-slate-800">
                                {lesson.topic}
                              </span>
                              <span className="text-sm font-semibold text-slate-500">
                                {formatDate(lesson.date)}
                              </span>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </main>
      </div>
    </div>
  );
};

export default TeacherStudentDetail;
