import { useMemo, useState } from "react";
import { useParams } from "react-router-dom";
import { teachers } from "../data/teachers";
import { getTestById, getTestStatistics } from "../data/mockTests";
import TeacherSidebar from "../components/TeacherSidebar";
import { TestContainer } from "../components/test";
import SelectStudentsModal from "../components/SelectStudentsModal";

const TeacherTest = () => {
  const { id, testId } = useParams();

  const teacher = useMemo(
    () => teachers.find((item) => item.id === id),
    [id]
  );

  const testData = useMemo(() => getTestById(testId ?? ""), [testId]);
  const statistics = useMemo(() => getTestStatistics(testId ?? ""), [testId]);

  const [isAudienceModalOpen, setIsAudienceModalOpen] = useState(false);

  if (!testData) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-[#1E73F7]">
        <div className="text-xl text-white">Тест не знайдено</div>
      </div>
    );
  }

  return (
    <div className="h-screen bg-[#1E73F7] text-slate-900 overflow-hidden flex">
      <TeacherSidebar
        teacherName={
          teacher ? `${teacher.firstName} ${teacher.lastName}` : "Вчитель"
        }
        activeItem="materials"
      >
        <div className="space-y-4">
            <div className="flex items-center gap-3">
              <span className="inline-block h-5 w-5 rounded-md bg-slate-200" />
              <span>Конспект. Іменник</span>
            </div>
            <div className="flex items-center gap-3">
              <span className="inline-block h-5 w-5 rounded-md bg-slate-200" />
              <span>Додатково</span>
            </div>
            <div className="flex items-center gap-3">
              <span className="inline-block h-5 w-5 rounded-md bg-slate-200" />
              <span>Конспект. Іменник</span>
            </div>
            <div className="flex items-center gap-3 text-[#1E73F7]">
              <span className="inline-block h-5 w-5 rounded-md bg-[#1E73F7]/20" />
              <span>{testData.title}</span>
            </div>
          </div>
      </TeacherSidebar>

      <main className="flex-1 px-10 py-8 flex flex-col h-full">
          {/* Breadcrumbs */}
          <div className="text-sm font-medium text-white/80 shrink-0">
            {testData.subject} / {testData.className} / {testData.topicName}
          </div>
          
          <h1 className="mt-2 text-2xl font-bold text-white shrink-0">
             {testData.title}
          </h1>

          {/* Main Card */}
          <div className="mt-4 flex-1 rounded-[32px] bg-white p-8 shadow-xl overflow-y-auto min-h-0">
             <TestContainer
               testData={testData}
               statistics={statistics}
               showStatistics={true}
               viewMode="teacher"
             />
          </div>

          {/* Footer Actions */}
          <div className="mt-6 flex items-center justify-between shrink-0">
             <button className="flex items-center gap-2 rounded-full bg-white px-6 py-3 text-sm font-bold text-[#1E73F7] shadow transition hover:-translate-y-0.5 hover:shadow-lg cursor-pointer">
                <svg width="16" height="20" viewBox="0 0 16 20" fill="currentColor">
                    <path d="M10 0H2C0.9 0 0 0.9 0 2V18C0 19.1 0.9 20 2 20H14C15.1 20 16 19.1 16 18V6L10 0ZM14 18H2V2H9V7H14V18Z" opacity="0.5"/>
                    <path d="M10 0H2C0.9 0 0 0.9 0 2V18C0 19.1 0.9 20 2 20H14C15.1 20 16 19.1 16 18V6L10 0ZM9 7V2L14 7H9Z"/>
                </svg>
                Завантажити в PDF
             </button>

             <button 
                onClick={() => setIsAudienceModalOpen(true)}
                className="flex items-center gap-3 rounded-full border-2 border-white bg-transparent px-8 py-3 text-base font-bold text-white transition hover:bg-white/10 cursor-pointer"
             >
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M21 12C21 16.9706 16.9706 21 12 21C9.69637 21 7.59565 20.1344 6.00003 18.7077M3 12C3 7.02944 7.02944 3 12 3C14.3036 3 16.4044 3.86558 18 5.29231" stroke="white" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"/>
                    <path d="M21 3V8H16" stroke="white" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"/>
                    <path d="M3 21V16H8" stroke="white" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"/>
                 </svg>
                 <span>Змінити цільову аудиторію</span>
             </button>
          </div>
      </main>

      <SelectStudentsModal
        isOpen={isAudienceModalOpen}
        onClose={() => setIsAudienceModalOpen(false)}
        classNameFilter={testData.className}
        onSave={(selection) => {
            console.log("Saved selection", selection);
            setIsAudienceModalOpen(false);
        }}
      />
    </div>
  );
};

export default TeacherTest;
