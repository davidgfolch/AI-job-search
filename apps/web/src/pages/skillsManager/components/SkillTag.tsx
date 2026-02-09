import { useState, useRef, useLayoutEffect } from 'react';
import { createPortal } from 'react-dom';
import ReactMarkdown from 'react-markdown';
import './SkillTag.css';

interface SkillTagProps {
  skill: string;
  description?: string;
  isInLearnList: boolean;
  onToggle: (skill: string) => void;
  onViewDetail?: (skill: string) => void;
}

export default function SkillTag({ skill, description, isInLearnList, onToggle, onViewDetail }: SkillTagProps) {
  const [showDescription, setShowDescription] = useState(false);
  const [descriptionStyle, setDescriptionStyle] = useState<React.CSSProperties>({});
  const buttonRef = useRef<HTMLButtonElement>(null);
  const cardRef = useRef<HTMLDivElement>(null);
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const handleMouseEnter = () => {
    if (timerRef.current) {
      clearTimeout(timerRef.current);
      timerRef.current = null;
    }
    setShowDescription(true);
  };

  const handleMouseLeave = () => {
    timerRef.current = setTimeout(() => {
      setShowDescription(false);
    }, 300);
  };

  useLayoutEffect(() => {
    if (showDescription && buttonRef.current && cardRef.current) {
      const buttonRect = buttonRef.current.getBoundingClientRect();
      const cardRect = cardRef.current.getBoundingClientRect();
      const viewportWidth = window.innerWidth;
      const viewportHeight = window.innerHeight;
      const gap = 8;

      let top = buttonRect.bottom + gap;
      let left = buttonRect.left + (buttonRect.width / 2) - (cardRect.width / 2);

      // Vertical positioning
      if (top + cardRect.height > viewportHeight - 10) {
         const topAbove = buttonRect.top - cardRect.height - gap;
         if (topAbove > 10) {
             top = topAbove;
         } else {
             if (viewportHeight - buttonRect.bottom > buttonRect.top) {
                 top = buttonRect.bottom + gap;
             } else {
                 top = 10;
             }
         }
      }

      // Horizontal positioning
      if (left < 10) left = 10;
      if (left + cardRect.width > viewportWidth - 10) {
          left = viewportWidth - cardRect.width - 10;
      }

      setDescriptionStyle({
        top: `${top}px`,
        left: `${left}px`,
        position: 'fixed',
        transform: 'none',
        visibility: 'visible',
        zIndex: 10000 // Ensure visible on top of everything
      });
    } else if (!showDescription) {
        setDescriptionStyle({});
    }
  }, [showDescription]);

  return (
    <span
      className={`skill-tag ${isInLearnList ? 'skill-tag-learn' : ''}`}
      onClick={() => onToggle(skill)}
      title={isInLearnList ? 'Click to remove from learn list' : 'Click to add to learn list'}
    >
      {skill}
      {onViewDetail && isInLearnList && (
        <div className="skill-detail-container">
           <button
            ref={buttonRef}
            className="skill-detail-btn"
            onClick={(e) => {
              e.stopPropagation();
              onViewDetail(skill);
            }}
            onMouseEnter={handleMouseEnter}
            onMouseLeave={handleMouseLeave}
            aria-label="View skill details"
          >
            👁
          </button>
          {showDescription && description && createPortal(
            <div 
                ref={cardRef}
                className="skill-description-card"
                style={descriptionStyle}
                onMouseEnter={handleMouseEnter}
                onMouseLeave={handleMouseLeave}
                onClick={(e) => e.stopPropagation()}
            >
              <ReactMarkdown>{description}</ReactMarkdown>
            </div>,
            document.body
          )}
        </div>
      )}
    </span>
  );
}
