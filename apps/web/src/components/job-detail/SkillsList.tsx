import SkillTag from '../skills/SkillTag';
import { useLearnList } from '../skills/useLearnList';

interface SkillsListProps {
    skills: string | null;
}

export default function SkillsList({ skills }: SkillsListProps) {
    const { toggleSkill, isInLearnList } = useLearnList();

    if (!skills) return null;

    return (
        <>
            {Array.from(new Set(skills.split(',').map(s => s.trim()).filter(Boolean))).map((skill) => (
                <SkillTag
                    key={skill}
                    skill={skill}
                    isInLearnList={isInLearnList(skill)}
                    onToggle={toggleSkill}
                />
            ))}
        </>
    );
}
