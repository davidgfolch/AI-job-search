import { render, screen } from '@testing-library/react';
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
});
