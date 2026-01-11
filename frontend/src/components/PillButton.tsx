import type { ReactNode } from "react";

interface PillButtonProps {
  label: string;
  onClick?: () => void;
  variant?: "light" | "white";
  size?: "sm" | "md";
  icon?: ReactNode;
  className?: string;
}

const variantClasses = {
  light: "bg-[#E9F1FF] text-[#1E73F7]",
  white: "bg-white text-[#1E73F7]",
};

const sizeClasses = {
  sm: "px-4 py-2 text-xs",
  md: "px-4 py-3 text-sm",
};

const PillButton = ({
  label,
  onClick,
  variant = "light",
  size = "sm",
  icon,
  className = "",
}: PillButtonProps) => {
  return (
    <button
      type="button"
      onClick={onClick}
      className={`inline-flex cursor-pointer items-center gap-2 rounded-full font-semibold transition ${variantClasses[variant]} ${sizeClasses[size]} ${className}`}
    >
      {icon}
      {label}
    </button>
  );
};

export default PillButton;
