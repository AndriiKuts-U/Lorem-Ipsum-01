import GlassSurface from './GlassSurface'
import GlassIcons from "./GlassIcons.jsx";
import {FiDollarSign, FiHeart} from "react-icons/fi";

const Header = () => {
    const items = [
        { icon: <FiDollarSign />, color: 'blue', label: 'Money' },
        { icon: <FiHeart />, color: 'purple', label: 'Products' },
        ];

    return (
            <div className="flex justify-end items-center p-5">
                <GlassSurface
                    width={150}
                    height={400}
                    borderRadius={999}
                    className="glass-class"
                >
                    <div style={{ height: '300px', position: 'relative' }}>
                        <GlassIcons items={items} className="custom-class"/>
                    </div>
                </GlassSurface>
            </div>
    );
}

export default Header;