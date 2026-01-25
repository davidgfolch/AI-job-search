import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { EditSkillModal } from '../EditSkillModal';

const queryClient = new QueryClient();

const renderWithClient = (ui: React.ReactElement) => {
    return render(
        <QueryClientProvider client={queryClient}>
            {ui}
        </QueryClientProvider>
    );
};

describe('EditSkillModal', () => {
    const mockSkill = {
        name: 'React',
        description: 'Lib',
        learningPath: [],
    };

    it('renders with skill data', () => {
        renderWithClient(<EditSkillModal skill={mockSkill} onSave={vi.fn()} onClose={vi.fn()} />);
        expect(screen.getByText('Edit Skill: React')).toBeInTheDocument();
        expect(screen.getByDisplayValue('Lib')).toBeInTheDocument();
    });

    it('should call onSave when Ctrl+Enter is pressed', () => {
        const onSave = vi.fn();
        renderWithClient(<EditSkillModal skill={mockSkill} onSave={onSave} onClose={vi.fn()} />);
        fireEvent.keyDown(window, { key: 'Enter', ctrlKey: true });
        expect(onSave).toHaveBeenCalledTimes(1);
    });

    it('should call onSave when Meta+Enter is pressed', () => {
        const onSave = vi.fn();
        renderWithClient(<EditSkillModal skill={mockSkill} onSave={onSave} onClose={vi.fn()} />);
        fireEvent.keyDown(window, { key: 'Enter', metaKey: true });
        expect(onSave).toHaveBeenCalledTimes(1);
    });
});

