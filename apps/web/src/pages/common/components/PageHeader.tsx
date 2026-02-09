import React, { useEffect } from 'react';
import HeaderMenu from './HeaderMenu';
import './PageHeader.css';
interface PageHeaderProps {
  title: string;
  children?: React.ReactNode;
}
const PageHeader: React.FC<PageHeaderProps> = ({ title, children }) => {
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
          <HeaderMenu />
        </div>
      </div>
    </header>
  );
};
export default PageHeader;
