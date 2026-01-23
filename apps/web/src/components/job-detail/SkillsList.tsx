import { useState } from 'react';
import SkillTag from '../skills/SkillTag';
import { useLearnList, type Skill } from '../skills/useLearnList';
import { EditSkillModal } from '../skills/EditSkillModal';

interface SkillsListProps {
    skills: string | null;
}

export default function SkillsList({ skills }: SkillsListProps) {
    const { toggleSkill, isInLearnList, skillExists, saveSkill } = useLearnList();
    const [editingSkill, setEditingSkill] = useState<Skill | null>(null);

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

    return (
        <>
            {Array.from(new Set(skills.split(',').map(s => s.trim()).filter(Boolean))).map((skill) => (
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
                    onClose={() => setEditingSkill(null)}
                />
            )}
        </>
    );
}
