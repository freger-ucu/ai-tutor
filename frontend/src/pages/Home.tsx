import { useState } from "react";
import Button from "../components/Button";
import Modal from "../components/Modal";
import { Link, useNavigate } from "react-router-dom";
import { teachers } from "../data/teachers";

const Home = () => {
  const [isTeacherModalOpen, setIsTeacherModalOpen] = useState(false);
  const navigate = useNavigate();
  const handleTeacherSelect = (teacherId: string) => {
    setIsTeacherModalOpen(false);
    navigate(`/teacher/${teacherId}`);
  };

  return (
    <div className="min-h-screen bg-[#1E73F7] flex items-center justify-center">
      <div className="flex gap-6">
        <Button label="Я Вчитель" onClick={() => setIsTeacherModalOpen(true)}/>
        <Link to="/student">
          <Button label="Я Учень" />
        </Link>
      </div>
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
    </div>
  );
};

export default Home;
