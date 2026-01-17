import { useEffect, useMemo, useState } from "react";
import { useParams } from "react-router-dom";
import BackButton from "../components/BackButton";
import Breadcrumbs from "../components/Breadcrumbs";
import LectureContent from "../components/LectureContent";
import StudentSidebar from "../components/StudentSidebar";
import { getMaterials } from "../data/materialsStorage";
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
const subjectLabelMap: Record<string, string> = {
  algebra: "Алгебра",
  history: "Історія України",
  "ukr-lang": "Українська мова",
};


const StudentNote = () => {
  const { studentId, courseId, topicId, noteId } = useParams();
  const [apiSubjects, setApiSubjects] = useState<string[]>([]);
  const [studentGrade, setStudentGrade] = useState<number | null>(null);
  const [studentClassId, setStudentClassId] = useState<number | null>(null);
  const [studentError, setStudentError] = useState<string | null>(null);

  const decodedCourse = courseId ? decodeURIComponent(courseId) : "";
  const decodedTopic = topicId ? decodeURIComponent(topicId) : "";
  const subjectSlug = decodedCourse.split("-").slice(0, -1).join("-") || decodedCourse;
  const subjectName = subjectLabelMap[subjectSlug] ?? decodedCourse;
  const encodedTopic = decodedTopic ? encodeURIComponent(decodedTopic) : "";
  const backToSubjectHref = `/student/${studentId}?subject=${subjectSlug}`;
  const backToTopicHref =
    courseId && encodedTopic
      ? `/student/${studentId}/topic/${courseId}/${encodedTopic}`
      : backToSubjectHref;
  const classLabel =
    studentGrade && studentClassId
      ? classIdToLabel(studentGrade, studentClassId)
      : studentGrade
      ? String(studentGrade)
      : "";

  const noteMaterial = useMemo(
    () => getMaterials({ type: "note" }).find((item) => item.id === noteId),
    [noteId]
  );
  const noteTitle = noteMaterial?.title ?? "Конспект";
  const availableSubjects = useMemo(() => {
    if (!apiSubjects.length) {
      return subjects;
    }
    const matches = subjects.filter(
      (subject) =>
        apiSubjects.includes(subject.label) || apiSubjects.includes(subject.id)
    );
    return matches.length ? matches : subjects;
  }, [apiSubjects]);

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

  if (studentError) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-[#1E73F7]">
        <div className="text-xl text-white">Учня не знайдено</div>
      </div>
    );
  }

  return (
    <div className="h-screen bg-[#1E73F7] text-slate-900 overflow-hidden flex">
        {/* Static sidebar - always shows only subjects list */}
        <StudentSidebar
          studentId={studentId || ""}
          classLabel={classLabel || undefined}
          subjects={availableSubjects}
          activeSubjectId={subjectSlug}
        />

        <main className="flex-1 px-8 py-10 flex flex-col h-full overflow-hidden">
          <div className="flex items-center gap-4 mb-4 shrink-0">
            <BackButton fallbackPath={backToTopicHref} />
            <Breadcrumbs
              items={[
                { label: subjectName, href: backToSubjectHref },
                { label: decodedTopic || "Тема", href: backToTopicHref },
                { label: noteTitle },
              ]}
            />
          </div>
          <h1 className="text-2xl font-bold text-white shrink-0">
            Конспект. {noteTitle}
          </h1>

          <div className="mt-5 flex-1 min-h-0 rounded-[28px] bg-white p-6 shadow-sm overflow-y-auto note-scrollbar">
            <div className="rounded-[20px] bg-white">
              <h2 className="text-lg font-semibold text-slate-900">
                {decodedTopic || noteTitle}
              </h2>
              <div className="mt-4 break-words">
                {noteMaterial?.content ? (
                  <LectureContent
                    content={noteMaterial.content}
                    sources={noteMaterial.sources ?? []}
                    userRole="student"
                    skipFirstHeading
                  />
                ) : (
                  <div className="space-y-6">
                    <p>
                      <strong>Іменник</strong> — самостійна частина мови, що
                      називає предмети, істот, явища, поняття і відповідає на
                      питання хто? що?
                    </p>

                    <div>
                      <strong>Значення іменників:</strong>
                      <ul className="list-disc pl-5 mt-1 space-y-1">
                        <li>істоти: учень, кіт</li>
                        <li>неістоти: стіл, дощ</li>
                        <li>абстрактні поняття: дружба, сміливість</li>
                      </ul>
                    </div>

                    <div>
                      <strong>Граматичні ознаки:</strong>
                      <ul className="list-disc pl-5 mt-1 space-y-1">
                        <li>Рід: чоловічий (день), жіночий (ніч), середній (вікно)</li>
                        <li>Число: однина (книга), множина (книги)</li>
                        <li>
                          Відмінки (7): називний, родовий, давальний,
                          знахідний, орудний, місцевий, кличний
                        </li>
                        <li>Відміни: I, II, III, IV</li>
                      </ul>
                    </div>

                    <div>
                      <strong>Власні й загальні іменники:</strong>
                      <ul className="list-disc pl-5 mt-1 space-y-1">
                        <li>власні: Київ, Марія (пишуться з великої літери)</li>
                        <li>загальні: місто, дівчина</li>
                      </ul>
                    </div>

                    <div>
                      <strong>Конкретні й абстрактні:</strong>
                      <ul className="list-disc pl-5 mt-1 space-y-1">
                        <li>конкретні: олівець, дерево</li>
                        <li>абстрактні: радість, знання</li>
                      </ul>
                    </div>

                    <div>
                      <strong>Синтаксична роль у реченні:</strong>
                      <ul className="list-disc pl-5 mt-1 space-y-1">
                        <li>підмет: Книга лежить на столі.</li>
                        <li>додаток: Я читаю книгу.</li>
                      </ul>
                    </div>

                    <div>
                      <strong>Правопис:</strong>
                      <ul className="list-disc pl-5 mt-1 space-y-1">
                        <li>з великої літери — власні назви</li>
                        <li>не з іменниками: не друг, неспокій</li>
                      </ul>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>

        </main>
    </div>
  );
};

export default StudentNote;
