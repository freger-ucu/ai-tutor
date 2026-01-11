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
      className={`px-6 py-6 text-center text-sm font-semibold text-white ${className}`}
    >
      {title}
      <div className="mt-3">
        <PillButton label={buttonLabel} variant="white" onClick={onClick} />
      </div>
    </Card>
  );
};

export default AddMaterialsCard;
