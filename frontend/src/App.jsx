import { useEffect, useRef, useState } from "react";
import { Routes, Route, useNavigate, useLocation } from "react-router-dom";
import Message from "./components/Message";
import PromptForm from "./components/PromptForm";
import Sidebar from "./components/Sidebar";
import ScenarioCards from "./components/ScenarioCards";
import { Menu } from "lucide-react";
import Dashboard from "./pages/Dashboard.jsx";

const App = () => {
  const navigate = useNavigate();
  const location = useLocation();

  // Main app state
  const [isLoading, setIsLoading] = useState(false);
  const typingInterval = useRef(null);
  const messagesContainerRef = useRef(null);
  const [isSidebarOpen, setIsSidebarOpen] = useState(
    () => window.innerWidth > 768
  );
  const [theme, setTheme] = useState(() => {
    const savedTheme = localStorage.getItem("theme");
    if (savedTheme) {
      return savedTheme;
    }
    const prefersDark = window.matchMedia(
      "(prefers-color-scheme: dark)"
    ).matches;
    return prefersDark ? "dark" : "light";
  });
  const [conversations, setConversations] = useState(() => {
    try {
      // Load conversations from localStorage or use default
      const saved = localStorage.getItem("conversations");
      return saved
        ? JSON.parse(saved)
        : [{ id: "default", title: "New Chat", messages: [] }];
    } catch {
      return [{ id: "default", title: "New Chat", messages: [] }];
    }
  });
  const [activeConversation, setActiveConversation] = useState(() => {
    return localStorage.getItem("activeConversation") || "default";
  });
  useEffect(() => {
    if (window.innerWidth < 768) {
      setIsSidebarOpen(false);
    }
  }, []);
  useEffect(() => {
    localStorage.setItem("activeConversation", activeConversation);
  }, [activeConversation]);
  // Save conversations to localStorage
  useEffect(() => {
    localStorage.setItem("conversations", JSON.stringify(conversations));
  }, [conversations]);
  // Handle theme changes
  useEffect(() => {
    localStorage.setItem("theme", theme);
    document.documentElement.classList.toggle("dark", theme === "dark");
  }, [theme]);
  // Get current active conversation
  const currentConversation =
    conversations.find((c) => c.id === activeConversation) || conversations[0];
  // Scroll to bottom of container
  const scrollToBottom = () => {
    if (messagesContainerRef.current) {
      messagesContainerRef.current.scrollTo({
        top: messagesContainerRef.current.scrollHeight,
        behavior: "smooth",
      });
    }
  };
  // Effect to scroll when messages change
  useEffect(() => {
    scrollToBottom();
  }, [conversations, activeConversation]);
  const typingEffect = (text, messageId) => {
    // Initially set the content to empty and mark as loading
    setConversations((prev) =>
      prev.map((conv) =>
        conv.id === activeConversation
          ? {
              ...conv,
              messages: conv.messages.map((msg) =>
                msg.id === messageId
                  ? { ...msg, content: "", loading: true }
                  : msg
              ),
            }
          : conv
      )
    );
    // Set up typing animation
    const words = text.split(" ");
    let wordIndex = 0;
    let currentText = "";
    clearInterval(typingInterval.current);
    typingInterval.current = setInterval(() => {
      if (wordIndex < words.length) {
        // Update the current text being displayed
        currentText += (wordIndex === 0 ? "" : " ") + words[wordIndex++];
        // Update state with current progress
        setConversations((prev) =>
          prev.map((conv) =>
            conv.id === activeConversation
              ? {
                  ...conv,
                  messages: conv.messages.map((msg) =>
                    msg.id === messageId
                      ? { ...msg, content: currentText, loading: true }
                      : msg
                  ),
                }
              : conv
          )
        );
        scrollToBottom();
      } else {
        // Animation complete
        clearInterval(typingInterval.current);
        // Final update, mark as finished loading
        setConversations((prev) =>
          prev.map((conv) =>
            conv.id === activeConversation
              ? {
                  ...conv,
                  messages: conv.messages.map((msg) =>
                    msg.id === messageId
                      ? { ...msg, content: currentText, loading: false }
                      : msg
                  ),
                }
              : conv
          )
        );
        setIsLoading(false);
      }
    }, 40);
  };
  // Generate AI response
  const generateResponse = async (conversation, botMessageId) => {
    // Get the last user message as the query
    const userMessages = conversation.messages.filter(
      (msg) => msg.role === "user"
    );
    const query = userMessages[userMessages.length - 1]?.content || "";

    try {
      const res = await fetch(`${import.meta.env.VITE_API_URL}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          query: query,
          thread_id: conversation.id,
          use_retrieval: true,
          top_k: 3,
        }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error?.message || "Request failed");

      // Use the response from RAG system
      const responseText = data.response;
      typingEffect(responseText, botMessageId);
    } catch (error) {
      setIsLoading(false);
      updateBotMessage(botMessageId, error.message, true);
    }
  };
  // Update specific bot message
  const updateBotMessage = (botId, content, isError = false) => {
    setConversations((prev) =>
      prev.map((conv) =>
        conv.id === activeConversation
          ? {
              ...conv,
              messages: conv.messages.map((msg) =>
                msg.id === botId
                  ? { ...msg, content, loading: false, error: isError }
                  : msg
              ),
            }
          : conv
      )
    );
  };

  const handleSelectScenario = (prompt) => {
    // Create user message
    const userMessageId = `user-${Date.now()}`;
    const botMessageId = `bot-${Date.now()}`;

    const userMessage = {
      id: userMessageId,
      role: "user",
      content: prompt,
    };

    const botMessage = {
      id: botMessageId,
      role: "bot",
      content: "...",
      loading: true,
    };

    // Update conversation with messages
    const updatedConversation = {
      ...currentConversation,
      title: prompt.slice(0, 30) + (prompt.length > 30 ? "..." : ""),
      messages: [...currentConversation.messages, userMessage, botMessage],
    };

    setConversations((prev) =>
      prev.map((conv) =>
        conv.id === activeConversation ? updatedConversation : conv
      )
    );

    setIsLoading(true);
    generateResponse(updatedConversation, botMessageId);
  };

  const getUserLocation = () => {
    return new Promise((resolve, reject) => {
      if (!navigator.geolocation) {
        reject(new Error("Geolocation is not supported by this browser"));
        return;
      }

      navigator.geolocation.getCurrentPosition(
        (position) => {
          const { latitude, longitude } = position.coords;
          resolve({ latitude, longitude });
        },
        (error) => {
          reject(error);
        },
        {
          enableHighAccuracy: true, // More accurate but slower
          timeout: 10000, // 10 seconds timeout
          maximumAge: 5 * 60 * 1000, // Cache location for 5 minutes
        }
      );
    });
  };

  // Usage
  const handleGetLocation = async () => {
    try {
      const { latitude, longitude } = await getUserLocation();
      console.log(`Latitude: ${latitude}, Longitude: ${longitude}`);

      await fetch(`${import.meta.env.VITE_API_URL}/session/location`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          thread_id: activeConversation,
          lat: latitude,
          lng: longitude,
        }),
      });
    } catch (error) {
      console.error("Error getting user location:", error);
    }
  };
  useEffect(() => {
    handleGetLocation();
  }, []);

  return (
      <div className={`app-container ${theme === "light" ? "light-theme" : "dark-theme"} flex h-screen`}>
          <Sidebar
              conversations={conversations}
              setConversations={setConversations}
              activeConversation={activeConversation}
              setActiveConversation={setActiveConversation}
              theme={theme}
              setTheme={setTheme}
              isSidebarOpen={isSidebarOpen}
              setIsSidebarOpen={setIsSidebarOpen}
              navigate={navigate}
              currentPath={location.pathname}
          />

          <main className={`flex-1 flex flex-col transition-[margin-left] duration-300 ${isSidebarOpen ? "ml-64" : "ml-20"} overflow-hidden`}>
              <header className="main-header p-2 flex items-center">
                  <button onClick={() => setIsSidebarOpen(true)} className="sidebar-toggle">
                      <Menu size={18} />
                  </button>
              </header>

              {currentConversation.messages.length === 0 ? (
                  <div className="welcome-container flex-1 flex flex-col items-center justify-center">
                      <h1 className="welcome-heading text-2xl font-bold">Create a meal</h1>
                      <p className="welcome-text mt-2 text-gray-500">Choose a scenario to get started</p>
                      <ScenarioCards onSelectScenario={handleSelectScenario} />
                  </div>
              ) : (
                  <div className="flex flex-1 gap-4 p-2 overflow-hidden">
                      {/* Left column: Chat */}
                      <div className="flex-1 flex flex-col h-full">
                          <div
                              className="messages-container flex-1 overflow-y-auto p-2"
                              ref={messagesContainerRef}
                          >
                              {currentConversation.messages.map((message) => (
                                  <Message key={message.id} message={message} />
                              ))}
                          </div>

                          <div className="prompt-container sticky bottom-0 bg-white/80 dark:bg-gray-800/80 p-2 rounded-t-lg">
                              <PromptForm
                                  conversations={conversations}
                                  setConversations={setConversations}
                                  activeConversation={activeConversation}
                                  generateResponse={generateResponse}
                                  isLoading={isLoading}
                                  setIsLoading={setIsLoading}
                              />
                              <p className="disclaimer-text text-xs text-gray-500 mt-1">
                                  Describe your goal or choose from templates
                              </p>
                          </div>
                      </div>

                      {/* Right column: Graphs */}
                      <div className="w-1/3 flex flex-col gap-4 h-full">
                          <div className="bg-white/10 backdrop-blur-md rounded-xl p-4 flex-1">
                              <h2 className="text-sm font-semibold mb-2">Graph 1</h2>
                          </div>
                          <div className="bg-white/10 backdrop-blur-md rounded-xl p-4 flex-1">
                              <h2 className="text-sm font-semibold mb-2">Graph 2</h2>
                          </div>
                      </div>
                  </div>
              )}
          </main>
      </div>

  );
};
export default App;
