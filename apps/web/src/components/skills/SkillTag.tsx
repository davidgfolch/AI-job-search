import './SkillTag.css';

interface SkillTagProps {
  skill: string;
  isInLearnList: boolean;
  onToggle: (skill: string) => void;
  onViewDetail?: (skill: string) => void;
}

export default function SkillTag({ skill, isInLearnList, onToggle, onViewDetail }: SkillTagProps) {
  const handleClick = () => {
    onToggle(skill);
  };

  return (
    <span
      className={`skill-tag ${isInLearnList ? 'skill-tag-learn' : ''}`}
      onClick={handleClick}
      title={isInLearnList ? 'Click to remove from learn list' : 'Click to add to learn list'}
    >
      {skill}
      {onViewDetail && isInLearnList && (
        <button
          className="skill-detail-btn"
          onClick={(e) => {
            e.stopPropagation();
            onViewDetail(skill);
          }}
          title="View skill details"
        >
          👁
        </button>
      )}
    </span>
  );
}
