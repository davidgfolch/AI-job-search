import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import SkillTag from '../SkillTag';

describe('SkillTag', () => {
  it('renders skill name correctly', () => {
    const onToggle = vi.fn();
    render(<SkillTag skill="React" isInLearnList={false} onToggle={onToggle} />);
    
    expect(screen.getByText('React')).toBeInTheDocument();
  });

  it('applies learn list class when skill is in learn list', () => {
    const onToggle = vi.fn();
    render(<SkillTag skill="TypeScript" isInLearnList={true} onToggle={onToggle} />);
    
    const tag = screen.getByText('TypeScript');
    expect(tag).toHaveClass('skill-tag-learn');
  });

  it('does not apply learn list class when skill is not in learn list', () => {
    const onToggle = vi.fn();
    render(<SkillTag skill="JavaScript" isInLearnList={false} onToggle={onToggle} />);
    
    const tag = screen.getByText('JavaScript');
    expect(tag).not.toHaveClass('skill-tag-learn');
  });

  it('calls onToggle when clicked', () => {
    const onToggle = vi.fn();
    render(<SkillTag skill="Node.js" isInLearnList={false} onToggle={onToggle} />);
    
    const tag = screen.getByText('Node.js');
    fireEvent.click(tag);
    
    expect(onToggle).toHaveBeenCalledWith('Node.js');
    expect(onToggle).toHaveBeenCalledTimes(1);
  });

  it('displays appropriate title for learn list items', () => {
    const onToggle = vi.fn();
    render(<SkillTag skill="Python" isInLearnList={true} onToggle={onToggle} />);
    
    const tag = screen.getByText('Python');
    expect(tag).toHaveAttribute('title', 'Click to remove from learn list');
  });

  it('displays appropriate title for non-learn list items', () => {
    const onToggle = vi.fn();
    render(<SkillTag skill="Java" isInLearnList={false} onToggle={onToggle} />);
    
    const tag = screen.getByText('Java');
    expect(tag).toHaveAttribute('title', 'Click to add to learn list');
  });

  it('renders view detail button when onViewDetail is provided and skill is in learn list', () => {
    const onToggle = vi.fn();
    const onViewDetail = vi.fn();
    render(<SkillTag skill="Go" isInLearnList={true} onToggle={onToggle} onViewDetail={onViewDetail} />);
    
    expect(screen.getByText('👁')).toBeInTheDocument();
  });

  it('does not render view detail button when skill is NOT in learn list', () => {
    const onToggle = vi.fn();
    const onViewDetail = vi.fn();
    render(<SkillTag skill="Go" isInLearnList={false} onToggle={onToggle} onViewDetail={onViewDetail} />);
    
    expect(screen.queryByText('👁')).not.toBeInTheDocument();
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
    
    expect(await screen.findByText('A systems programming language')).toBeInTheDocument();
    
    fireEvent.mouseLeave(button);
    // Since it's in a portal, we might need to wait for removal or use queryByText
    await vi.waitFor(() => {
        expect(screen.queryByText('A systems programming language')).not.toBeInTheDocument();
    });
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
