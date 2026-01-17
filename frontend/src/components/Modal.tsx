import { useEffect } from "react";
import type { ReactNode } from "react";

type ModalSize = "sm" | "md" | "lg" | "xl";

interface ModalProps {
  isOpen: boolean;
  onClose: () => void;
  title?: string;
  children: ReactNode;
  footer?: ReactNode;
  size?: ModalSize;
  closeOnOverlayClick?: boolean;
  closeOnEsc?: boolean;
  showCloseButton?: boolean;
  className?: string;
}

const sizeClasses: Record<ModalSize, string> = {
  sm: "w-[360px]",
  md: "w-[520px]",
  lg: "w-[720px]",
  xl: "w-[900px]",
};

const Modal = ({
  isOpen,
  onClose,
  title,
  children,
  footer,
  size = "md",
  closeOnOverlayClick = true,
  closeOnEsc = true,
  showCloseButton = true,
  className = "",
}: ModalProps) => {
  useEffect(() => {
    if (!isOpen || !closeOnEsc) {
      return;
    }

    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        onClose();
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isOpen, closeOnEsc, onClose]);

  if (!isOpen) {
    return null;
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div
        className="absolute inset-0 bg-black/50"
        onClick={closeOnOverlayClick ? onClose : undefined}
      />
      <div
        role="dialog"
        aria-modal="true"
        className={`relative z-10 max-w-[90vw] rounded-2xl bg-white p-6 text-sm shadow-2xl lg:text-base ${sizeClasses[size]} ${className}`}
      >
        {((title && title.length > 0) || showCloseButton) && (
          <div className="relative flex items-center justify-center">
            {title ? (
              <div className="text-xl font-semibold text-slate-900 lg:text-3xl">
                {title}
              </div>
            ) : null}
            {showCloseButton ? (
              <button
                type="button"
                onClick={onClose}
                className="absolute right-0 rounded-full px-2 py-1 text-xl text-slate-500 transition hover:bg-slate-100 hover:text-slate-700 cursor-pointer lg:text-2xl"
                aria-label="Close modal"
              >
                ×
              </button>
            ) : null}
          </div>
        )}
        <div className="mt-8">{children}</div>
        {footer ? <div className="mt-6">{footer}</div> : null}
      </div>
    </div>
  );
};

export default Modal;
