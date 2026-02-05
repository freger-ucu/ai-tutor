interface ButtonProps {
  label?: string;
  onClick?: () => void;
}
const Button = ({ label, onClick }: ButtonProps) => {
  return (
    <button
      className="inline-flex cursor-pointer items-center gap-4 rounded-full border border-white bg-white px-10 py-4 text-2xl font-semibold tracking-tight text-[#1E73F7] transition hover:bg-[#E9F1FF] hover:border-[#1557c0]"
      onClick={onClick}
    >
      {label}
    </button>
  );
};

export default Button;
