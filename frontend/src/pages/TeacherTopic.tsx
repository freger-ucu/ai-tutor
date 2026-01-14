import { useEffect, useMemo, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { teachers } from "../data/teachers";
import AddMaterialsCard from "../components/AddMaterialsCard";
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
  const teacher = useMemo(
    () => teachers.find((item) => item.id === id),
    [id]
  );
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
  const apiTeacherId = teacher?.apiId ?? toNumericId(id) ?? 0;
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
      className: classLabel,
      topicName: decodedTopic,
      type: "note",
    }).map((item) => ({ id: item.id, title: item.title }));
    const storedTests = getMaterials({
      teacherId: id,
      courseId: decodedCourse,
      className: classLabel,
      topicName: decodedTopic,
      type: "test",
    }).map((item) => ({ id: item.id, title: item.title }));
    setNotes(storedNotes);
    setTests(storedTests);
  }, [id, decodedCourse, classLabel, decodedTopic]);

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

  const buildFallbackNote = (topicDefinition: string) => {
    const fallbackTitle =
      topicDefinition.trim() || decodedTopic || "Конспект";
    return {
      title: `Конспект. ${fallbackTitle}`,
      contents: topicDefinition.trim() || `Матеріали для теми: ${fallbackTitle}`,
      teacher_notes: "Створено локально (без відповіді сервера).",
    };
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
            teacher ? `${teacher.firstName} ${teacher.lastName}` : "Вчитель"
          }
          activeItem="materials"
          afterPrimaryNav={
            <Link
              to={backToClassHref}
              className="flex w-full items-start justify-start gap-3 rounded-2xl px-4 py-3 text-sm font-medium text-slate-800 hover:bg-slate-100"
            >
              <span className="mt-0.5 inline-block h-5 w-5 rounded-md bg-slate-200" />
              <span>Назад до класу</span>
            </Link>
          }
        >
          <div className="space-y-4">
            {notes.map((item) => (
              <Link
                key={item.id}
                to={`/teacher/${id}/note/${courseId}/${classId}/${topicId}/${item.id}`}
                className="flex w-full items-start justify-start gap-3 rounded-2xl px-4 py-3 text-slate-700 hover:bg-slate-100"
              >
                <span className="mt-0.5 inline-block h-5 w-5 rounded-md bg-slate-200" />
                <span>{item.title}</span>
              </Link>
            ))}
            {tests.map((item) => (
              <Link
                key={item.id}
                to={`/teacher/${id}/test/${item.id}`}
                className="flex w-full items-start justify-start gap-3 rounded-2xl px-4 py-3 text-slate-700 hover:bg-slate-100"
              >
                <span className="mt-0.5 inline-block h-5 w-5 rounded-md bg-slate-200" />
                <span>{item.title}</span>
              </Link>
            ))}
          </div>
        </TeacherSidebar>
        <main className="flex-1 px-10 py-10">
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
              <div className="flex items-center justify-start md:justify-end">
                <PillButton
                  label="Приєднатись"
                  size="md"
                  className="rounded-2xl"
                  icon={
                    <span className="inline-block h-5 w-5 rounded-full bg-[#1E73F7]/20" />
                  }
                />
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
                      <span className="inline-block h-6 w-6 rounded-md bg-slate-200" />
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
                onClick={() => setActiveModal("material")}
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
                      {[0, 1, 2, 3].map((idx) => (
                        <div
                          key={idx}
                          className="h-8 w-8 rounded-full border-2 border-white bg-slate-200"
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
        onClose={() => setActiveModal(null)}
        size="xl"
        title="Опишіть тему"
      >
        <GenerateModalContent
          placeholder="Детально опишіть тему"
          value={materialName}
          onChange={setMaterialName}
          primaryLabel="Згенерувати"
          onSecondaryClick={() => handleOpenAudience("material")}
          onPrimaryClick={async () => {
            if (!materialName.trim() || isGeneratingMaterial) {
              return;
            }
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

              const payload = response?.title
                ? response
                : buildFallbackNote(topicDefinition);

              const created = addMaterial({
                type: "note",
                title: payload.title,
                content: payload.contents,
                teacherNotes: payload.teacher_notes,
                teacherId: id,
                courseId: decodedCourse,
                className: classLabel,
                topicName: decodedTopic,
              });
              setNotes((prev) => [
                ...prev,
                { id: created.id, title: created.title },
              ]);
            } catch (error) {
              console.error(error);
              const fallback = buildFallbackNote(materialName.trim());
              const created = addMaterial({
                type: "note",
                title: fallback.title,
                content: fallback.contents,
                teacherNotes: fallback.teacher_notes,
                teacherId: id,
                courseId: decodedCourse,
                className: classLabel,
                topicName: decodedTopic,
              });
              setNotes((prev) => [
                ...prev,
                { id: created.id, title: created.title },
              ]);
            } finally {
              setIsGeneratingMaterial(false);
            }
            setActiveModal(null);
            setMaterialName("");
          }}
        />
      </Modal>
      <Modal
        isOpen={isTestModalOpen}
        onClose={() => setActiveModal(null)}
        size="xl"
        title="Опишіть тему"
      >
        <GenerateModalContent
          placeholder="Детально опишіть тему"
          value={testName}
          onChange={setTestName}
          primaryLabel="Згенерувати"
          onSecondaryClick={() => handleOpenAudience("test")}
          onPrimaryClick={async () => {
            if (!testName.trim() || isGeneratingTest) {
              return;
            }
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
                className: classLabel,
                topicName: decodedTopic,
              });
              setTests((prev) => [
                ...prev,
                { id: created.id, title: created.title },
              ]);
            } catch (error) {
              console.error(error);
              const fallback = buildFallbackTest(testName.trim());
              const created = addMaterial({
                type: "test",
                title: fallback.title,
                questions: fallback.questions,
                teacherId: id,
                courseId: decodedCourse,
                className: classLabel,
                topicName: decodedTopic,
              });
              setTests((prev) => [
                ...prev,
                { id: created.id, title: created.title },
              ]);
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
        classNameFilter={classLabel}
        onSave={handleAudienceSave}
      />
    </div>
  );
};

export default TeacherTopic;
