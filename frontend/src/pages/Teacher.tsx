
import { useEffect, useMemo, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { teachers } from "../data/teachers";
import Modal from "../components/Modal";
import Panel from "../components/Panel";
import TeacherSidebar from "../components/TeacherSidebar";
import { addTopic, getTopics } from "../data/materialsStorage";

const courses = [
  {
    grade: "8 клас",
    items: [
      { id: "algebra-8", name: "Алгебра" },
      { id: "history-8", name: "Історія України" },
      { id: "ukr-lang-8", name: "Українська мова" },
    ],
  },
  {
    grade: "9 клас",
    items: [
      { id: "algebra-9", name: "Алгебра" },
      { id: "history-9", name: "Історія України" },
      { id: "ukr-lang-9", name: "Українська мова" },
    ],
  },
];

const classesByCourse: Record<string, string[]> = {
  "algebra-8": ["8-А", "8-Б", "8-В"],
  "history-8": ["8-А", "8-Б", "8-В"],
  "ukr-lang-8": ["8-А", "8-Б", "8-В"],
  "algebra-9": ["9-А", "9-Б", "9-В"],
  "history-9": ["9-А", "9-Б", "9-В"],
  "ukr-lang-9": ["9-А", "9-Б", "9-В"],
};

const Teacher = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const teacher = useMemo(
    () => teachers.find((item) => item.id === id),
    [id]
  );

  // Filter courses based on teacher's allowed subjects
  const filteredCourses = useMemo(() => {
    if (!teacher || !teacher.subjectIds) return courses;
    
    return courses.map(gradeGroup => ({
      ...gradeGroup,
      // Check if course ID starts with anty of the allowed subject IDs
      // e.g. "algebra-8" starts with "algebra"
      items: gradeGroup.items.filter(item => 
        teacher.subjectIds?.some(subjectId => item.id.startsWith(subjectId))
      )
    })).filter(group => group.items.length > 0);
  }, [teacher]);


  // Update initial selection logic to look at filtered courses
  const initialCourseId = filteredCourses[0]?.items[0]?.id ?? "";
  
  // Reset selection when teacher changes
  useEffect(() => {
    if (filteredCourses[0]?.items[0]?.id) {
       setSelectedCourseId(filteredCourses[0].items[0].id);
       const firstCourseId = filteredCourses[0].items[0].id;
       const classes = classesByCourse[firstCourseId] ?? [];
       setSelectedClass(classes[0] ?? "");
    }
  }, [teacher, filteredCourses]); // Re-run when teacher changes

  const [selectedCourseId, setSelectedCourseId] = useState(initialCourseId);
  const currentClasses = classesByCourse[selectedCourseId] ?? [];
  const [selectedClass, setSelectedClass] = useState(
    currentClasses[0] ?? ""
  );
  const [topicsByClass, setTopicsByClass] = useState<
    Record<string, string[]>
  >({});
  const currentTopics = topicsByClass[selectedClass] ?? [];
  const [isTopicModalOpen, setIsTopicModalOpen] = useState(false);
  const [newTopic, setNewTopic] = useState("");

  const handleCourseSelect = (courseId: string) => {
    setSelectedCourseId(courseId);
    const nextClasses = classesByCourse[courseId] ?? [];
    setSelectedClass(nextClasses[0] ?? "");
  };

  useEffect(() => {
    const storedTopics = getTopics({ teacherId: id, courseId: selectedCourseId });
    const nextTopicsByClass = storedTopics.reduce<Record<string, string[]>>(
      (acc, item) => {
        const classKey = item.className ?? "";
        if (!classKey) {
          return acc;
        }
        if (!acc[classKey]) {
          acc[classKey] = [];
        }
        acc[classKey].push(item.title);
        return acc;
      },
      {}
    );
    setTopicsByClass(nextTopicsByClass);
  }, [id, selectedCourseId]);

  const handleAddTopic = () => {
    const trimmedTopic = newTopic.trim();
    if (!trimmedTopic || !selectedClass) {
      return;
    }

    const created = addTopic({
      title: trimmedTopic,
      teacherId: id,
      courseId: selectedCourseId,
      className: selectedClass,
    });
    setTopicsByClass((prev) => {
      const existing = prev[selectedClass] ?? [];
      if (existing.includes(created.title)) {
        return prev;
      }

      return {
        ...prev,
        [selectedClass]: [...existing, created.title],
      };
    });
    setIsTopicModalOpen(false);
    setNewTopic("");
  };

  const handleTopicOpen = (topic: string) => {
    if (!id) {
      return;
    }

    const encodedClass = encodeURIComponent(selectedClass);
    const encodedTopic = encodeURIComponent(topic);
    navigate(`/teacher/${id}/topic/${selectedCourseId}/${encodedClass}/${encodedTopic}`);
  };

  return (
    <div className="min-h-screen bg-[#1E73F7] text-slate-900">
      <div className="flex min-h-screen">
        <TeacherSidebar
          teacherName={
            teacher ? `${teacher.firstName} ${teacher.lastName}` : "Вчитель"
          }
          activeItem="materials"
        />
        <main className="flex-1 px-8 py-10">
          <div className="relative min-h-[calc(100vh-5rem)]">
            <div className="grid gap-6 lg:grid-cols-[1.1fr_0.9fr_1fr]">
              <Panel title="Курси">
                <div className="space-y-6">
                  {filteredCourses.map((group) => (
                    <div key={group.grade}>
                      <div className="text-sm font-semibold text-slate-700">
                        {group.grade}
                      </div>
                      <div className="mt-3 space-y-3">
                        {group.items.map((course) => (
                          <button
                            key={course.id}
                            type="button"
                            onClick={() => handleCourseSelect(course.id)}
                            className={`flex w-full items-center justify-between rounded-2xl border px-4 py-3 text-left text-sm font-medium transition ${
                              selectedCourseId === course.id
                                ? "border-[#BFD6FF] bg-[#E9F1FF] text-slate-900"
                                : "border-slate-200 bg-white text-slate-800 hover:border-slate-300"
                            } cursor-pointer`}
                          >
                            <span>{course.name}</span>
                            <span className="text-lg text-slate-500">›</span>
                          </button>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              </Panel>
              <Panel title="Класи">
                <div className="space-y-3">
                  {currentClasses.map((item) => (
                    <button
                      key={item}
                      type="button"
                      onClick={() => setSelectedClass(item)}
                      className={`flex w-full items-center justify-between rounded-2xl border px-4 py-3 text-left text-sm font-medium transition ${
                        selectedClass === item
                          ? "border-[#BFD6FF] bg-[#E9F1FF] text-slate-900"
                          : "border-slate-200 bg-white text-slate-800 hover:border-slate-300"
                      } cursor-pointer`}
                    >
                      <span>{item}</span>
                      <span className="text-lg text-slate-500">›</span>
                    </button>
                  ))}
                </div>
              </Panel>
              <Panel title="Теми">
                <div className="space-y-3">
                  {currentTopics.map((topic) => (
                    <button
                      key={topic}
                      type="button"
                      onClick={() => handleTopicOpen(topic)}
                      className="flex w-full items-center justify-between rounded-2xl border border-slate-200 px-4 py-3 text-left text-sm font-medium text-slate-800 transition hover:border-slate-300 hover:bg-slate-50 cursor-pointer"
                    >
                      <span>{topic}</span>
                      <span className="text-lg text-slate-400">›</span>
                    </button>
                  ))}
                </div>
              </Panel>
            </div>
            <button
              type="button"
              className="absolute bottom-0 right-0 flex items-center gap-2 rounded-full bg-white px-6 py-3 text-sm font-semibold text-[#1E73F7] shadow-lg transition hover:-translate-y-0.5 hover:bg-blue-50 hover:shadow-xl cursor-pointer"
              onClick={() => setIsTopicModalOpen(true)}
            >
              <span className="text-lg">＋</span>
              Додати тему
            </button>
          </div>
        </main>
      </div>
      <Modal
        isOpen={isTopicModalOpen}
        onClose={() => setIsTopicModalOpen(false)}
        title="Додайте тему"
        size="lg"
      >
        <div className="flex flex-col items-center gap-6">
          <input
            type="text"
            value={newTopic}
            onChange={(event) => setNewTopic(event.target.value)}
            placeholder="Введіть тему"
            className="w-full rounded-full bg-[#E9F1FF] px-8 py-5 text-lg font-medium text-slate-700 placeholder-slate-500 outline-none transition focus:bg-white focus:ring-2 focus:ring-[#BFD6FF]"
          />
          <button
            type="button"
            className="ml-auto rounded-full bg-[#1E73F7] px-8 py-4 text-lg font-semibold text-white shadow transition hover:-translate-y-0.5 hover:bg-[#1A63D6] hover:shadow-lg cursor-pointer"
            onClick={handleAddTopic}
          >
            Додати
          </button>
        </div>
      </Modal>
    </div>
  );
};

export default Teacher;
