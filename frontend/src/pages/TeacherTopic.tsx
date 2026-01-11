import { useEffect, useMemo, useState } from "react";
import { useParams } from "react-router-dom";
import { teachers } from "../data/teachers";
import AddMaterialsCard from "../components/AddMaterialsCard";
import Card from "../components/Card";
import GenerateModalContent from "../components/GenerateModalContent";
import Modal from "../components/Modal";
import Panel from "../components/Panel";
import PillButton from "../components/PillButton";
import TeacherSidebar from "../components/TeacherSidebar";
import { addMaterial, getMaterials } from "../data/materialsStorage";

const courseLabels: Record<string, string> = {
  "world-lit-8": "Зарубіжна література",
  "ukr-lang-8": "Українська мова",
  "ukr-lit-8": "Українська література",
  "world-lit-9": "Зарубіжна література",
  "ukr-lang-9": "Українська мова",
  "ukr-lit-9": "Українська література",
};

const TeacherTopic = () => {
  const { id, courseId, classId, topicId } = useParams();
  const teacher = useMemo(
    () => teachers.find((item) => item.id === id),
    [id]
  );
  const [activeModal, setActiveModal] = useState<"material" | "test" | null>(
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
                    <PillButton label="Переглянути" />
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
                  <Card key={item} className="px-5 py-5">
                    <div className="flex items-center justify-between">
                      <div className="text-sm font-semibold text-slate-900">
                        {item}
                      </div>
                      <PillButton label="Переглянути" />
                    </div>
                    <div className="mt-4 text-sm text-slate-700">Учнів 20</div>
                    <div className="mt-3 flex -space-x-2">
                      {[0, 1, 2, 3].map((index) => (
                        <div
                          key={index}
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
    </div>
  );
};

export default TeacherTopic;
