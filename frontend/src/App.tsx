import "./App.css";
import Home from "./pages/Home";
import Teacher from "./pages/Teacher";
import TeacherTopic from "./pages/TeacherTopic";
import Student from "./pages/Student";
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
      <Route path="/student" element={<Student />} />
    </Routes>
  );
}

export default App;
