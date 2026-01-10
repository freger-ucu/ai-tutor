interface ButtonProps {
  label?: string;
  onClick?: () => void;
}
const Button = ({ label, onClick }: ButtonProps) => {
  return (
    <button
      className="inline-flex items-center gap-4 rounded-full bg-white px-10 py-4 text-2xl font-light tracking-tight text-[#1E73F7] shadow-sm transition-colors hover:bg-blue-50"
      onClick={onClick}
    >
      {label}
    </button>
  );
};

export default Button;
