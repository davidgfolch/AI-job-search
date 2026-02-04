import { useState, useMemo } from 'react';
import SkillTag from '../../../skillsManager/components/SkillTag';
import { useLearnList, type Skill } from '../../../skillsManager/hooks/useLearnList';
import { EditSkillModal } from '../../../skillsManager/components/EditSkillModal';
import { normalizeName } from '../../../skillsManager/utils/skillUtils';

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
        const rawSkills = sourceSkills.split(',').map(s => s.trim()).filter(Boolean);
        const seen = new Set<string>();
        const uniqueByNormalized: string[] = [];
        for (const skill of rawSkills) {
            const normalized = normalizeName(skill);
            if (!seen.has(normalized)) {
                seen.add(normalized);
                uniqueByNormalized.push(skill);
            }
        }
        return uniqueByNormalized.filter(skill => skillExists(skill));
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

    const currentIndex = editingSkill ? navigableSkills.findIndex(s => normalizeName(s) === normalizeName(editingSkill.name)) : -1;
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
            {parsedSkills.map((skill) => {
                const skillObj = skillExists(skill);
                return (
                    <SkillTag
                        key={skill}
                        skill={skill}
                        description={skillObj?.description}
                        isInLearnList={isInLearnList(skill)}
                        onToggle={toggleSkill}
                        onViewDetail={handleViewDetail}
                    />
                );
            })}
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
