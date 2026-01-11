import type { ReactNode } from "react";
import Card from "./Card";

interface PanelProps {
  title?: string;
  children: ReactNode;
  className?: string;
  titleClassName?: string;
  contentClassName?: string;
}

const Panel = ({
  title,
  children,
  className = "",
  titleClassName = "",
  contentClassName = "",
}: PanelProps) => {
  return (
    <Card className={`rounded-[28px] p-6 ${className}`}>
      {title ? (
        <h2 className={`text-xl font-semibold text-slate-900 ${titleClassName}`}>
          {title}
        </h2>
      ) : null}
      <div className={`${title ? "mt-6 " : ""}${contentClassName}`}>
        {children}
      </div>
    </Card>
  );
};

export default Panel;
