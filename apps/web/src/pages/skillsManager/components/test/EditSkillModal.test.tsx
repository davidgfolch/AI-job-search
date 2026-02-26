import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { EditSkillModal } from '../EditSkillModal';

const queryClient = new QueryClient();
const renderWithClient = (ui: React.ReactElement) => render(
    <QueryClientProvider client={queryClient}>{ui}</QueryClientProvider>
);

describe('EditSkillModal', () => {
    const mockSkill = { name: 'React', description: 'Lib', learningPath: [] };

    it('renders in View mode by default for existing skills', () => {
        renderWithClient(<EditSkillModal skill={mockSkill} onSave={vi.fn()} onClose={vi.fn()} />);
        expect(screen.getByText('Skill: React')).toBeInTheDocument();
        expect(screen.getByText('Lib')).toBeInTheDocument();
        expect(screen.getByRole('button', { name: /Edit/i })).toBeInTheDocument();
        expect(screen.queryByText('Save Changes')).not.toBeInTheDocument();
    });

    it('opens new skill in Edit mode by default', () => {
        renderWithClient(<EditSkillModal skill={{ ...mockSkill, name: '' }} onSave={vi.fn()} onClose={vi.fn()} />);
        expect(screen.getByText('Add New Skill')).toBeInTheDocument();
        expect(screen.getByText('Create Skill')).toBeInTheDocument();
        expect(screen.queryByRole('button', { name: /Edit/i })).not.toBeInTheDocument(); 
    });

    it('switches between View and Edit modes', () => {
        renderWithClient(<EditSkillModal skill={mockSkill} onSave={vi.fn()} onClose={vi.fn()} />);
        fireEvent.click(screen.getByRole('button', { name: /Edit/i }));
        expect(screen.getByText('Edit Skill: React')).toBeInTheDocument();
        expect(screen.getByDisplayValue('Lib')).toBeInTheDocument();
        expect(screen.getByText('Save Changes')).toBeInTheDocument();
        
        fireEvent.click(screen.getByRole('button', { name: /View/i }));
        expect(screen.getByText('Skill: React')).toBeInTheDocument();
    });

    it.each([
        { shortcut: 'Ctrl+Enter', ctrlKey: true, metaKey: false },
        { shortcut: 'Meta+Enter', ctrlKey: false, metaKey: true },
    ])('submits form on $shortcut in Edit Mode', ({ ctrlKey, metaKey }) => {
        const onSave = vi.fn();
        renderWithClient(<EditSkillModal skill={mockSkill} onSave={onSave} onClose={vi.fn()} />);
        fireEvent.click(screen.getByRole('button', { name: /Edit/i }));
        fireEvent.keyDown(window, { key: 'Enter', ctrlKey, metaKey });
        expect(onSave).toHaveBeenCalled();
    });

    it('toggles expand mode', () => {
        renderWithClient(<EditSkillModal skill={mockSkill} onSave={vi.fn()} onClose={vi.fn()} />);
        const expandBtn = screen.getByTitle('Expand');
        fireEvent.click(expandBtn);
        expect(screen.getByTitle('Collapse')).toBeInTheDocument();
        fireEvent.click(screen.getByTitle('Collapse'));
        expect(screen.getByTitle('Expand')).toBeInTheDocument();
    });

    it.each([
        { title: 'Next Skill', prop: 'onNext' },
        { title: 'Previous Skill', prop: 'onPrevious' },
    ])('calls $prop when $title is clicked', ({ title, prop }) => {
        const callbacks = { onNext: vi.fn(), onPrevious: vi.fn() };
        renderWithClient(
            <EditSkillModal 
                skill={mockSkill} onSave={vi.fn()} onClose={vi.fn()} 
                hasNext={true} hasPrevious={true}
                {...callbacks}
            />
        );
        fireEvent.click(screen.getByTitle(title));
        expect(callbacks[prop as keyof typeof callbacks]).toHaveBeenCalled();
    });

    it('disables navigation buttons when no more skills', () => {
        renderWithClient(
            <EditSkillModal 
                skill={mockSkill} onSave={vi.fn()} onClose={vi.fn()} 
                hasNext={false} hasPrevious={false}
            />
        );
        expect(screen.getByTitle('Next Skill')).toBeDisabled();
        expect(screen.getByTitle('Previous Skill')).toBeDisabled();
    });

    it('handles AI auto-fill button visibility and state', () => {
        vi.stubGlobal('__AI_ENRICHNEW_SKILL_ENABLED__', true);
        const { rerender } = renderWithClient(<EditSkillModal skill={mockSkill} onSave={vi.fn()} onClose={vi.fn()} />);
        expect(screen.getByRole('button', { name: /Auto-fill with AI/i })).not.toBeDisabled();

        rerender(
            <QueryClientProvider client={queryClient}>
                <EditSkillModal skill={{ ...mockSkill, name: '' }} onSave={vi.fn()} onClose={vi.fn()} />
            </QueryClientProvider>
        );
        expect(screen.getByRole('button', { name: /Auto-fill with AI/i })).toBeDisabled();
        vi.stubGlobal('__AI_ENRICHNEW_SKILL_ENABLED__', false);
    });
});


