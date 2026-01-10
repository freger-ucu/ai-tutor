
import { useState } from "react";
import { useNavigate } from "react-router-dom";

const Teacher = () => {
  const [subject, setSubject] = useState("");
  const navigate = useNavigate();

  const handleSubjectChange = (event: React.ChangeEvent<HTMLSelectElement>) => {
    const value = event.target.value;
    setSubject(value);
    navigate(`/teacher/${value}`);
  };

  return (
    <div className="min-h-screen flex items-center justify-center">
      <div className="flex flex-col items-center gap-4">
        <h1 className="text-3xl font-semibold text-white">Вчитель</h1>
        <select
          className="rounded-full bg-white px-6 py-3 text-lg font-medium text-[#1E73F7] shadow-sm"
          value={subject}
          onChange={handleSubjectChange}
        >
          <option value="" disabled>
            Оберіть предмет
          </option>
          <option value="math">Математика</option>
          <option value="history">Історія</option>
          <option value="ukrainian">Українська мова</option>
        </select>
      </div>
    </div>
  );
};

export default Teacher;
