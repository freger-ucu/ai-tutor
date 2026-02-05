import { useEffect, useMemo, useState, useCallback } from "react";
import { useParams, useNavigate } from "react-router-dom";
import BackButton from "../components/BackButton";
import Breadcrumbs from "../components/Breadcrumbs";
import ConfirmDeleteModal from "../components/ConfirmDeleteModal";
import LectureContent from "../components/LectureContent";
import MarkdownContent from "../components/MarkdownContent";
import NoteEditModal from "../components/NoteEditModal";
import SelectStudentsModal from "../components/SelectStudentsModal";
import TeacherSidebar from "../components/TeacherSidebar";
import { deleteMaterial, getMaterials, updateMaterial } from "../data/materialsStorage";
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
  const navigate = useNavigate();

  const [isAudienceModalOpen, setIsAudienceModalOpen] = useState(false);
  const [isEditModalOpen, setIsEditModalOpen] = useState(false);
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

  const handleSaveEdit = useCallback((content: string) => {
    if (!noteId) return;
    updateMaterial(noteId, {
      content,
    });
    setMaterialVersion((v) => v + 1);
  }, [noteId]);

  const handleDelete = useCallback(() => {
    if (!noteId) return;
    const success = deleteMaterial(noteId);
    if (success) {
      navigate(backToTopicHref);
    }
    setIsDeleteModalOpen(false);
  }, [noteId, navigate, backToTopicHref]);

  return (
    <div className="min-h-screen lg:h-screen bg-[#1E73F7] text-slate-900 overflow-y-auto lg:overflow-hidden flex flex-col lg:flex-row">
      {/* Static sidebar - always shows only "Materials" and "Students" links */}
      <div className="hidden lg:flex">
        <TeacherSidebar
          teacherName={teacherId ? `Вчитель ${teacherId}` : "Вчитель"}
          activeItem="materials"
          onMaterialsClick={() => navigate(`/teacher/${teacherId}`)}
          onStudentsClick={() => navigate(`/teacher/${teacherId}?view=students`)}
        />
      </div>

      <main
        className="flex-1 px-4 py-6 w-full flex flex-col overflow-y-auto lg:px-10 lg:py-6 lg:h-full lg:overflow-hidden"
        data-scroll-root="mobile"
      >
          <div className="flex items-center gap-4 mb-4 shrink-0">
            <BackButton fallbackPath={backToTopicHref} />
            <div className="hidden lg:flex">
              <Breadcrumbs
                items={[
                  { label: subjectName || "Предмет", href: backToClassHref },
                  { label: classLabel || "Клас", href: backToClassHref },
                  { label: sidebarTopicName || "Тема", href: backToTopicHref },
                  { label: noteTitle },
                ]}
              />
            </div>
          </div>
          <div className="flex items-center justify-between gap-4 shrink-0 lg:pr-4">
            <h1 className="text-xl font-bold text-white">
              {noteTitle}
            </h1>

            {/* Edit/Delete buttons */}
            {noteMaterial && (
              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={() => setIsEditModalOpen(true)}
                  className="flex items-center gap-2 rounded-full border border-white/20 bg-white/10 px-4 py-2 text-sm font-semibold text-white transition hover:bg-[#1557c0] hover:border-[#1557c0]"
                >
                  <PencilIcon />
                  <span className="hidden lg:inline">Редагувати конспект</span>
                </button>
                <button
                  type="button"
                  onClick={() => setIsDeleteModalOpen(true)}
                  className="flex items-center gap-2 rounded-full border border-white/20 bg-white/10 px-4 py-2 text-sm font-semibold text-white transition hover:bg-red-500 hover:border-red-500"
                  aria-label="Видалити конспект"
                >
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M3 6h18" />
                    <path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6" />
                    <path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2" />
                  </svg>
                </button>
              </div>
            )}
          </div>

          <div className="mt-4 flex-1 min-h-0 rounded-[28px] bg-white p-4 shadow-sm flex flex-col overflow-visible lg:mt-5 lg:p-6 lg:overflow-hidden">
            <div className="flex-1 min-h-0 grid gap-6 lg:grid-cols-[1fr_300px]">
              <div className="rounded-[20px] bg-white overflow-y-visible lg:overflow-y-auto lg:pr-2">
                <div className="break-words">
                  {noteMaterial?.content ? (
                    <LectureContent
                      content={noteMaterial.content}
                      sources={noteMaterial.sources ?? []}
                      userRole="teacher"
                      title={noteTitle}
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

              <div className="rounded-[20px] bg-[#E9F1FF] p-4 h-full flex flex-col overflow-visible lg:p-5 lg:overflow-hidden">
                <h3 className="text-sm font-bold text-slate-900 shrink-0">Нотатки</h3>
                <div className="mt-2 flex-1 min-h-0 overflow-visible lg:overflow-hidden">
                  {teacherNotes ? (
                    <div className="text-sm leading-relaxed text-slate-700 overflow-y-visible lg:overflow-y-auto lg:h-full">
                      <MarkdownContent content={teacherNotes} />
                    </div>
                  ) : (
                    <div className="text-sm text-slate-700">
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

      <NoteEditModal
        isOpen={isEditModalOpen}
        noteTitle={noteTitle}
        content={noteMaterial?.content ?? ""}
        onSave={handleSaveEdit}
        onClose={() => setIsEditModalOpen(false)}
      />
    </div>
  );
};

export default TeacherNote;
