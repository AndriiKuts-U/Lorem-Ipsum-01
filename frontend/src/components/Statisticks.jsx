import { useEffect, useRef, useState } from "react";

const Statistics = () => {
    const [sidebar, setSidebar] = useState(null);
    const [uncheckedItems, setUncheckedItems] = useState([]);
    const fetchedRef = useRef(false);

    const handleCheck = (item) => {
        setUncheckedItems((prev) => prev.filter((i) => i !== item));
    };

    useEffect(() => {
        if (fetchedRef.current) return;
        fetchedRef.current = true;

        const handleFetchDashboard = async () => {
            try {
                const res = await fetch(`${import.meta.env.VITE_API_URL}/chat`, {
                    method: "GET",
                    headers: { "Content-Type": "application/json" },
                });

                const data = await res.json();
                setSidebar(data?.side_bar);
            } catch (error) {
                console.error("Error fetching dashboard:", error);
            }
        };

        handleFetchDashboard();
    }, []);

    if (!sidebar) return <></>;

    /** Filter remaining grocery items */
    const visibleGroceries = sidebar?.grocery_list.filter(
        (item) => !uncheckedItems.includes(item)
    );

    return (
        <div className="statistics-container flex flex-col gap-5 items-center mt-4">

            {sidebar && sidebar.shops_to_visit(sidebar.shops_to_visit.map((store, index) => (
                <div
                    key={index}
                    className="store-card w-80 p-3 rounded-lg shadow-md border border-gray-200"
                >
                    <div className="flex flex-row items-start gap-2">
                        <h3 className="text-lg font-semibold">{store}</h3>
                        <p className="text-sm">Distance: 200 m</p>
                    </div>
                </div>
            )))}

            {visibleGroceries.length > 0 && (
                <div className="w-80 mt-4 flex flex-col gap-2 shadow rounded-xl p-2">
                    {visibleGroceries && visibleGroceries(visibleGroceries.map((item, idx) => (
                        <label
                            key={idx}
                            className="flex justify-between items-center p-2 border border-gray-300 shadow rounded-2xl bg-white/50"
                        >
                            <div className="flex items-center gap-2">
                                <input
                                    type="checkbox"
                                    className="accent-[#e20074] scale-110"
                                    onChange={() => handleCheck(item)}
                                />
                                <span>{item}</span>
                            </div>
                        </label>
                    )))}
                </div>
            )}

            <div className="flex flex-row items-start gap-4">
                <h3 className="text-lg font-semibold">Total: {sidebar?.spent_total}</h3>
                <h3 className="text-lg font-semibold">Saved: {sidebar?.saved_total}</h3>
            </div>
        </div>
    );
};

export default Statistics;
