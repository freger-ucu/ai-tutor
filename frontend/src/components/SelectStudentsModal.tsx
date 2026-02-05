import { useState, useMemo, useEffect } from "react";
import Modal from "./Modal";

interface SelectStudentsModalProps {
  isOpen: boolean;
  onClose: () => void;
  students?: { id: number; label?: string }[];
  onSave?: (selection: { levels: string[]; students: string[] }) => void;
  /** Initial level selection to restore when reopening */
  initialLevels?: string[];
  /** Initial student selection to restore when reopening */
  initialStudents?: string[];
}

const SelectStudentsModal = ({
  isOpen,
  onClose,
  students,
  onSave,
  initialLevels,
  initialStudents,
}: SelectStudentsModalProps) => {
  // Determine initial tab based on what was previously selected
  const getInitialTab = (): "levels" | "individual" => {
    if (initialStudents && initialStudents.length > 0) return "individual";
    return "levels";
  };

  const [activeTab, setActiveTab] = useState<"levels" | "individual">(getInitialTab);

  // Level selections
  const [selectedLevels, setSelectedLevels] = useState<string[]>(initialLevels ?? []);

  // Student selections
  const [selectedStudents, setSelectedStudents] = useState<string[]>(initialStudents ?? []);

  // Restore state when modal opens with initial values
  useEffect(() => {
    if (isOpen) {
      // Restore previous selection if provided
      if (initialStudents && initialStudents.length > 0) {
        setActiveTab("individual");
        setSelectedStudents(initialStudents);
        setSelectedLevels([]);
      } else if (initialLevels && initialLevels.length > 0) {
        setActiveTab("levels");
        setSelectedLevels(initialLevels);
        setSelectedStudents([]);
      } else {
        // No previous selection - start fresh
        setActiveTab("levels");
        setSelectedLevels([]);
        setSelectedStudents([]);
      }
    }
  }, [isOpen, initialLevels, initialStudents]);

  // Clear opposite selection when switching tabs to prevent mixed assignment
  const handleTabChange = (tab: "levels" | "individual") => {
    if (tab === "levels") {
      setSelectedStudents([]);
    } else {
      setSelectedLevels([]);
    }
    setActiveTab(tab);
  };

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
            <div className="flex gap-2">
                <button
                    onClick={() => handleTabChange("levels")}
                    className={`flex-1 rounded-full border px-4 py-2 text-sm font-semibold transition ${
                        activeTab === "levels"
                        ? "border-[#1E73F7] bg-[#1E73F7] text-white"
                        : "border-slate-200 bg-white text-slate-700 hover:border-[#1557c0] hover:bg-[#E9F1FF]"
                    }`}
                >
                    Рівень
                </button>
                <button
                    onClick={() => handleTabChange("individual")}
                    className={`flex-1 rounded-full border px-4 py-2 text-sm font-semibold transition ${
                        activeTab === "individual"
                        ? "border-[#1E73F7] bg-[#1E73F7] text-white"
                        : "border-slate-200 bg-white text-slate-700 hover:border-[#1557c0] hover:bg-[#E9F1FF]"
                    }`}
                >
                    Індивидуально
                </button>
            </div>

            {/* Content */}
            <div className="min-h-75">
                {activeTab === "levels" && (
                    <div className="space-y-3">
                        {[
                          { id: "strong", label: "Високий" },
                          { id: "medium", label: "Середній" },
                          { id: "weak", label: "Низький" },
                        ].map((level) => (
                             <label
                                key={level.id}
                                className={`flex cursor-pointer items-center gap-4 rounded-xl px-4 py-3 transition ${
                                    selectedLevels.includes(level.id) ? "bg-[#E9F1FF]" : "bg-slate-50 hover:bg-slate-100"
                                }`}
                             >
                                <div className={`flex h-6 w-6 items-center justify-center rounded border transition ${
                                    selectedLevels.includes(level.id) ? "border-[#1E73F7] bg-[#1E73F7]" : "border-slate-300 bg-white"
                                }`}>
                                     {selectedLevels.includes(level.id) && (
                                        <svg width="14" height="10" viewBox="0 0 14 10" fill="none" xmlns="http://www.w3.org/2000/svg">
                                            <path d="M1 5L4.5 8.5L13 1" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                                        </svg>
                                     )}
                                </div>
                                <input
                                    type="checkbox"
                                    className="hidden"
                                    checked={selectedLevels.includes(level.id)}
                                    onChange={() => toggleLevel(level.id)}
                                />
                                <span className={`text-sm font-semibold ${selectedLevels.includes(level.id) ? "text-[#1E73F7]" : "text-slate-700"}`}>
                                    {level.label}
                                </span>
                             </label>
                        ))}
                    </div>
                )}

                {activeTab === "individual" && (
                     <div className="space-y-3 max-h-75 overflow-y-auto pr-2">
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
                className="w-full rounded-full border border-[#1E73F7] bg-[#1E73F7] px-4 py-4 text-base font-semibold text-white transition hover:bg-[#1557c0] hover:border-[#1557c0]"
            >
                Зберегти
            </button>
        </div>
    </Modal>
  );
};

export default SelectStudentsModal;
