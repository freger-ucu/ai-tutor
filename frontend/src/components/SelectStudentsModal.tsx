import { useState, useMemo } from "react";
import Modal from "./Modal";

interface SelectStudentsModalProps {
  isOpen: boolean;
  onClose: () => void;
  students?: { id: number; label?: string }[];
  onSave?: (selection: { levels: string[]; students: string[] }) => void;
}

const SelectStudentsModal = ({
  isOpen,
  onClose,
  students,
  onSave,
}: SelectStudentsModalProps) => {
  const [activeTab, setActiveTab] = useState<"levels" | "individual">("levels");
  
  // Level selections
  const [selectedLevels, setSelectedLevels] = useState<string[]>([]);
  
  // Student selections
  const [selectedStudents, setSelectedStudents] = useState<string[]>([]);

  const classStudents = useMemo(
    () =>
      (students ?? []).map((student) => ({
        id: String(student.id),
        label: student.label ?? `Учень ${student.id}`,
      })),
    [students]
  );

  const toggleLevel = (level: string) => {
    setSelectedLevels((prev) =>
      prev.includes(level)
        ? prev.filter((l) => l !== level)
        : [...prev, level]
    );
  };

  const toggleStudent = (studentId: string) => {
    setSelectedStudents((prev) =>
      prev.includes(studentId)
        ? prev.filter((id) => id !== studentId)
        : [...prev, studentId]
    );
  };

  const handleSave = () => {
    if (onSave) {
        onSave({
            levels: activeTab === "levels" ? selectedLevels : [],
            students: activeTab === "individual" ? selectedStudents : [],
        });
    }
    onClose();
  };

  return (
    <Modal
        isOpen={isOpen}
        onClose={onClose}
        title="Оберіть учнів"
        size="lg" // Adjust size as needed
    >
        <div className="space-y-6">
            <div className="text-center text-sm text-slate-500">
                Оберіть учнів, на яких будуть орієнтовані навчальні матеріали
            </div>

            {/* Tabs */}
            <div className="flex rounded-xl bg-[#E9F1FF] p-1">
                <button
                    onClick={() => setActiveTab("levels")}
                    className={`flex-1 rounded-lg py-2 text-sm font-semibold transition ${
                        activeTab === "levels"
                        ? "bg-[#1E73F7] text-white shadow-sm"
                        : "text-slate-500 hover:text-slate-700"
                    }`}
                >
                    Рівень
                </button>
                <button
                    onClick={() => setActiveTab("individual")}
                    className={`flex-1 rounded-lg py-2 text-sm font-semibold transition ${
                        activeTab === "individual"
                        ? "bg-[#1E73F7] text-white shadow-sm"
                        : "text-slate-500 hover:text-slate-700"
                    }`}
                >
                    Індивидуально
                </button>
            </div>

            {/* Content */}
            <div className="min-h-[300px]">
                {activeTab === "levels" && (
                    <div className="space-y-3">
                        {["Високий", "Середній", "Низький"].map((level) => (
                             <label
                                key={level}
                                className={`flex cursor-pointer items-center gap-4 rounded-xl px-4 py-3 transition ${
                                    selectedLevels.includes(level) ? "bg-[#E9F1FF]" : "bg-slate-50 hover:bg-slate-100"
                                }`}
                             >
                                <div className={`flex h-6 w-6 items-center justify-center rounded border transition ${
                                    selectedLevels.includes(level) ? "border-[#1E73F7] bg-[#1E73F7]" : "border-slate-300 bg-white"
                                }`}>
                                     {selectedLevels.includes(level) && (
                                        <svg width="14" height="10" viewBox="0 0 14 10" fill="none" xmlns="http://www.w3.org/2000/svg">
                                            <path d="M1 5L4.5 8.5L13 1" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                                        </svg>
                                     )}
                                </div>
                                <input
                                    type="checkbox"
                                    className="hidden"
                                    checked={selectedLevels.includes(level)}
                                    onChange={() => toggleLevel(level)}
                                />
                                <span className={`text-sm font-semibold ${selectedLevels.includes(level) ? "text-[#1E73F7]" : "text-slate-700"}`}>
                                    {level}
                                </span>
                             </label>
                        ))}
                    </div>
                )}

                {activeTab === "individual" && (
                     <div className="space-y-3 max-h-[300px] overflow-y-auto pr-2">
                        {classStudents.length === 0 && (
                          <div className="rounded-xl bg-slate-50 px-4 py-3 text-sm text-slate-500">
                            Немає учнів для вибору.
                          </div>
                        )}
                        {classStudents.map((student) => (
                             <label
                                key={student.id}
                                className={`flex cursor-pointer items-center gap-4 rounded-xl px-4 py-3 transition ${
                                    selectedStudents.includes(student.id) ? "bg-[#E9F1FF]" : "bg-slate-50 hover:bg-slate-100"
                                }`}
                             >
                                <div className="h-8 w-8 overflow-hidden rounded-full bg-slate-200">
                                     <img 
                                        src={`https://api.dicebear.com/7.x/avataaars/svg?seed=${student.id}`} 
                                        alt={student.label}
                                        className="h-full w-full object-cover" 
                                     />
                                </div>
                                <div className={`flex-1 text-sm font-semibold ${selectedStudents.includes(student.id) ? "text-[#1E73F7]" : "text-slate-700"}`}>
                                    {student.label}
                                </div>
                                <div className={`flex h-6 w-6 items-center justify-center rounded border transition ${
                                    selectedStudents.includes(student.id) ? "border-[#1E73F7] bg-[#1E73F7]" : "border-slate-300 bg-white"
                                }`}>
                                     {selectedStudents.includes(student.id) && (
                                        <svg width="14" height="10" viewBox="0 0 14 10" fill="none" xmlns="http://www.w3.org/2000/svg">
                                            <path d="M1 5L4.5 8.5L13 1" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                                        </svg>
                                     )}
                                </div>
                                <input
                                    type="checkbox"
                                    className="hidden"
                                    checked={selectedStudents.includes(student.id)}
                                    onChange={() => toggleStudent(student.id)}
                                />
                             </label>
                        ))}
                     </div>
                )}
            </div>

            <button
                onClick={handleSave}
                className="w-full rounded-xl bg-[#1E73F7] py-4 text-base font-semibold text-white shadow-lg shadow-blue-500/20 transition hover:bg-[#1A63D6] hover:shadow-xl"
            >
                Зберегти
            </button>
        </div>
    </Modal>
  );
};

export default SelectStudentsModal;
