import './SkillTag.css';

interface SkillTagProps {
  skill: string;
  isInLearnList: boolean;
  onToggle: (skill: string) => void;
}

export default function SkillTag({ skill, isInLearnList, onToggle }: SkillTagProps) {
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
    </span>
  );
}
