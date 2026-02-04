import { useState } from "react";
import type { AssignmentScope } from "../data/materialsStorage";

interface AudienceInfoProps {
  assignmentScope?: AssignmentScope;
  assignedLevels?: ("weak" | "medium" | "strong")[];
  assignedStudents?: number[];
}

const levelLabels: Record<string, string> = {
  weak: "Низький",
  medium: "Середній",
  strong: "Високий",
};

const levelColors: Record<string, string> = {
  weak: "bg-pink-100 text-pink-700",
  medium: "bg-yellow-100 text-yellow-700",
  strong: "bg-green-100 text-green-700",
};

/**
 * Displays audience/assignment information for a material.
 * Shows levels or students with expandable list.
 */
const AudienceInfo = ({
  assignmentScope,
  assignedLevels,
  assignedStudents,
}: AudienceInfoProps) => {
  const [isExpanded, setIsExpanded] = useState(false);

  // If no assignment scope or it's "class", show nothing
  if (!assignmentScope || assignmentScope === "class") {
    return (
      <div className="flex items-center gap-2 text-sm text-white/80">
        <svg
          width="16"
          height="16"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
        >
          <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" />
          <circle cx="9" cy="7" r="4" />
          <path d="M23 21v-2a4 4 0 0 0-3-3.87" />
          <path d="M16 3.13a4 4 0 0 1 0 7.75" />
        </svg>
        <span>Весь клас</span>
      </div>
    );
  }

  // Show levels
  if (assignmentScope === "levels" && assignedLevels && assignedLevels.length > 0) {
    return (
      <div className="flex items-center gap-2 text-sm">
        <span className="text-white/60">Рівні:</span>
        <div className="flex gap-1.5">
          {assignedLevels.map((level) => (
            <span
              key={level}
              className={`rounded-full px-2.5 py-0.5 text-xs font-medium ${levelColors[level]}`}
            >
              {levelLabels[level]}
            </span>
          ))}
        </div>
      </div>
    );
  }

  // Show students with expandable list
  if (assignmentScope === "students" && assignedStudents && assignedStudents.length > 0) {
    const hasMany = assignedStudents.length > 3;
    const displayStudents = isExpanded ? assignedStudents : assignedStudents.slice(0, 3);

    return (
      <div className="flex flex-wrap items-center gap-2 text-sm">
        <span className="text-white/60">Учні:</span>
        <div className="flex flex-wrap gap-1.5">
          {displayStudents.map((studentId) => (
            <span
              key={studentId}
              className="rounded-full bg-white/20 px-2.5 py-0.5 text-xs font-medium text-white"
            >
              {studentId}
            </span>
          ))}
          {hasMany && !isExpanded && (
            <button
              type="button"
              onClick={() => setIsExpanded(true)}
              className="rounded-full bg-white/10 px-2.5 py-0.5 text-xs font-medium text-white/80 hover:bg-white/20 transition"
            >
              +{assignedStudents.length - 3} ще
            </button>
          )}
          {hasMany && isExpanded && (
            <button
              type="button"
              onClick={() => setIsExpanded(false)}
              className="rounded-full bg-white/10 px-2.5 py-0.5 text-xs font-medium text-white/80 hover:bg-white/20 transition"
            >
              згорнути
            </button>
          )}
        </div>
      </div>
    );
  }

  return (
    <div className="text-sm text-white/60">
      Не призначено
    </div>
  );
};

export default AudienceInfo;
