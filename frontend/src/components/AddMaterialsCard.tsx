import Card from "./Card";
import PillButton from "./PillButton";

interface AddMaterialsCardProps {
  title: string;
  buttonLabel: string;
  onClick?: () => void;
  className?: string;
}

const AddMaterialsCard = ({
  title,
  buttonLabel,
  onClick,
  className = "",
}: AddMaterialsCardProps) => {
  return (
    <Card
      variant="glass"
      className={`px-3 py-3 text-center text-sm font-semibold text-white border-0 bg-transparent shadow-none lg:px-6 lg:py-6 lg:border lg:border-white/30 lg:bg-white/10 ${className}`}
    >
      <span className="hidden lg:block">{title}</span>
      <div className="mt-3">
        <PillButton
          label={buttonLabel}
          variant="white"
          onClick={onClick}
          className="w-full justify-center lg:w-auto"
        />
      </div>
    </Card>
  );
};

export default AddMaterialsCard;
