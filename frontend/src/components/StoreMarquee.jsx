// frontend/src/components/StoreMarquee.jsx
import { motion } from 'framer-motion';

const stores = [
    { name: 'Lidl', color: '#0050AA' },
    { name: 'Kaufland', color: '#E10915' },
    { name: 'Tesco', color: '#00539F' },
    { name: 'Billa', color: '#FFD100' },
    { name: 'Fresh', color: '#7AB929' },
];

// Duplicate stores for seamless loop
const duplicatedStores = [...stores, ...stores, ...stores, ...stores];

const StoreMarquee = () => {
    return (
        <div className="marquee-container">
            <motion.div
                className="marquee-track"
                animate={{ x: ['0%', '-50%'] }}
                transition={{
                    x: {
                        repeat: Infinity,
                        repeatType: 'loop',
                        duration: 20,
                        ease: 'linear',
                    },
                }}
            >
                {duplicatedStores.map((store, index) => (
                    <div
                        key={index}
                        className="marquee-item"
                    >
                        <span
                            className="store-badge"
                            style={{
                                background: `${store.color}15`,
                                borderColor: `${store.color}40`,
                                color: store.color
                            }}
                        >
                            {store.name}
                        </span>
                    </div>
                ))}
            </motion.div>
        </div>
    );
};

export default StoreMarquee;