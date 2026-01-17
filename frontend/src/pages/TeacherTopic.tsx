import { useEffect, useState } from "react";
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
import { addMaterial, deleteMaterial, getMaterials } from "../data/materialsStorage";
import {
  generateNotesByLevel,
  generateNotesIndividual,
  generateTest,
  getTeacherStudents,
} from "../api/teacher";
import { classIdToLabel } from "../data/classUtils";
import { toNumericId } from "../api/idUtils";

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
  const [activeModal, setActiveModal] = useState<"material" | "test" | "audience" | null>(
    null
  );
  // Keep track of which flow opened the audience selector
  const [previousModal, setPreviousModal] = useState<"material" | "test" | null>(
    null
  );
  const [audienceSelection, setAudienceSelection] = useState<{
    levels: ("weak" | "medium" | "strong")[];
    students: number[];
  } | null>(null);

  const [materialName, setMaterialName] = useState("");
  const [testName, setTestName] = useState("");
  const [isGeneratingMaterial, setIsGeneratingMaterial] = useState(false);
  const [isGeneratingTest, setIsGeneratingTest] = useState(false);
  const [materialGenerationStarted, setMaterialGenerationStarted] = useState(false);
  const [testGenerationStarted, setTestGenerationStarted] = useState(false);
  const [materialError, setMaterialError] = useState<string | null>(null);
  const [classStudents, setClassStudents] = useState<number[]>([]);
  const decodedClassId = classId ? Number(decodeURIComponent(classId)) : null;
  const decodedTopic = topicId ? decodeURIComponent(topicId) : "";
  const decodedCourse = courseId ? decodeURIComponent(courseId) : "";
  const courseLabel = decodedCourse
    ? courseLabels[decodedCourse] ?? decodedCourse
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

  const [notes, setNotes] = useState<{ id: string; title: string }[]>([]);
  const [tests, setTests] = useState<{ id: string; title: string }[]>([]);
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
    const storedNotes = getMaterials({
      teacherId: id,
      courseId: decodedCourse,
      subject: subjectName,
      classId: apiClassId || undefined,
      className: classLabel,
      topicName: decodedTopic,
      type: "note",
    }).map((item) => ({ id: item.id, title: item.title }));
    const storedTests = getMaterials({
      teacherId: id,
      courseId: decodedCourse,
      subject: subjectName,
      classId: apiClassId || undefined,
      className: classLabel,
      topicName: decodedTopic,
      type: "test",
    }).map((item) => ({ id: item.id, title: item.title }));
    setNotes(storedNotes);
    setTests(storedTests);
  }, [id, decodedCourse, classLabel, decodedTopic, apiClassId, subjectName]);

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

  const handleOpenAudience = (from: "material" | "test") => {
    setPreviousModal(from);
    setActiveModal("audience");
  };

  const handleAudienceSave = (selection: {
    levels: string[];
    students: string[];
  }) => {
    // SelectStudentsModal now returns stable identifiers directly ("weak", "medium", "strong")
    const validLevels: ("weak" | "medium" | "strong")[] = ["weak", "medium", "strong"];
    setAudienceSelection({
      levels: selection.levels.filter(
        (level): level is "weak" | "medium" | "strong" => validLevels.includes(level as "weak" | "medium" | "strong")
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
        setNotes((prev) => prev.filter((item) => item.id !== deleteTarget.id));
      } else {
        setTests((prev) => prev.filter((item) => item.id !== deleteTarget.id));
      }
    }
    setDeleteTarget(null);
  };

  const buildFallbackTest = (topicDefinition: string) => {
    const fallbackTitle =
      topicDefinition.trim() || decodedTopic || "Тест";
    return {
      title: `Тест. ${fallbackTitle}`,
      questions: [
        {
          question: `Запитання за темою: ${fallbackTitle}`,
          type: "single_choice",
          difficulty: "easy",
          answer_options: [
            { answer: "Правильна відповідь", correct: true },
            { answer: "Варіант 2", correct: false },
            { answer: "Варіант 3", correct: false },
            { answer: "Варіант 4", correct: false },
          ],
          explanation:
            "Це демо-запитання. Додайте серверну генерацію для реальних тестів.",
          topic: fallbackTitle,
          subtopics: [],
        },
      ],
    };
  };

  return (
    <div className="min-h-screen bg-[#1E73F7] text-slate-900">
      <div className="flex min-h-screen">
        {/* Static sidebar - always shows only "Materials" and "Students" links */}
        <TeacherSidebar
          teacherName={id ? `Вчитель ${id}` : "Вчитель"}
          activeItem="materials"
          onMaterialsClick={() => navigate(`/teacher/${id}`)}
          onStudentsClick={() => navigate(`/teacher/${id}?view=students`)}
        />
        <main className="flex-1 px-10 py-10">
          <div className="flex items-center gap-4 mb-6">
            <BackButton fallbackPath={`/teacher/${id}`} />
            <Breadcrumbs
              items={[
                { label: "Матеріали", href: `/teacher/${id}` },
                { label: `${subjectName}. ${classLabel}. id-${decodedClassId}` || "Клас", href: `/teacher/${id}` },
                { label: decodedTopic || "Тема" },
              ]}
            />
          </div>
          <Panel>
            <div className="grid gap-6 md:grid-cols-[1fr_1fr_1fr_auto]">
              <div>
                <div className="text-xs font-semibold uppercase text-slate-400">
                  Дата
                </div>
                <div className="mt-2 text-sm font-semibold text-slate-900">
                  22 вересня 2025
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
          <div className="mt-8 grid gap-8 lg:grid-cols-[1.05fr_0.95fr] overflow-visible">
            <section className="overflow-visible">
              <h2 className="text-xl font-semibold text-white">Конспекти</h2>
              <div className="mt-4 space-y-4 overflow-visible">
                {notes.map((item) => (
                  <Card
                    key={item.id}
                    className="flex items-center justify-between px-5 py-4 cursor-pointer transition-all duration-300 ease-in-out hover:-translate-y-1 hover:shadow-lg hover:shadow-[#1E73F7]/20 hover:border-[#1E73F7]/30 active:scale-[0.98]"
                  >
                    <Link
                      to={`/teacher/${id}/note/${courseId}/${classId}/${topicId}/${item.id}`}
                      className="flex flex-1 items-center gap-3 text-sm font-semibold text-slate-900"
                    >
                      <span className="inline-flex h-6 w-6 items-center justify-center rounded-full bg-[#1E73F7]/15 transition-all duration-300 group-hover:bg-[#1E73F7]/25">
                        <img src="/src/assets/Vector.svg" alt="" className="h-4 w-5" />
                      </span>
                      {item.title}
                    </Link>
                    <button
                      type="button"
                      onClick={() => setDeleteTarget({ id: item.id, title: item.title, type: "conspect" })}
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
                ))}
              </div>
              <AddMaterialsCard
                className="mt-4"
                title="Додайте навчальні матеріали"
                buttonLabel="Згенерувати конспект"
                onClick={() => {
                  setMaterialError(null);
                  setAudienceSelection(null);
                  setActiveModal("material");
                }}
              />
            </section>
            <section className="overflow-visible">
              <h2 className="text-xl font-semibold text-white">Тести</h2>
              <div className="mt-4 space-y-4 overflow-visible">
                {tests.map((item) => (
                  <Card
                    key={item.id}
                    className="flex items-center justify-between px-5 py-4 cursor-pointer transition-all duration-300 ease-in-out hover:-translate-y-1 hover:shadow-lg hover:shadow-[#1E73F7]/20 hover:border-[#1E73F7]/30 active:scale-[0.98]"
                  >
                    <Link
                      to={`/teacher/${id}/test/${item.id}`}
                      className="flex flex-1 items-center gap-3 text-sm font-semibold text-slate-900"
                    >
                      <img src="/src/assets/Group.svg" alt="" className="h-6 w-6 transition-transform duration-300" />
                      {item.title}
                    </Link>
                    <button
                      type="button"
                      onClick={() => setDeleteTarget({ id: item.id, title: item.title, type: "test" })}
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
          setMaterialGenerationStarted(false);
        }}
        size="xl"
        title="Опишіть тему"
      >
        <div className="space-y-4">
          {materialError && (
            <div className="rounded-2xl bg-red-50 px-4 py-3 text-sm text-red-700">
              {materialError}
            </div>
          )}
          <GenerateModalContent
            placeholder="Детально опишіть тему"
            value={materialName}
            onChange={(value) => {
              setMaterialName(value);
              if (materialError) {
                setMaterialError(null);
              }
            }}
            primaryLabel={isGeneratingMaterial ? "Генерується..." : "Згенерувати"}
            isLoading={isGeneratingMaterial}
            onSecondaryClick={() => handleOpenAudience("material")}
            secondaryDisabled={materialGenerationStarted || isGeneratingMaterial}
            onPrimaryClick={async () => {
              if (!materialName.trim() || isGeneratingMaterial) {
                return;
              }
              setMaterialError(null);
              setMaterialGenerationStarted(true);
              setIsGeneratingMaterial(true);
              try {
                const topicDefinition = materialName.trim();

                // PRIORITY ORDER (highest to lowest):
                // 1. Levels selected → assign to all students in those levels
                // 2. Individual students selected → assign only to those students
                // 3. No selection → assign to entire class (default)
                const hasLevels = audienceSelection?.levels && audienceSelection.levels.length > 0;
                const hasStudents = audienceSelection?.students && audienceSelection.students.length > 0;

                let response;
                let assignmentScope: "class" | "levels" | "students";
                let assignedLevels: ("weak" | "medium" | "strong")[] | undefined;
                let assignedStudents: number[] | undefined;

                if (hasLevels) {
                  // PRIORITY 1: Level assignment (overrides any student selection)
                  assignmentScope = "levels";
                  assignedLevels = audienceSelection.levels;
                  assignedStudents = undefined; // Explicitly clear
                  response = await generateNotesByLevel({
                    class_id: apiClassId,
                    teacher_id: apiTeacherId,
                    subject: subjectName,
                    level_list: audienceSelection.levels,
                    topic_definition: topicDefinition,
                  });
                } else if (hasStudents) {
                  // PRIORITY 2: Individual student assignment
                  assignmentScope = "students";
                  assignedLevels = undefined; // Explicitly clear
                  assignedStudents = audienceSelection.students;
                  response = await generateNotesIndividual({
                    class_id: apiClassId,
                    teacher_id: apiTeacherId,
                    subject: subjectName,
                    student_list: audienceSelection.students,
                    topic_definition: topicDefinition,
                  });
                } else {
                  // PRIORITY 3: No selection → entire class (all levels)
                  assignmentScope = "class";
                  assignedLevels = undefined;
                  assignedStudents = undefined;
                  response = await generateNotesByLevel({
                    class_id: apiClassId,
                    teacher_id: apiTeacherId,
                    subject: subjectName,
                    level_list: ["weak", "medium", "strong"],
                    topic_definition: topicDefinition,
                  });
                }

                if (!response?.title || !response?.contents) {
                  throw new Error("Invalid notes response");
                }

                const created = addMaterial({
                  type: "note",
                  title: response.title,
                  content: response.contents,
                  teacherNotes: response.teacher_notes,
                  // Save sources from backend response (visible only to teachers)
                  sources: response.sources,
                  teacherId: id,
                  courseId: decodedCourse,
                  subject: subjectName,
                  classId: apiClassId || undefined,
                  className: classLabel,
                  topicName: decodedTopic,
                  assignmentScope,
                  assignedLevels,
                  assignedStudents,
                });
                setNotes((prev) => [
                  ...prev,
                  { id: created.id, title: created.title },
                ]);
                setActiveModal(null);
                setMaterialName("");
                if (id && courseId && classId && topicId) {
                  navigate(
                    `/teacher/${id}/note/${courseId}/${classId}/${topicId}/${created.id}`
                  );
                }
              } catch (error) {
                console.error(error);
                setMaterialError(
                  "Не вдалося згенерувати конспект. Спробуйте ще раз."
                );
              } finally {
                setIsGeneratingMaterial(false);
              }
            }}
          />
        </div>
      </Modal>
      <Modal
        isOpen={isTestModalOpen}
        onClose={() => {
          setActiveModal(null);
          setTestGenerationStarted(false);
        }}
        size="xl"
        title="Опишіть тему"
      >
        <GenerateModalContent
          placeholder="Детально опишіть тему"
          value={testName}
          onChange={setTestName}
          primaryLabel={isGeneratingTest ? "Генерується..." : "Згенерувати"}
          isLoading={isGeneratingTest}
          onSecondaryClick={() => handleOpenAudience("test")}
          secondaryDisabled={testGenerationStarted || isGeneratingTest}
          onPrimaryClick={async () => {
            if (!testName.trim() || isGeneratingTest) {
              return;
            }
            setTestGenerationStarted(true);
            setIsGeneratingTest(true);

            // PRIORITY ORDER (highest to lowest):
            // 1. Levels selected → assign to all students in those levels
            // 2. Individual students selected → assign only to those students
            // 3. No selection → assign to entire class (default)
            const hasLevels = audienceSelection?.levels && audienceSelection.levels.length > 0;
            const hasStudents = audienceSelection?.students && audienceSelection.students.length > 0;

            let assignmentScope: "class" | "levels" | "students";
            let assignedLevels: ("weak" | "medium" | "strong")[] | undefined;
            let assignedStudents: number[] | undefined;

            if (hasLevels) {
              assignmentScope = "levels";
              assignedLevels = audienceSelection.levels;
              assignedStudents = undefined;
            } else if (hasStudents) {
              assignmentScope = "students";
              assignedLevels = undefined;
              assignedStudents = audienceSelection.students;
            } else {
              assignmentScope = "class";
              assignedLevels = undefined;
              assignedStudents = undefined;
            }

            try {
              const topicDefinition = testName.trim();
              const response = await generateTest({
                class_id: apiClassId,
                teacher_id: apiTeacherId,
                subject: subjectName,
                topic_definition: topicDefinition,
              });
              const payload = response?.title
                ? response
                : buildFallbackTest(topicDefinition);
              const created = addMaterial({
                type: "test",
                title: payload.title,
                questions: payload.questions,
                teacherId: id,
                courseId: decodedCourse,
                subject: subjectName,
                classId: apiClassId || undefined,
                className: classLabel,
                topicName: decodedTopic,
                assignmentScope,
                assignedLevels,
                assignedStudents,
              });
              setTests((prev) => [
                ...prev,
                { id: created.id, title: created.title },
              ]);
              if (id) {
                navigate(`/teacher/${id}/test/${created.id}`);
              }
            } catch (error) {
              console.error(error);
              const fallback = buildFallbackTest(testName.trim());
              const created = addMaterial({
                type: "test",
                title: fallback.title,
                questions: fallback.questions,
                teacherId: id,
                courseId: decodedCourse,
                subject: subjectName,
                classId: apiClassId || undefined,
                className: classLabel,
                topicName: decodedTopic,
                assignmentScope,
                assignedLevels,
                assignedStudents,
              });
              setTests((prev) => [
                ...prev,
                { id: created.id, title: created.title },
              ]);
              if (id) {
                navigate(`/teacher/${id}/test/${created.id}`);
              }
            } finally {
              setIsGeneratingTest(false);
            }
            setActiveModal(null);
            setTestName("");
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
