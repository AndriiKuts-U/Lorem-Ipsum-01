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
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
} from "recharts";

const totalSavings = 142.75;
const storeVisits = [
  { name: "Lidl", visits: 22, color: "#0050AA", logo: "🟦" },
  { name: "Kaufland", visits: 18, color: "#E10915", logo: "🟥" },
  { name: "Tesco", visits: 14, color: "#00539F", logo: "🔵" },
  { name: "Billa", visits: 10, color: "#FFD100", logo: "🟨" },
  { name: "Fresh", visits: 6, color: "#7AB929", logo: "🟩" },
];

const STORE_COLORS = ["#0050AA", "#E10915", "#00539F", "#FFD100", "#7AB929"];

// Mock data for spending over time (in EUR)
const spendingData = [
  { month: "Jún", amount: 285 },
  { month: "Júl", amount: 312 },
  { month: "Aug", amount: 298 },
  { month: "Sep", amount: 345 },
  { month: "Okt", amount: 378 },
  { month: "Nov", amount: 356 },
];

// Mock data for frequent products (prices in EUR)
const frequentProducts = [
  {
    name: "Mlieko",
    purchases: 14,
    avgPrice: 1.29,
    priceChange: 4.8,
    trend: "up",
    emoji: "🥛",
  },
  {
    name: "Chlieb",
    purchases: 16,
    avgPrice: 1.49,
    priceChange: -1.5,
    trend: "down",
    emoji: "🍞",
  },
  {
    name: "Vajcia (10ks)",
    purchases: 8,
    avgPrice: 2.89,
    priceChange: 8.2,
    trend: "up",
    emoji: "🥚",
  },
  {
    name: "Kuracie prsia",
    purchases: 7,
    avgPrice: 6.99,
    priceChange: 3.1,
    trend: "up",
    emoji: "🍗",
  },
  {
    name: "Banány",
    purchases: 12,
    avgPrice: 1.49,
    priceChange: -5.2,
    trend: "down",
    emoji: "🍌",
  },
  {
    name: "Káva",
    purchases: 4,
    avgPrice: 5.99,
    priceChange: 2.4,
    trend: "up",
    emoji: "☕",
  },
];

// Price history for products (in EUR)
const priceHistory = [
  { month: "Jún", Mlieko: 1.19, Chlieb: 1.45, Vajcia: 2.49 },
  { month: "Júl", Mlieko: 1.22, Chlieb: 1.45, Vajcia: 2.59 },
  { month: "Aug", Mlieko: 1.25, Chlieb: 1.49, Vajcia: 2.69 },
  { month: "Sep", Mlieko: 1.25, Chlieb: 1.49, Vajcia: 2.79 },
  { month: "Okt", Mlieko: 1.29, Chlieb: 1.49, Vajcia: 2.85 },
  { month: "Nov", Mlieko: 1.29, Chlieb: 1.49, Vajcia: 2.89 },
];

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
      className={`${colorClass} opacity-80 shadow-xl  border-white/5 backdrop-blur-md border rounded-xl p-4 flex flex-col gap-2 hover:bg-white/10 transition-colors duration-200`}
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
const StoreCard = ({ store, maxVisits }) => {
  const percentage = (store.visits / maxVisits) * 100;
  return (
    <div className="flex items-center gap-3 bg-white/5 backdrop-blur-md border border-white/10 rounded-xl p-3 hover:bg-white/10 transition-colors duration-200">
      <div
        className="w-10 h-10 flex items-center justify-center rounded-lg"
        style={{ background: `${store.color}20`, color: store.color }}
      >
        {store.name.charAt(0)}
      </div>
      <div className="flex-1 min-w-0">
        <div className="text-sm font-semibold">{store.name}</div>
        <div className="text-xs text-white/70">{store.visits} návštev</div>
      </div>
      <div className="w-20 h-1 bg-white/10 rounded-full overflow-hidden">
        <div
          className="h-full rounded-full"
          style={{ width: `${percentage}%`, background: store.color }}
        ></div>
      </div>
    </div>
  );
};

// Product Row Component
const ProductRow = ({ product }) => (
  <div className="flex items-center gap-3 bg-white/5 backdrop-blur-md border border-white/10 rounded-xl p-3 hover:bg-white/10 transition-colors duration-200">
    <div
      className="w-10 h-10 flex items-center justify-center rounded-lg text-xl"
      style={{ background: "rgba(255,255,255,0.1)" }}
    >
      {product.emoji}
    </div>
    <div className="flex-1 min-w-0">
      <div className="text-sm font-semibold">{product.name}</div>
      <div className="text-xs text-white/70">
        {product.purchases}× tento mesiac
      </div>
    </div>
    <div className="text-right">
      <div className="text-sm font-semibold">{`€${product.avgPrice.toFixed(
        2
      )}`}</div>
      <div
        className={`flex items-center justify-end gap-1 text-xs font-semibold ${
          product.trend === "up" ? "text-red-400" : "text-green-400"
        }`}
      >
        {product.trend === "up" ? (
          <TrendingUp size={12} />
        ) : (
          <TrendingDown size={12} />
        )}
        <span>
          {product.priceChange > 0 ? "+" : ""}
          {product.priceChange}%
        </span>
      </div>
    </div>
  </div>
);

const Dashboard = ({ theme }) => {
  const maxVisits = Math.max(...storeVisits.map((s) => s.visits));
  const totalSpentThisMonth = 356;
  const avgSpending = 329;
  const lastPurchase = 47.85;

  const [health, setHealth] = useState(null);
  const fetchedRef = useRef(false);

  useEffect(() => {
    if (fetchedRef.current) return;
    fetchedRef.current = true;

    const handleHealth = async () => {
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

    handleHealth();
  }, []);

  return (
    <div className="dashboard-container ">
      <div className="dashboard-header">
        <h1 className="dashboard-title">Prehľad nákupov</h1>
        <p className="dashboard-subtitle">
          Sledujte svoje výdavky a šetrite peniaze
        </p>
      </div>

      {/* Stats Row */}
      <div className="parent">
        <div className="div1">
          <StatCard
            title="Tento mesiac"
            value={`€${totalSpentThisMonth.toLocaleString()}`}
            icon={Calendar}
            trend="down"
            trendValue={5.8}
          />
        </div>
        <div className="div2">
          <StatCard
            title="Mesačný priemer"
            value={`€${avgSpending.toLocaleString()}`}
            icon={DollarSign}
          />
        </div>

        <div className="list-card div4">
          <div className="list-header">
            <h3 className="list-title">
              <Store size={18} />
              Najnavštevovanejšie obchody
            </h3>
          </div>
          <div className="stores-list">
            {storeVisits.map((store, index) => (
              <StoreCard key={index} store={store} maxVisits={maxVisits} />
            ))}
          </div>
        </div>
        <div className="div3">
          <StatCard
            title={`${health ? health.status : "Načítavanie..."}`}
            value="Navrh"
            icon={Package}
          />
        </div>
        <div className="list-card div5">
          <div className="list-header">
            <h3 className="list-title">
              <Store size={18} />
              Najnavštevovanejšie obchody
            </h3>
          </div>
          <div className="stores-list">
            {storeVisits.map((store, index) => (
              <StoreCard key={index} store={store} maxVisits={maxVisits} />
            ))}
          </div>
        </div>
        <div className="div6">
          <StatCard
            title="Tento mesiac"
            value={`€${totalSpentThisMonth.toLocaleString()}`}
            icon={Calendar}
            trend="down"
            trendValue={5.8}
          />
        </div>
        <div className="div7">
          <StatCard
            title="Mesačný priemer"
            value={`€${avgSpending.toLocaleString()}`}
            icon={DollarSign}
          />
        </div>
        <div className="div8">
          <StatCard
            title="Mesačný priemer"
            value={`€${avgSpending.toLocaleString()}`}
            icon={DollarSign}
          />
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
