/**
 * useSidebarFilter - Dynamic sidebar filtering hook
 *
 * This hook filters sidebar items based on the current page/route.
 * When viewing a specific item (note, test, topic), that item is hidden
 * from the sidebar to avoid redundant navigation links.
 *
 * @example
 * // In a Note page - filters out the current note
 * const { filteredNotes, filteredTests } = useSidebarFilter({
 *   notes: sidebarNotes,
 *   tests: sidebarTests,
 *   currentItemId: noteId,
 *   currentItemType: 'note'
 * });
 */

import { useMemo } from 'react';

// Generic item interface - supports any item with an id property
interface WithId {
  id: string;
}

// Configuration for the filter
interface SidebarFilterConfig<TNote extends WithId, TTest extends WithId> {
  /** Array of note items to filter */
  notes: TNote[];
  /** Array of test items to filter */
  tests: TTest[];
  /** Current item ID from route params (noteId, testId, topicId) */
  currentItemId?: string;
  /** Type of the current item being viewed */
  currentItemType: 'note' | 'test' | 'topic' | null;
}

// Return type with filtered arrays
interface SidebarFilterResult<TNote extends WithId, TTest extends WithId> {
  /** Notes array with current item filtered out (if viewing a note) */
  filteredNotes: TNote[];
  /** Tests array with current item filtered out (if viewing a test) */
  filteredTests: TTest[];
  /** Whether the current item is a note */
  isViewingNote: boolean;
  /** Whether the current item is a test */
  isViewingTest: boolean;
}

/**
 * Hook to filter sidebar items based on current route/page
 *
 * Behavior:
 * - When viewing a note: that note is hidden from sidebar notes list
 * - When viewing a test: that test is hidden from sidebar tests list
 * - When viewing a topic: all items are shown (no filtering)
 * - All other items remain visible in the sidebar
 *
 * @param config - Configuration object with notes, tests, currentItemId, and currentItemType
 * @returns Object with filteredNotes, filteredTests, and view state booleans
 */
export function useSidebarFilter<TNote extends WithId, TTest extends WithId>(
  config: SidebarFilterConfig<TNote, TTest>
): SidebarFilterResult<TNote, TTest> {
  const { notes, tests, currentItemId, currentItemType } = config;

  return useMemo(() => {
    const isViewingNote = currentItemType === 'note';
    const isViewingTest = currentItemType === 'test';

    // Filter notes: remove current note if viewing a note page
    const filteredNotes = isViewingNote && currentItemId
      ? notes.filter((note) => note.id !== currentItemId)
      : notes;

    // Filter tests: remove current test if viewing a test page
    const filteredTests = isViewingTest && currentItemId
      ? tests.filter((test) => test.id !== currentItemId)
      : tests;

    return {
      filteredNotes,
      filteredTests,
      isViewingNote,
      isViewingTest,
    };
  }, [notes, tests, currentItemId, currentItemType]);
}

export default useSidebarFilter;
