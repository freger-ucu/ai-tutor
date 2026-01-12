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

const courseLabels: Record<string, string> = {
  "algebra-8": "Алгебра",
  "history-8": "Історія України",
  "ukr-lang-8": "Українська мова",
  "algebra-9": "Алгебра",
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

  const [materialName, setMaterialName] = useState("");
  const [testName, setTestName] = useState("");
  const decodedClass = classId ? decodeURIComponent(classId) : "";
  const decodedTopic = topicId ? decodeURIComponent(topicId) : "";
  const courseLabel = courseId ? courseLabels[courseId] ?? courseId : "";

  const [notes, setNotes] = useState<string[]>([]);
  const [tests, setTests] = useState<string[]>([]);
  const isMaterialModalOpen = activeModal === "material";
  const isTestModalOpen = activeModal === "test";
  const isAudienceModalOpen = activeModal === "audience";

  useEffect(() => {
    const storedNotes = getMaterials({
      teacherId: id,
      courseId,
      className: decodedClass,
      topicName: decodedTopic,
      type: "note",
    }).map((item) => item.title);
    const storedTests = getMaterials({
      teacherId: id,
      courseId,
      className: decodedClass,
      topicName: decodedTopic,
      type: "test",
    }).map((item) => item.title);
    setNotes(storedNotes);
    setTests(storedTests);
  }, [id, courseId, decodedClass, decodedTopic]);

  const handleOpenAudience = (from: "material" | "test") => {
    setPreviousModal(from);
    setActiveModal("audience");
  };

  const handleAudienceSave = (selection: {
    levels: string[];
    students: string[];
  }) => {
    // In a real app, we would store this selection to use when generating
    console.log("Audience selected:", selection);
    // Return to the previous modal
    if (previousModal) {
      setActiveModal(previousModal);
    } else {
      setActiveModal(null);
    }
  };

  return (
    <div className="min-h-screen bg-[#1E73F7] text-slate-900">
      <div className="flex min-h-screen">
        <TeacherSidebar
          teacherName={
            teacher ? `${teacher.firstName} ${teacher.lastName}` : "Вчитель"
          }
          activeItem="materials"
        >
          <div className="space-y-4">
            {notes.map((item) => (
              <div key={item} className="flex items-center gap-3">
                <span className="inline-block h-5 w-5 rounded-md bg-slate-200" />
                <span>{item}</span>
              </div>
            ))}
            {tests.map((item) => (
              <div key={item} className="flex items-center gap-3">
                <span className="inline-block h-5 w-5 rounded-md bg-slate-200" />
                <span>{item}</span>
              </div>
            ))}
          </div>
        </TeacherSidebar>
        <main className="flex-1 px-10 py-10">
          <div className="text-sm font-medium text-white/80">
            {courseLabel} / {decodedClass} / {decodedTopic}
          </div>
          <Panel className="mt-6">
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
                  {decodedClass}
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
                    key={item}
                    className="flex items-center justify-between px-5 py-4"
                  >
                    <div className="flex items-center gap-3 text-sm font-semibold text-slate-900">
                      <span className="inline-block h-6 w-6 rounded-md bg-slate-200" />
                      {item}
                    </div>
                    {/* Link to Note View */}
                    <Link to={`/teacher/${id}/note/${courseId}/${topicId}/${encodeURIComponent(item)}`}>
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
                {tests.map((item, index) => (
                  <Card key={item} className="px-5 py-5">
                    <div className="flex items-center justify-between">
                      <div className="text-sm font-semibold text-slate-900">
                        {item}
                      </div>
                      <Link to={`/teacher/${id}/test/test-${index + 1}`}>
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
          onPrimaryClick={() => {
            if (!materialName.trim()) {
              return;
            }
            const created = addMaterial({
              type: "note",
              title: materialName.trim(),
              teacherId: id,
              courseId,
              className: decodedClass,
              topicName: decodedTopic,
            });
            setNotes((prev) => [...prev, created.title]);
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
          onPrimaryClick={() => {
            if (!testName.trim()) {
              return;
            }
            const created = addMaterial({
              type: "test",
              title: testName.trim(),
              teacherId: id,
              courseId,
              className: decodedClass,
              topicName: decodedTopic,
            });
            setTests((prev) => [...prev, created.title]);
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
        classNameFilter={decodedClass}
        onSave={handleAudienceSave}
      />
    </div>
  );
};

export default TeacherTopic;
