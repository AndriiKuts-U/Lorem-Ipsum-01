// frontend/src/components/ScenarioCards.jsx
import { Utensils, Salad, Clock, Heart } from 'lucide-react';
import GlassSurface from "@/components/GlassSurface.jsx";

const scenarios = [
    {
        id: 1,
        title: "Quick Dinner",
        prompt: "Suggest a quick and easy dinner recipe that can be prepared in under 30 minutes"
    },
    {
        id: 2,
        title: "Healthy Meal",
        prompt: "Create a healthy, balanced meal plan with lean protein and vegetables"
    },
    {
        id: 3,
        title: "Meal Prep",
        prompt: "Help me create a weekly meal prep plan for busy weekdays"
    },
    {
        id: 4,
        title: "Comfort Food",
        prompt: "Suggest a comforting homemade dish for a cozy evening"
    }
];

const ScenarioCards = ({ onSelectScenario }) => {
    return (
        <div className="scenario-cards-container">
            <div className="scenario-cards-grid">
                {scenarios.map((scenario) => (
                    <button
                        key={scenario.id}
                        className="scenario-card"
                        onClick={() => onSelectScenario(scenario.prompt)}
                    >
                        <h3 className="scenario-title">{scenario.title}</h3>
                    </button>
                ))}
            </div>
        </div>
    );
};

export default ScenarioCards;