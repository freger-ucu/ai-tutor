import { useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { teachers } from "../data/teachers";
import TeacherSidebar from "../components/TeacherSidebar";
import SelectStudentsModal from "../components/SelectStudentsModal";
import { getMaterials } from "../data/materialsStorage";
import { classIdToLabel } from "../data/classUtils";

const TeacherNote = () => {
  const { teacherId, courseId, classId, topicId, noteId } = useParams();
  
  const teacher = useMemo(
    () => teachers.find((item) => item.id === teacherId),
    [teacherId]
  );

  const [isAudienceModalOpen, setIsAudienceModalOpen] = useState(false);

  const decodedClassId = classId ? Number(decodeURIComponent(classId)) : null;
  const decodedTopic = topicId ? decodeURIComponent(topicId) : "";
  const decodedNote = noteId ? decodeURIComponent(noteId) : "Іменник"; 
  const decodedCourse = courseId ? decodeURIComponent(courseId) : "";
  const classNumberMatch = decodedCourse.match(/(\d+)$/);
  const classNumber = classNumberMatch ? Number(classNumberMatch[1]) : null;
  const classLabel =
    decodedClassId && classNumber
      ? classIdToLabel(classNumber, decodedClassId)
      : "";
  const noteMaterial = useMemo(
    () => getMaterials({ type: "note" }).find((item) => item.id === noteId),
    [noteId]
  );
  const noteTitle = noteMaterial?.title ?? decodedNote;
  const sidebarCourseId = noteMaterial?.courseId ?? decodedCourse;
  const sidebarTopicName = noteMaterial?.topicName ?? decodedTopic;
  const encodedTopic = sidebarTopicName ? encodeURIComponent(sidebarTopicName) : "";
  const backToTopicHref =
    sidebarCourseId && classId && encodedTopic
      ? `/teacher/${teacherId}/topic/${sidebarCourseId}/${classId}/${encodedTopic}`
      : teacherId
      ? `/teacher/${teacherId}`
      : "/";
  const backToClassHref = teacherId ? `/teacher/${teacherId}` : "/";
  const sidebarMaterials = useMemo(() => {
    const sidebarClassName = noteMaterial?.className ?? classLabel;
    if (!teacherId || !sidebarClassName || !sidebarTopicName) {
      return [];
    }
    const filters: {
      teacherId?: string;
      courseId?: string;
      className?: string;
      topicName?: string;
    } = {
      teacherId,
      className: sidebarClassName,
      topicName: sidebarTopicName,
    };
    if (sidebarCourseId) {
      filters.courseId = sidebarCourseId;
    }
    return getMaterials(filters);
  }, [teacherId, classLabel, noteMaterial?.className, noteMaterial?.topicName, sidebarCourseId, sidebarTopicName]);
  const sidebarNotes = sidebarMaterials.filter((item) => item.type === "note");
  const sidebarTests = sidebarMaterials.filter((item) => item.type === "test");

  return (
    <div className="h-screen bg-[#1E73F7] text-slate-900 overflow-hidden">
      <div className="flex h-full">
        <TeacherSidebar
          teacherName={
            teacher ? `${teacher.firstName} ${teacher.lastName}` : "Вчитель"
          }
          activeItem="materials"
          afterPrimaryNav={
            <div className="space-y-2">
              <Link
                to={backToClassHref}
                className="flex w-full items-start justify-start gap-3 rounded-2xl px-4 py-3 text-sm font-medium text-slate-800 hover:bg-slate-100"
              >
                <span className="mt-0.5 inline-block h-5 w-5 rounded-md bg-slate-200" />
                <span>Назад до класу</span>
              </Link>
              <Link
                to={backToTopicHref}
                className="flex w-full items-start justify-start gap-3 rounded-2xl px-4 py-3 text-sm font-medium text-slate-800 hover:bg-slate-100"
              >
                <span className="mt-0.5 inline-block h-5 w-5 rounded-md bg-slate-200" />
                <span>Назад до теми</span>
              </Link>
            </div>
          }
        >
          <div className="space-y-4">
            {sidebarNotes.map((item) => (
              <Link
                key={item.id}
                to={`/teacher/${teacherId}/note/${sidebarCourseId}/${classId}/${encodedTopic}/${item.id}`}
                className={`flex w-full items-start justify-start gap-3 rounded-2xl px-4 py-3 ${
                  item.id === noteId
                    ? "text-[#1E73F7]"
                    : "text-slate-700 hover:bg-slate-100"
                }`}
              >
                <span
                  className={`mt-0.5 inline-block h-5 w-5 rounded-md ${
                    item.id === noteId ? "bg-[#1E73F7]/20" : "bg-slate-200"
                  }`}
                />
                <span>{item.title}</span>
              </Link>
            ))}
            {sidebarTests.map((item) => (
              <Link
                key={item.id}
                to={`/teacher/${teacherId}/test/${item.id}`}
                className="flex w-full items-start justify-start gap-3 rounded-2xl px-4 py-3 text-slate-700 hover:bg-slate-100"
              >
                <span className="mt-0.5 inline-block h-5 w-5 rounded-md bg-slate-200" />
                <span>{item.title}</span>
              </Link>
            ))}
          </div>
        </TeacherSidebar>

        <main className="flex-1 px-10 py-8 flex flex-col h-full">
          <h1 className="mt-2 text-2xl font-bold text-white shrink-0">
            Конспект. {noteTitle}
          </h1>

          {/* Main Card */}
          <div className="mt-4 flex-1 rounded-[32px] bg-white p-2 shadow-xl flex flex-col md:flex-row overflow-hidden min-h-0">
             
             {/* Note Content Area */}
             <div className="flex-1 p-8 md:p-10 overflow-y-auto">
                <h2 className="text-xl font-bold text-slate-900 mb-6">{noteTitle}</h2>
                
                {noteMaterial?.content ? (
                  <div className="text-sm leading-relaxed text-slate-800 whitespace-pre-wrap">
                    {noteMaterial.content}
                  </div>
                ) : (
                  <div className="space-y-6 text-sm leading-relaxed text-slate-800">
                      <p>
                          <strong>Іменник</strong> — самостійна частина мови, що називає предмети, істот, явища, поняття і відповідає на питання хто? що?
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
                              <li>Відмінки (7): називний, родовий, давальний, знахідний, орудний, місцевий, кличний</li>
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
                  </div>
                )}
             </div>

             {/* Right Sidebar - "Notes" / TOC */}
             <div className="w-full md:w-80 bg-[#E9F1FF] rounded-[24px] m-2 p-6 overflow-y-auto">
                <h3 className="text-base font-bold text-slate-900 mb-4">Нотатки</h3>
                <ul className="space-y-2 text-xs font-medium text-slate-700">
                    <li>Самостійна частина мови</li>
                    <li>Питання хто? що?</li>
                    <li>Лексичне значення</li>
                    <li>Назви істот / неістоти</li>
                    <li>Абстрактні іменники</li>
                    <li>Конкретні іменники</li>
                    <li>Власні іменники</li>
                    <li>Загальні іменники</li>
                    <li>Число іменника (однина, множина)</li>
                    <li>Відмінок</li>
                    <li>Відмінювання</li>
                    <li>Відміни іменників (I–IV)</li>
                    <li>Синтаксична роль (підмет, додаток)</li>
                    <li>Правопис іменників</li>
                    <li>Велика літера в іменниках</li>
                </ul>
             </div>

          </div>

          {/* Footer Actions */}
          <div className="mt-6 flex items-center justify-between shrink-0">
             <button className="flex items-center gap-2 rounded-full bg-white px-6 py-3 text-sm font-bold text-[#1E73F7] shadow transition hover:-translate-y-0.5 hover:shadow-lg cursor-pointer">
                <svg width="16" height="20" viewBox="0 0 16 20" fill="currentColor">
                    <path d="M10 0H2C0.9 0 0 0.9 0 2V18C0 19.1 0.9 20 2 20H14C15.1 20 16 19.1 16 18V6L10 0ZM14 18H2V2H9V7H14V18Z" opacity="0.5"/>
                    <path d="M10 0H2C0.9 0 0 0.9 0 2V18C0 19.1 0.9 20 2 20H14C15.1 20 16 19.1 16 18V6L10 0ZM9 7V2L14 7H9Z"/>
                </svg>
                Завантажити в PDF
             </button>

             <button 
                onClick={() => setIsAudienceModalOpen(true)}
                className="flex items-center gap-2 rounded-full border-2 border-white bg-transparent px-6 py-3 text-sm font-bold text-white transition hover:bg-white/10 cursor-pointer"
             >
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M21 12C21 16.9706 16.9706 21 12 21C9.69637 21 7.59565 20.1344 6.00003 18.7077M3 12C3 7.02944 7.02944 3 12 3C14.3036 3 16.4044 3.86558 18 5.29231" stroke="white" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"/>
                    <path d="M21 3V8H16" stroke="white" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"/>
                    <path d="M3 21V16H8" stroke="white" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"/>
                 </svg>
                 <span>Змінити цільову аудиторію</span>
             </button>
          </div>
        </main>
      </div>

      <SelectStudentsModal
        isOpen={isAudienceModalOpen}
        onClose={() => setIsAudienceModalOpen(false)}
        classNameFilter={classLabel}
        onSave={(selection) => {
            console.log("Saved selection", selection);
            setIsAudienceModalOpen(false);
        }}
      />
    </div>
  );
};

export default TeacherNote;
