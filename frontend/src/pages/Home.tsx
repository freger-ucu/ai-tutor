import { useState } from "react";
import Button from "../components/Button";
import Modal from "../components/Modal";
import { useNavigate } from "react-router-dom";
import { teachers } from "../data/teachers";
import { students } from "../data/students";

const Home = () => {
  const [isTeacherModalOpen, setIsTeacherModalOpen] = useState(false);
  const [isStudentModalOpen, setIsStudentModalOpen] = useState(false);
  const navigate = useNavigate();

  const handleTeacherSelect = (teacherId: string) => {
    setIsTeacherModalOpen(false);
    navigate(`/teacher/${teacherId}`);
  };

  const handleStudentSelect = (studentId: string) => {
    setIsStudentModalOpen(false);
    navigate(`/student/${studentId}`);
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
        onClose={() => setIsTeacherModalOpen(false)}
        title="Оберіть вчителя"
      >
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
          {teachers.map((teacher) => (
            <button
              key={teacher.id}
              type="button"
              onClick={() => handleTeacherSelect(teacher.id)}
              className="rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 text-left text-slate-900 transition hover:-translate-y-0.5 hover:border-slate-300 hover:bg-white hover:shadow cursor-pointer"
            >
              <div className="text-sm font-semibold">
                {teacher.firstName} {teacher.lastName}
              </div>
            </button>
          ))}
        </div>
      </Modal>

      {/* Student Selection Modal */}
      <Modal
        isOpen={isStudentModalOpen}
        onClose={() => setIsStudentModalOpen(false)}
        title="Оберіть учня"
      >
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
          {students.map((student) => (
            <button
              key={student.id}
              type="button"
              onClick={() => handleStudentSelect(student.id)}
              className="rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 text-left text-slate-900 transition hover:-translate-y-0.5 hover:border-slate-300 hover:bg-white hover:shadow cursor-pointer"
            >
              <div className="text-sm font-semibold">
                {student.firstName} {student.lastName}
              </div>
              <div className="mt-1 text-xs text-slate-500">
                Клас: {student.className}
              </div>
            </button>
          ))}
        </div>
      </Modal>
    </div>
  );
};

export default Home;

