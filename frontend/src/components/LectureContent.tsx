/**
 * LectureContent - Component for displaying lecture notes with role-based source visibility
 *
 * This component renders lecture content (main text) for all users, but only shows
 * the list of sources to teachers. This allows teachers to see references and citations
 * while keeping the student view focused on the content itself.
 *
 * @example
 * // Teacher view with structured sources - shows content AND sources
 * <LectureContent
 *   content="Main lecture text about algebra..."
 *   sources={[
 *     { name: "Підручник 1", pages: "19-25" },
 *     { name: "Підручник 2", pages: "10-18" }
 *   ]}
 *   userRole="teacher"
 * />
 *
 * @example
 * // Teacher view with simple string sources (backward compatible)
 * <LectureContent
 *   content="Main lecture text about algebra..."
 *   sources={["Textbook A", "Article B"]}
 *   userRole="teacher"
 * />
 *
 * @example
 * // Student view - shows content only (sources hidden)
 * <LectureContent
 *   content="Main lecture text about algebra..."
 *   sources={[{ name: "Підручник 1", pages: "19-25" }]}
 *   userRole="student"
 * />
 */

import MarkdownContent from "./MarkdownContent";

/**
 * Supported user roles for the component.
 * - "teacher": Full access, sees content + sources
 * - "student": Limited access, sees content only
 */
type UserRole = "teacher" | "student";

/**
 * Structured source reference with name and optional pages.
 * Used for textbook references with page numbers.
 */
export interface SourceItem {
  /** Name of the source (e.g., "Підручник 1", "Українська мова 8 клас") */
  name: string;
  /** Optional page range (e.g., "19-25", "10-18") */
  pages?: string;
}

/**
 * Source can be either a simple string or a structured object.
 * This allows backward compatibility with existing string sources
 * while supporting the new structured format.
 */
export type Source = string | SourceItem;

interface LectureContentProps {
  /** Main lecture text content (supports markdown formatting) */
  content: string;
  /** Array of source references - can be strings or structured objects */
  sources: Source[];
  /** User role - determines whether sources are displayed */
  userRole: UserRole;
  /** Optional CSS classes for the container */
  className?: string;
  /** Optional: Skip the first heading in content (useful when topic is shown separately) */
  skipFirstHeading?: boolean;
  /** Optional: Title to display as heading before content */
  title?: string;
}

/**
 * Formats a source item for display.
 * - For strings: returns the string as-is
 * - For objects: formats as "Name: X-Y сторінка" or just "Name" if no pages
 *
 * @param source - Source to format (string or SourceItem)
 * @returns Formatted string for display
 */
const formatSource = (source: Source): string => {
  // Handle simple string sources (backward compatibility)
  if (typeof source === "string") {
    return source;
  }

  // Handle structured source objects
  const { name, pages } = source;

  // If no pages specified, return just the name
  if (!pages || pages.trim() === "") {
    return name;
  }

  // Format as "Name: pages сторінка"
  return `${name}: ${pages} сторінка`;
};

/**
 * LectureContent displays lecture material with role-based source visibility.
 *
 * The component uses the existing MarkdownContent component to render the main
 * lecture text with proper formatting (headings, lists, LaTeX math, etc.).
 *
 * Sources are displayed in a visually distinct section at the bottom, styled
 * with a lighter color and smaller font to differentiate from main content.
 * This section is ONLY visible to users with the "teacher" role.
 */
const LectureContent = ({
  content,
  sources,
  userRole,
  className = "",
  skipFirstHeading = false,
  title,
}: LectureContentProps) => {
  // Determine if sources should be shown based on user role
  // Only teachers can see the sources section
  const showSources = userRole === "teacher" && sources.length > 0;

  return (
    <div className={`lecture-content ${className}`}>
      {/* Title heading - visible to ALL users if provided */}
      {title && (
        <h1 className="text-xl font-bold text-slate-900 mb-4">{title}</h1>
      )}

      {/* Main lecture content - visible to ALL users */}
      <div className="lecture-content__body">
        {content ? (
          <MarkdownContent content={content} skipFirstHeading={skipFirstHeading} />
        ) : (
          <p className="text-slate-500 italic">Зміст лекції відсутній.</p>
        )}
      </div>

      {/*
       * Sources section - ONLY visible to teachers.
       * Styled with smaller font and lighter color to distinguish from main content.
       * Uses a top border to visually separate it from the lecture body.
       *
       * Sources are formatted as:
       * - "Підручник 1: 19-25 сторінка" (if pages specified)
       * - "Підручник 1" (if no pages)
       * - Simple string as-is (backward compatibility)
       */}
      {showSources && (
        <div className="lecture-content__sources mt-8 pt-6 border-t border-slate-200">
          <h4 className="text-sm font-semibold text-slate-500 mb-3">
            Джерела:
          </h4>
          <ul className="space-y-1.5">
            {sources.map((source, index) => (
              <li
                key={index}
                className="text-xs text-slate-400 leading-relaxed flex items-start gap-2"
              >
                {/* Numbered marker for each source */}
                <span className="text-slate-300 select-none">{index + 1}.</span>
                <span>{formatSource(source)}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
};

export default LectureContent;
