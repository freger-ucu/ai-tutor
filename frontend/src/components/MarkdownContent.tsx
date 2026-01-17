import { useEffect, useRef } from "react";
import katex from "katex";
import "katex/dist/katex.min.css";

const escapeHtml = (value: string) =>
  value
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");

// Placeholder system to protect LaTeX from escaping/formatting
// Using distinctive markers that won't appear in normal text
const PLACEHOLDER_PREFIX = "%%%LATEX_PLACEHOLDER_";
const PLACEHOLDER_SUFFIX = "_END%%%";

const extractAndRenderLatex = (
  text: string
): { processed: string; placeholders: Map<string, string> } => {
  const placeholders = new Map<string, string>();
  let counter = 0;
  let result = text;

  const createPlaceholder = (rendered: string): string => {
    const key = `${PLACEHOLDER_PREFIX}${counter++}${PLACEHOLDER_SUFFIX}`;
    placeholders.set(key, rendered);
    return key;
  };

  // Process block math first ($$...$$)
  result = result.replace(/\$\$([^$]+)\$\$/g, (_, latex) => {
    try {
      const rendered = `<div class="katex-block my-4">${katex.renderToString(latex.trim(), {
        displayMode: true,
        throwOnError: false,
        strict: false,
      })}</div>`;
      return createPlaceholder(rendered);
    } catch {
      return createPlaceholder(
        `<div class="katex-block my-4 text-red-500">[Math Error: ${escapeHtml(latex)}]</div>`
      );
    }
  });

  // Process inline math ($...$) - be careful not to match escaped $ or currency
  result = result.replace(/\$([^$\n]+)\$/g, (match, latex) => {
    // Skip if it looks like currency (e.g., $100)
    if (/^\d/.test(latex.trim())) {
      return match;
    }
    try {
      const rendered = katex.renderToString(latex.trim(), {
        displayMode: false,
        throwOnError: false,
        strict: false,
      });
      return createPlaceholder(rendered);
    } catch {
      return createPlaceholder(
        `<span class="text-red-500">[Math Error: ${escapeHtml(latex)}]</span>`
      );
    }
  });

  // Also handle \[...\] for block (alternative LaTeX delimiters) - use non-greedy match
  result = result.replace(/\\\[(.+?)\\\]/g, (_, latex) => {
    try {
      const rendered = `<div class="katex-block my-4">${katex.renderToString(latex.trim(), {
        displayMode: true,
        throwOnError: false,
        strict: false,
      })}</div>`;
      return createPlaceholder(rendered);
    } catch {
      return createPlaceholder(
        `<div class="katex-block my-4 text-red-500">[Math Error: ${escapeHtml(latex)}]</div>`
      );
    }
  });

  // Handle \(...\) for inline - use non-greedy match to handle nested parentheses
  result = result.replace(/\\\((.+?)\\\)/g, (_, latex) => {
    try {
      const rendered = katex.renderToString(latex.trim(), {
        displayMode: false,
        throwOnError: false,
        strict: false,
      });
      return createPlaceholder(rendered);
    } catch {
      return createPlaceholder(
        `<span class="text-red-500">[Math Error: ${escapeHtml(latex)}]</span>`
      );
    }
  });

  return { processed: result, placeholders };
};

const restorePlaceholders = (
  text: string,
  placeholders: Map<string, string>
): string => {
  let result = text;
  for (const [key, value] of placeholders) {
    result = result.split(key).join(value);
  }
  return result;
};

const formatInline = (
  value: string,
  placeholders: Map<string, string>
): string => {
  let result = value;

  // Apply inline formatting (code, bold, italic)
  result = result.replace(
    /`([^`]+)`/g,
    '<code class="rounded bg-slate-100 px-1 py-0.5 text-xs font-semibold text-slate-900">$1</code>'
  );
  result = result.replace(
    /\*\*([^*]+)\*\*/g,
    '<strong class="font-semibold text-slate-900">$1</strong>'
  );
  result = result.replace(
    /\*([^*]+)\*/g,
    '<em class="italic text-slate-800">$1</em>'
  );

  // Restore LaTeX placeholders after all formatting
  result = restorePlaceholders(result, placeholders);

  return result;
};

const renderMarkdown = (markdown: string): string => {
  // First, extract and render all LaTeX before any other processing
  const { processed, placeholders } = extractAndRenderLatex(markdown);

  // Clean up stray backslashes (LaTeX line break artifacts)
  const cleaned = processed.replace(/\\$/gm, "").replace(/\\\s*$/gm, "");

  const lines = cleaned.replace(/\r\n/g, "\n").split("\n");
  let html = "";
  let currentList: "ul" | "ol" | null = null;

  const closeLists = () => {
    if (currentList) {
      html += currentList === "ul" ? "</ul>" : "</ol>";
      currentList = null;
    }
  };

  let prevWasEmpty = false;
  for (const line of lines) {
    const trimmed = line.trim();
    if (!trimmed) {
      closeLists();
      if (!prevWasEmpty) {
        prevWasEmpty = true;
      }
      continue;
    }
    prevWasEmpty = false;

    // Check headings from most specific to least (#### before ###)
    if (trimmed.startsWith("#### ")) {
      closeLists();
      const content = formatInline(escapeHtml(trimmed.slice(5)), placeholders);
      html += `<h4 class="mt-5 text-sm font-semibold text-slate-900">${content}</h4>`;
      continue;
    }
    if (trimmed.startsWith("### ")) {
      closeLists();
      const content = formatInline(escapeHtml(trimmed.slice(4)), placeholders);
      html += `<h3 class="mt-6 text-base font-semibold text-slate-900">${content}</h3>`;
      continue;
    }
    if (trimmed.startsWith("## ")) {
      closeLists();
      const content = formatInline(escapeHtml(trimmed.slice(3)), placeholders);
      html += `<h2 class="mt-6 text-lg font-semibold text-slate-900">${content}</h2>`;
      continue;
    }
    if (trimmed.startsWith("# ")) {
      closeLists();
      const content = formatInline(escapeHtml(trimmed.slice(2)), placeholders);
      html += `<h1 class="mt-6 text-xl font-bold text-slate-900">${content}</h1>`;
      continue;
    }

    // Bullet points
    if (trimmed.startsWith("- ") || trimmed.startsWith("• ") || trimmed.startsWith("* ")) {
      if (currentList !== "ul") {
        closeLists();
        html += '<ul class="mt-3 list-disc space-y-2 pl-5">';
        currentList = "ul";
      }
      const content = formatInline(escapeHtml(trimmed.slice(2)), placeholders);
      html += `<li>${content}</li>`;
      continue;
    }

    // Numbered lists (1. or 1))
    const orderedMatch = trimmed.match(/^(\d+)[\.\)]\s+/);
    if (orderedMatch) {
      if (currentList !== "ol") {
        closeLists();
        html += '<ol class="mt-3 list-decimal space-y-2 pl-5">';
        currentList = "ol";
      }
      const content = formatInline(
        escapeHtml(trimmed.slice(orderedMatch[0].length)),
        placeholders
      );
      html += `<li>${content}</li>`;
      continue;
    }

    closeLists();
    const content = formatInline(escapeHtml(trimmed), placeholders);
    html += `<p class="mt-3">${content}</p>`;
  }

  closeLists();
  return html;
};

interface MarkdownContentProps {
  content: string;
  className?: string;
  skipFirstHeading?: boolean;
}

const removeFirstHeading = (markdown: string): string => {
  const lines = markdown.replace(/\r\n/g, "\n").split("\n");
  let foundFirstContent = false;
  const filteredLines: string[] = [];

  for (let i = 0; i < lines.length; i++) {
    const trimmed = lines[i].trim();

    // Skip leading empty lines
    if (!foundFirstContent && trimmed === "") {
      continue;
    }

    // Check if this is the first content (heading or paragraph to skip)
    if (!foundFirstContent) {
      // If it's a markdown heading, skip it
      if (trimmed.startsWith("# ") || trimmed.startsWith("## ") || trimmed.startsWith("### ")) {
        foundFirstContent = true;
        continue;
      }

      // If it's a regular paragraph (not a list item or numbered item), skip it
      // This handles cases like "Коротке нагадування ключових понять..."
      if (!trimmed.startsWith("- ") && !trimmed.match(/^\d+[\.\)]\s/)) {
        foundFirstContent = true;
        continue;
      }
    }

    filteredLines.push(lines[i]);
  }

  // Remove leading empty lines after removing the heading/paragraph
  while (filteredLines.length > 0 && filteredLines[0].trim() === "") {
    filteredLines.shift();
  }

  return filteredLines.join("\n");
};

const MarkdownContent = ({ content, className = "", skipFirstHeading = false }: MarkdownContentProps) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const processedContent = skipFirstHeading ? removeFirstHeading(content) : content;
  const html = renderMarkdown(processedContent);

  useEffect(() => {
    // Re-render KaTeX if needed after mount
    if (containerRef.current) {
      // KaTeX is already rendered in the HTML string, but we trigger
      // a check to ensure all fonts are loaded
      const katexElements = containerRef.current.querySelectorAll(".katex");
      if (katexElements.length > 0) {
        // Force a reflow to ensure KaTeX renders properly
        containerRef.current.offsetHeight;
      }
    }
  }, [content]);

  return (
    <div
      ref={containerRef}
      className={`text-sm leading-relaxed text-slate-800 ${className}`}
      dangerouslySetInnerHTML={{ __html: html }}
    />
  );
};

export default MarkdownContent;
