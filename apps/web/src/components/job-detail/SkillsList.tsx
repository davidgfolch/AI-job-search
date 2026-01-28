import { useState, useMemo } from 'react';
import SkillTag from '../skills/SkillTag';
import { useLearnList, type Skill } from '../skills/useLearnList';
import { EditSkillModal } from '../skills/EditSkillModal';

interface SkillsListProps {
    skills: string | null;
    allJobSkills?: string | null;
}

export default function SkillsList({ skills, allJobSkills }: SkillsListProps) {
    const { toggleSkill, isInLearnList, skillExists, saveSkill } = useLearnList();
    const [editingSkill, setEditingSkill] = useState<Skill | null>(null);

    const parsedSkills = useMemo(() => {
        if (!skills) return [];
        return Array.from(new Set(skills.split(',').map(s => s.trim()).filter(Boolean)));
    }, [skills]);

    const navigableSkills = useMemo(() => {
        const sourceSkills = allJobSkills || skills;
        if (!sourceSkills) return [];
        const uniqueSkills = Array.from(new Set(sourceSkills.split(',').map(s => s.trim()).filter(Boolean)));
        return uniqueSkills.filter(skill => skillExists(skill));
    }, [skills, allJobSkills, skillExists]);

    if (!skills) return null;

    const handleViewDetail = (skillName: string) => {
        const existing = skillExists(skillName);
        if (existing) {
            setEditingSkill(existing);
        } else {
            setEditingSkill({
                name: skillName.trim(),
                description: '',
                learningPath: [],
                disabled: false
            });
        }
    };

    const handleSaveSkill = (updates: { description: string; learningPath: string[] }) => {
        if (editingSkill) {
            saveSkill({
                ...editingSkill,
                ...updates
            });
            setEditingSkill(null);
        }
    };

    const currentIndex = editingSkill ? navigableSkills.indexOf(editingSkill.name) : -1;
    const hasPrevious = currentIndex > 0;
    const hasNext = currentIndex !== -1 && currentIndex < navigableSkills.length - 1;

    const handlePrevious = () => {
        if (hasPrevious) {
            handleViewDetail(navigableSkills[currentIndex - 1]);
        }
    };

    const handleNext = () => {
        if (hasNext) {
            handleViewDetail(navigableSkills[currentIndex + 1]);
        }
    };

    return (
        <>
            {parsedSkills.map((skill) => (
                <SkillTag
                    key={skill}
                    skill={skill}
                    isInLearnList={isInLearnList(skill)}
                    onToggle={toggleSkill}
                    onViewDetail={handleViewDetail}
                />
            ))}
            {editingSkill && (
                <EditSkillModal
                    skill={editingSkill}
                    onSave={handleSaveSkill}
                    onUpdate={saveSkill}
                    onClose={() => setEditingSkill(null)}
                    onNext={handleNext}
                    onPrevious={handlePrevious}
                    hasNext={hasNext}
                    hasPrevious={hasPrevious}
                />
            )}
        </>
    );
}
