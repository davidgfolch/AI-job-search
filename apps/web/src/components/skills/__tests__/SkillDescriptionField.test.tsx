import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { SkillDescriptionField } from '../SkillDescriptionField';
import type { Skill } from '../useLearnList';

describe('SkillDescriptionField', () => {
    const mockSkill: Skill = {
        name: 'React',
        description: 'Lib',
        learningPath: [],
    };

    const defaultProps = {
        description: 'Lib',
        setDescription: vi.fn(),
        isViewMode: true,
        skill: mockSkill,
    };

    it('renders description in view mode', () => {
        render(<SkillDescriptionField {...defaultProps} />);
        expect(screen.getByText('Lib')).toBeInTheDocument();
        expect(screen.queryByRole('textbox')).not.toBeInTheDocument();
    });

    it('renders textarea in edit mode', () => {
        render(<SkillDescriptionField {...defaultProps} isViewMode={false} />);
        expect(screen.getByRole('textbox')).toBeInTheDocument();
        expect(screen.getByDisplayValue('Lib')).toBeInTheDocument();
    });

    it('calls setDescription on change', () => {
        const setDescription = vi.fn();
        render(<SkillDescriptionField {...defaultProps} isViewMode={false} setDescription={setDescription} />);
        const textarea = screen.getByRole('textbox');
        fireEvent.change(textarea, { target: { value: 'New Desc' } });
        expect(setDescription).toHaveBeenCalledWith('New Desc');
    });
});
