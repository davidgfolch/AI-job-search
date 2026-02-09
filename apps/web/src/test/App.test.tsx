import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import App from '../App';

// Mock child components to avoid full rendering and reliance on their internal logic
vi.mock('../pages/viewer/Viewer', () => ({
  default: () => <div data-testid="viewer-page">Viewer Page</div>
}));

vi.mock('../pages/common/components/HeaderMenu', () => ({
  default: () => <div data-testid="header-menu">Header Menu</div>
}));

vi.mock('../pages/statistics/Statistics', () => ({
  default: () => <div data-testid="statistics-page">Statistics Page</div>
}));

vi.mock('../pages/skillsManager/SkillsManager', () => ({
  default: () => <div data-testid="skills-manager-page">Skills Manager Page</div>
}));

describe('App', () => {
  it('renders Viewer page on root route', () => {
    render(
      <MemoryRouter initialEntries={['/']}>
        <App />
      </MemoryRouter>
    );
    expect(screen.getByTestId('viewer-page')).toBeInTheDocument();
  });

  it('renders Statistics page on /statistics route', () => {
    render(
      <MemoryRouter initialEntries={['/statistics']}>
        <App />
      </MemoryRouter>
    );
    expect(screen.getByTestId('statistics-page')).toBeInTheDocument();
    expect(screen.queryByTestId('viewer-page')).not.toBeInTheDocument();
  });

  it('renders Skills Manager page on /skills-manager route', () => {
    render(
      <MemoryRouter initialEntries={['/skills-manager']}>
        <App />
      </MemoryRouter>
    );
    expect(screen.getByTestId('skills-manager-page')).toBeInTheDocument();
    expect(screen.queryByTestId('viewer-page')).not.toBeInTheDocument();
  });
});
