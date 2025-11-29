import { useState, useRef, useEffect } from "react";
import { ReactLenis } from 'lenis/react'
import Sidebar from "./components/Sidebar.jsx";
import Header from "./components/Header.jsx";

function App() {
  const [messages, setMessages] = useState([]);
  const [inputValue, setInputValue] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef(null);
  const [dashboard, setDashboard] = useState(false);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!inputValue.trim() || isLoading) return;

    const userMessage = inputValue.trim();
    setInputValue("");

    // Add user message to chat
    const newMessages = [...messages, { role: "user", content: userMessage }];
    setMessages(newMessages);
    setIsLoading(true);

    try {
      // Simulate AI response (replace with actual API call)
      const response = await fetch("https://api.x.ai/v1/chat/completions", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: "Bearer YOUR_API_KEY", // Replace with actual xAI API key
        },
        body: JSON.stringify({
          messages: [
            { role: "system", content: "You are a helpful assistant." },
            ...newMessages,
          ],
          model: "grok-3",
          stream: false,
          temperature: 0.7,
        }),
      });

      if (!response.ok) {
        throw new Error("Failed to get response from server");
      }

      const data = await response.json();
      const aiMessage = data.choices[0].message.content;

      // Add AI response to chat
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: aiMessage },
      ]);
    } catch (error) {
      // Fallback response if API call fails
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content:
            "Sorry, I encountered an error while processing your request. Please try again.",
        },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  const handleScene = async (e) => {
    const newMessages = [{ role: "user", content: "Make a meal" }];
    setMessages(newMessages);

    setIsLoading(true);
    try {
      // Simulate AI response (replace with actual API call)
      const response = await fetch("https://api.x.ai/v1/chat/completions", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: "Bearer YOUR_API_KEY", // Replace with actual xAI API key
        },
        body: JSON.stringify({
          messages: [
            { role: "system", content: "You are a helpful assistant." },
            ...newMessages,
          ],
          model: "grok-3",
          stream: false,
          temperature: 0.7,
        }),
      });

      if (!response.ok) {
        throw new Error("Failed to get response from server");
      }

      const data = await response.json();
      const aiMessage = data.choices[0].message.content;

      // Add AI response to chat
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: aiMessage },
      ]);
    } catch (error) {
      // Fallback response if API call fails
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content:
            "Sorry, I encountered an error while processing your request. Please try again.",
        },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <main
      className={`flex  pt-20 flex-row gap-8 ${
        messages.length === 0 ? "justify-center" : ""
      }`}
    >
      <div
        className={`relative flex flex-col overflow-hidden ${
          messages.length === 0 ? "h-[80vh] w-[50vw]" : "min-w-[20vw] h-[87vh]"
        } `}
      >
        <div className="flex-1 p-6 overflow-y-auto">
          {messages.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-full text-gray-100">
              <h2 className="text-2xl font-semibold mb-4">
                Welcome to xAI Chat!
              </h2>
              <button
                onClick={handleScene}
                className="text-gray-400 bg-[#2a2929] p-2 rounded-xl hover:cursor-pointer"
              >
                Make a meal
              </button>
            </div>
          ) : (
            <div className="space-y-4">
              {messages.map((message, index) => (
                <div
                  key={index}
                  className={`flex ${
                    message.role === "user" ? "justify-end" : "justify-start"
                  }`}
                >
                  <div
                    className={`max-w-[70%] p-4 rounded-2xl ${
                      message.role === "user"
                        ? "bg-[#514a3e] text-white"
                        : "bg-[#232323] text-white"
                    }`}
                  >
                    <p className="whitespace-pre-wrap">{message.content}</p>
                  </div>
                </div>
              ))}
              {isLoading && (
                <div className="flex justify-start">
                  <div className="max-w-[70%] p-4 rounded-2xl bg-[#232323] text-white">
                    <div className="flex items-center space-x-2">
                      <div className="flex space-x-1">
                        <div className="w-3 h-3 bg-gray-400 rounded-full animate-bounce"></div>
                        <div
                          className="w-3 h-3 bg-gray-400 rounded-full animate-bounce"
                          style={{ animationDelay: "0.1s" }}
                        ></div>
                        <div
                          className="w-3 h-3 bg-gray-400 rounded-full animate-bounce"
                          style={{ animationDelay: "0.2s" }}
                        ></div>
                      </div>
                      <span>Thinking...</span>
                    </div>
                  </div>
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>
          )}
        </div>

        <form
          onSubmit={handleSubmit}
          className="bg-[#484848] p-4 m-4 rounded-4xl flex gap-4"
        >
          <input
            type="text"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyPress={handleKeyPress}
            className="flex-1 p-4  text-white rounded-2xl focus:outline-none"
            placeholder="Message here..."
            disabled={isLoading}
          />
          <button
            type="submit"
            disabled={!inputValue.trim() || isLoading}
            className="px-8 py-4 bg-[#413727] hover:bg-[#524532] disabled:bg-[#767676] rounded-2xl text-white font-semibold transition-colors disabled:cursor-not-allowed"
          >
            {">"}
          </button>
        </form>
      </div>
      {messages.length > 0 && (
        <div className="h-screen -mt-20 w-[1000px] bg-[#283628] rounded-tl-4xl rounded-bl-4xl p-5">
          Dashboard Placeholder
        </div>
      )}
    </main>
  );
}

export default App;
