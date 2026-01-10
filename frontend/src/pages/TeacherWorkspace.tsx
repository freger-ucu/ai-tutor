import { useParams } from "react-router-dom";

const TeacherWorkspace = () => {
  const { subject } = useParams();

  return (
    <div className="min-h-screen p-8 text-white">
      <h1 className="text-3xl font-semibold">Планування</h1>
      <p className="mt-2 text-lg">
        Предмет: <span className="font-medium">{subject}</span>
      </p>
    </div>
  );
};

export default TeacherWorkspace;
