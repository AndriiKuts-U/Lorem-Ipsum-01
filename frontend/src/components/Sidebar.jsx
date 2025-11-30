import { Menu, Moon, Plus, Sparkles, Sun, Trash2, LayoutDashboard, MessageSquare } from "lucide-react";

const Sidebar = ({
                     isSidebarOpen,
                     setIsSidebarOpen,
                     conversations,
                     setConversations,
                     activeConversation,
                     setActiveConversation,
                     theme,
                     setTheme,
                     navigate,
                     currentPath
                 }) => {
    // ... existing code (createNewConversation, deleteConversation) ...

    return (
        <aside className={`sidebar ${isSidebarOpen ? "open" : "closed"}`}>
            {/* Sidebar Header */}
            <div className="sidebar-header">
                <button className="sidebar-toggle" onClick={() => setIsSidebarOpen((prev) => !prev)}>
                    <Menu size={18} />
                </button>
                <button className="new-chat-btn" onClick={() => { createNewConversation(); navigate('/'); }}>
                    <Plus size={20} />
                    <span>New chat</span>
                </button>
            </div>

            {/* Navigation */}
            <div className="sidebar-nav">
                <button
                    className={`nav-item ${currentPath === '/' ? 'active' : ''}`}
                    onClick={() => navigate('/')}
                >
                    <MessageSquare size={18} />
                    <span>Chat</span>
                </button>
                <button
                    className={`nav-item ${currentPath === '/dashboard' ? 'active' : ''}`}
                    onClick={() => navigate('/dashboard')}
                >
                    <LayoutDashboard size={18} />
                    <span>Dashboard</span>
                </button>
            </div>

            {/* Conversation List */}
            <div className="sidebar-content">
                <h2 className="sidebar-title">Chat history</h2>
                <ul className="conversation-list">
                    {conversations.map((conv) => (
                        <li
                            key={conv.id}
                            className={`conversation-item ${activeConversation === conv.id ? "active" : ""}`}
                            onClick={() => { setActiveConversation(conv.id); navigate('/'); }}
                        >
                            <div className="conversation-icon-title">
                                <div className="conversation-icon">
                                    <Sparkles size={14} />
                                </div>
                                <span className="conversation-title">{conv.title}</span>
                            </div>
                            <button
                                className={`delete-btn ${conversations.length > 1 || conv.title !== "New Chat" ? "" : "hide"}`}
                                onClick={(e) => deleteConversation(conv.id, e)}
                            >
                                <Trash2 size={16} />
                            </button>
                        </li>
                    ))}
                </ul>
            </div>

            {/* Theme Toggle */}
            <div className="sidebar-footer">
                <button className="theme-toggle" onClick={() => setTheme(theme === "light" ? "dark" : "light")}>
                    {theme === "light" ? (
                        <>
                            <Moon size={20} />
                            <span>Dark mode</span>
                        </>
                    ) : (
                        <>
                            <Sun size={20} />
                            <span>Light mode</span>
                        </>
                    )}
                </button>
            </div>
        </aside>
    );
};

export default Sidebar;