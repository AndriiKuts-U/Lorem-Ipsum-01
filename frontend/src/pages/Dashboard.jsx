
import {
    TrendingUp,
    TrendingDown,
    ShoppingCart,
    Store,
    DollarSign,
    Package,
    Calendar,
    ArrowUpRight,
    ArrowDownRight
} from 'lucide-react';
import {
    AreaChart,
    Area,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    ResponsiveContainer,
    BarChart,
    Bar,
    PieChart,
    Pie,
    Cell
} from 'recharts';

// Slovak stores with brand colors
const storeVisits = [
    { name: 'Lidl', visits: 22, color: '#0050AA', logo: '🟦' },        // Lidl blue
    { name: 'Kaufland', visits: 18, color: '#E10915', logo: '🟥' },    // Kaufland red
    { name: 'Tesco', visits: 14, color: '#00539F', logo: '🔵' },       // Tesco blue
    { name: 'Billa', visits: 10, color: '#FFD100', logo: '🟨' },       // Billa yellow
    { name: 'Fresh', visits: 6, color: '#7AB929', logo: '🟩' },        // Fresh green
];

// Brand colors array for charts
const STORE_COLORS = ['#0050AA', '#E10915', '#00539F', '#FFD100', '#7AB929'];

// Mock data for spending over time (in EUR)
const spendingData = [
    { month: 'Jún', amount: 285 },
    { month: 'Júl', amount: 312 },
    { month: 'Aug', amount: 298 },
    { month: 'Sep', amount: 345 },
    { month: 'Okt', amount: 378 },
    { month: 'Nov', amount: 356 },
];

// Mock data for frequent products (prices in EUR)
const frequentProducts = [
    {
        name: 'Mlieko',
        purchases: 14,
        avgPrice: 1.29,
        priceChange: 4.8,
        trend: 'up',
        emoji: '🥛'
    },
    {
        name: 'Chlieb',
        purchases: 16,
        avgPrice: 1.49,
        priceChange: -1.5,
        trend: 'down',
        emoji: '🍞'
    },
    {
        name: 'Vajcia (10ks)',
        purchases: 8,
        avgPrice: 2.89,
        priceChange: 8.2,
        trend: 'up',
        emoji: '🥚'
    },
    {
        name: 'Kuracie prsia',
        purchases: 7,
        avgPrice: 6.99,
        priceChange: 3.1,
        trend: 'up',
        emoji: '🍗'
    },
    {
        name: 'Banány',
        purchases: 12,
        avgPrice: 1.49,
        priceChange: -5.2,
        trend: 'down',
        emoji: '🍌'
    },
    {
        name: 'Káva',
        purchases: 4,
        avgPrice: 5.99,
        priceChange: 2.4,
        trend: 'up',
        emoji: '☕'
    },
];

// Price history for products (in EUR)
const priceHistory = [
    { month: 'Jún', Mlieko: 1.19, Chlieb: 1.45, Vajcia: 2.49 },
    { month: 'Júl', Mlieko: 1.22, Chlieb: 1.45, Vajcia: 2.59 },
    { month: 'Aug', Mlieko: 1.25, Chlieb: 1.49, Vajcia: 2.69 },
    { month: 'Sep', Mlieko: 1.25, Chlieb: 1.49, Vajcia: 2.79 },
    { month: 'Okt', Mlieko: 1.29, Chlieb: 1.49, Vajcia: 2.85 },
    { month: 'Nov', Mlieko: 1.29, Chlieb: 1.49, Vajcia: 2.89 },
];

// Stat Card Component
const StatCard = ({ title, value, subtitle, trend, trendValue }) => (
    <div className="stat-card">
        <div className="stat-card-header">
            <div className="stat-icon">
                {/*<Icon size={20} />*/}
            </div>
            {trend && (
                <div className={`stat-trend ${trend}`}>
                    {trend === 'up' ? <ArrowUpRight size={14} /> : <ArrowDownRight size={14} />}
                    <span>{trendValue}%</span>
                </div>
            )}
        </div>
        <div className="stat-value">{value}</div>
        <div className="stat-title">{title}</div>
        {subtitle && <div className="stat-subtitle">{subtitle}</div>}
    </div>
);

// Store Card Component with brand colors
const StoreCard = ({ store, maxVisits }) => {
    const percentage = (store.visits / maxVisits) * 100;
    return (
        <div className="store-card">
            <div className="store-logo" style={{ background: `${store.color}20` }}>
                <span style={{ color: store.color, fontWeight: 700, fontSize: '0.75rem' }}>
                    {store.name.charAt(0)}
                </span>
            </div>
            <div className="store-info">
                <div className="store-name">{store.name}</div>
                <div className="store-visits">{store.visits} návštev</div>
            </div>
            <div className="store-bar-container">
                <div
                    className="store-bar"
                    style={{
                        width: `${percentage}%`,
                        background: store.color
                    }}
                />
            </div>
        </div>
    );
};

// Product Row Component
const ProductRow = ({ product }) => (
    <div className="product-row">
        <div className="product-emoji">{product.emoji}</div>
        <div className="product-info">
            <div className="product-name">{product.name}</div>
            <div className="product-purchases">{product.purchases}× tento mesiac</div>
        </div>
        <div className="product-price">
            <div className="price-value">€{product.avgPrice.toFixed(2)}</div>
            <div className={`price-change ${product.trend}`}>
                {product.trend === 'up' ? <TrendingUp size={12} /> : <TrendingDown size={12} />}
                <span>{product.priceChange > 0 ? '+' : ''}{product.priceChange}%</span>
            </div>
        </div>
    </div>
);

const Dashboard = ({ theme }) => {
    const maxVisits = Math.max(...storeVisits.map(s => s.visits));
    const totalSpentThisMonth = 356;
    const avgSpending = 329;
    const lastPurchase = 47.85;

    return (
        <div className="dashboard-container">
            <div className="dashboard-header">
                <h1 className="dashboard-title">Prehľad nákupov</h1>
                <p className="dashboard-subtitle">Sledujte svoje výdavky a šetrite peniaze</p>
            </div>

            {/* Stats Row */}
            <div className="stats-grid">
                <StatCard
                    title="Tento mesiac"
                    value={`€${totalSpentThisMonth.toLocaleString()}`}
                    icon={Calendar}
                    trend="down"
                    trendValue={5.8}
                />
                <StatCard
                    title="Mesačný priemer"
                    value={`€${avgSpending.toLocaleString()}`}
                    icon={DollarSign}
                />
                <StatCard
                    title="Posledný nákup"
                    value={`€${lastPurchase.toFixed(2)}`}
                    subtitle="Pred 2 dňami v Lidl"
                    icon={ShoppingCart}
                />
                <StatCard
                    title="Celkom nákupov"
                    value="70"
                    subtitle="Tento mesiac"
                    icon={Package}
                />
            </div>

            {/* Charts Row */}
            <div className="charts-grid">
                {/* Spending Chart */}
                <div className="chart-card large">
                    <h3 className="chart-title">Výdavky za obdobie</h3>
                    <div className="chart-container">
                        <ResponsiveContainer width="100%" height={250}>
                            <AreaChart data={spendingData}>
                                <defs>
                                    <linearGradient id="colorAmount" x1="0" y1="0" x2="0" y2="1">
                                        <stop offset="5%" stopColor="#0050AA" stopOpacity={0.3}/>
                                        <stop offset="95%" stopColor="#0050AA" stopOpacity={0}/>
                                    </linearGradient>
                                </defs>
                                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
                                <XAxis
                                    dataKey="month"
                                    stroke="rgba(255,255,255,0.5)"
                                    fontSize={12}
                                />
                                <YAxis
                                    stroke="rgba(255,255,255,0.5)"
                                    fontSize={12}
                                    tickFormatter={(value) => `€${value}`}
                                />
                                <Tooltip
                                    contentStyle={{
                                        background: 'rgba(30,30,40,0.9)',
                                        border: '1px solid rgba(255,255,255,0.1)',
                                        borderRadius: '12px',
                                        backdropFilter: 'blur(10px)'
                                    }}
                                    formatter={(value) => [`€${value}`, 'Výdavky']}
                                />
                                <Area
                                    type="monotone"
                                    dataKey="amount"
                                    stroke="#0050AA"
                                    strokeWidth={2}
                                    fillOpacity={1}
                                    fill="url(#colorAmount)"
                                />
                            </AreaChart>
                        </ResponsiveContainer>
                    </div>
                </div>

                {/* Store Visits Pie Chart */}
                <div className="chart-card">
                    <h3 className="chart-title">Rozdelenie obchodov</h3>
                    <div className="chart-container pie-chart-container">
                        <ResponsiveContainer width="100%" height={200}>
                            <PieChart>
                                <Pie
                                    data={storeVisits}
                                    cx="50%"
                                    cy="50%"
                                    innerRadius={50}
                                    outerRadius={80}
                                    paddingAngle={5}
                                    dataKey="visits"
                                >
                                    {storeVisits.map((entry, index) => (
                                        <Cell key={`cell-${index}`} fill={STORE_COLORS[index % STORE_COLORS.length]} />
                                    ))}
                                </Pie>
                                <Tooltip
                                    contentStyle={{
                                        background: 'rgba(30,30,40,0.9)',
                                        border: '1px solid rgba(255,255,255,0.1)',
                                        borderRadius: '12px'
                                    }}
                                    formatter={(value, name) => [`${value} návštev`, name]}
                                />
                            </PieChart>
                        </ResponsiveContainer>
                        <div className="pie-legend">
                            {storeVisits.slice(0, 3).map((store, index) => (
                                <div key={index} className="legend-item">
                                    <span className="legend-dot" style={{ background: store.color }}></span>
                                    <span>{store.name}</span>
                                </div>
                            ))}
                        </div>
                    </div>
                </div>
            </div>

            {/* Bottom Row */}
            <div className="bottom-grid">
                {/* Store Visits List */}
                <div className="list-card">
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

                {/* Frequent Products */}
                <div className="list-card">
                    <div className="list-header">
                        <h3 className="list-title">
                            <Package size={18} />
                            Časté produkty
                        </h3>
                    </div>
                    <div className="products-list">
                        {frequentProducts.map((product, index) => (
                            <ProductRow key={index} product={product} />
                        ))}
                    </div>
                </div>

                {/* Price Trends Chart */}
                <div className="chart-card price-chart">
                    <h3 className="chart-title">Vývoj cien</h3>
                    <div className="chart-container">
                        <ResponsiveContainer width="100%" height={220}>
                            <BarChart data={priceHistory}>
                                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
                                <XAxis
                                    dataKey="month"
                                    stroke="rgba(255,255,255,0.5)"
                                    fontSize={12}
                                />
                                <YAxis
                                    stroke="rgba(255,255,255,0.5)"
                                    fontSize={12}
                                    tickFormatter={(value) => `€${value}`}
                                />
                                <Tooltip
                                    contentStyle={{
                                        background: 'rgba(30,30,40,0.9)',
                                        border: '1px solid rgba(255,255,255,0.1)',
                                        borderRadius: '12px'
                                    }}
                                    formatter={(value) => [`€${value.toFixed(2)}`, '']}
                                />
                                <Bar dataKey="Mlieko" fill="#0050AA" radius={[4, 4, 0, 0]} name="Mlieko" />
                                <Bar dataKey="Chlieb" fill="#7AB929" radius={[4, 4, 0, 0]} name="Chlieb" />
                                <Bar dataKey="Vajcia" fill="#E10915" radius={[4, 4, 0, 0]} name="Vajcia" />
                            </BarChart>
                        </ResponsiveContainer>
                        <div className="chart-legend">
                            <div className="legend-item"><span className="legend-dot" style={{background: '#0050AA'}}></span>Mlieko</div>
                            <div className="legend-item"><span className="legend-dot" style={{background: '#7AB929'}}></span>Chlieb</div>
                            <div className="legend-item"><span className="legend-dot" style={{background: '#E10915'}}></span>Vajcia</div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default Dashboard;