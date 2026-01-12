import { useState, useMemo } from "react";
import { useParams } from "react-router-dom";
import { students } from "../data/students";
import { getTopics } from "../data/materialsStorage";
import PillButton from "../components/PillButton";

const Subjects = [
  { id: "algebra", label: "Алгебра", icon: <span className="text-xl">√x</span> },
  {
    id: "history",
    label: "Історія України",
    icon: (
      <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
        <path d="M5 16L3 5L8.5 10L12 4L15.5 10L21 5L19 16H5M19 19C19 19.6 18.6 20 18 20H6C5.4 20 5 19.6 5 19V18H19V19Z" />
      </svg>
    ),
  },
  {
    id: "ukr-lang",
    label: "Українська мова",
    icon: (
      <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
        <path d="M20 2H4C2.9 2 2 2.9 2 4V16C2 17.1 2.9 18 4 18H8V21C8 21.6 8.4 22 9 22H15C15.6 22 16 21.6 16 21V18H20C21.1 18 22 17.1 22 16V4C22 2.9 21.1 2 20 2M6 6H8V8H6V6M6 10H8V12H6V10M16 14H12V10H16V14M12 6H18V8H12V6M18 10V12H16V10H18Z" />
      </svg>
    ),
  },
];

const Student = () => {
  const { studentId } = useParams();
  const [activeSubjectId, setActiveSubjectId] = useState("ukr-lang");

  const student = useMemo(
    () => students.find((s) => s.id === studentId),
    [studentId]
  );

  // Get topics for the current context
  // In a real app, we'd filter by the activeSubjectId mapping to a real courseId
  // For demo, we'll fetch all and filter loosely or just show mock data if empty
  const topics = useMemo(() => {
    // Mapping our sidebar IDs to the mock data course IDs likely used
    const courseIdMap: Record<string, string> = {
      "ukr-lang": "ukr-lang-8", // Assuming 8th grade based on student mock
      algebra: "algebra-8",
      history: "history-8",
    };

    const targetCourseId = courseIdMap[activeSubjectId] || activeSubjectId;
    
    // Fetch topics from storage for the student's class and selected subject
    let fetched = getTopics({ 
      courseId: targetCourseId,
      className: student?.className // "8-А"
    });
    
    return fetched.map((t, idx) => ({
        ...t,
        // Simulate completed status for demo: first one is new, others are completed? 
        // Or just random. Let's make the last added new, others completed.
        // For now, simple modulo logic is fine.
        isCompleted: idx % 2 !== 0 
    }));
  }, [activeSubjectId, student]);

  const newTopics = topics.filter((t) => !t.isCompleted);
  const completedTopics = topics.filter((t) => t.isCompleted);

  if (!student) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-[#1E73F7]">
        <div className="text-xl text-white">Учня не знайдено</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#1E73F7] font-sans text-slate-900">
      <div className="flex min-h-screen">
        {/* Sidebar */}
        <aside className="fixed left-0 top-0 h-screen w-64 bg-white flex flex-col z-10">
          <div className="px-6 py-8">
            <div className="flex items-center gap-3">
               {/* Avatar */}
              <div
                className="h-10 w-10 overflow-hidden rounded-full bg-slate-200"
                style={{
                  backgroundImage: "url('https://images.unsplash.com/photo-1599566150163-29194dcaad36?ixlib=rb-4.0.3&auto=format&fit=crop&w=200&q=80')",
                  backgroundSize: "cover",
                }}
              />
              <div className="text-sm font-bold text-slate-900">
                {student.firstName} {student.lastName}
              </div>
            </div>
          </div>

          <div className="mt-4 flex-1 space-y-1 px-4">
            {Subjects.map((subject) => {
              const isActive = activeSubjectId === subject.id;
              return (
                <button
                  key={subject.id}
                  onClick={() => setActiveSubjectId(subject.id)}
                  className={`flex w-full items-center gap-4 rounded-xl px-4 py-3 text-sm font-semibold transition-all ${
                    isActive
                      ? "bg-[#E9F1FF] text-[#1E73F7]"
                      : "text-slate-900 hover:bg-slate-50"
                  }`}
                >
                  <div className={`flex items-center justify-center ${isActive ? "text-[#1E73F7]" : "text-slate-900"}`}>
                    {subject.icon}
                  </div>
                  {subject.label}
                </button>
              );
            })}
          </div>
        </aside>

        {/* Main Content */}
        <div className="ml-64 w-full p-10">
          <h1 className="text-2xl font-semibold text-white">Теми</h1>
          
          <div className="mt-8 grid grid-cols-2 gap-8">
            {/* New Topics (Left) */}
            <div className="space-y-4">
              <div className="text-sm text-white/80 font-medium">Нові</div>
              {newTopics.map((topic) => (
                <div
                  key={topic.id}
                  className="flex items-center justify-between rounded-2xl bg-white px-6 py-5 shadow-sm"
                >
                  <div className="font-bold text-slate-900">{topic.title}</div>
                  <PillButton 
                    label="Переглянути" 
                    className="bg-[#E9F1FF] text-[#1E73F7] hover:bg-[#D4E4FF]"
                  />
                </div>
              ))}
              {newTopics.length === 0 && (
                <div className="rounded-2xl bg-white/10 px-6 py-8 text-center text-sm text-white/60">
                  Немає нових тем
                </div>
              )}
            </div>

            {/* Completed Topics (Right) */}
             <div className="space-y-4">
              <div className="text-sm text-white/80 font-medium">Пройдені</div>
              {completedTopics.map((topic) => (
                <div
                  key={topic.id}
                  className="flex items-center justify-between rounded-2xl border border-white/30 bg-[#1E73F7] px-6 py-5"
                >
                  <div className="font-semibold text-white">{topic.title}</div>
                  <button className="rounded-xl bg-white px-4 py-2 text-sm font-semibold text-[#1E73F7] transition-colors hover:bg-slate-50">
                    Переглянути
                  </button>
                </div>
              ))}
              {completedTopics.length === 0 && (
                <div className="rounded-2xl border border-white/10 px-6 py-8 text-center text-sm text-white/40">
                  Немає пройдених тем
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Student;

