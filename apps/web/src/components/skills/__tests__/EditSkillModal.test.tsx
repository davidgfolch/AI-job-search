import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { EditSkillModal } from '../EditSkillModal';

describe('EditSkillModal', () => {
    const mockSkill = {
        name: 'React',
        description: 'Lib',
        learningPath: [],
    };

    it('renders with skill data', () => {
        render(<EditSkillModal skill={mockSkill} onSave={vi.fn()} onClose={vi.fn()} />);
        expect(screen.getByText('Edit Skill: React')).toBeInTheDocument();
        expect(screen.getByDisplayValue('Lib')).toBeInTheDocument();
    });

    it('should call onSave when Ctrl+Enter is pressed', () => {
        const onSave = vi.fn();
        render(<EditSkillModal skill={mockSkill} onSave={onSave} onClose={vi.fn()} />);
        fireEvent.keyDown(window, { key: 'Enter', ctrlKey: true });
        expect(onSave).toHaveBeenCalledTimes(1);
    });

    it('should call onSave when Meta+Enter is pressed', () => {
        const onSave = vi.fn();
        render(<EditSkillModal skill={mockSkill} onSave={onSave} onClose={vi.fn()} />);
        fireEvent.keyDown(window, { key: 'Enter', metaKey: true });
        expect(onSave).toHaveBeenCalledTimes(1);
    });
});
