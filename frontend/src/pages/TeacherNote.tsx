import { useEffect, useMemo, useState, useCallback } from "react";
import { useParams, useNavigate } from "react-router-dom";
import BackButton from "../components/BackButton";
import Breadcrumbs from "../components/Breadcrumbs";
import ConfirmDeleteModal from "../components/ConfirmDeleteModal";
import LectureContent from "../components/LectureContent";
import SelectStudentsModal from "../components/SelectStudentsModal";
import TeacherSidebar from "../components/TeacherSidebar";
import { deleteMaterial, getMaterials, updateMaterial } from "../data/materialsStorage";
import type { Source } from "../components/LectureContent";
import { classIdToLabel } from "../data/classUtils";
import { toNumericId } from "../api/idUtils";
import { getTeacherStudents } from "../api/teacher";

/**
 * Converts a Source (string or SourceItem) to a display string for editing.
 * Format: "Name: pages" or just "Name" if no pages.
 */
const sourceToEditString = (source: Source): string => {
  if (typeof source === "string") {
    return source;
  }
  // Structured source object
  if (source.pages && source.pages.trim()) {
    return `${source.name}: ${source.pages}`;
  }
  return source.name;
};

/**
 * Parses an edit string back to a Source object.
 * Format: "Name: pages" → { name: "Name", pages: "pages" }
 * Or just "Name" → { name: "Name" }
 */
const parseEditStringToSource = (str: string): Source => {
  const trimmed = str.trim();
  // Check if it contains ": " which indicates "name: pages" format
  const colonIndex = trimmed.indexOf(": ");
  if (colonIndex > 0) {
    const name = trimmed.substring(0, colonIndex).trim();
    const pages = trimmed.substring(colonIndex + 2).trim();
    if (pages) {
      return { name, pages };
    }
    return { name };
  }
  // No colon found, treat as simple name
  return { name: trimmed };
};

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
  const navigate = useNavigate();

  const [isAudienceModalOpen, setIsAudienceModalOpen] = useState(false);
  const [isEditMode, setIsEditMode] = useState(false);
  const [editContent, setEditContent] = useState("");
  const [editTeacherNotes, setEditTeacherNotes] = useState("");
  // Sources editing state - stored as newline-separated string for easier textarea editing
  const [editSources, setEditSources] = useState("");
  const [materialVersion, setMaterialVersion] = useState(0);
  const [isDeleteModalOpen, setIsDeleteModalOpen] = useState(false);

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

  // Fetch class students for audience selection modal
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
    // Convert sources array to newline-separated string for editing
    // Handles both string sources and structured { name, pages } objects
    const sourcesText = (noteMaterial?.sources ?? [])
      .map(sourceToEditString)
      .join("\n");
    setEditSources(sourcesText);
    setIsEditMode(true);
  }, [noteMaterial?.content, noteMaterial?.teacherNotes, noteMaterial?.sources]);

  const handleCancelEdit = useCallback(() => {
    setIsEditMode(false);
    setEditContent("");
    setEditTeacherNotes("");
    setEditSources("");
  }, []);

  const handleSaveEdit = useCallback(() => {
    if (!noteId) return;
    // Parse sources from newline-separated string, filtering out empty lines
    // Each line is parsed as "Name: pages" or just "Name"
    const sourcesArray = editSources
      .split("\n")
      .map((s) => s.trim())
      .filter((s) => s.length > 0)
      .map(parseEditStringToSource);
    updateMaterial(noteId, {
      content: editContent,
      teacherNotes: editTeacherNotes,
      sources: sourcesArray,
    });
    setMaterialVersion((v) => v + 1);
    setIsEditMode(false);
  }, [noteId, editContent, editTeacherNotes, editSources]);

  const handleDelete = useCallback(() => {
    if (!noteId) return;
    const success = deleteMaterial(noteId);
    if (success) {
      navigate(backToTopicHref);
    }
    setIsDeleteModalOpen(false);
  }, [noteId, navigate, backToTopicHref]);

  return (
    <div className="h-screen bg-[#1E73F7] text-slate-900 overflow-hidden flex">
      {/* Static sidebar - always shows only "Materials" and "Students" links */}
      <TeacherSidebar
        teacherName={teacherId ? `Вчитель ${teacherId}` : "Вчитель"}
        activeItem="materials"
        onMaterialsClick={() => navigate(`/teacher/${teacherId}`)}
        onStudentsClick={() => navigate(`/teacher/${teacherId}?view=students`)}
      />

      <main className="flex-1 px-10 py-6 w-full flex flex-col h-full overflow-hidden">
          <div className="flex items-center gap-4 mb-4 shrink-0">
            <BackButton fallbackPath={backToTopicHref} />
            <Breadcrumbs
              items={[
                { label: subjectName || "Предмет", href: backToClassHref },
                { label: classLabel || "Клас", href: backToClassHref },
                { label: sidebarTopicName || "Тема", href: backToTopicHref },
                { label: noteTitle },
              ]}
            />
          </div>
          <div className="flex items-center gap-4 shrink-0">
            <h1 className="text-2xl font-bold text-white">
              Конспект. {noteTitle}
            </h1>

            {/* Edit/Delete buttons - shown when not in edit mode and material exists */}
            {!isEditMode && noteMaterial && (
              <>
                <button
                  type="button"
                  onClick={handleStartEdit}
                  className="flex items-center gap-2 rounded-full border border-white/20 bg-white/10 px-4 py-2 text-sm font-semibold text-white transition hover:bg-[#1557c0] hover:border-[#1557c0]"
                >
                  <PencilIcon />
                  Редагувати конспект
                </button>
                <button
                  type="button"
                  onClick={() => setIsDeleteModalOpen(true)}
                  className="flex items-center gap-2 rounded-full border border-white/20 bg-white/10 px-4 py-2 text-sm font-semibold text-white transition hover:bg-red-500 hover:border-red-500"
                >
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M3 6h18" />
                    <path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6" />
                    <path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2" />
                  </svg>
                  Видалити
                </button>
              </>
            )}

            {/* Save/Cancel buttons - shown in edit mode */}
            {isEditMode && (
              <>
                <button
                  type="button"
                  onClick={handleSaveEdit}
                  className="flex items-center gap-2 rounded-full bg-white px-4 py-2 text-sm font-semibold text-[#1E73F7] transition hover:bg-slate-100"
                >
                  Зберегти зміни
                </button>
                <button
                  type="button"
                  onClick={handleCancelEdit}
                  className="flex items-center gap-2 rounded-full border border-white/20 bg-white/10 px-4 py-2 text-sm font-semibold text-white transition hover:bg-white/20"
                >
                  Скасувати
                </button>
              </>
            )}
          </div>

          <div className="mt-5 flex-1 min-h-0 rounded-[28px] bg-white p-6 shadow-sm flex flex-col overflow-hidden">
            <div className="flex-1 min-h-0 grid gap-6 lg:grid-cols-[1fr_300px]">
              <div className="rounded-[20px] bg-white overflow-y-auto note-scrollbar pr-2">
                <div className="break-words">
                  {isEditMode ? (
                    <div className="space-y-6">
                      {/* Content editing */}
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

                      {/* Sources editing - teacher-only feature */}
                      <div>
                        <label className="text-sm font-medium text-slate-700 mb-2 block">
                          Джерела
                          <span className="ml-2 text-xs text-slate-400 font-normal">
                            (видимі тільки для вчителя, кожне джерело з нового рядка)
                          </span>
                        </label>
                        <textarea
                          value={editSources}
                          onChange={(e) => setEditSources(e.target.value)}
                          className="min-h-[100px] w-full rounded-xl border border-slate-200 p-4 text-sm text-slate-800 resize-none focus:border-[#1E73F7] focus:outline-none focus:ring-1 focus:ring-[#1E73F7]"
                          placeholder="Підручник з алгебри, 7 клас&#10;Стаття про квадратні рівняння&#10;https://example.com/math"
                        />
                      </div>
                    </div>
                  ) : noteMaterial?.content ? (
                    <LectureContent
                      content={noteMaterial.content}
                      sources={noteMaterial.sources ?? []}
                      userRole="teacher"
                      skipFirstHeading
                    />
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

              </div>

              <div className="rounded-[20px] bg-[#E9F1FF] p-5 h-full flex flex-col overflow-hidden">
                <h3 className="text-sm font-bold text-slate-900 shrink-0">Нотатки</h3>
                <div className="mt-2 flex-1 min-h-0 overflow-hidden">
                  {isEditMode ? (
                    <textarea
                      value={editTeacherNotes}
                      onChange={(e) => setEditTeacherNotes(e.target.value)}
                      className="h-full w-full rounded-xl border border-slate-200 bg-white p-3 text-[10px] leading-snug text-slate-700 resize-none focus:border-[#1E73F7] focus:outline-none focus:ring-1 focus:ring-[#1E73F7]"
                      placeholder="Нотатки для вчителя..."
                    />
                  ) : teacherNotes ? (
                    <div className="text-[10px] leading-snug text-slate-700 whitespace-pre-wrap overflow-hidden h-full">
                      {teacherNotes}
                    </div>
                  ) : (
                    <div className="text-[10px] text-slate-700">
                      Нотатки відсутні.
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>
        </main>

      <SelectStudentsModal
        isOpen={isAudienceModalOpen}
        onClose={() => setIsAudienceModalOpen(false)}
        students={classStudents.map((studentId) => ({ id: studentId }))}
        onSave={(selection) => {
            console.log("Saved selection", selection);
            setIsAudienceModalOpen(false);
        }}
      />

      <ConfirmDeleteModal
        isOpen={isDeleteModalOpen}
        onClose={() => setIsDeleteModalOpen(false)}
        onConfirm={handleDelete}
        title={noteTitle}
        itemType="conspect"
      />
    </div>
  );
};

export default TeacherNote;
