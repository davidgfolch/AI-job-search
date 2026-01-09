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
            {skills.split(',').map((skill) => (
                <SkillTag
                    key={skill.trim()}
                    skill={skill.trim()}
                    isInLearnList={isInLearnList(skill.trim())}
                    onToggle={toggleSkill}/>
            ))}
        </>
    );
}
