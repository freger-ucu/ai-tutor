import "./App.css";
import { useEffect } from "react";
import Home from "./pages/Home";
import Teacher from "./pages/Teacher";
import TeacherStudentDetail from "./pages/TeacherStudentDetail";
import TeacherTopic from "./pages/TeacherTopic";
import TeacherTest from "./pages/TeacherTest";
import Student from "./pages/Student";
import StudentTopic from "./pages/StudentTopic";
import TeacherNote from "./pages/TeacherNote";
import StudentTest from "./pages/StudentTest";
import { Routes, Route, useLocation } from "react-router-dom";
import StudentNote from "./pages/StudentNote";


function App() {
  const location = useLocation();

  useEffect(() => {
    if (window.innerWidth >= 1024) {
      return;
    }
    window.scrollTo({ top: 0, left: 0, behavior: "auto" });
    document.querySelectorAll("[data-scroll-root=\"mobile\"]").forEach((node) => {
      if (node instanceof HTMLElement) {
        node.scrollTop = 0;
      }
    });
  }, [location.pathname]);

  return (
    <Routes>
      <Route path="/" element={<Home />} />
      <Route
        path="/teacher/:teacherId/note/:courseId/:classId/:topicId/:noteId"
        element={<TeacherNote />}
      />
      <Route path="/teacher/:id" element={<Teacher />} />
      <Route
        path="/teacher/:id/class/:courseId/:classId/student/:studentId"
        element={<TeacherStudentDetail />}
      />
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
