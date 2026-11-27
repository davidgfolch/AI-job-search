import React, { useEffect } from 'react';
import HeaderMenu from './HeaderMenu';
import type { ShortcutsMenuData } from './core/ShortcutsPopup';
import './PageHeader.css';
interface PageHeaderProps {
  title: string;
  children?: React.ReactNode;
  shortcuts?: ShortcutsMenuData;
}
const PageHeader: React.FC<PageHeaderProps> = ({ title, children, shortcuts }) => {
  const fullTitle = `AI Job Search - ${title}`;
  useEffect(() => {
    document.title = fullTitle;
  }, [fullTitle]);
  return (
    <header className="app-header">
      <div className="header-content">
        <h1>{fullTitle}</h1>
        <div className="header-actions">
          {children}
          <HeaderMenu shortcuts={shortcuts} />
        </div>
      </div>
    </header>
  );
};
export default PageHeader;
