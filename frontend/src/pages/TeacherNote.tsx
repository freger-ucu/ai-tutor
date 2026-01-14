import { useEffect, useMemo, useState, useCallback } from "react";
import { Link, useParams } from "react-router-dom";
import BackButton from "../components/BackButton";
import Breadcrumbs from "../components/Breadcrumbs";
import TeacherSidebar from "../components/TeacherSidebar";
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

const escapeHtml = (value: string) =>
  value
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");

const formatInline = (value: string) => {
  const withCode = value.replace(
    /`([^`]+)`/g,
    "<code class=\"rounded bg-slate-100 px-1 py-0.5 text-xs font-semibold text-slate-900\">$1</code>"
  );
  const withBold = withCode.replace(
    /\*\*([^*]+)\*\*/g,
    "<strong class=\"font-semibold text-slate-900\">$1</strong>"
  );
  return withBold.replace(
    /\*([^*]+)\*/g,
    "<em class=\"italic text-slate-800\">$1</em>"
  );
};

const renderMarkdown = (markdown: string) => {
  const lines = markdown.replace(/\r\n/g, "\n").split("\n");
  let html = "";
  let inUl = false;
  let inOl = false;

  const closeLists = () => {
    if (inUl) {
      html += "</ul>";
      inUl = false;
    }
    if (inOl) {
      html += "</ol>";
      inOl = false;
    }
  };

  for (const line of lines) {
    const trimmed = line.trim();
    if (!trimmed) {
      closeLists();
      html += "<br />";
      continue;
    }

    const safe = formatInline(escapeHtml(trimmed));

    if (trimmed.startsWith("### ")) {
      closeLists();
      html += `<h3 class="mt-6 text-base font-semibold text-slate-900">${safe.slice(4)}</h3>`;
      continue;
    }
    if (trimmed.startsWith("## ")) {
      closeLists();
      html += `<h2 class="mt-6 text-lg font-semibold text-slate-900">${safe.slice(3)}</h2>`;
      continue;
    }
    if (trimmed.startsWith("# ")) {
      closeLists();
      html += `<h1 class="mt-6 text-xl font-bold text-slate-900">${safe.slice(2)}</h1>`;
      continue;
    }

    if (trimmed.startsWith("- ")) {
      if (!inUl) {
        closeLists();
        html += "<ul class=\"mt-3 list-disc space-y-1 pl-5\">";
        inUl = true;
      }
      html += `<li>${safe.slice(2)}</li>`;
      continue;
    }

    const orderedMatch = trimmed.match(/^(\d+)\.\s+/);
    if (orderedMatch) {
      if (!inOl) {
        closeLists();
        html += "<ol class=\"mt-3 list-decimal space-y-1 pl-5\">";
        inOl = true;
      }
      html += `<li>${safe.slice(orderedMatch[0].length)}</li>`;
      continue;
    }

    closeLists();
    html += `<p class="mt-3">${safe}</p>`;
  }

  closeLists();
  return html;
};

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
  const noteContentHtml = noteMaterial?.content
    ? renderMarkdown(noteMaterial.content)
    : null;
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
    <div className="h-screen bg-[#1E73F7] text-slate-900 overflow-hidden">
      <div className="flex h-full">
        <TeacherSidebar
          teacherName={
            teacherId ? `Вчитель ${teacherId}` : "Вчитель"
          }
          activeItem="materials"
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
          <div className="flex items-center gap-4 mb-4 shrink-0">
            <BackButton fallbackPath={backToTopicHref} />
            <Breadcrumbs
              items={[
                { label: "Матеріали", href: backToClassHref },
                { label: classLabel || "Клас", href: backToTopicHref },
                { label: sidebarTopicName || "Тема", href: backToTopicHref },
                { label: noteTitle },
              ]}
            />
          </div>
          <h1 className="text-2xl font-bold text-white shrink-0">
            Конспект. {noteTitle}
          </h1>

          {/* Main Card */}
          <div className="mt-4 flex-1 rounded-[32px] bg-white p-2 shadow-xl flex flex-col md:flex-row overflow-hidden min-h-0">

             {/* Note Content Area */}
             <div className="flex-1 p-8 md:p-10 overflow-y-auto flex flex-col">
                <h2 className="text-xl font-bold text-slate-900 mb-6">{noteTitle}</h2>

                {isEditMode ? (
                  <div className="flex-1 flex flex-col">
                    <label className="text-sm font-medium text-slate-700 mb-2">
                      Зміст конспекту 
                    </label>
                    <textarea
                      value={editContent}
                      onChange={(e) => setEditContent(e.target.value)}
                      className="flex-1 min-h-[300px] w-full rounded-xl border border-slate-200 p-4 text-sm text-slate-800 resize-none focus:border-[#1E73F7] focus:outline-none focus:ring-1 focus:ring-[#1E73F7]"
                      placeholder="Введіть зміст конспекту..."
                    />
                  </div>
                ) : noteContentHtml ? (
                  <div
                    className="text-sm leading-relaxed text-slate-800 flex-1"
                    dangerouslySetInnerHTML={{ __html: noteContentHtml }}
                  />
                ) : (
                  <div className="space-y-6 text-sm leading-relaxed text-slate-800 flex-1">
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

                {/* Edit/Save buttons at bottom */}
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

             {/* Right Sidebar - "Notes" / TOC */}
             <div className="w-full md:w-80 bg-[#E9F1FF] rounded-[24px] m-2 p-6 overflow-y-auto flex flex-col">
                <h3 className="text-base font-bold text-slate-900 mb-4">Нотатки</h3>
                {isEditMode ? (
                  <textarea
                    value={editTeacherNotes}
                    onChange={(e) => setEditTeacherNotes(e.target.value)}
                    className="flex-1 min-h-[200px] w-full rounded-xl border border-slate-200 bg-white p-4 text-xs text-slate-700 resize-none focus:border-[#1E73F7] focus:outline-none focus:ring-1 focus:ring-[#1E73F7]"
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
