import {FiPlus} from "react-icons/fi";
import {useState} from "react";
// import Header from "./components/Header.jsx";


const Sidebar = ({ chatHistory }) => {
    const [isOpen, setIsOpen] = useState(false);
    return (
        <aside className="bg-neutral-600 border-r border-neutral-800 shadow-2xl rounded-r-xl h-[100vh] w-[20vw] p-3">
            <h1 className="text-neutral-200 text-center text-2xl font-semibold">Your chats</h1>
            <div className="flex flex-col p-2 gap-4 justify-center items-center">
                <button className="bg-gradient-to-r from-0% from-blue-900 to-100% to-violet-900 hover:from-blue-950 hover:to-violet-950 opacity-80 hover:scale-105 w-1/2 justify-center items-center text-white font-bold py-2 px-4 rounded-xl flex flex-row gap-2"><FiPlus className="text-amber-700 p-2 "/> New chat</button>
                {chatHistory && Object.values(chatHistory).map((chat, index) => (
                    <div className={`border border-neutral-300 w-full items-center justify-center flex flex-row rounded-xl gap-4 p-2 bg-neutral-500 ${isOpen ? "opacity-75" : "opacity-20"}`}>
                        <h1 className="text-neutral-200 text-center text-xl font-semibold ">{chat.name}</h1>
                        <button className="border border-neutral-300 opacity-95 bg-neutral-500 hover:border-blue-950 hover:scale-105 text-white font-bold py-1.5 px-3 rounded-xl">Delete</button>
                    </div>
                ))}
            </div>
            {/*<Header />*/}
        </aside>
    );
}

export default Sidebar;