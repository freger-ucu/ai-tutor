import { useEffect, useMemo, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { students } from "../data/students";
import Card from "../components/Card";
import Panel from "../components/Panel";
import PillButton from "../components/PillButton";
import { getMaterials } from "../data/materialsStorage";

const courseLabels: Record<string, string> = {
  "algebra-8": "Алгебра",
  "history-8": "Історія України",
  "ukr-lang-8": "Українська мова",
  "algebra-9": "Алгебра",
  "history-9": "Історія України",
  "ukr-lang-9": "Українська мова",
};

const StudentTopic = () => {
  const { studentId, courseId, topicId } = useParams();
  
  const student = useMemo(
    () => students.find((s) => s.id === studentId),
    [studentId]
  );

  const decodedTopic = topicId ? decodeURIComponent(topicId) : "";
  const courseLabel = courseId ? courseLabels[courseId] ?? courseId : "";
  
  const [notes, setNotes] = useState<string[]>([]);
  const [tests, setTests] = useState<{id: string, title: string}[]>([]);

  useEffect(() => {
    if (!student) return;

    const materials = getMaterials({
        courseId,
        className: student.className,
        topicName: decodedTopic,
    });

    const storedNotes = materials
        .filter(m => m.type === "note")
        .map(m => m.title);
        
    const storedTests = materials
        .filter(m => m.type === "test")
        .map(m => ({ id: m.id, title: m.title }));

    setNotes(storedNotes);
    setTests(storedTests);
  }, [student, courseId, decodedTopic]);

  if (!student) {
    return (
        <div className="flex min-h-screen items-center justify-center bg-[#1E73F7]">
          <div className="text-xl text-white">Учня не знайдено</div>
        </div>
      );
  }

  return (
    <div className="min-h-screen bg-[#1E73F7] text-slate-900">
      <div className="flex min-h-screen">
        {/* Sidebar */}
        <aside className="fixed left-0 top-0 h-screen w-64 bg-white px-6 py-8 flex flex-col z-10">
          <div className="flex items-center gap-3">
            <div
                className="h-10 w-10 overflow-hidden rounded-full bg-slate-200"
                style={{
                  backgroundImage: "url('https://images.unsplash.com/photo-1599566150163-29194dcaad36?ixlib=rb-4.0.3&auto=format&fit=crop&w=200&q=80')",
                  backgroundSize: "cover",
                }}
             />
            <div>
              <div className="text-base font-semibold text-slate-900">
                {student.firstName} {student.lastName}
              </div>
              <div className="text-xs text-slate-500">Клас: {student.className}</div>
            </div>
          </div>

          <div className="mt-8">
            <Link
              to={`/student/${studentId}`}
              className="flex items-center gap-2 text-sm text-slate-500 hover:text-slate-700"
            >
              ← На головну
            </Link>
          </div>
        </aside>

        <main className="ml-64 flex-1 px-10 py-10 w-full">
           <div className="text-sm font-medium text-white/80">
            {courseLabel} / {decodedTopic}
          </div>

          <Panel className="mt-6">
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-2xl font-bold text-slate-900">{decodedTopic}</h1>
                    <div className="mt-1 text-sm text-slate-500">{courseLabel}</div>
                </div>
            </div>
          </Panel>

          <div className="mt-8 grid gap-8 lg:grid-cols-[1.05fr_0.95fr]">
            <section>
              <h2 className="text-xl font-semibold text-white">Конспекти</h2>
              <div className="mt-4 space-y-4">
                {notes.length > 0 ? notes.map((item) => (
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
                )) : (
                     <div className="rounded-2xl border border-white/10 px-6 py-8 text-center text-sm text-white/40">
                        Немає конспектів
                    </div>
                )}
              </div>
            </section>

            <section>
              <h2 className="text-xl font-semibold text-white">Тести</h2>
              <div className="mt-4 space-y-4">
                {tests.length > 0 ? tests.map((item) => (
                  <Card key={item.id} className="px-5 py-5">
                    <div className="flex items-center justify-between">
                      <div className="text-sm font-semibold text-slate-900">
                        {item.title}
                      </div>
                       {/* Pass the test ID to the route */}
                      <Link to={`/student/${studentId}/test/${item.id}`}>
                        <PillButton label="Пройти тест" />
                      </Link>
                    </div>
                    <div className="mt-4 text-sm text-slate-700">Оцінка: -</div>
                  </Card>
                )) : (
                     <div className="rounded-2xl border border-white/10 px-6 py-8 text-center text-sm text-white/40">
                        Немає тестів
                    </div>
                )}
              </div>
            </section>
          </div>
        </main>
      </div>
    </div>
  );
};

export default StudentTopic;
