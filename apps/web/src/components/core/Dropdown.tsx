import { useState, useRef, useEffect, type ReactNode } from 'react';
import './Dropdown.css';

interface DropdownProps {
  trigger: ReactNode;
  children: ReactNode;
  className?: string;
}

const Dropdown = ({ trigger, children, className = '' }: DropdownProps) => {
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  const toggleDropdown = () => setIsOpen(!isOpen);

  const closeDropdown = () => setIsOpen(false);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };

    const handleEscapeKey = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        setIsOpen(false);
      }
    };

    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
      document.addEventListener('keydown', handleEscapeKey);
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
      document.removeEventListener('keydown', handleEscapeKey);
    };
  }, [isOpen]);

  return (
    <div className={`dropdown ${className}`} ref={dropdownRef}>
      <div onClick={toggleDropdown} className="dropdown-trigger">
        {trigger}
      </div>
      {isOpen && (
        <div className="dropdown-content" onClick={closeDropdown}>
          {children}
        </div>
      )}
    </div>
  );
};

export default Dropdown;
