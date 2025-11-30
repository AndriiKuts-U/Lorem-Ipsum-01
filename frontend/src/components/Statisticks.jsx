import { useEffect, useRef, useState } from "react";

const SideBar = {
    grocery_list: {
        Milk: "1.25",
        Eggs: "2.25",
        Tomatoes: "3.25",
        Piper: "4.25",
    },
    shops_to_visit: ["Fresh", "Lidl", "Tesko"],
    spent_total: "23.25",
    saved_total: "6.80",
};

const Statistics = () => {
    const [check, setCheck] = useState(SideBar.grocery_list);
    const [health, setHealth] = useState(null);
    const [other, setOther] = useState(null);
    const fetchedRef = useRef(false);

    const handleCheck = (item) => {
        const newChecklist = { ...check };
        delete newChecklist[item];
        setCheck(newChecklist);
    };

    const handleFetchHealth = async () => {
        try {
            const response = await fetch(
                `${import.meta.env.VITE_API_URL}/health-status`,
                {
                    method: "GET",
                    headers: { "Content-Type": "application/json" },
                }
            );
            const data = await response.json();
            setHealth(data);
        } catch (error) {
            console.error("Error fetching health:", error);
            setHealth(null);
        }
    };

    const handleFetchOther = async () => {
        try {
            const res = await fetch(`${import.meta.env.VITE_API_URL}/dashboard`, {
                method: "GET",
                headers: { "Content-Type": "application/json" },
            });
            const da = await res.json();
            setOther(da);
        } catch (error) {
            console.error("Error fetching dashboard:", error);
            setOther(null);
        }
    };

    useEffect(() => {
        if (fetchedRef.current) return;
        fetchedRef.current = true;

        handleFetchHealth();
        handleFetchOther();
    }, []);

    return (
        <div className="statistics-container flex flex-col gap-5 items-center mt-4">
            {/* Shops */}
            {SideBar.shops_to_visit.map((store, index) => (
                <div
                    key={index}
                    className="store-card w-80 p-3 rounded-lg shadow-md border border-gray-200"
                >
                    <div className="flex flex-row items-start gap-2">
                        <h3 className="text-lg font-semibold">{store}</h3>
                        <p>Distance: 200 m</p>
                    </div>
                </div>
            ))}

            {Object.keys(check).length > 0 && (
                <div className="w-80 mt-4 flex flex-col gap-2 shadow bg-gradient-to-r from-[#e20074] to-[#79d98c] rounded-xl p-2">
                    {Object.entries(check).map(([item, price], idx) => (
                        <label
                            key={idx}
                            className="flex justify-between items-center p-2 border border-white shadow-xl rounded-2xl bg-white/50"
                        >
                            <div className="flex items-center gap-2">
                                <input
                                    type="checkbox"
                                    className="accent-[#e20074] scale-110"
                                    onChange={() => handleCheck(item)}
                                />
                                <span>{item}</span>
                            </div>
                            <span className="font-semibold">${price}</span>
                        </label>
                    ))}
                </div>
            )}

            <div className="flex flex-row items-start gap-4">
                <h3 className="text-lg">Total: {SideBar.spent_total}</h3>
                <h3 className="text-lg">Saved: {SideBar.saved_total}</h3>
            </div>

            {/*{health && <p className="mt-4">Health Status: {JSON.stringify(health)}</p>}*/}
        </div>
    );
}

export default Statistics;
