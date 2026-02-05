import { useState } from "react";
import type { AssignmentScope } from "../data/materialsStorage";

interface TargetAudienceIndicatorProps {
  /** The type of assignment: class, levels, or students */
  assignmentScope?: AssignmentScope;
  /** Array of assigned levels when scope is "levels" */
  assignedLevels?: ("weak" | "medium" | "strong")[];
  /** Array of assigned student IDs when scope is "students" */
  assignedStudents?: number[];
  /** Optional: Total count of students (for display purposes) */
  studentCount?: number;
  /** Optional: Map of student IDs to names for tooltip display */
  studentNames?: Record<number, string>;
  /** Optional: Compact mode for smaller cards */
  compact?: boolean;
}

const levelLabels: Record<string, string> = {
  weak: "Низький",
  medium: "Середній",
  strong: "Високий",
};

const levelColors: Record<string, { bg: string; text: string }> = {
  weak: { bg: "bg-pink-100", text: "text-pink-700" },
  medium: { bg: "bg-yellow-100", text: "text-yellow-700" },
  strong: { bg: "bg-green-100", text: "text-green-700" },
};

/**
 * Displays target audience information on material cards (notes/tests).
 *
 * Three scenarios:
 * 1. Whole Class: Shows "Весь клас" badge
 * 2. By Level: Shows level chips (Високий, Середній, Низький)
 * 3. Individual Students: Shows overlapping avatars with tooltips
 *
 * Styling: Background #1E73F7 at 10% opacity, text #000000 at 50% opacity
 */
const TargetAudienceIndicator = ({
  assignmentScope,
  assignedLevels,
  assignedStudents,
  studentCount,
  studentNames = {},
  compact = false,
}: TargetAudienceIndicatorProps) => {
  const [hoveredStudentId, setHoveredStudentId] = useState<number | null>(null);
  const [isExpanded, setIsExpanded] = useState(false);

  // Calculate the count of students to display
  const displayCount =
    assignmentScope === "students" && assignedStudents
      ? assignedStudents.length
      : assignmentScope === "levels" && assignedLevels
        ? (studentCount ?? assignedLevels.length)
        : (studentCount ?? 0);

  // Whole class scenario
  if (!assignmentScope || assignmentScope === "class") {
    return (
      <div className="flex items-center gap-2">
        <span
          className="text-xs font-medium"
          style={{ color: "rgba(0, 0, 0, 0.5)" }}
        >
          Учнів: {studentCount ?? "—"}
        </span>
        <span
          className="rounded-full px-2.5 py-0.5 text-xs font-medium"
          style={{
            backgroundColor: "rgba(30, 115, 247, 0.1)",
            color: "rgba(0, 0, 0, 0.5)",
          }}
        >
          Весь клас
        </span>
      </div>
    );
  }

  // By Level scenario
  if (
    assignmentScope === "levels" &&
    assignedLevels &&
    assignedLevels.length > 0
  ) {
    return (
      <div className="flex items-center gap-2">
        <span
          className="text-xs font-medium"
          style={{ color: "rgba(0, 0, 0, 0.5)" }}
        >
          Учнів: {displayCount}
        </span>
        <div className={`flex ${compact ? "gap-1" : "gap-1.5"}`}>
          {assignedLevels.map((level) => (
            <span
              key={level}
              className={`rounded-full ${compact ? "px-2 py-0.5 text-[10px]" : "px-2.5 py-0.5 text-xs"} font-medium ${levelColors[level].bg} ${levelColors[level].text}`}
            >
              {levelLabels[level]}
            </span>
          ))}
        </div>
      </div>
    );
  }

  // Individual Students scenario
  if (
    assignmentScope === "students" &&
    assignedStudents &&
    assignedStudents.length > 0
  ) {
    const maxVisible = compact ? 3 : 5;
    const hasMore = assignedStudents.length > maxVisible;
    const visibleStudents = isExpanded
      ? assignedStudents
      : assignedStudents.slice(0, maxVisible);
    const remainingCount = assignedStudents.length - maxVisible;

    return (
      <div className="flex flex-wrap items-center gap-2">
        <span
          className="text-xs font-medium"
          style={{ color: "rgba(0, 0, 0, 0.5)" }}
        >
          Учнів: {assignedStudents.length}
        </span>
        <div className="flex flex-wrap -space-x-2 gap-y-1">
          {visibleStudents.map((studentId, index) => {
            const studentName = studentNames[studentId] || `Учень ${studentId}`;
            return (
              <div
                key={studentId}
                className="relative"
                style={{ zIndex: visibleStudents.length - index }}
                onMouseEnter={() => setHoveredStudentId(studentId)}
                onMouseLeave={() => setHoveredStudentId(null)}
              >
                <div
                  className={`${compact ? "h-6 w-6" : "h-7 w-7"} overflow-hidden rounded-full border-2 border-white transition-transform hover:scale-110 hover:z-10`}
                >
                  <img
                    src={`https://api.dicebear.com/7.x/avataaars/svg?seed=${studentId}`}
                    alt={studentName}
                    className="h-full w-full object-cover"
                  />
                </div>
                {/* Tooltip */}
                {hoveredStudentId === studentId && (
                  <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 whitespace-nowrap rounded-lg bg-slate-800 px-2.5 py-1.5 text-xs font-medium text-white shadow-lg z-50">
                    {studentName}
                    <div className="absolute top-full left-1/2 -translate-x-1/2 border-4 border-transparent border-t-slate-800" />
                  </div>
                )}
              </div>
            );
          })}
          {hasMore && !isExpanded && (
            <button
              type="button"
              onClick={(e) => {
                e.preventDefault();
                e.stopPropagation();
                setIsExpanded(true);
              }}
              className={`flex ${compact ? "h-6 w-6 text-[10px]" : "h-7 w-7 text-xs"} items-center justify-center rounded-full border-2 border-white font-semibold cursor-pointer transition-all hover:scale-110`}
              style={{
                backgroundColor: "rgba(30, 115, 247, 0.1)",
                color: "rgba(0, 0, 0, 0.5)",
              }}
              title="Показати всіх"
            >
              +{remainingCount}
            </button>
          )}
          {hasMore && isExpanded && (
            <button
              type="button"
              onClick={(e) => {
                e.preventDefault();
                e.stopPropagation();
                setIsExpanded(false);
              }}
              className={`flex ${compact ? "h-6 px-2 text-[10px]" : "h-7 px-2.5 text-xs"} items-center justify-center rounded-full border-2 border-white font-semibold cursor-pointer transition-all hover:scale-105 ml-1`}
              style={{
                backgroundColor: "rgba(30, 115, 247, 0.1)",
                color: "rgba(0, 0, 0, 0.5)",
              }}
              title="Згорнути"
            >
              ←
            </button>
          )}
        </div>
      </div>
    );
  }

  // Fallback - not assigned
  return (
    <span
      className="text-xs font-medium"
      style={{ color: "rgba(0, 0, 0, 0.3)" }}
    >
      Не призначено
    </span>
  );
};

export default TargetAudienceIndicator;
