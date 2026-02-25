import { Link } from 'react-router-dom';
import Dropdown from './core/Dropdown';
import './HeaderMenu.css';

const HeaderMenu = () => {
  const trigger = (
    <button className="menu-button" aria-label="Menu">
      Menu
    </button>
  );

  return (
    <Dropdown trigger={trigger} className="header-menu">
      <div className="menu-items">
        <Link to="/statistics" target="_blank" className="menu-item">
          Statistics
        </Link>
        <Link to="/skills-manager" className="menu-item" target="_blank">
          Skills Manager
        </Link>
        <Link to="/settings" className="menu-item" target="_blank">
          Settings
        </Link>
      </div>
    </Dropdown>
  );
};

export default HeaderMenu;
