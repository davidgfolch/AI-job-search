import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import SkillTag from '../SkillTag';

describe('SkillTag', () => {
  describe.each([
    { skill: 'React', isInLearnList: false, shouldHaveClass: false },
    { skill: 'TypeScript', isInLearnList: true, shouldHaveClass: true },
    { skill: 'JavaScript', isInLearnList: false, shouldHaveClass: false },
    { skill: 'Python', isInLearnList: true, shouldHaveClass: true }
  ])('skill "$skill" with isInLearnList=$isInLearnList', ({ skill, isInLearnList, shouldHaveClass }) => {
    it(`renders skill name correctly`, () => {
      const onToggle = vi.fn();
      render(<SkillTag skill={skill} isInLearnList={isInLearnList} onToggle={onToggle} />);
      
      expect(screen.getByText(skill)).toBeInTheDocument();
    });

    it(`${shouldHaveClass ? 'applies' : 'does not apply'} learn list class`, () => {
      const onToggle = vi.fn();
      render(<SkillTag skill={skill} isInLearnList={isInLearnList} onToggle={onToggle} />);
      
      const tag = screen.getByText(skill);
      if (shouldHaveClass) {
        expect(tag).toHaveClass('skill-tag-learn');
      } else {
        expect(tag).not.toHaveClass('skill-tag-learn');
      }
    });

    it(`displays appropriate title`, () => {
      const onToggle = vi.fn();
      render(<SkillTag skill={skill} isInLearnList={isInLearnList} onToggle={onToggle} />);
      
      const tag = screen.getByText(skill);
      const expectedTitle = isInLearnList ? 'Click to remove from learn list' : 'Click to add to learn list';
      expect(tag).toHaveAttribute('title', expectedTitle);
    });
  });

  describe.each([
    { skill: 'Node.js', isInLearnList: false },
    { skill: 'Go', isInLearnList: true },
    { skill: 'Rust', isInLearnList: true },
    { skill: 'Java', isInLearnList: false }
  ])('click behavior for "$skill"', ({ skill, isInLearnList }) => {
    it('calls onToggle when clicked', () => {
      const onToggle = vi.fn();
      render(<SkillTag skill={skill} isInLearnList={isInLearnList} onToggle={onToggle} />);
      
      const tag = screen.getByText(skill);
      fireEvent.click(tag);
      
      expect(onToggle).toHaveBeenCalledWith(skill);
      expect(onToggle).toHaveBeenCalledTimes(1);
    });
  });

  describe.each([
    { skill: 'Go', isInLearnList: true, shouldShowButton: true },
    { skill: 'Go', isInLearnList: false, shouldShowButton: false },
    { skill: 'TypeScript', isInLearnList: true, shouldShowButton: true },
    { skill: 'TypeScript', isInLearnList: false, shouldShowButton: false }
  ])('view detail button for "$skill"', ({ skill, isInLearnList, shouldShowButton }) => {
    it(`${shouldShowButton ? 'renders' : 'does not render'} view detail button`, () => {
      const onToggle = vi.fn();
      const onViewDetail = vi.fn();
      render(<SkillTag skill={skill} isInLearnList={isInLearnList} onToggle={onToggle} onViewDetail={onViewDetail} />);
      
      if (shouldShowButton) {
        expect(screen.getByText('👁')).toBeInTheDocument();
      } else {
        expect(screen.queryByText('👁')).not.toBeInTheDocument();
      }
    });
  });

  it('calls onViewDetail and stops propagation when button is clicked', () => {
    const onToggle = vi.fn();
    const onViewDetail = vi.fn();
    render(<SkillTag skill="Rust" isInLearnList={true} onToggle={onToggle} onViewDetail={onViewDetail} />);
    
    const button = screen.getByText('👁');
    fireEvent.click(button);
    
    expect(onViewDetail).toHaveBeenCalledWith('Rust');
    expect(onToggle).not.toHaveBeenCalled();
  });

  it('displays description card on hover when provided', async () => {
    const onToggle = vi.fn();
    const onViewDetail = vi.fn();
    render(
      <SkillTag 
        skill="Rust" 
        description="A systems programming language"
        isInLearnList={true} 
        onToggle={onToggle} 
        onViewDetail={onViewDetail} 
      />
    );
    
    const button = screen.getByLabelText('View skill details');
    
    fireEvent.mouseEnter(button);
    
    expect(screen.getByText('A systems programming language')).toBeInTheDocument();
  });

  it('does not display default title on button', () => {
    const onToggle = vi.fn();
    const onViewDetail = vi.fn();
    render(
      <SkillTag 
        skill="Rust" 
        isInLearnList={true} 
        onToggle={onToggle} 
        onViewDetail={onViewDetail} 
      />
    );
    
    const button = screen.getByLabelText('View skill details');
    expect(button).not.toHaveAttribute('title');
  });
});