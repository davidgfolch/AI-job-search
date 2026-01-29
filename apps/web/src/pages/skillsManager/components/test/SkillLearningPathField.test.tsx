import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { SkillLearningPathField } from '../SkillLearningPathField';

describe('SkillLearningPathField', () => {
    const defaultProps = {
        learningPath: ['https://example.com'],
        skillLearningPath: ['https://example.com'],
        isViewMode: true,
        newLinkInput: '',
        setNewLinkInput: vi.fn(),
        handleAddLink: vi.fn(),
        handleRemoveLink: vi.fn(),
        handleLinkInputKeyDown: vi.fn(),
    };

    it('renders links in view mode', () => {
        render(<SkillLearningPathField {...defaultProps} />);
        expect(screen.getByRole('link', { name: 'https://example.com' })).toBeInTheDocument();
        expect(screen.queryByRole('textbox')).not.toBeInTheDocument();
    });

    it('renders links and input in edit mode', () => {
        render(<SkillLearningPathField {...defaultProps} isViewMode={false} />);
        expect(screen.getByText('https://example.com')).toBeInTheDocument();
        expect(screen.getByRole('textbox')).toBeInTheDocument();
        expect(screen.getByTitle('Add link')).toBeInTheDocument();
    });

    it('calls handleAddLink when add button is clicked', () => {
        const handleAddLink = vi.fn();
        render(<SkillLearningPathField {...defaultProps} isViewMode={false} newLinkInput="https://test.com" handleAddLink={handleAddLink} />);
        fireEvent.click(screen.getByTitle('Add link'));
        expect(handleAddLink).toHaveBeenCalled();
    });
});
