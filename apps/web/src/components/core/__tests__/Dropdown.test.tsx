import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import Dropdown from '../Dropdown';

describe('Dropdown', () => {
  it('renders trigger button correctly', () => {
    const trigger = <button>Click Me</button>;
    render(<Dropdown trigger={trigger}>Content</Dropdown>);
    
    expect(screen.getByText('Click Me')).toBeInTheDocument();
  });

  it('does not show content initially', () => {
    const trigger = <button>Click Me</button>;
    render(<Dropdown trigger={trigger}><div>Dropdown Content</div></Dropdown>);
    
    expect(screen.queryByText('Dropdown Content')).not.toBeInTheDocument();
  });

  it('opens dropdown when trigger is clicked', () => {
    const trigger = <button>Click Me</button>;
    render(<Dropdown trigger={trigger}><div>Dropdown Content</div></Dropdown>);
    
    fireEvent.click(screen.getByText('Click Me'));
    expect(screen.getByText('Dropdown Content')).toBeInTheDocument();
  });

  it('closes dropdown when clicking outside', () => {
    const trigger = <button>Click Me</button>;
    render(
      <div>
        <Dropdown trigger={trigger}><div>Dropdown Content</div></Dropdown>
        <div>Outside</div>
      </div>
    );
    
    fireEvent.click(screen.getByText('Click Me'));
    expect(screen.getByText('Dropdown Content')).toBeInTheDocument();
    
    fireEvent.mouseDown(screen.getByText('Outside'));
    expect(screen.queryByText('Dropdown Content')).not.toBeInTheDocument();
  });

  it('closes dropdown when Escape key is pressed', () => {
    const trigger = <button>Click Me</button>;
    render(<Dropdown trigger={trigger}><div>Dropdown Content</div></Dropdown>);
    
    fireEvent.click(screen.getByText('Click Me'));
    expect(screen.getByText('Dropdown Content')).toBeInTheDocument();
    
    fireEvent.keyDown(document, { key: 'Escape' });
    expect(screen.queryByText('Dropdown Content')).not.toBeInTheDocument();
  });

  it('toggles dropdown on multiple clicks', () => {
    const trigger = <button>Click Me</button>;
    render(<Dropdown trigger={trigger}><div>Dropdown Content</div></Dropdown>);
    
    fireEvent.click(screen.getByText('Click Me'));
    expect(screen.getByText('Dropdown Content')).toBeInTheDocument();
    
    fireEvent.click(screen.getByText('Click Me'));
    expect(screen.queryByText('Dropdown Content')).not.toBeInTheDocument();
  });

  it('closes dropdown when clicking inside content', () => {
    const trigger = <button>Click Me</button>;
    render(<Dropdown trigger={trigger}><div>Dropdown Content</div></Dropdown>);
    
    fireEvent.click(screen.getByText('Click Me'));
    expect(screen.getByText('Dropdown Content')).toBeInTheDocument();
    
    fireEvent.click(screen.getByText('Dropdown Content'));
    expect(screen.queryByText('Dropdown Content')).not.toBeInTheDocument();
  });
});
