import { useEffect, useMemo, useState, useCallback } from "react";
import { Link, useParams } from "react-router-dom";
import BackButton from "../components/BackButton";
import Breadcrumbs from "../components/Breadcrumbs";
import MarkdownContent from "../components/MarkdownContent";
import SelectStudentsModal from "../components/SelectStudentsModal";
import { getMaterials, updateMaterial } from "../data/materialsStorage";
import { classIdToLabel } from "../data/classUtils";
import { toNumericId } from "../api/idUtils";
import { getTeacherStudents } from "../api/teacher";

const PencilIcon = () => (
  <svg
    width="16"
    height="16"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="2"
    strokeLinecap="round"
    strokeLinejoin="round"
  >
    <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7" />
    <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z" />
  </svg>
);

const TeacherNote = () => {
  const { teacherId, courseId, classId, topicId, noteId } = useParams();

  const [isAudienceModalOpen, setIsAudienceModalOpen] = useState(false);
  const [isEditMode, setIsEditMode] = useState(false);
  const [editContent, setEditContent] = useState("");
  const [editTeacherNotes, setEditTeacherNotes] = useState("");
  const [materialVersion, setMaterialVersion] = useState(0);

  const decodedClassId = classId ? Number(decodeURIComponent(classId)) : null;
  const decodedTopic = topicId ? decodeURIComponent(topicId) : "";
  const decodedNote = noteId ? decodeURIComponent(noteId) : "Іменник"; 
  const decodedCourse = courseId ? decodeURIComponent(courseId) : "";
  const subjectSlug = decodedCourse.split("-").slice(0, -1).join("-");
  const subjectLabelMap: Record<string, string> = {
    algebra: "Алгебра",
    geometry: "Геометрія",
    "ukr-lang": "Українська мова",
    history: "Історія України",
  };
  const subjectName = subjectLabelMap[subjectSlug] ?? decodedCourse;
  const classNumberMatch = decodedCourse.match(/(\d+)$/);
  const classNumber = classNumberMatch ? Number(classNumberMatch[1]) : null;
  const classLabel =
    decodedClassId && classNumber
      ? classIdToLabel(classNumber, decodedClassId)
      : "";
  const apiTeacherId = toNumericId(teacherId) ?? 0;
  const apiClassId = decodedClassId ?? 0;
  const [classStudents, setClassStudents] = useState<number[]>([]);
  const noteMaterial = useMemo(
    () => getMaterials({ type: "note" }).find((item) => item.id === noteId),
    [noteId, materialVersion]
  );
  const noteTitle = noteMaterial?.title ?? decodedNote;
  const teacherNotes = noteMaterial?.teacherNotes?.trim();
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
      subject?: string;
      classId?: number;
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
    if (subjectName) {
      filters.subject = subjectName;
    }
    if (apiClassId) {
      filters.classId = apiClassId;
    }
    return getMaterials(filters);
  }, [
    teacherId,
    classLabel,
    noteMaterial?.className,
    noteMaterial?.topicName,
    sidebarCourseId,
    sidebarTopicName,
    subjectName,
    apiClassId,
  ]);
  const sidebarNotes = sidebarMaterials.filter((item) => item.type === "note");
  const sidebarTests = sidebarMaterials.filter((item) => item.type === "test");
  useEffect(() => {
    if (!apiTeacherId || !apiClassId || !subjectName) {
      setClassStudents([]);
      return;
    }
    getTeacherStudents({
      class_id: apiClassId,
      teacher_id: apiTeacherId,
      subject: subjectName,
    })
      .then((response) => {
        setClassStudents(response.students.map((student) => student.student_id));
      })
      .catch((error) => {
        console.error(error);
        setClassStudents([]);
      });
  }, [apiTeacherId, apiClassId, subjectName]);

  const handleStartEdit = useCallback(() => {
    setEditContent(noteMaterial?.content ?? "");
    setEditTeacherNotes(noteMaterial?.teacherNotes ?? "");
    setIsEditMode(true);
  }, [noteMaterial?.content, noteMaterial?.teacherNotes]);

  const handleCancelEdit = useCallback(() => {
    setIsEditMode(false);
    setEditContent("");
    setEditTeacherNotes("");
  }, []);

  const handleSaveEdit = useCallback(() => {
    if (!noteId) return;
    updateMaterial(noteId, {
      content: editContent,
      teacherNotes: editTeacherNotes,
    });
    setMaterialVersion((v) => v + 1);
    setIsEditMode(false);
  }, [noteId, editContent, editTeacherNotes]);

  return (
    <div className="min-h-screen bg-[#1E73F7] text-slate-900">
      <div className="flex min-h-screen">
        {/* Fixed Sidebar - matching student layout */}
        <aside className="fixed left-0 top-0 h-screen w-64 bg-white px-6 py-8 flex flex-col z-10 overflow-y-auto">
          <div className="flex items-center gap-3">
            <div
              className="h-12 w-12 overflow-hidden rounded-full bg-slate-200"
              style={{
                backgroundImage: "url('https://i1.poltava.to/uploads/2017/09/2017-09-19/best.jpg')",
                backgroundSize: "cover",
                backgroundPosition: "center",
              }}
            />
            <div className="text-base font-semibold text-slate-900">
              {teacherId ? `Вчитель ${teacherId}` : "Вчитель"}
            </div>
          </div>

          <div className="mt-6 border-t border-slate-200 pt-6 space-y-4 text-sm">
            {sidebarNotes.map((item) => (
              <Link
                key={item.id}
                to={`/teacher/${teacherId}/note/${sidebarCourseId}/${classId}/${encodedTopic}/${item.id}`}
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
                to={`/teacher/${teacherId}/test/${item.id}`}
                className="flex items-center gap-3 rounded-xl px-4 py-3 text-slate-700 hover:bg-slate-50"
              >
                <img src="/src/assets/Group.svg" alt="" className="h-4 w-4" />
                Тест. {item.title}
              </Link>
            ))}
          </div>
        </aside>

        <main className="ml-64 flex-1 px-10 py-6 w-full">
          <div className="flex items-center gap-4 mb-4">
            <BackButton fallbackPath={backToTopicHref} />
            <Breadcrumbs
              items={[
                { label: "Матеріали", href: backToClassHref },
                { label: classLabel || "Клас", href: backToClassHref },
                { label: sidebarTopicName || "Тема", href: backToTopicHref },
                { label: noteTitle },
              ]}
            />
          </div>
          <h1 className="text-2xl font-bold text-white">
            Конспект. {noteTitle}
          </h1>

          <div className="mt-5 rounded-[28px] bg-white p-6 shadow-sm">
            <div className="grid gap-6 lg:grid-cols-[1fr_260px]">
              <div className="rounded-[20px] bg-white">
                <h2 className="text-lg font-semibold text-slate-900">
                  {sidebarTopicName || noteTitle}
                </h2>
                <div className="mt-4">
                  {isEditMode ? (
                    <div>
                      <label className="text-sm font-medium text-slate-700 mb-2 block">
                        Зміст конспекту
                      </label>
                      <textarea
                        value={editContent}
                        onChange={(e) => setEditContent(e.target.value)}
                        className="min-h-[300px] w-full rounded-xl border border-slate-200 p-4 text-sm text-slate-800 resize-none focus:border-[#1E73F7] focus:outline-none focus:ring-1 focus:ring-[#1E73F7]"
                        placeholder="Введіть зміст конспекту..."
                      />
                    </div>
                  ) : noteMaterial?.content ? (
                    <MarkdownContent content={noteMaterial.content} />
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

                {/* Edit/Save buttons */}
                <div className="mt-6 pt-4 border-t border-slate-100">
                  {isEditMode ? (
                    <div className="flex items-center gap-3">
                      <button
                        type="button"
                        onClick={handleSaveEdit}
                        className="flex items-center gap-2 rounded-full bg-[#1E73F7] px-5 py-2.5 text-sm font-semibold text-white transition hover:bg-[#1A63D6]"
                      >
                        Зберегти зміни
                      </button>
                      <button
                        type="button"
                        onClick={handleCancelEdit}
                        className="flex items-center gap-2 rounded-full border border-slate-200 bg-white px-5 py-2.5 text-sm font-semibold text-slate-700 transition hover:bg-slate-50"
                      >
                        Скасувати
                      </button>
                    </div>
                  ) : noteMaterial ? (
                    <button
                      type="button"
                      onClick={handleStartEdit}
                      className="flex items-center gap-2 rounded-full border border-slate-200 bg-white px-5 py-2.5 text-sm font-semibold text-slate-700 transition hover:bg-slate-50 hover:border-[#1E73F7] hover:text-[#1E73F7]"
                    >
                      <PencilIcon />
                      Редагувати конспект
                    </button>
                  ) : null}
                </div>
              </div>

              <div className="rounded-[20px] bg-[#E9F1FF] p-6">
                <h3 className="text-sm font-bold text-slate-900">Нотатки</h3>
                <div className="mt-3">
                  {isEditMode ? (
                    <textarea
                      value={editTeacherNotes}
                      onChange={(e) => setEditTeacherNotes(e.target.value)}
                      className="min-h-[200px] w-full rounded-xl border border-slate-200 bg-white p-4 text-xs text-slate-700 resize-none focus:border-[#1E73F7] focus:outline-none focus:ring-1 focus:ring-[#1E73F7]"
                      placeholder="Нотатки для вчителя..."
                    />
                  ) : teacherNotes ? (
                    <div className="text-xs leading-relaxed text-slate-700 whitespace-pre-wrap">
                      {teacherNotes}
                    </div>
                  ) : (
                    <div className="text-xs text-slate-700">
                      Нотатки відсутні.
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>
        </main>
      </div>

      <SelectStudentsModal
        isOpen={isAudienceModalOpen}
        onClose={() => setIsAudienceModalOpen(false)}
        students={classStudents.map((studentId) => ({ id: studentId }))}
        onSave={(selection) => {
            console.log("Saved selection", selection);
            setIsAudienceModalOpen(false);
        }}
      />
    </div>
  );
};

export default TeacherNote;
