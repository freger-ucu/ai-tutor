import type { ReactNode } from "react";

interface CardProps {
  children: ReactNode;
  variant?: "white" | "glass";
  className?: string;
}

const variantClasses = {
  white: "bg-white shadow-sm",
  glass: "border border-white/30 bg-white/10",
};

const Card = ({ children, variant = "white", className = "" }: CardProps) => {
  return (
    <div
      className={`rounded-[22px] ${variantClasses[variant]} ${className}`}
    >
      {children}
    </div>
  );
};

export default Card;
