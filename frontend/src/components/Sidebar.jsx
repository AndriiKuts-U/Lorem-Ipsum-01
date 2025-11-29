import { GoPlus } from "react-icons/go";

const Sidebar = () => {
    return (
        <aside className="bg-neutral-600 border border-neutral-300 shadow-2xl rounded-r-xl h-[100vh] w-[20vw]">
            <h1 className="text-neutral-200 text-center text-2xl font-semibold">Sidebar</h1>
            <div className="flex flex-col p-2 gap-4 justify-center items-center">
                <button className="bg-gradient-to-r from-0% from-blue-900 to-100% to-violet-900 hover:from-blue-950 hover:to-violet-950 opacity-80 hover:scale-105 w-1/2 justify-center items-center text-white font-bold py-2 px-4 rounded-xl flex flex-row gap-2"><GoPlus className="bg-neutral-200 p-2 "/> New chat</button>
                <div className="border border-neutral-300 w-full items-center justify-center flex flex-row rounded-xl gap-4 p-2 opacity-75 bg-neutral-500">
                    <h1 className="text-neutral-200 text-center text-xl font-semibold ">Current chat</h1>
                    <button className="border border-neutral-300 opacity-95 bg-neutral-500 hover:border-blue-950 hover:scale-105 text-white font-bold py-1.5 px-3 rounded-xl">Delete</button>
                </div>
            </div>
        </aside>
    );
}

export default Sidebar;