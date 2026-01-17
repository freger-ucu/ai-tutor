import { useState } from "react";
import Button from "../components/Button";
import Modal from "../components/Modal";
import { useNavigate } from "react-router-dom";
import { toNumericId } from "../api/idUtils";

const Home = () => {
  const [isTeacherModalOpen, setIsTeacherModalOpen] = useState(false);
  const [isStudentModalOpen, setIsStudentModalOpen] = useState(false);
  const [teacherIdInput, setTeacherIdInput] = useState("");
  const [teacherIdError, setTeacherIdError] = useState<string | null>(null);
  const [studentIdInput, setStudentIdInput] = useState("");
  const [studentIdError, setStudentIdError] = useState<string | null>(null);
  const navigate = useNavigate();
  const teacherQuickOptions = [
    { id: "14", label: "Вчитель 14", hint: "Історія" },
    { id: "4", label: "Вчитель 4", hint: "Алгебра" },
    { id: "17", label: "Вчитель 17", hint: "Українська мова" },
  ];
  const studentQuickOptions = [
    { id: "114", label: "Учень 114", hint: "Сильний учень" },
    { id: "162", label: "Учень 162", hint: "Середній учень" },
    { id: "118", label: "Учень 118", hint: "Слабкий учень" },
  ];

  const handleTeacherSelect = (teacherId: string) => {
    setIsTeacherModalOpen(false);
    navigate(`/teacher/${teacherId}`);
  };

  const handleTeacherSubmit = () => {
    const numericId = toNumericId(teacherIdInput);
    if (!numericId) {
      setTeacherIdError("Вкажіть коректний ID вчителя.");
      return;
    }
    setTeacherIdError(null);
    handleTeacherSelect(String(numericId));
  };

  const handleStudentSelect = (studentId: string) => {
    setIsStudentModalOpen(false);
    navigate(`/student/${studentId}`);
  };

  const handleStudentSubmit = () => {
    const numericId = toNumericId(studentIdInput);
    if (!numericId) {
      setStudentIdError("Вкажіть коректний ID учня.");
      return;
    }
    setStudentIdError(null);
    handleStudentSelect(String(numericId));
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-[#1E73F7] via-[#2B7BFA] to-[#1A63D6] flex items-center justify-center">
      <div className="flex flex-col items-center gap-6 sm:flex-row">
        <Button label="Я Вчитель" onClick={() => setIsTeacherModalOpen(true)}/>
        <Button label="Я Учень" onClick={() => setIsStudentModalOpen(true)} />
      </div>

      {/* Teacher Selection Modal */}
      <Modal
        isOpen={isTeacherModalOpen}
        onClose={() => {
          setIsTeacherModalOpen(false);
          setTeacherIdInput("");
          setTeacherIdError(null);
        }}
        title="Оберіть вчителя"
      >
        <div className="space-y-6">
          <div className="space-y-2">
            <label className="text-xs font-semibold uppercase text-slate-500">
              ID вчителя
            </label>
            <input
              type="number"
              min="1"
              value={teacherIdInput}
              onChange={(event) => {
                setTeacherIdInput(event.target.value);
                if (teacherIdError) {
                  setTeacherIdError(null);
                }
              }}
              onKeyDown={(event) => {
                if (event.key === "Enter") {
                  event.preventDefault();
                  handleTeacherSubmit();
                }
              }}
              placeholder="Наприклад, 12"
              className="w-full rounded-xl border border-slate-200 px-4 py-3 text-sm text-slate-900 outline-none focus:border-slate-400"
            />
            {teacherIdError && (
              <div className="text-sm text-red-600">{teacherIdError}</div>
            )}
          </div>
          <div className="space-y-3">
            <div className="text-xs font-semibold uppercase text-slate-500">
              Швидкий вибір
            </div>
            <div className="flex flex-wrap gap-3">
              {teacherQuickOptions.map((option) => (
                <div key={option.id} className="group relative flex-1">
                  <button
                    type="button"
                    onClick={() => handleTeacherSelect(option.id)}
                    className="w-full rounded-xl border border-slate-200 bg-white px-4 py-3 text-sm font-semibold text-slate-700 transition hover:border-[#1E73F7] hover:text-slate-900"
                  >
                    {option.label}
                  </button>
                  <div className="pointer-events-none absolute -top-2 left-1/2 -translate-x-1/2 -translate-y-full whitespace-nowrap rounded-lg bg-slate-900 px-3 py-2 text-sm font-semibold text-white opacity-0 shadow-lg transition-opacity duration-75 group-hover:opacity-100">
                    {option.hint}
                  </div>
                </div>
              ))}
            </div>
          </div>
          <button
            type="button"
            onClick={handleTeacherSubmit}
            className="w-full rounded-xl bg-[#1E73F7] px-4 py-3 text-sm font-semibold text-white transition hover:bg-[#1A63D6]"
          >
            Продовжити
          </button>
        </div>
      </Modal>

      {/* Student Selection Modal */}
      <Modal
        isOpen={isStudentModalOpen}
        onClose={() => {
          setIsStudentModalOpen(false);
          setStudentIdInput("");
          setStudentIdError(null);
        }}
        title="Оберіть учня"
      >
        <div className="space-y-6">
          <div className="space-y-2">
            <label className="text-xs font-semibold uppercase text-slate-500">
              ID учня
            </label>
            <input
              type="number"
              min="1"
              value={studentIdInput}
              onChange={(event) => {
                setStudentIdInput(event.target.value);
                if (studentIdError) {
                  setStudentIdError(null);
                }
              }}
              onKeyDown={(event) => {
                if (event.key === "Enter") {
                  event.preventDefault();
                  handleStudentSubmit();
                }
              }}
              placeholder="Наприклад, 1001"
              className="w-full rounded-xl border border-slate-200 px-4 py-3 text-sm text-slate-900 outline-none focus:border-slate-400"
            />
            {studentIdError && (
              <div className="text-sm text-red-600">{studentIdError}</div>
            )}
          </div>
          <div className="space-y-3">
            <div className="text-xs font-semibold uppercase text-slate-500">
              Швидкий вибір
            </div>
            <div className="flex flex-wrap gap-3">
              {studentQuickOptions.map((option) => (
                <div key={option.id} className="group relative flex-1">
                  <button
                    type="button"
                    onClick={() => handleStudentSelect(option.id)}
                    className="w-full rounded-xl border border-slate-200 bg-white px-4 py-3 text-sm font-semibold text-slate-700 transition hover:border-[#1E73F7] hover:text-slate-900"
                  >
                    {option.label}
                  </button>
                  <div className="pointer-events-none absolute -top-2 left-1/2 -translate-x-1/2 -translate-y-full whitespace-nowrap rounded-lg bg-slate-900 px-3 py-2 text-sm font-semibold text-white opacity-0 shadow-lg transition-opacity duration-75 group-hover:opacity-100">
                    {option.hint}
                  </div>
                </div>
              ))}
            </div>
          </div>
          <button
            type="button"
            onClick={handleStudentSubmit}
            className="w-full rounded-xl bg-[#1E73F7] px-4 py-3 text-sm font-semibold text-white transition hover:bg-[#1A63D6]"
          >
            Продовжити
          </button>
        </div>
      </Modal>
    </div>
  );
};

export default Home;
