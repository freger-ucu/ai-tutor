import type { ReactNode } from "react";

interface TeacherSidebarProps {
  teacherName: string;
  activeItem?: "materials" | "students";
  children?: ReactNode;
}

const TeacherSidebar = ({
  teacherName,
  activeItem = "materials",
  children,
}: TeacherSidebarProps) => {
  const baseClass =
    "flex w-full items-center gap-3 rounded-2xl px-4 py-3 text-sm";
  const activeClass = "bg-[#E9F1FF] font-semibold text-[#1E73F7]";
  const inactiveClass = "font-medium text-slate-800 hover:bg-slate-100";

  return (
    <aside className="w-64 shrink-0 bg-white px-6 py-8">
      <div className="flex items-center gap-3">
        <div className="h-12 w-12 rounded-full bg-slate-200" />
        <div className="text-base font-semibold text-slate-900">
          {teacherName}
        </div>
      </div>
      <div className="mt-10 space-y-3">
        <button
          type="button"
          className={`${baseClass} ${
            activeItem === "materials" ? activeClass : inactiveClass
          } cursor-pointer`}
        >
          <span className="inline-block h-5 w-5 rounded-md bg-[#1E73F7]/20" />
          Навчальні матеріали
        </button>
        <button
          type="button"
          className={`${baseClass} ${
            activeItem === "students" ? activeClass : inactiveClass
          } cursor-pointer`}
        >
          <span className="inline-block h-5 w-5 rounded-md bg-slate-200" />
          Учні
        </button>
      </div>
      {children ? (
        <div className="mt-10 border-t border-slate-200 pt-6 text-sm text-slate-500">
          {children}
        </div>
      ) : null}
    </aside>
  );
};

export default TeacherSidebar;
