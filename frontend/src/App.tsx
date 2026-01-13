import "./App.css";
import Home from "./pages/Home";
import Teacher from "./pages/Teacher";
import TeacherTopic from "./pages/TeacherTopic";
import TeacherTest from "./pages/TeacherTest";
import Student from "./pages/Student";
import StudentTopic from "./pages/StudentTopic";
import TeacherNote from "./pages/TeacherNote";
import StudentTest from "./pages/StudentTest";
import StudentNote from "./pages/StudentNote";
import { Routes, Route } from "react-router-dom";


function App() {

  return (
    <Routes>
      <Route path="/" element={<Home />} />
      <Route
        path="/teacher/:teacherId/note/:courseId/:classId/:topicId/:noteId"
        element={<TeacherNote />}
      />
      <Route path="/teacher/:id" element={<Teacher />} />
      <Route
        path="/teacher/:id/topic/:courseId/:classId/:topicId"
        element={<TeacherTopic />}
      />
      <Route path="/teacher/:id/test/:testId" element={<TeacherTest />} />
      <Route path="/student/:studentId" element={<Student />} />
      <Route
        path="/student/:studentId/note/:courseId/:topicId/:noteId"
        element={<StudentNote />}
      />
      <Route path="/student/:studentId/topic/:courseId/:topicId" element={<StudentTopic />} />
      <Route path="/student/:studentId/test/:testId" element={<StudentTest />} />
    </Routes>
  );
}

export default App;
