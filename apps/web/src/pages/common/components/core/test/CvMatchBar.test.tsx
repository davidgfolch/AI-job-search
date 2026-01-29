import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import CvMatchBar from '../CvMatchBar';

describe('CvMatchBar', () => {
    it('renders correctly with a valid percentage', () => {
        render(<CvMatchBar percentage={75} />);
        
        const progressBar = screen.getByTitle('75% Match');
        expect(progressBar).toBeInTheDocument();
        
        const text = screen.getByText('75%');
        expect(text).toBeInTheDocument();
        
        // Check if the visual bar width is set correctly
        // Note: we might need to look at styles specifically
        const fill = progressBar.querySelector('.cv-match-bar-fill');
        expect(fill).toHaveStyle({ width: '75%' });
    });

    it('clamps percentage to 0 if negative', () => {
        render(<CvMatchBar percentage={-10} />);
        
        const progressBar = screen.getByTitle('-10% Match');
        expect(progressBar).toBeInTheDocument();
        
        const text = screen.getByText('-10%');
        expect(text).toBeInTheDocument();
        
        const fill = progressBar.querySelector('.cv-match-bar-fill');
        expect(fill).toHaveStyle({ width: '0%' });
    });

    it('clamps percentage to 100 if greater than 100', () => {
        render(<CvMatchBar percentage={150} />);
        
        const progressBar = screen.getByTitle('150% Match');
        expect(progressBar).toBeInTheDocument();
        
        const text = screen.getByText('150%');
        expect(text).toBeInTheDocument();
        
        const fill = progressBar.querySelector('.cv-match-bar-fill');
        expect(fill).toHaveStyle({ width: '100%' });
    });
});
