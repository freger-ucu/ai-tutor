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
    <div className="min-h-screen bg-[#1E73F7] flex items-center justify-center">
      <div className="flex gap-6">
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
        <div className="space-y-4">
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
        <div className="space-y-4">
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
