import Button from "../components/Button";
import { Link } from "react-router-dom";

const Home = () => {
  return (
    <div className="min-h-screen bg-[#1E73F7] flex items-center justify-center">
      <div className="flex gap-6">
        <Link to="/teacher">
          <Button label="Я Вчитель" />
        </Link>
        <Link to="/student">
          <Button label="Я Учень" />
        </Link>
      </div>
    </div>
  );
};

export default Home;
