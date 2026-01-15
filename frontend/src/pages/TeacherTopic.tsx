import { useEffect, useState, useMemo } from "react";
import { useParams, Link, useNavigate } from "react-router-dom";
import AddMaterialsCard from "../components/AddMaterialsCard";
import BackButton from "../components/BackButton";
import Breadcrumbs from "../components/Breadcrumbs";
import Card from "../components/Card";
import GenerateModalContent from "../components/GenerateModalContent";
import Modal from "../components/Modal";
import Panel from "../components/Panel";
import PillButton from "../components/PillButton";
import SelectStudentsModal from "../components/SelectStudentsModal";
import TeacherSidebar from "../components/TeacherSidebar";
import { addMaterial, getMaterials } from "../data/materialsStorage";
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
  const backToClassHref = id ? `/teacher/${id}` : "/";
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
  const isMaterialModalOpen = activeModal === "material";
  const isTestModalOpen = activeModal === "test";
  const isAudienceModalOpen = activeModal === "audience";

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
    const levelMap: Record<string, "weak" | "medium" | "strong"> = {
      Високий: "strong",
      Середній: "medium",
      Низький: "weak",
    };
    setAudienceSelection({
      levels: selection.levels
        .map((level) => levelMap[level])
        .filter(Boolean),
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
        <TeacherSidebar
          teacherName={
            id ? `Вчитель ${id}` : "Вчитель"
          }
          activeItem="materials"
        >
          <div className="space-y-4">
            {notes.map((item) => (
              <Link
                key={item.id}
                to={`/teacher/${id}/note/${courseId}/${classId}/${topicId}/${item.id}`}
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
                to={`/teacher/${id}/test/${item.id}`}
                className="flex items-center gap-3 rounded-xl px-4 py-3 text-slate-700 hover:bg-slate-50"
              >
                <img src="/src/assets/Group.svg" alt="" className="h-4 w-4" />
                Тест. {item.title}
              </Link>
            ))}
          </div>
        </TeacherSidebar>
        <main className="flex-1 px-10 py-10">
          <div className="flex items-center gap-4 mb-6">
            <BackButton fallbackPath={`/teacher/${id}`} />
            <Breadcrumbs
              items={[
                { label: "Матеріали", href: `/teacher/${id}` },
                { label: classLabel || "Клас", href: `/teacher/${id}` },
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
          <div className="mt-8 grid gap-8 lg:grid-cols-[1.05fr_0.95fr]">
            <section>
              <h2 className="text-xl font-semibold text-white">Конспекти</h2>
              <div className="mt-4 space-y-4">
                {notes.map((item) => (
                  <Card
                    key={item.id}
                    className="flex items-center justify-between px-5 py-4"
                  >
                    <div className="flex items-center gap-3 text-sm font-semibold text-slate-900">
                      <span className="inline-flex h-6 w-6 items-center justify-center rounded-full bg-[#1E73F7]/15 text-[#1E73F7]">
                        <svg width="14" height="16" viewBox="0 0 16 20" fill="currentColor">
                          <path d="M10 0H2C0.9 0 0 0.9 0 2V18C0 19.1 0.9 20 2 20H14C15.1 20 16 19.1 16 18V6L10 0ZM14 18H2V2H9V7H14V18Z" opacity="0.5"/>
                          <path d="M10 0H2C0.9 0 0 0.9 0 2V18C0 19.1 0.9 20 2 20H14C15.1 20 16 19.1 16 18V6L10 0ZM9 7V2L14 7H9Z"/>
                        </svg>
                      </span>
                      {item.title}
                    </div>
                    {/* Link to Note View */}
                    <Link
                      to={`/teacher/${id}/note/${courseId}/${classId}/${topicId}/${item.id}`}
                    >
                        <PillButton label="Переглянути" />
                    </Link>
                  </Card>
                ))}
              </div>
              <AddMaterialsCard
                className="mt-4"
                title="Додайте навчальні матеріали"
                buttonLabel="Згенерувати конспект"
                onClick={() => {
                  setMaterialError(null);
                  setActiveModal("material");
                }}
              />
            </section>
            <section>
              <h2 className="text-xl font-semibold text-white">Тести</h2>
              <div className="mt-4 space-y-4">
                {tests.map((item) => (
                  <Card key={item.id} className="px-5 py-5">
                    <div className="flex items-center justify-between">
                      <div className="text-sm font-semibold text-slate-900">
                        {item.title}
                      </div>
                      <Link to={`/teacher/${id}/test/${item.id}`}>
                        <PillButton label="Переглянути" />
                      </Link>
                    </div>
                    <div className="mt-4 text-sm text-slate-700">Учнів 20</div>
                    <div className="mt-3 flex -space-x-2">
                      {[
                        "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcR7bjVWye1D9XdNJzLXjVI84qCNzt77U0uCxQ&s",
                        "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcR5yYM7PLjs7AXxqJg_RSgtk2qVFdgnHP7k-1xfXoYiFA&s",
                        "https://thumbs.dreamstime.com/b/high-school-boy-handsome-writing-class-work-31576857.jpg",
                        "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTYrDIbET-W6GdhKsrq_n6bNnY86FDX8N_6uA&s",
                      ].map((url, idx) => (
                        <img
                          key={idx}
                          src={url}
                          alt=""
                          className="h-8 w-8 rounded-full border-2 border-white object-cover"
                        />
                      ))}
                    </div>
                  </Card>
                ))}
              </div>
              <AddMaterialsCard
                className="mt-4"
                title="Додайте навчальні матеріали"
                buttonLabel="Згенерувати тест"
                onClick={() => setActiveModal("test")}
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
                const response =
                  audienceSelection?.students?.length
                    ? await generateNotesIndividual({
                        class_id: apiClassId,
                        teacher_id: apiTeacherId,
                        subject: subjectName,
                        student_list: audienceSelection.students,
                        topic_definition: topicDefinition,
                      })
                    : await generateNotesByLevel({
                        class_id: apiClassId,
                        teacher_id: apiTeacherId,
                        subject: subjectName,
                        level_list:
                          audienceSelection?.levels?.length
                            ? audienceSelection.levels
                            : ["weak", "medium", "strong"],
                        topic_definition: topicDefinition,
                      });

                if (!response?.title || !response?.contents) {
                  throw new Error("Invalid notes response");
                }

                const created = addMaterial({
                  type: "note",
                  title: response.title,
                  content: response.contents,
                  teacherNotes: response.teacher_notes,
                  teacherId: id,
                  courseId: decodedCourse,
                  subject: subjectName,
                  classId: apiClassId || undefined,
                  className: classLabel,
                  topicName: decodedTopic,
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
    </div>
  );
};

export default TeacherTopic;
