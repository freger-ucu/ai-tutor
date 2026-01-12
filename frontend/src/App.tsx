import "./App.css";
import Home from "./pages/Home";
import Teacher from "./pages/Teacher";
import TeacherTopic from "./pages/TeacherTopic";
import TeacherTest from "./pages/TeacherTest";
import Student from "./pages/Student";
import StudentTest from "./pages/StudentTest";
import { Routes, Route } from "react-router-dom";


function App() {

  return (
    <Routes>
      <Route path="/" element={<Home />} />
      <Route path="/teacher/:id" element={<Teacher />} />
      <Route
        path="/teacher/:id/topic/:courseId/:classId/:topicId"
        element={<TeacherTopic />}
      />
      <Route path="/teacher/:id/test/:testId" element={<TeacherTest />} />
      <Route path="/student/:studentId" element={<Student />} />
      <Route path="/student/:studentId/test/:testId" element={<StudentTest />} />
    </Routes>
  );
}

export default App;
