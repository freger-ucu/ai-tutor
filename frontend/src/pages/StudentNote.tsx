import { useMemo } from "react";
import { Link, useParams, useNavigate } from "react-router-dom";
import { students } from "../data/students";
import { getMaterials } from "../data/materialsStorage";

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

const noteOutline = [
  "Самостійна частина мови",
  "Питання хто? що?",
  "Лексичне значення",
  "Назви істот / неістот",
  "Абстрактні іменники",
  "Конкретні іменники",
  "Власні іменники",
  "Загальні іменники",
  "Число іменника (однина, множина)",
  "Відмінок",
  "Відмінювання",
  "Відміни іменників (I–IV)",
  "Синтаксична роль (підмет, додаток)",
  "Правопис іменників",
  "Велика літера в іменниках",
];

const StudentNote = () => {
  const { studentId, courseId, topicId, noteId } = useParams();
  const navigate = useNavigate();

  const student = useMemo(
    () => students.find((s) => s.id === studentId),
    [studentId]
  );

  const decodedCourse = courseId ? decodeURIComponent(courseId) : "";
  const decodedTopic = topicId ? decodeURIComponent(topicId) : "";
  const subjectSlug = decodedCourse.split("-").slice(0, -1).join("-") || decodedCourse;
  const encodedTopic = decodedTopic ? encodeURIComponent(decodedTopic) : "";
  const backToTopicHref =
    courseId && encodedTopic
      ? `/student/${studentId}/topic/${courseId}/${encodedTopic}`
      : `/student/${studentId}`;

  const noteMaterial = useMemo(
    () => getMaterials({ type: "note" }).find((item) => item.id === noteId),
    [noteId]
  );
  const noteTitle = noteMaterial?.title ?? "Конспект";
  const materials = useMemo(() => {
    if (!student) {
      return [];
    }
    return getMaterials({
      courseId: decodedCourse,
      className: student.className,
      topicName: decodedTopic,
    });
  }, [student, decodedCourse, decodedTopic]);
  const sidebarNotes = materials.filter((item) => item.type === "note");
  const sidebarTests = materials.filter((item) => item.type === "test");

  if (!student) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-[#1E73F7]">
        <div className="text-xl text-white">Учня не знайдено</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#1E73F7] text-slate-900">
      <div className="flex min-h-screen">
        <aside className="fixed left-0 top-0 h-screen w-72 bg-white px-6 py-8 flex flex-col z-10">
          <div className="flex items-center gap-3">
            <div
              className="h-10 w-10 overflow-hidden rounded-full bg-slate-200"
              style={{
                backgroundImage:
                  "url('https://images.unsplash.com/photo-1599566150163-29194dcaad36?ixlib=rb-4.0.3&auto=format&fit=crop&w=200&q=80')",
                backgroundSize: "cover",
              }}
            />
            <div>
              <div className="text-sm font-bold text-slate-900">
                {student.firstName} {student.lastName}
              </div>
              <div className="text-xs text-slate-500">
                Клас: {student.className}
              </div>
            </div>
          </div>

          <div className="mt-8 space-y-2">
            {subjects.map((subject) => {
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

          <div className="mt-6">
            <Link
              to={backToTopicHref}
              className="flex items-center gap-3 rounded-xl px-4 py-3 text-sm font-semibold text-slate-700 hover:bg-slate-50"
            >
              <span className="inline-block h-5 w-5 rounded-md bg-slate-200" />
              Назад до теми
            </Link>
          </div>

          <div className="mt-4 border-t border-slate-200 pt-6 space-y-4 text-sm">
            {sidebarNotes.map((item) => (
              <Link
                key={item.id}
                to={`/student/${studentId}/note/${courseId}/${topicId}/${item.id}`}
                className={`flex items-center gap-3 rounded-xl px-4 py-3 font-semibold transition ${
                  item.id === noteId
                    ? "bg-[#E9F1FF] text-[#1E73F7]"
                    : "text-slate-800 hover:bg-slate-50"
                }`}
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
            {sidebarTests.map((item) => (
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

        <main className="ml-72 flex-1 px-10 py-6 w-full">
          <h1 className="text-2xl font-bold text-white">
            Конспект. {noteTitle}
          </h1>

          <div className="mt-5 rounded-[28px] bg-white p-6 shadow-sm min-h-[70vh]">
            <div className="grid gap-6 lg:grid-cols-[1fr_260px]">
              <div className="rounded-[20px] bg-white">
                <h2 className="text-lg font-semibold text-slate-900">
                  {decodedTopic || noteTitle}
                </h2>
                <div className="mt-4 text-sm leading-relaxed text-slate-800 whitespace-pre-wrap">
                  {noteMaterial?.content ? (
                    noteMaterial.content
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

              <div className="rounded-[20px] bg-[#E9F1FF] p-6 min-h-[520px]">
                <h3 className="text-sm font-bold text-slate-900">Нотатки</h3>
                <ul className="mt-3 space-y-1 text-xs font-medium text-slate-700">
                  {noteOutline.map((item) => (
                    <li key={item}>{item}</li>
                  ))}
                </ul>
              </div>
            </div>
          </div>

          <button className="mt-5 inline-flex items-center gap-3 rounded-full bg-white px-6 py-3 text-sm font-semibold text-[#1E73F7] shadow transition hover:-translate-y-0.5 hover:shadow-lg cursor-pointer">
            <svg width="16" height="20" viewBox="0 0 16 20" fill="currentColor">
              <path d="M10 0H2C0.9 0 0 0.9 0 2V18C0 19.1 0.9 20 2 20H14C15.1 20 16 19.1 16 18V6L10 0ZM14 18H2V2H9V7H14V18Z" opacity="0.5"/>
              <path d="M10 0H2C0.9 0 0 0.9 0 2V18C0 19.1 0.9 20 2 20H14C15.1 20 16 19.1 16 18V6L10 0ZM9 7V2L14 7H9Z"/>
            </svg>
            Завантажити в PDF
          </button>
        </main>
      </div>
    </div>
  );
};

export default StudentNote;
