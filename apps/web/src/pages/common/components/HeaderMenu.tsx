import { useState } from 'react';
import { Link } from 'react-router-dom';
import Dropdown from './core/Dropdown';
import ShortcutsPopup, { type ShortcutsMenuData } from './core/ShortcutsPopup';
import './HeaderMenu.css';

const HeaderMenu = ({ shortcuts }: { shortcuts?: ShortcutsMenuData }) => {
  const [showShortcuts, setShowShortcuts] = useState(false);
  const trigger = (
    <button className="menu-button" aria-label="Menu">
      Menu
    </button>
  );

  return (
    <>
      <Dropdown trigger={trigger} className="header-menu">
        <div className="menu-items">
          <Link to="/dashboard" target="_blank" className="menu-item">
            Dashboard
          </Link>
          <Link to="/statistics" target="_blank" className="menu-item">
            Statistics
          </Link>
          <Link to="/skills-manager" className="menu-item" target="_blank">
            Skills Manager
          </Link>
          <Link to="/company-synonyms" className="menu-item" target="_blank">
            Company Synonyms
          </Link>
          <Link to="/settings" className="menu-item" target="_blank">
            Settings
          </Link>
          {shortcuts && (
            <button className="menu-item" onClick={() => setShowShortcuts(true)}>
              Shortcuts
            </button>
          )}
        </div>
      </Dropdown>
      {shortcuts && <ShortcutsPopup {...shortcuts} isOpen={showShortcuts} onClose={() => setShowShortcuts(false)} />}
    </>
  );
};

export default HeaderMenu;
