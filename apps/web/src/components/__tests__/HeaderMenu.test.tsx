import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
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
});
