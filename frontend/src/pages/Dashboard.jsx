import { useState, useEffect, useRef } from "react";
import {
  TrendingUp,
  TrendingDown,
  ShoppingCart,
  Store,
  DollarSign,
  Package,
  Calendar,
  ArrowUpRight,
  ArrowDownRight,
} from "lucide-react";

const colors = [
  "bg-red-500/10",
  "bg-green-400/10",
  "bg-blue-500/10",
  "bg-yellow-400/10",
  "bg-pink-500/10",
];
// Stat Card Component
const StatCard = ({ title, value, subtitle, trend, trendValue }) => {
  // eslint-disable-next-line react-hooks/purity
  const colorClass = colors[Math.floor(Math.random() * colors.length)];
  return (
    <div
      className={`${colorClass} opacity-80 shadow-xl w-full h-full border-white/5 backdrop-blur-md border rounded-xl p-4 flex flex-col gap-2 hover:bg-white/10 transition-colors duration-200`}
    >
      <div className="flex justify-between items-center">
        {trend && (
          <div
            className={`flex items-center gap-1 text-sm font-semibold rounded-2xl p-1 px-1.5 ${
              trend === "up"
                ? "text-green-400 bg-[#03411b]"
                : "text-red-400 bg-[#430101]"
            }`}
          >
            {trend === "up" ? (
              <ArrowUpRight size={14} />
            ) : (
              <ArrowDownRight size={14} />
            )}
            <span>{trendValue}%</span>
          </div>
        )}
      </div>
      <div className="text-xl font-bold">{value}</div>
      <div className="text-sm font-semibold">{title}</div>
      {subtitle && <div className="text-xs text-white/70">{subtitle}</div>}
    </div>
  );
};

// Store Card Component with brand colors
const StoreCard = ({ data }) => {
  return (
    <div className="flex items-center gap-3 bg-white/5 backdrop-blur-md border border-white/10 rounded-xl p-3 hover:bg-white/10 transition-colors duration-200">
      <div className="flex-1 min-w-0">
        <div className="text-sm font-semibold">{data}</div>
      </div>
    </div>
  );
};

const Dashboard = () => {
  const [health, setHealth] = useState(null);
  const [other, setOther] = useState(null);
  const fetchedRef = useRef(false);

  useEffect(() => {
    if (fetchedRef.current) return;
    fetchedRef.current = true;

    const handleFetchHealth = async () => {
      try {
        const response = await fetch(
          `${import.meta.env.VITE_API_URL}/health-status`,
          {
            method: "GET",
            headers: {
              "Content-Type": "application/json",
            },
          }
        );
        const data = await response.json();
        setHealth(data);
      } catch (error) {
        console.error("Error getting user location:", error);
        setHealth(null);
      }
    };

    const handleFetchOther = async () => {
      try {
        const res = await fetch(`${import.meta.env.VITE_API_URL}/dashboard`, {
          method: "GET",
          headers: {
            "Content-Type": "application/json",
          },
        });
        const da = await res.json();
        setOther(da);
      } catch (error) {
        console.error("Error getting user location:", error);
        setOther(null);
      }
    };

    handleFetchHealth();
    handleFetchOther();
  }, []);

  const handleHealthStatus = (stat) => {
    switch (stat) {
      case 1:
        return "Bad";
      case 2:
        return "Worse tha avarage";
      case 3:
        return "Avarage";
      case 4:
        return "Better than avarage";
      case 5:
        return "Good";
      default:
        return "Unknown";
    }
  };

  return (
    <div className="dashboard-container ">
      <div className="dashboard-header">
        <h1 className="dashboard-title">Your dashboard</h1>
        <p className="dashboard-subtitle">Track your expenses and save money</p>
      </div>

      {/* Stats Row */}
      <div className="parent">
        <div className="div1">
          <div className="flex flex-col justify-center w-full h-full items-center gap-3 bg-blue-500/10 backdrop-blur-md border border-white/10 rounded-xl p-3 hover:bg-white/10 transition-colors duration-200">
            <h3>Health status is {handleHealthStatus(health?.rating || 0)}</h3>
            <div
              className="w-[90%] h-[25px] rounded-full relative"
              style={{
                background: "linear-gradient(to left, #22c55e, #ef4444)",
              }}
            >
              <div
                className="absolute top-1/2 -translate-y-1/2 w-8 h-8 bg-white rounded-full shadow-lg border-2 border-white/50 transition-all duration-300"
                style={{ left: `calc(${health?.rating * 20}% - 16px)` }}
              ></div>
            </div>
          </div>
        </div>
        <div className="div2">
          <StatCard
            title="Meal of the day"
            value={health?.suggested_recipe || "Loading..."}
          />
        </div>
        <div className="list-card div4">
          <div className="list-header">
            <h3 className="list-title">
              <Store size={18} />
              Favorite recipes
            </h3>
          </div>
          {other && other.top_recipes && (
            <div className="stores-list">
              {other.top_recipes.map((recipe, index) => (
                <StoreCard key={index} data={recipe.title} />
              ))}
            </div>
          )}
        </div>
        <div className="div3">
          <StatCard
            title={health?.status || "Loading..."}
            value="Health suggestion"
          />
        </div>
        <div className="list-card div5">
          <div className="list-header">
            <h3 className="list-title">
              <Store size={18} />
              Favorite products
            </h3>
          </div>
          {other && other.top_favorites && (
            <div className="stores-list">
              {other.top_favorites.map((product, index) => (
                <StoreCard key={index} data={product.name} />
              ))}
            </div>
          )}
        </div>
        <div className="div6">
          <StatCard
            title="Total spent"
            value={other?.spent_total || "Loading..."}
          />
        </div>
        <div className="div7">
          <StatCard
            title="Total saved"
            value={other?.saved_total || "Loading..."}
          />
        </div>
        <div className="div8">
          <StatCard
            title={other?.recommendation || "Loading..."}
            value="Finance suggestion"
          />
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
