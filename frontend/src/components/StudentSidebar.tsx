/**
 * StudentSidebar - Static navigation sidebar for student interface
 *
 * This sidebar is intentionally STATIC and displays only:
 * 1. Student profile (name and class)
 * 2. List of subjects the student is taking
 *
 * IMPORTANT: This sidebar must NEVER change based on:
 * - Current page or route
 * - Selected topics, tests, or materials
 * - Any other dynamic content
 *
 * The sidebar provides consistent navigation to subject views only.
 * Navigation back to topics or materials should use breadcrumbs, NOT the sidebar.
 */

import type { ReactNode } from "react";
import { useNavigate } from "react-router-dom";

export interface SubjectItem {
  /** Unique identifier for the subject (e.g., "algebra", "history") */
  id: string;
  /** Display label for the subject (e.g., "Алгебра", "Історія України") */
  label: string;
  /** Icon element to display next to the subject label */
  icon: ReactNode;
}

interface StudentSidebarProps {
  /** Student ID used for navigation */
  studentId: string;
  /** Student display name shown at top of sidebar */
  studentName?: string;
  /** Class label (e.g., "8-А") shown below student name */
  classLabel?: string;
  /** Array of subjects the student is taking - fetched from backend */
  subjects: SubjectItem[];
  /** Which subject is currently active/selected */
  activeSubjectId?: string;
}

/**
 * StudentSidebar component - renders a STATIC sidebar with student profile and subjects.
 *
 * This component intentionally does NOT accept children or any dynamic content props.
 * The sidebar always displays the same structure regardless of application state:
 * - Student profile section (avatar, name, class)
 * - List of subjects (fetched from backend, passed via props)
 *
 * No other links, buttons, or navigation elements should appear.
 */
const StudentSidebar = ({
  studentId,
  studentName,
  classLabel,
  subjects,
  activeSubjectId,
}: StudentSidebarProps) => {
  const navigate = useNavigate();
  const displayName = studentName || `Учень ${studentId}`;

  // Static CSS classes for subject buttons
  const baseClass =
    "flex w-full items-center justify-start gap-3 rounded-2xl px-4 py-3 text-sm cursor-pointer";
  const activeClass = "bg-[#E9F1FF] font-semibold text-[#1E73F7]";
  const inactiveClass = "font-medium text-slate-800 hover:bg-slate-100";

  const handleLogout = () => {
    navigate("/");
  };

  return (
    <aside className="w-64 shrink-0 bg-white px-6 py-8 flex flex-col">
      {/* Student profile section */}
      <div className="flex items-center gap-3">
        <div
          className="h-12 w-12 overflow-hidden rounded-full bg-slate-200"
          style={{
            backgroundImage:
              "url('https://images.unsplash.com/photo-1599566150163-29194dcaad36?ixlib=rb-4.0.3&auto=format&fit=crop&w=200&q=80')",
            backgroundSize: "cover",
            backgroundPosition: "center",
          }}
        />
        <div>
          <div className="text-base font-semibold text-slate-900">
            {displayName}
          </div>
          {classLabel && (
            <div className="text-xs text-slate-500">Клас: {classLabel}</div>
          )}
        </div>
      </div>

      {/*
       * STATIC NAVIGATION - Shows ONLY the list of subjects.
       *
       * These buttons navigate to the main subject views and do NOT
       * change based on current page, topic, or material being viewed.
       *
       * The subject list comes from the backend and updates automatically
       * if the student's enrolled subjects change.
       */}
      <div className="mt-10 space-y-3">
        {subjects.map((subject) => {
          const isActive = activeSubjectId === subject.id;
          return (
            <button
              key={subject.id}
              type="button"
              onClick={() =>
                navigate(`/student/${studentId}?subject=${subject.id}`)
              }
              className={`${baseClass} ${isActive ? activeClass : inactiveClass}`}
            >
              <span
                className={`flex items-center justify-center ${
                  isActive ? "text-[#1E73F7]" : "text-slate-600"
                }`}
              >
                {subject.icon}
              </span>
              <span className="flex-1 text-left leading-5">{subject.label}</span>
            </button>
          );
        })}
      </div>

      {/* Logout button at the bottom */}
      <div className="mt-auto pt-6">
        <button
          type="button"
          onClick={handleLogout}
          className="flex w-full items-center justify-start gap-3 rounded-2xl px-4 py-3 text-sm font-medium text-slate-500 hover:bg-red-50 hover:text-red-600 cursor-pointer transition"
        >
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" />
            <polyline points="16 17 21 12 16 7" />
            <line x1="21" y1="12" x2="9" y2="12" />
          </svg>
          <span className="text-left leading-5">Вийти</span>
        </button>
      </div>
    </aside>
  );
};

export default StudentSidebar;
