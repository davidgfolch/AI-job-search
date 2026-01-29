import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { SkillsTable } from '../SkillsTable';

describe('SkillsTable', () => {


    it('renders skills', () => {
        const skillsWithMarkdown = [
            { name: 'React', description: '**desc**', learningPath: [] 
        }];
        render(<SkillsTable skills={skillsWithMarkdown} onReorder={vi.fn()} onEdit={vi.fn()} onRemove={vi.fn()} />);
        expect(screen.getByText('React')).toBeInTheDocument();
        // Check for strong tag which indicates markdown rendering
        expect(screen.getByText('desc').tagName).toBe('STRONG');
    });

    it('toggles description expansion on click', () => {
        const skills = [{ name: 'Test Skill', description: 'Long description', learningPath: [] }];
        render(<SkillsTable skills={skills} onReorder={vi.fn()} onEdit={vi.fn()} onRemove={vi.fn()} />);
        
        const descriptionText = screen.getByText('Long description');
        // The click handler is on the parent div with class read-only-text
        // We can find it by closest or by walking up, but since ReactMarkdown is used, 
        // the text is inside a p usually (if markdown) or direct.
        // In the test setup, it renders direct text if no markdown chars are used? 
        // ReactMarkdown wraps in p by default.
        // Let's modify the query to be safe.
        
        // Actually, let's use a simpler approach. Search by class? No, better by text then parent.
        // render renders: <div class="read-only-text"><p>Long description</p></div> (usually)
        
        const cell = descriptionText.closest('.read-only-text');
        expect(cell).toBeInTheDocument();
        expect(cell).not.toHaveClass('expanded');
        
        if (cell) {
             fireEvent.click(cell);
             expect(cell).toHaveClass('expanded');
             
             fireEvent.click(cell);
             expect(cell).not.toHaveClass('expanded');
        }
    });
});
