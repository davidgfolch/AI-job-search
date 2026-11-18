import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { BrowserRouter } from 'react-router-dom';
import HeaderMenu from '../HeaderMenu';

const renderWithRouter = (component: React.ReactElement) => {
  return render(<BrowserRouter>{component}</BrowserRouter>);
};

describe('HeaderMenu', () => {
  it('renders menu button correctly', () => {
    renderWithRouter(<HeaderMenu />);
    
    expect(screen.getByText('Menu')).toBeInTheDocument();
    expect(screen.getByLabelText('Menu')).toBeInTheDocument();
  });

  it('does not show menu items initially', () => {
    renderWithRouter(<HeaderMenu />);
    
    expect(screen.queryByText('Statistics')).not.toBeInTheDocument();
  });

  it('opens dropdown when menu button is clicked', () => {
    renderWithRouter(<HeaderMenu />);
    
    fireEvent.click(screen.getByText('Menu'));
    expect(screen.getByText('Statistics')).toBeInTheDocument();
  });

  it('Statistics link has correct attributes', () => {
    renderWithRouter(<HeaderMenu />);
    
    fireEvent.click(screen.getByText('Menu'));
    const statsLink = screen.getByText('Statistics');
    
    expect(statsLink).toHaveAttribute('href', '/statistics');
    expect(statsLink).toHaveAttribute('target', '_blank');
  });

  it('closes dropdown when menu button is clicked again', () => {
    renderWithRouter(<HeaderMenu />);
    
    fireEvent.click(screen.getByText('Menu'));
    expect(screen.getByText('Statistics')).toBeInTheDocument();
    
    fireEvent.click(screen.getByText('Menu'));
    expect(screen.queryByText('Statistics')).not.toBeInTheDocument();
  });

  it('closes dropdown when Statistics link is clicked', () => {
    renderWithRouter(<HeaderMenu />);
    
    fireEvent.click(screen.getByText('Menu'));
    expect(screen.getByText('Statistics')).toBeInTheDocument();
    
    fireEvent.click(screen.getByText('Statistics'));
    expect(screen.queryByText('Statistics')).not.toBeInTheDocument();
  });

  const shortcuts = {
    enabled: true,
    onToggle: vi.fn(),
    shortcuts: [{ label: 'Ignore job', description: 'Mark selected job as ignored', display: 'Alt+I' }],
  };

  it('does not show the Shortcuts item without shortcut data', () => {
    renderWithRouter(<HeaderMenu />);

    fireEvent.click(screen.getByText('Menu'));
    expect(screen.queryByText('Shortcuts')).not.toBeInTheDocument();
  });

  it('opens the shortcuts popup from the menu item', () => {
    renderWithRouter(<HeaderMenu shortcuts={shortcuts} />);

    fireEvent.click(screen.getByText('Menu'));
    fireEvent.click(screen.getByText('Shortcuts'));
    expect(screen.getByText('Keyboard shortcuts')).toBeInTheDocument();
    expect(screen.getByText('Alt+I')).toBeInTheDocument();
    expect(screen.queryByText('Statistics')).not.toBeInTheDocument();
  });

  it('toggles shortcuts from the popup header', () => {
    const onToggle = vi.fn();
    renderWithRouter(<HeaderMenu shortcuts={{ ...shortcuts, onToggle }} />);

    fireEvent.click(screen.getByText('Menu'));
    fireEvent.click(screen.getByText('Shortcuts'));
    fireEvent.click(screen.getByTitle('Keyboard shortcuts enabled'));
    expect(onToggle).toHaveBeenCalledOnce();
  });
});
