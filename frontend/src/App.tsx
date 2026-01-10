import "./App.css";
import Home from "./pages/Home";
import Teacher from "./pages/Teacher";
import TeacherWorkspace from "./pages/TeacherWorkspace";
import Student from "./pages/Student";
import { Routes, Route } from "react-router-dom";


function App() {

  return (
    <Routes>
      <Route path="/" element={<Home />} />
      <Route path="/teacher" element={<Teacher />} />
      <Route path="/teacher/:subject" element={<TeacherWorkspace />} />
      <Route path="/student" element={<Student />} />
    </Routes>
  );
}

export default App;
