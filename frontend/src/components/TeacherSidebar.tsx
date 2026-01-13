import type { ReactNode } from "react";

interface TeacherSidebarProps {
  teacherName: string;
  activeItem?: "materials" | "students";
  children?: ReactNode;
  showPrimaryNav?: boolean;
  afterPrimaryNav?: ReactNode;
}

const TeacherSidebar = ({
  teacherName,
  activeItem = "materials",
  children,
  showPrimaryNav = true,
  afterPrimaryNav,
}: TeacherSidebarProps) => {
  const baseClass =
    "flex w-full items-start justify-start gap-3 rounded-2xl px-4 py-3 text-sm";
  const activeClass = "bg-[#E9F1FF] font-semibold text-[#1E73F7]";
  const inactiveClass = "font-medium text-slate-800 hover:bg-slate-100";
  const hasTopSection = showPrimaryNav || Boolean(afterPrimaryNav);
  const dividerClass = hasTopSection
    ? afterPrimaryNav
      ? "mt-6 border-t border-slate-200 pt-6 text-sm text-slate-500"
      : "mt-10 border-t border-slate-200 pt-6 text-sm text-slate-500"
    : "mt-8 text-sm text-slate-500";

  return (
    <aside className="w-64 shrink-0 bg-white px-6 py-8">
      <div className="flex items-center gap-3">
        <div className="h-12 w-12 rounded-full bg-slate-200" />
        <div className="text-base font-semibold text-slate-900">
          {teacherName}
        </div>
      </div>
      {showPrimaryNav ? (
        <div className="mt-10 space-y-3">
          <button
            type="button"
            className={`${baseClass} ${
              activeItem === "materials" ? activeClass : inactiveClass
            } cursor-pointer`}
          >
            <span className="mt-0.5 inline-block h-5 w-5 rounded-md bg-[#1E73F7]/20" />
            <span className="flex-1 text-left leading-5">Навчальні матеріали</span>
          </button>
          <button
            type="button"
            className={`${baseClass} ${
              activeItem === "students" ? activeClass : inactiveClass
            } cursor-pointer`}
          >
            <span className="mt-0.5 inline-block h-5 w-5 rounded-md bg-slate-200" />
            <span className="flex-1 text-left leading-5">Учні</span>
          </button>
        </div>
      ) : null}
      {afterPrimaryNav ? (
        <div className={showPrimaryNav ? "mt-4" : "mt-8"}>
          {afterPrimaryNav}
        </div>
      ) : null}
      {children ? (
        <div className={dividerClass}>
          {children}
        </div>
      ) : null}
    </aside>
  );
};

export default TeacherSidebar;
