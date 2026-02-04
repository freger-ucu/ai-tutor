import { useEffect, useState, useMemo } from "react";
import { useParams, Link, useNavigate } from "react-router-dom";
import AddMaterialsCard from "../components/AddMaterialsCard";
import BackButton from "../components/BackButton";
import Breadcrumbs from "../components/Breadcrumbs";
import Card from "../components/Card";
import ConfirmDeleteModal from "../components/ConfirmDeleteModal";
import GenerateModalContent from "../components/GenerateModalContent";
import Modal from "../components/Modal";
import Panel from "../components/Panel";
import SelectStudentsModal from "../components/SelectStudentsModal";
import TeacherSidebar from "../components/TeacherSidebar";
import TargetAudienceIndicator from "../components/TargetAudienceIndicator";
import { deleteMaterial, getMaterials, getTopics } from "../data/materialsStorage";
import type { AssignmentScope } from "../data/materialsStorage";
import { getTeacherStudents } from "../api/teacher";
import { classIdToLabel } from "../data/classUtils";
import { toNumericId } from "../api/idUtils";
import { useGeneration } from "../context/GenerationContext";

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

const TeacherTopic = () => {
  const { id, courseId, classId, topicId } = useParams();
  const navigate = useNavigate();
  const {
    startNoteGeneration,
    startTestGeneration,
    getGeneratingItemsForTopic,
    getCompletedItemsForTopic,
    clearCompletedItem,
  } = useGeneration();

  const [activeModal, setActiveModal] = useState<
    "material" | "test" | "audience" | null
  >(null);
  // Keep track of which flow opened the audience selector
  const [previousModal, setPreviousModal] = useState<
    "material" | "test" | null
  >(null);
  const [audienceSelection, setAudienceSelection] = useState<{
    levels: ("weak" | "medium" | "strong")[];
    students: number[];
  } | null>(null);

  const [materialName, setMaterialName] = useState("");
  const [testName, setTestName] = useState("");
  const [materialError, setMaterialError] = useState<string | null>(null);
  const [testError, setTestError] = useState<string | null>(null);
  const [classStudents, setClassStudents] = useState<number[]>([]);
  const decodedClassId = classId ? Number(decodeURIComponent(classId)) : null;
  const decodedTopic = topicId ? decodeURIComponent(topicId) : "";
  const decodedCourse = courseId ? decodeURIComponent(courseId) : "";
  const courseLabel = decodedCourse
    ? (courseLabels[decodedCourse] ?? decodedCourse)
    : "";
  const subjectName = courseLabel || decodedCourse;
  const classNumberMatch = decodedCourse.match(/(\d+)$/);
  const classNumber = classNumberMatch ? Number(classNumberMatch[1]) : null;
  const classLabel =
    decodedClassId && classNumber
      ? classIdToLabel(classNumber, decodedClassId)
      : "";
  const apiTeacherId = toNumericId(id) ?? 0;
  const apiClassId = decodedClassId ?? 0;

  // Get topic date from storage
  const topicDate = useMemo(() => {
    const topics = getTopics({ courseId: decodedCourse });
    const topic = topics.find((t) => t.title === decodedTopic);
    return topic?.createdAt;
  }, [decodedCourse, decodedTopic]);

  const formatDate = (value?: string) => {
    if (!value) return "—";
    const parsed = new Date(value);
    if (Number.isNaN(parsed.getTime())) return "—";
    return parsed.toLocaleDateString("uk-UA", {
      day: "numeric",
      month: "long",
      year: "numeric",
    });
  };

  interface StoredMaterialItem {
    id: string;
    title: string;
    assignmentScope?: AssignmentScope;
    assignedLevels?: ("weak" | "medium" | "strong")[];
    assignedStudents?: number[];
  }

  const [storedNotes, setStoredNotes] = useState<StoredMaterialItem[]>([]);
  const [storedTests, setStoredTests] = useState<StoredMaterialItem[]>([]);

  // Get generating items from context
  const generatingNotes = getGeneratingItemsForTopic(
    decodedCourse,
    decodedTopic,
  ).filter((item) => item.type === "note");
  const generatingTests = getGeneratingItemsForTopic(
    decodedCourse,
    decodedTopic,
  ).filter((item) => item.type === "test");
  const completedItems = getCompletedItemsForTopic(decodedCourse, decodedTopic);

  // Handle completed items - refresh from storage to get the real data
  useEffect(() => {
    if (completedItems.length === 0) return;

    // Refresh materials from localStorage to get actual saved items
    const fetchedNotes = getMaterials({
      courseId: decodedCourse,
      topicName: decodedTopic,
      type: "note",
    }).map((item) => ({
      id: item.id,
      title: item.title,
      assignmentScope: item.assignmentScope,
      assignedLevels: item.assignedLevels,
      assignedStudents: item.assignedStudents,
    }));
    const fetchedTests = getMaterials({
      courseId: decodedCourse,
      topicName: decodedTopic,
      type: "test",
    }).map((item) => ({
      id: item.id,
      title: item.title,
      assignmentScope: item.assignmentScope,
      assignedLevels: item.assignedLevels,
      assignedStudents: item.assignedStudents,
    }));

    setStoredNotes(fetchedNotes);
    setStoredTests(fetchedTests);

    // Clear completed items from context
    completedItems.forEach((item) => {
      clearCompletedItem(item.tempId);
    });
  }, [completedItems, clearCompletedItem, decodedCourse, decodedTopic]);

  // Combine stored and generating items
  const notes = useMemo(() => {
    const generating = generatingNotes.map((item) => ({
      id: item.tempId,
      title: item.title,
      isGenerating: true,
      assignmentScope: undefined as AssignmentScope | undefined,
      assignedLevels: undefined as ("weak" | "medium" | "strong")[] | undefined,
      assignedStudents: undefined as number[] | undefined,
    }));
    const stored = storedNotes.map((item) => ({
      ...item,
      isGenerating: false,
    }));
    return [...stored, ...generating];
  }, [storedNotes, generatingNotes]);

  const tests = useMemo(() => {
    const generating = generatingTests.map((item) => ({
      id: item.tempId,
      title: item.title,
      isGenerating: true,
      assignmentScope: undefined as AssignmentScope | undefined,
      assignedLevels: undefined as ("weak" | "medium" | "strong")[] | undefined,
      assignedStudents: undefined as number[] | undefined,
    }));
    const stored = storedTests.map((item) => ({
      ...item,
      isGenerating: false,
    }));
    return [...stored, ...generating];
  }, [storedTests, generatingTests]);
  const [deleteTarget, setDeleteTarget] = useState<{
    id: string;
    title: string;
    type: "conspect" | "test";
  } | null>(null);
  const isMaterialModalOpen = activeModal === "material";
  const isTestModalOpen = activeModal === "test";
  const isAudienceModalOpen = activeModal === "audience";
  const isDeleteModalOpen = deleteTarget !== null;

  useEffect(() => {
    // Only filter by stable URL parameters to avoid re-fetching on derived value changes
    // Use courseId and topicName as primary filters (from URL)
    // Don't filter by teacherId - materials should be visible regardless of which teacher created them
    // This matches how students see materials (without teacherId filter)
    if (!decodedCourse || !decodedTopic) {
      // Don't fetch until we have the required URL params
      return;
    }
    const fetchedNotes = getMaterials({
      courseId: decodedCourse,
      topicName: decodedTopic,
      type: "note",
    }).map((item) => ({
      id: item.id,
      title: item.title,
      assignmentScope: item.assignmentScope,
      assignedLevels: item.assignedLevels,
      assignedStudents: item.assignedStudents,
    }));
    const fetchedTests = getMaterials({
      courseId: decodedCourse,
      topicName: decodedTopic,
      type: "test",
    }).map((item) => ({
      id: item.id,
      title: item.title,
      assignmentScope: item.assignmentScope,
      assignedLevels: item.assignedLevels,
      assignedStudents: item.assignedStudents,
    }));
    setStoredNotes(fetchedNotes);
    setStoredTests(fetchedTests);
  }, [decodedCourse, decodedTopic]);

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
        setClassStudents(
          response.students.map((student) => student.student_id),
        );
      })
      .catch((error) => {
        console.error(error);
        setClassStudents([]);
      });
  }, [apiTeacherId, apiClassId, subjectName]);

  const handleOpenAudience = (from: "material" | "test") => {
    setPreviousModal(from);
    setActiveModal("audience");
  };

  const handleAudienceSave = (selection: {
    levels: string[];
    students: string[];
  }) => {
    // SelectStudentsModal now returns stable identifiers directly ("weak", "medium", "strong")
    const validLevels: ("weak" | "medium" | "strong")[] = [
      "weak",
      "medium",
      "strong",
    ];
    setAudienceSelection({
      levels: selection.levels.filter(
        (level): level is "weak" | "medium" | "strong" =>
          validLevels.includes(level as "weak" | "medium" | "strong"),
      ),
      students: selection.students
        .map((studentId) => toNumericId(studentId))
        .filter((value): value is number => value !== null),
    });
    // Return to the previous modal
    if (previousModal) {
      setActiveModal(previousModal);
    } else {
      setActiveModal(null);
    }
  };

  const handleDelete = () => {
    if (!deleteTarget) return;
    const success = deleteMaterial(deleteTarget.id);
    if (success) {
      if (deleteTarget.type === "conspect") {
        setStoredNotes((prev) =>
          prev.filter((item) => item.id !== deleteTarget.id),
        );
      } else {
        setStoredTests((prev) =>
          prev.filter((item) => item.id !== deleteTarget.id),
        );
      }
    }
    setDeleteTarget(null);
  };

  return (
    <div className="min-h-screen bg-[#1E73F7] text-slate-900">
      <div className="flex min-h-screen">
        {/* Static sidebar - always shows only "Materials" and "Students" links */}
        <div className="hidden lg:flex">
          <TeacherSidebar
            teacherName={id ? `Вчитель ${id}` : "Вчитель"}
            activeItem="materials"
            onMaterialsClick={() => navigate(`/teacher/${id}`)}
            onStudentsClick={() => navigate(`/teacher/${id}?view=students`)}
          />
        </div>
        <main
          className="flex-1 px-4 py-6 overflow-y-auto lg:px-10 lg:py-10 lg:overflow-visible"
          data-scroll-root="mobile"
        >
          <div className="flex items-center gap-4 mb-6">
            <BackButton fallbackPath={`/teacher/${id}`} />
            <div className="hidden lg:flex">
              <Breadcrumbs
                items={[
                  { label: subjectName || "Предмет", href: `/teacher/${id}` },
                  { label: classLabel || "Клас", href: `/teacher/${id}` },
                  { label: decodedTopic || "Тема" },
                ]}
              />
            </div>
          </div>
          <Panel>
            <div className="grid gap-6 md:grid-cols-4">
              <div>
                <div className="text-xs font-semibold uppercase text-slate-400">
                  Дата
                </div>
                <div className="mt-2 text-sm font-semibold text-slate-900">
                  {formatDate(topicDate)}
                </div>
              </div>
              <div>
                <div className="text-xs font-semibold uppercase text-slate-400">
                  Предмет
                </div>
                <div className="mt-2 text-sm font-semibold text-slate-900">
                  {subjectName}
                </div>
              </div>
              <div>
                <div className="text-xs font-semibold uppercase text-slate-400">
                  Клас
                </div>
                <div className="mt-2 text-sm font-semibold text-slate-900">
                  {classLabel}
                </div>
              </div>
              <div>
                <div className="text-xs font-semibold uppercase text-slate-400">
                  Тема
                </div>
                <div className="mt-2 text-sm font-semibold text-slate-900">
                  {decodedTopic}
                </div>
              </div>
            </div>
          </Panel>
          <div className="mt-6 grid gap-6 lg:mt-8 lg:grid-cols-[1.05fr_0.95fr] overflow-visible">
            <section className="overflow-visible">
              <h2 className="text-lg font-semibold text-white lg:text-xl">
                Конспекти
              </h2>
              <div className="mt-4 space-y-4 overflow-visible">
                {notes.map((item) =>
                  item.isGenerating ? (
                    <Card
                      key={item.id}
                      className="flex items-center justify-between px-5 py-4 transition-all duration-300 ease-in-out opacity-70"
                    >
                      <div className="flex flex-1 items-center gap-3 text-sm font-semibold text-slate-500">
                        <span className="inline-flex h-6 w-6 items-center justify-center rounded-full bg-white shadow-sm">
                          <img src="/src/assets/Vector.svg" alt="" className="h-4 w-4" />
                        </span>
                        {item.title}
                      </div>
                      <div className="flex h-9 w-9 items-center justify-center">
                        <svg
                          className="h-5 w-5 animate-spin text-[#1E73F7]"
                          xmlns="http://www.w3.org/2000/svg"
                          fill="none"
                          viewBox="0 0 24 24"
                        >
                          <circle
                            className="opacity-25"
                            cx="12"
                            cy="12"
                            r="10"
                            stroke="currentColor"
                            strokeWidth="4"
                          />
                          <path
                            className="opacity-75"
                            fill="currentColor"
                            d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                          />
                        </svg>
                      </div>
                    </Card>
                  ) : (
                    <Link
                      key={item.id}
                      to={`/teacher/${id}/note/${courseId}/${classId}/${topicId}/${item.id}`}
                    >
                      <Card
                        className="flex items-center justify-between px-5 py-4 transition-all duration-300 ease-in-out cursor-pointer hover:-translate-y-1 hover:shadow-lg hover:shadow-[#1E73F7]/20 hover:border-[#1E73F7]/30 active:scale-[0.98]"
                      >
                        <div className="flex flex-1 items-center gap-3 text-sm font-semibold text-slate-900">
                          <span className="inline-flex h-6 w-6 items-center justify-center rounded-full bg-white shadow-sm">
                            <img src="/src/assets/Vector.svg" alt="" className="h-4 w-4" />
                          </span>
                          {item.title}
                        </div>
                        <button
                          type="button"
                          onClick={(e) => {
                            e.preventDefault();
                            e.stopPropagation();
                            setDeleteTarget({ id: item.id, title: item.title, type: "conspect" });
                          }}
                          className="flex h-9 w-9 items-center justify-center rounded-full text-slate-400 transition-all duration-200 hover:bg-red-50 hover:text-red-500 hover:scale-110"
                          title="Видалити"
                        >
                          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                            <path d="M3 6h18" />
                            <path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6" />
                            <path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2" />
                          </svg>
                        </button>
                      </Card>
                    </Link>
                  )
                )}
                {notes.map((item) => (
                  <Card
                    key={item.id}
                    className={`px-5 py-4 transition-all duration-300 ease-in-out ${
                      item.isGenerating
                        ? "opacity-70"
                        : "cursor-pointer hover:-translate-y-1 hover:shadow-lg hover:shadow-[#1E73F7]/20 hover:border-[#1E73F7]/30 active:scale-[0.98]"
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      {item.isGenerating ? (
                        <div className="flex flex-1 items-center gap-3 text-sm font-semibold text-slate-500">
                          <span className="inline-flex h-6 w-6 items-center justify-center rounded-full bg-white shadow-sm">
                            <img
                              src="/src/assets/Vector.svg"
                              alt=""
                              className="h-4 w-4"
                            />
                          </span>
                          {item.title}
                        </div>
                      ) : (
                        <Link
                          to={`/teacher/${id}/note/${courseId}/${classId}/${topicId}/${item.id}`}
                          className="flex flex-1 items-center gap-3 text-sm font-semibold text-slate-900"
                        >
                          <span className="inline-flex h-6 w-6 items-center justify-center rounded-full bg-white shadow-sm">
                            <img
                              src="/src/assets/Vector.svg"
                              alt=""
                              className="h-4 w-4"
                            />
                          </span>
                          {item.title}
                        </Link>
                      )}
                      {item.isGenerating ? (
                        <div className="flex h-9 w-9 items-center justify-center">
                          <svg
                            className="h-5 w-5 animate-spin text-[#1E73F7]"
                            xmlns="http://www.w3.org/2000/svg"
                            fill="none"
                            viewBox="0 0 24 24"
                          >
                            <circle
                              className="opacity-25"
                              cx="12"
                              cy="12"
                              r="10"
                              stroke="currentColor"
                              strokeWidth="4"
                            />
                            <path
                              className="opacity-75"
                              fill="currentColor"
                              d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                            />
                          </svg>
                        </div>
                      ) : (
                        <button
                          type="button"
                          onClick={() =>
                            setDeleteTarget({
                              id: item.id,
                              title: item.title,
                              type: "conspect",
                            })
                          }
                          className="flex h-9 w-9 items-center justify-center rounded-full text-slate-400 transition-all duration-200 hover:bg-red-50 hover:text-red-500 hover:scale-110"
                          title="Видалити"
                        >
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
                            <path d="M3 6h18" />
                            <path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6" />
                            <path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2" />
                          </svg>
                        </button>
                      )}
                    </div>
                    {!item.isGenerating && (
                      <div className="mt-3 pl-9">
                        <TargetAudienceIndicator
                          assignmentScope={item.assignmentScope}
                          assignedLevels={item.assignedLevels}
                          assignedStudents={item.assignedStudents}
                          studentCount={classStudents.length}
                          compact
                        />
                      </div>
                    )}
                  </Card>
                ))}
              </div>
              <AddMaterialsCard
                className="mt-4"
                title="Додайте навчальні матеріали"
                buttonLabel="Згенерувати конспект"
                onClick={() => {
                  setAudienceSelection(null);
                  setActiveModal("material");
                }}
              />
            </section>
            <section className="overflow-visible">
              <h2 className="text-lg font-semibold text-white lg:text-xl">
                Тести
              </h2>
              <div className="mt-4 space-y-4 overflow-visible">
                {tests.map((item) => (
                  <Card
                    key={item.id}
                    className={`px-5 py-4 transition-all duration-300 ease-in-out ${
                      item.isGenerating
                        ? "opacity-70"
                        : "cursor-pointer hover:-translate-y-1 hover:shadow-lg hover:shadow-[#1E73F7]/20 hover:border-[#1E73F7]/30 active:scale-[0.98]"
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      {item.isGenerating ? (
                        <div className="flex flex-1 items-center gap-3 text-sm font-semibold text-slate-500">
                          <img
                            src="/src/assets/Group.svg"
                            alt=""
                            className="h-6 w-6 transition-transform duration-300"
                          />
                          {item.title}
                        </div>
                      ) : (
                        <Link
                          to={`/teacher/${id}/test/${item.id}`}
                          className="flex flex-1 items-center gap-3 text-sm font-semibold text-slate-900"
                        >
                          <img
                            src="/src/assets/Group.svg"
                            alt=""
                            className="h-6 w-6 transition-transform duration-300"
                          />
                          {item.title}
                        </Link>
                      )}
                      {item.isGenerating ? (
                        <div className="flex h-9 w-9 items-center justify-center">
                          <svg
                            className="h-5 w-5 animate-spin text-[#1E73F7]"
                            xmlns="http://www.w3.org/2000/svg"
                            fill="none"
                            viewBox="0 0 24 24"
                          >
                            <circle
                              className="opacity-25"
                              cx="12"
                              cy="12"
                              r="10"
                              stroke="currentColor"
                              strokeWidth="4"
                            />
                            <path
                              className="opacity-75"
                              fill="currentColor"
                              d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                            />
                          </svg>
                        </div>
                      ) : (
                        <button
                          type="button"
                          onClick={() =>
                            setDeleteTarget({
                              id: item.id,
                              title: item.title,
                              type: "test",
                            })
                          }
                          className="flex h-9 w-9 items-center justify-center rounded-full text-slate-400 transition-all duration-200 hover:bg-red-50 hover:text-red-500 hover:scale-110"
                          title="Видалити"
                        >
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
                            <path d="M3 6h18" />
                            <path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6" />
                            <path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2" />
                          </svg>
                        </button>
                      )}
                    </div>
                    {!item.isGenerating && (
                      <div className="mt-3 pl-9">
                        <TargetAudienceIndicator
                          assignmentScope={item.assignmentScope}
                          assignedLevels={item.assignedLevels}
                          assignedStudents={item.assignedStudents}
                          studentCount={classStudents.length}
                          compact
                        />
                      </div>
                    )}
                  </Card>
                ))}
              </div>
              <AddMaterialsCard
                className="mt-4"
                title="Додайте навчальні матеріали"
                buttonLabel="Згенерувати тест"
                onClick={() => {
                  setAudienceSelection(null);
                  setActiveModal("test");
                }}
              />
            </section>
          </div>
        </main>
      </div>
      <Modal
        isOpen={isMaterialModalOpen}
        onClose={() => {
          setActiveModal(null);
          setTestError(null);
        }}
        size="xl"
        title="Опишіть тему"
      >
        <GenerateModalContent
          placeholder="Детально опишіть тему"
          value={materialName}
          onChange={(value) => {
            setMaterialName(value);
            if (materialError) {
              setMaterialError(null);
            }
          }}
          primaryLabel="Згенерувати"
          isLoading={false}
          onSecondaryClick={() => handleOpenAudience("material")}
          errorText={materialError ?? undefined}
          onPrimaryClick={() => {
            if (!materialName.trim()) {
              setMaterialError("Напишіть тему");
              return;
            }
            const topicDefinition = materialName.trim();
            const tempId = `generating-note-${Date.now()}`;

            // Close modal immediately
            setActiveModal(null);
            setMaterialName("");
            setMaterialError(null);

            // Start generation in context (runs in background)
            startNoteGeneration({
              tempId,
              title: `Конспект: ${topicDefinition.slice(0, 50)}...`,
              topicDefinition,
              teacherId: id || "",
              apiTeacherId,
              apiClassId,
              subjectName,
              courseId: decodedCourse,
              classLabel,
              topicName: decodedTopic,
              audienceSelection,
            });

            setAudienceSelection(null);
          }}
        />
      </Modal>
      <Modal
        isOpen={isTestModalOpen}
        onClose={() => {
          setActiveModal(null);
          setTestError(null);
        }}
        size="xl"
        title="Опишіть тему"
      >
        <GenerateModalContent
          placeholder="Детально опишіть тему"
          value={testName}
          onChange={(value) => {
            setTestName(value);
            if (testError) {
              setTestError(null);
            }
          }}
          primaryLabel="Згенерувати"
          isLoading={false}
          onSecondaryClick={() => handleOpenAudience("test")}
          errorText={testError ?? undefined}
          onPrimaryClick={() => {
            if (!testName.trim()) {
              setTestError("Напишіть тему");
              return;
            }
            const topicDefinition = testName.trim();
            const tempId = `generating-test-${Date.now()}`;

            // Close modal immediately
            setActiveModal(null);
            setTestName("");
            setTestError(null);

            // Start generation in context (runs in background)
            startTestGeneration({
              tempId,
              title: `Тест: ${topicDefinition.slice(0, 50)}...`,
              topicDefinition,
              teacherId: id || "",
              apiTeacherId,
              apiClassId,
              subjectName,
              courseId: decodedCourse,
              classLabel,
              topicName: decodedTopic,
              audienceSelection,
            });

            setAudienceSelection(null);
          }}
        />
      </Modal>

      <SelectStudentsModal
        isOpen={isAudienceModalOpen}
        onClose={() => {
          if (previousModal) setActiveModal(previousModal);
          else setActiveModal(null);
        }}
        students={classStudents.map((studentId) => ({ id: studentId }))}
        onSave={handleAudienceSave}
        initialLevels={audienceSelection?.levels}
        initialStudents={audienceSelection?.students.map(String)}
      />

      <ConfirmDeleteModal
        isOpen={isDeleteModalOpen}
        onClose={() => setDeleteTarget(null)}
        onConfirm={handleDelete}
        title={deleteTarget?.title ?? ""}
        itemType={deleteTarget?.type ?? "conspect"}
      />
    </div>
  );
};

export default TeacherTopic;
