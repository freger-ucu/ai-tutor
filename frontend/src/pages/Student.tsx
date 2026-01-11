import { getMaterials } from "../data/materialsStorage";

const Student = () => {
  const materials = getMaterials();
  const notes = materials.filter((item) => item.type === "note");
  const tests = materials.filter((item) => item.type === "test");

  return (
    <div className="min-h-screen bg-[#1E73F7] px-8 py-10 text-white">
      <h1 className="text-3xl font-semibold">Я Студент</h1>
      <div className="mt-8 grid gap-8 md:grid-cols-2">
        <section>
          <h2 className="text-xl font-semibold">Конспекти</h2>
          <div className="mt-4 space-y-3">
            {notes.length ? (
              notes.map((item) => (
                <div
                  key={item.id}
                  className="rounded-2xl bg-white px-4 py-3 text-sm font-medium text-slate-900"
                >
                  {item.title}
                </div>
              ))
            ) : (
              <div className="text-sm text-white/70">
                Немає збережених конспектів
              </div>
            )}
          </div>
        </section>
        <section>
          <h2 className="text-xl font-semibold">Тести</h2>
          <div className="mt-4 space-y-3">
            {tests.length ? (
              tests.map((item) => (
                <div
                  key={item.id}
                  className="rounded-2xl bg-white px-4 py-3 text-sm font-medium text-slate-900"
                >
                  {item.title}
                </div>
              ))
            ) : (
              <div className="text-sm text-white/70">
                Немає збережених тестів
              </div>
            )}
          </div>
        </section>
      </div>
    </div>
  );
};

export default Student;
