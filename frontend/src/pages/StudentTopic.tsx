import { useEffect, useMemo, useState } from "react";
import { useParams, Link, useNavigate } from "react-router-dom";
import Card from "../components/Card";
import Panel from "../components/Panel";
import PillButton from "../components/PillButton";
import { getMaterials } from "../data/materialsStorage";
import { getStudentTestCompletionMap } from "../data/studentProgress";
import { getStudentData } from "../api/student";
import { toNumericId } from "../api/idUtils";
import { classIdToLabel } from "../data/classUtils";

const subjects = [
  { id: "algebra", label: "Алгебра", icon: <span className="text-xl">√x</span> },
  {
    id: "history",
    label: "Історія України",
    icon: (
      <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
        <path d="M5 16L3 5L8.5 10L12 4L15.5 10L21 5L19 16H5M19 19C19 19.6 18.6 20 18 20H6C5.4 20 5 19.6 5 19V18H19V19Z" />
      </svg>
    ),
  },
  {
    id: "ukr-lang",
    label: "Українська мова",
    icon: (
      <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
        <path d="M20 2H4C2.9 2 2 2.9 2 4V16C2 17.1 2.9 18 4 18H8V21C8 21.6 8.4 22 9 22H15C15.6 22 16 21.6 16 21V18H20C21.1 18 22 17.1 22 16V4C22 2.9 21.1 2 20 2M6 6H8V8H6V6M6 10H8V12H6V10M16 14H12V10H16V14M12 6H18V8H12V6M18 10V12H16V10H18Z" />
      </svg>
    ),
  },
];

const courseLabels: Record<string, string> = {
  "algebra-8": "Алгебра",
  "geometry-8": "Геометрія",
  "history-8": "Історія України",
  "ukr-lang-8": "Українська мова",
  "algebra-9": "Алгебра",
  "geometry-9": "Геометрія",
  "history-9": "Історія України",
  "ukr-lang-9": "Українська мова",
};
const subjectLabelMap: Record<string, string> = {
  algebra: "Алгебра",
  geometry: "Геометрія",
  "ukr-lang": "Українська мова",
  history: "Історія України",
};

const StudentTopic = () => {
  const { studentId, courseId, topicId } = useParams();
  const navigate = useNavigate();
  const [apiSubjects, setApiSubjects] = useState<string[]>([]);
  const [studentGrade, setStudentGrade] = useState<number | null>(null);
  const [studentClassId, setStudentClassId] = useState<number | null>(null);
  const [studentError, setStudentError] = useState<string | null>(null);

  const decodedTopic = topicId ? decodeURIComponent(topicId) : "";
  const decodedCourse = courseId ? decodeURIComponent(courseId) : "";
  const courseLabel = decodedCourse ? courseLabels[decodedCourse] ?? decodedCourse : "";
  const subjectSlug = decodedCourse.split("-").slice(0, -1).join("-") || decodedCourse;
  const subjectName = subjectLabelMap[subjectSlug] ?? courseLabel ?? "";
  const classLabel =
    studentGrade && studentClassId
      ? classIdToLabel(studentGrade, studentClassId)
      : studentGrade
      ? String(studentGrade)
      : "";
  
  const [notes, setNotes] = useState<{ id: string; title: string }[]>([]);
  const [tests, setTests] = useState<
    {
      id: string;
      title: string;
      scoreText: string;
      percent: number;
    }[]
  >([]);

  useEffect(() => {
    const apiId = toNumericId(studentId);
    if (!apiId) {
      setStudentError("Учня не знайдено");
      return;
    }
    getStudentData(apiId)
      .then((response) => {
        setApiSubjects(response.subjects);
        setStudentGrade(response.class_number);
        setStudentClassId(response.class_id);
        setStudentError(null);
      })
      .catch((error) => {
        console.error(error);
        setStudentError("Учня не знайдено");
      });
  }, [studentId]);

  const availableSubjects = apiSubjects.length
    ? subjects.filter((subject) => apiSubjects.includes(subject.label))
    : subjects;

  useEffect(() => {
    if (studentError) return;

    const materials = getMaterials({
        courseId: decodedCourse,
        subject: subjectName,
        classId: studentClassId ?? undefined,
        className: classLabel,
        topicName: decodedTopic,
    });

    const storedNotes = materials
        .filter(m => m.type === "note")
        .map(m => ({ id: m.id, title: m.title }));
        
    const completionMap = getStudentTestCompletionMap(studentId);

    const storedTests = materials
        .filter(m => m.type === "test")
        .map(m => {
          const completion = completionMap.get(m.id);
          const scoreText = completion
            ? `${completion.correctAnswers}/${completion.totalQuestions}`
            : "-";
          const percent =
            completion?.percent ??
            (completion && completion.totalQuestions > 0
              ? Math.round(
                  (completion.correctAnswers / completion.totalQuestions) * 100
                )
              : 0);
          return { id: m.id, title: m.title, scoreText, percent };
        });

    setNotes(storedNotes);
    setTests(storedTests);
  }, [
    studentError,
    classLabel,
    studentClassId,
    decodedCourse,
    decodedTopic,
    studentId,
    subjectName,
  ]);

  if (studentError) {
    return (
        <div className="flex min-h-screen items-center justify-center bg-[#1E73F7]">
          <div className="text-xl text-white">Учня не знайдено</div>
        </div>
      );
  }

  return (
    <div className="min-h-screen bg-[#1E73F7] text-slate-900">
      <div className="flex min-h-screen">
        {/* Sidebar */}
        <aside className="fixed left-0 top-0 h-screen w-72 bg-white px-6 py-8 flex flex-col z-10">
          <div className="flex items-center gap-3">
            <div
                className="h-10 w-10 overflow-hidden rounded-full bg-slate-200"
                style={{
                  backgroundImage: "url('https://images.unsplash.com/photo-1599566150163-29194dcaad36?ixlib=rb-4.0.3&auto=format&fit=crop&w=200&q=80')",
                  backgroundSize: "cover",
                }}
              />
            <div>
              <div className="text-base font-semibold text-slate-900">
                {studentId ? `Учень ${studentId}` : "Учень"}
              </div>
              <div className="text-xs text-slate-500">
                Клас: {classLabel || "—"}
              </div>
            </div>
          </div>

          <div className="mt-8 space-y-2">
            {availableSubjects.map((subject) => {
              const isActive = subjectSlug === subject.id;
              return (
                <button
                  key={subject.id}
                  type="button"
                  onClick={() => navigate(`/student/${studentId}`)}
                  className={`flex w-full items-center gap-4 rounded-xl px-4 py-3 text-sm font-semibold transition-all ${
                    isActive
                      ? "bg-[#E9F1FF] text-[#1E73F7]"
                      : "text-slate-900 hover:bg-slate-50"
                  }`}
                >
                  <div
                    className={`flex items-center justify-center ${
                      isActive ? "text-[#1E73F7]" : "text-slate-900"
                    }`}
                  >
                    {subject.icon}
                  </div>
                  {subject.label}
                </button>
              );
            })}
          </div>

          <div className="mt-6 border-t border-slate-200 pt-6 space-y-4 text-sm">
            {notes.map((item) => (
              <Link
                key={item.id}
                to={`/student/${studentId}/note/${courseId}/${topicId}/${item.id}`}
                className="flex items-center gap-3 rounded-xl px-4 py-3 font-semibold text-slate-800 hover:bg-slate-50"
              >
                <span className="inline-flex h-6 w-6 items-center justify-center rounded-full bg-[#1E73F7]/15 text-[#1E73F7]">
                  <svg width="14" height="16" viewBox="0 0 16 20" fill="currentColor">
                    <path d="M10 0H2C0.9 0 0 0.9 0 2V18C0 19.1 0.9 20 2 20H14C15.1 20 16 19.1 16 18V6L10 0ZM14 18H2V2H9V7H14V18Z" opacity="0.5"/>
                    <path d="M10 0H2C0.9 0 0 0.9 0 2V18C0 19.1 0.9 20 2 20H14C15.1 20 16 19.1 16 18V6L10 0ZM9 7V2L14 7H9Z"/>
                  </svg>
                </span>
                {item.title}
              </Link>
            ))}
            {tests.map((item) => (
              <Link
                key={item.id}
                to={`/student/${studentId}/test/${item.id}`}
                className="flex items-center gap-3 rounded-xl px-4 py-3 text-slate-700 hover:bg-slate-50"
              >
                <img src="/src/assets/Group.svg" alt="" className="h-4 w-4" />
                Тест. {item.title}
              </Link>
            ))}
          </div>
        </aside>

        <main className="ml-72 flex-1 px-10 py-10 w-full">

          <Panel className="mt-6">
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-2xl font-bold text-slate-900">{decodedTopic}</h1>
                    <div className="mt-1 text-sm text-slate-500">{courseLabel}</div>
                </div>
            </div>
          </Panel>

          <div className="mt-8 grid gap-8 lg:grid-cols-[1.05fr_0.95fr]">
            <section>
              <h2 className="text-xl font-semibold text-white">Конспекти</h2>
              <div className="mt-4 space-y-4">
                {notes.length > 0 ? notes.map((item) => (
                  <Card
                    key={item.id}
                    className="flex items-center justify-between px-5 py-4"
                  >
                    <div className="flex items-center gap-3 text-sm font-semibold text-slate-900">
                      <span className="inline-block h-6 w-6 rounded-md bg-slate-200" />
                      {item.title}
                    </div>
                    <Link to={`/student/${studentId}/note/${courseId}/${topicId}/${item.id}`}>
                      <PillButton label="Переглянути" />
                    </Link>
                  </Card>
                )) : (
                     <div className="rounded-2xl border border-white/10 px-6 py-8 text-center text-sm text-white/40">
                        Немає конспектів
                    </div>
                )}
              </div>
            </section>

            <section>
              <h2 className="text-xl font-semibold text-white">Тести</h2>
              <div className="mt-4 space-y-4">
                {tests.length > 0 ? tests.map((item) => {
                  const filledSegments = Math.round(item.percent / 10);
                  return (
                    <Card key={item.id} className="px-5 py-5">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3 text-sm font-semibold text-slate-900">
                          <img
                            src="/src/assets/Group.svg"
                            alt=""
                            className="h-6 w-6"
                          />
                          {item.title}
                        </div>
                        <Link to={`/student/${studentId}/test/${item.id}`}>
                          <PillButton label="Пройти" />
                        </Link>
                      </div>
                      <div className="mt-4 flex items-center justify-between">
                        <div className="flex items-center gap-1.5">
                          {Array.from({ length: 10 }).map((_, index) => (
                            <span
                              key={index}
                              className={`h-4 w-2.5 rounded-full ${
                                index < filledSegments
                                  ? "bg-[#68E2B0]"
                                  : "bg-[#E6EEF9]"
                              }`}
                            />
                          ))}
                        </div>
                        <div className="text-sm text-slate-600">
                          Остання спроба: {item.scoreText}
                        </div>
                      </div>
                    </Card>
                  );
                }) : (
                     <div className="rounded-2xl border border-white/10 px-6 py-8 text-center text-sm text-white/40">
                        Немає тестів
                    </div>
                )}
              </div>
            </section>
          </div>
        </main>
      </div>
    </div>
  );
};

export default StudentTopic;
