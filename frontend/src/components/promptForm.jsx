import { ArrowUp } from "lucide-react";
import { useState } from "react";

const PromptForm = ({ conversations, setConversations, activeConversation, generateResponse, isLoading, setIsLoading, myMargin }) => {
    const [promptText, setPromptText] = useState("");
    const handleSubmit = (e) => {
        e.preventDefault();
        if (isLoading || !promptText.trim()) return;
        setIsLoading(true);
        const currentConvo = conversations.find((convo) => convo.id === activeConversation) || conversations[0];
        let newTitle = currentConvo.title;
        if (currentConvo.messages.length === 0) {
            newTitle = promptText.length > 25 ? promptText.substring(0, 25) + "..." : promptText;
        }
        const userMessage = {
            id: `user-${Date.now()}`,
            role: "user",
            content: promptText,
        };
        const apiConversation = {
            ...currentConvo,
            messages: [...currentConvo.messages, userMessage],
        };
        setConversations(conversations.map((conv) => (conv.id === activeConversation ? { ...conv, title: newTitle, messages: [...conv.messages, userMessage] } : conv)));
        setPromptText("");
        setTimeout(() => {
            const botMessageId = `bot-${Date.now()}`;
            const botMessage = {
                id: botMessageId,
                role: "bot",
                content: "Just a sec...",
                loading: true,
            };
            setConversations((prev) => prev.map((conv) => (conv.id === activeConversation ? { ...conv, title: newTitle, messages: [...conv.messages, botMessage] } : conv)));
            generateResponse(apiConversation, botMessageId);
        }, 300);
    };
    return (
        <div className="prompt-wrapper">
            <form className={`prompt-form flex items-center ${myMargin}`} onSubmit={handleSubmit}>
                <input placeholder="Describe your goal..." className="prompt-input flex-1" value={promptText} onChange={(e) => setPromptText(e.target.value)} required />
                <button type="submit" className="send-prompt-btn">
                    <ArrowUp size={20} />
                </button>
            </form>
        </div>
    );
};

export default PromptForm;