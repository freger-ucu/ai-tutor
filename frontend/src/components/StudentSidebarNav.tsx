import { Link } from "react-router-dom";

interface NavItem {
  label: string;
  href?: string;
  isActive?: boolean;
}

interface StudentSidebarNavProps {
  items: NavItem[];
}

const BackIcon = () => (
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
    <polyline points="15 18 9 12 15 6" />
  </svg>
);

const StudentSidebarNav = ({ items }: StudentSidebarNavProps) => {
  if (items.length === 0) return null;

  const activeItem = items.find((item) => item.isActive);
  const backItems = items.filter((item) => !item.isActive && item.href);

  return (
    <div className="space-y-2">
      {/* Back navigation - show only the immediate parent for simplicity */}
      {backItems.length > 0 && (
        <div className="space-y-1">
          {backItems.slice(-1).map((item, index) => (
            <Link
              key={index}
              to={item.href!}
              className="flex items-center gap-2 rounded-xl px-3 py-2 text-sm font-medium text-slate-500 transition-all hover:bg-slate-100 hover:text-slate-700"
            >
              <BackIcon />
              <span className="truncate">{item.label}</span>
            </Link>
          ))}
        </div>
      )}

      {/* Current location */}
      {activeItem && (
        <div className="rounded-xl bg-[#E9F1FF] px-4 py-2.5 text-sm font-semibold text-[#1E73F7]">
          <span className="truncate block">{activeItem.label}</span>
        </div>
      )}
    </div>
  );
};

export default StudentSidebarNav;
