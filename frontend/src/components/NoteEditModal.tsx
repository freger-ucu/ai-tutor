/**
 * NoteEditModal - Full-screen modal for editing note content
 *
 * Provides a complete interface for teachers to:
 * - Edit note content in markdown format
 * - Preview the rendered content
 * - Save changes or discard them
 *
 * Styled consistently with TestEditModal for a unified editing experience.
 */

import { useCallback, useEffect, useState } from "react";
import MarkdownContent from "./MarkdownContent";

interface NoteEditModalProps {
  /** Whether the modal is open */
  isOpen: boolean;
  /** The note title (for display) */
  noteTitle: string;
  /** Initial content */
  content: string;
  /** Callback when changes are saved */
  onSave: (content: string) => void;
  /** Callback when modal is closed (without saving) */
  onClose: () => void;
}

const NoteEditModal = ({
  isOpen,
  noteTitle,
  content,
  onSave,
  onClose,
}: NoteEditModalProps) => {
  const [draftContent, setDraftContent] = useState("");
  const [isPreviewMode, setIsPreviewMode] = useState(false);
  const [isSaving, setIsSaving] = useState(false);

  // Initialize draft when modal opens
  useEffect(() => {
    if (isOpen) {
      setDraftContent(content);
      setIsPreviewMode(false);
    }
  }, [isOpen, content]);

  // Check if there are unsaved changes
  const hasChanges = draftContent !== content;

  /**
   * Handle save - commit changes and close modal
   */
  const handleSave = useCallback(() => {
    if (isSaving) return;

    setIsSaving(true);
    try {
      onSave(draftContent);
      onClose();
    } finally {
      setIsSaving(false);
    }
  }, [draftContent, onSave, onClose, isSaving]);

  /**
   * Handle reset - discard all changes
   */
  const handleReset = useCallback(() => {
    setDraftContent(content);
  }, [content]);

  /**
   * Handle close - warn if unsaved changes
   */
  const handleClose = useCallback(() => {
    if (hasChanges) {
      const confirmed = window.confirm("Ви маєте незбережені зміни. Закрити без збереження?");
      if (!confirmed) return;
    }
    onClose();
  }, [hasChanges, onClose]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex flex-col bg-[#1E73F7]">
      {/* Header */}
      <header className="shrink-0 px-6 py-4">
        <div className="flex items-center justify-between max-w-6xl mx-auto">
          <div className="flex items-center gap-4">
            <button
              type="button"
              onClick={handleClose}
              className="rounded-lg p-2 text-white/70 hover:bg-white/10 hover:text-white"
              title="Закрити"
            >
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M18 6L6 18M6 6l12 12" />
              </svg>
            </button>
            <div>
              <h1 className="text-xl font-bold text-white">
                Редагування конспекту
              </h1>
              <p className="text-sm text-white/70">{noteTitle}</p>
            </div>
          </div>

          {/* Action buttons */}
          <div className="flex items-center gap-3">
            {/* Preview toggle */}
            <button
              type="button"
              onClick={() => setIsPreviewMode(!isPreviewMode)}
              className="rounded-full border border-white/20 bg-white/10 px-5 py-2.5 text-sm font-semibold text-white transition hover:bg-white/20"
            >
              {isPreviewMode ? "Редагувати" : "Перегляд"}
            </button>

            {/* Save button */}
            <button
              type="button"
              onClick={handleSave}
              disabled={!hasChanges || isSaving}
              className="rounded-full border border-white bg-white px-5 py-2.5 text-sm font-semibold text-[#1E73F7] transition hover:bg-slate-100 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
            >
              {isSaving ? (
                <>
                  <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                  </svg>
                  Збереження...
                </>
              ) : (
                "Зберегти"
              )}
            </button>
          </div>
        </div>
      </header>

      {/* Content area */}
      <main className="flex-1 min-h-0 py-4">
        <div className="max-w-4xl mx-auto px-6 h-full">
          {isPreviewMode ? (
            <div className="rounded-[22px] bg-white p-6 shadow-lg h-full flex flex-col">
              <div className="prose prose-slate max-w-none flex-1 overflow-y-auto">
                {draftContent ? (
                  <MarkdownContent content={draftContent} />
                ) : (
                  <p className="text-slate-400 italic">Вміст відсутній</p>
                )}
              </div>
            </div>
          ) : (
            <div className="rounded-[22px] bg-white p-6 shadow-lg h-full flex flex-col">
              <label className="text-sm font-medium text-slate-700 mb-3 block shrink-0">
                Зміст конспекту (Markdown)
              </label>
              <textarea
                value={draftContent}
                onChange={(e) => setDraftContent(e.target.value)}
                className="flex-1 w-full rounded-xl border border-slate-200 p-4 text-sm text-slate-800 resize-none focus:border-[#1E73F7] focus:outline-none focus:ring-1 focus:ring-[#1E73F7] font-mono"
                placeholder="Введіть зміст конспекту..."
              />
              <p className="mt-2 text-xs text-slate-400 shrink-0">
                Підтримується Markdown: **жирний**, *курсив*, # заголовки, - списки
              </p>
            </div>
          )}
        </div>
      </main>

      {/* Footer with status */}
      <footer className="shrink-0 px-6 py-3">
        <div className="max-w-6xl mx-auto flex items-center justify-between text-sm text-white/70">
          <div>
            Символів: <span className="font-semibold text-white">{draftContent.length}</span>
          </div>
          {hasChanges && (
            <div className="flex items-center gap-2 text-amber-300">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
                <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z" />
              </svg>
              Є незбережені зміни
            </div>
          )}
        </div>
      </footer>
    </div>
  );
};

export default NoteEditModal;
