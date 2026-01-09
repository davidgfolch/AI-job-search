import { render, screen } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { SkillsTable } from '../SkillsTable';

describe('SkillsTable', () => {
    const skills = [
        { name: 'React', description: 'desc', learningPath: [] 
    }];

    it('renders skills', () => {
        render(<SkillsTable skills={skills} onReorder={vi.fn()} onEdit={vi.fn()} onRemove={vi.fn()} />);
        expect(screen.getByText('React')).toBeInTheDocument();
        expect(screen.getByText('desc')).toBeInTheDocument();
    });
});
