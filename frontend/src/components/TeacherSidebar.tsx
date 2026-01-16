/**
 * TeacherSidebar - Static navigation sidebar for teacher interface
 *
 * This sidebar is intentionally STATIC and displays exactly two navigation items:
 * 1. "Навчальні матеріали" (Learning Materials)
 * 2. "Учні" (Students)
 *
 * IMPORTANT: This sidebar must NEVER change based on:
 * - Current page or route
 * - Edit mode or viewing state
 * - Selected topics, tests, or materials
 *
 * The sidebar provides consistent navigation back to the main teacher views
 * and does not support dynamic content or additional links.
 */

interface TeacherSidebarProps {
  /** Teacher display name shown at top of sidebar */
  teacherName: string;
  /** Which navigation item is currently active */
  activeItem?: "materials" | "students";
  /** Handler for clicking "Learning Materials" button */
  onMaterialsClick?: () => void;
  /** Handler for clicking "Students" button */
  onStudentsClick?: () => void;
}

const MaterialsIcon = () => (
  <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
    <path d="M19 3H5C3.9 3 3 3.9 3 5V19C3 20.1 3.9 21 5 21H19C20.1 21 21 20.1 21 19V5C21 3.9 20.1 3 19 3ZM9 17H7V10H9V17ZM13 17H11V7H13V17ZM17 17H15V13H17V17Z" />
  </svg>
);

const StudentsIcon = () => (
  <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
    <path d="M16 11C17.66 11 18.99 9.66 18.99 8C18.99 6.34 17.66 5 16 5C14.34 5 13 6.34 13 8C13 9.66 14.34 11 16 11ZM8 11C9.66 11 10.99 9.66 10.99 8C10.99 6.34 9.66 5 8 5C6.34 5 5 6.34 5 8C5 9.66 6.34 11 8 11ZM8 13C5.67 13 1 14.17 1 16.5V19H15V16.5C15 14.17 10.33 13 8 13ZM16 13C15.71 13 15.38 13.02 15.03 13.05C16.19 13.89 17 15.02 17 16.5V19H23V16.5C23 14.17 18.33 13 16 13Z" />
  </svg>
);

/**
 * TeacherSidebar component - renders a STATIC sidebar with exactly two navigation items.
 *
 * This component intentionally does NOT accept children or any dynamic content props.
 * The sidebar always displays the same two buttons regardless of application state.
 */
const TeacherSidebar = ({
  teacherName,
  activeItem = "materials",
  onMaterialsClick,
  onStudentsClick,
}: TeacherSidebarProps) => {
  // Static CSS classes for navigation buttons
  const baseClass =
    "flex w-full items-center justify-start gap-3 rounded-2xl px-4 py-3 text-sm cursor-pointer";
  const activeClass = "bg-[#E9F1FF] font-semibold text-[#1E73F7]";
  const inactiveClass = "font-medium text-slate-800 hover:bg-slate-100";

  return (
    <aside className="w-64 min-w-64 max-w-64 shrink-0 flex-shrink-0 flex-grow-0 bg-white px-6 py-8">
      {/* Teacher profile section */}
      <div className="flex items-center gap-3">
        <div
          className="h-12 w-12 overflow-hidden rounded-full bg-slate-200"
          style={{
            backgroundImage: "url('https://i1.poltava.to/uploads/2017/09/2017-09-19/best.jpg')",
            backgroundSize: "cover",
            backgroundPosition: "center",
          }}
        />
        <div className="text-base font-semibold text-slate-900">
          {teacherName}
        </div>
      </div>

      {/*
       * STATIC NAVIGATION - Always shows exactly two items:
       * 1. Learning Materials (Навчальні матеріали)
       * 2. Students (Учні)
       *
       * These buttons navigate to the main teacher views and do NOT
       * change based on current page, topic, or editing state.
       */}
      <div className="mt-10 space-y-3">
        <button
          type="button"
          onClick={onMaterialsClick}
          className={`${baseClass} ${
            activeItem === "materials" ? activeClass : inactiveClass
          }`}
        >
          <span className={`flex items-center justify-center ${activeItem === "materials" ? "text-[#1E73F7]" : "text-slate-600"}`}>
            <MaterialsIcon />
          </span>
          <span className="flex-1 text-left leading-5">Навчальні матеріали</span>
        </button>
        <button
          type="button"
          onClick={onStudentsClick}
          className={`${baseClass} ${
            activeItem === "students" ? activeClass : inactiveClass
          }`}
        >
          <span className={`flex items-center justify-center ${activeItem === "students" ? "text-[#1E73F7]" : "text-slate-600"}`}>
            <StudentsIcon />
          </span>
          <span className="flex-1 text-left leading-5">Учні</span>
        </button>
      </div>
    </aside>
  );
};

export default TeacherSidebar;
