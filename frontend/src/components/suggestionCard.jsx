// src/components/SuggestionCards.jsx
import { Code, Lightbulb, PenLine, Sparkles } from "lucide-react";

const suggestions = [
    {
        icon: <PenLine size={24} />,
        title: "Write",
        description: "Help me write an email to my team about the project update",
        gradient: "linear-gradient(135deg, #667eea 0%, #764ba2 100%)"
    },
    {
        icon: <Code size={24} />,
        title: "Code",
        description: "Explain how async/await works in JavaScript",
        gradient: "linear-gradient(135deg, #f093fb 0%, #f5576c 100%)"
    },
    {
        icon: <Lightbulb size={24} />,
        title: "Brainstorm",
        description: "Give me 5 creative ideas for a birthday gift",
        gradient: "linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)"
    },
    {
        icon: <Sparkles size={24} />,
        title: "Create",
        description: "Generate a short story about a time traveler",
        gradient: "linear-gradient(135deg, #43e97b 0%, #38f9d7 100%)"
    }
];

const SuggestionCards = ({ onSuggestionClick }) => {
    return (
        <div className="suggestion-cards-container">
            <div className="suggestion-header">
                <h2 className="suggestion-title">How can I help you today?</h2>
                <p className="suggestion-subtitle">Choose a suggestion or type your own message</p>
            </div>
            <div className="suggestion-cards-grid">
                {suggestions.map((suggestion, index) => (
                    <button
                        key={index}
                        className="suggestion-card"
                        onClick={() => onSuggestionClick(suggestion.description)}
                    >
                        <div
                            className="suggestion-card-icon"
                            style={{ background: suggestion.gradient }}
                        >
                            {suggestion.icon}
                        </div>
                        <div className="suggestion-card-content">
                            <h3 className="suggestion-card-title">{suggestion.title}</h3>
                            <p className="suggestion-card-description">{suggestion.description}</p>
                        </div>
                    </button>
                ))}
            </div>
        </div>
    );
};

export default SuggestionCards;