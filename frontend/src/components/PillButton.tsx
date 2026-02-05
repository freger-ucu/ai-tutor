import type { ReactNode } from "react";

interface PillButtonProps {
  label: string;
  onClick?: () => void;
  variant?: "secondary" | "primary" | "danger" | "light" | "white";
  size?: "sm" | "md";
  icon?: ReactNode;
  className?: string;
  disabled?: boolean;
  type?: "button" | "submit" | "reset";
}

const variantClasses = {
  // Secondary - glass style for dark backgrounds (reference: "Редагувати конспект")
  secondary: "border border-white/20 bg-white/10 text-white hover:bg-[#1557c0] hover:border-[#1557c0]",
  // Primary - solid blue for main actions
  primary: "bg-[#1E73F7] text-white hover:bg-[#1557c0]",
  // Danger - for delete/destructive actions
  danger: "border border-white/20 bg-white/10 text-white hover:bg-red-500 hover:border-red-500",
  // Light - for light backgrounds
  light: "bg-[#E9F1FF] text-[#1E73F7] hover:bg-[#D4E4FF]",
  // White - white background button
  white: "bg-white text-[#1E73F7] hover:bg-slate-100",
};

const sizeClasses = {
  sm: "px-4 py-2 text-sm",
  md: "px-5 py-3 text-sm",
};

const PillButton = ({
  label,
  onClick,
  variant = "secondary",
  size = "sm",
  icon,
  className = "",
  disabled = false,
  type = "button",
}: PillButtonProps) => {
  return (
    <button
      type={type}
      onClick={onClick}
      disabled={disabled}
      className={`inline-flex cursor-pointer items-center justify-center gap-2 rounded-full font-semibold transition ${variantClasses[variant]} ${sizeClasses[size]} disabled:opacity-50 disabled:cursor-not-allowed ${className}`}
    >
      {icon}
      {label}
    </button>
  );
};

export default PillButton;
