import { renderHook, act } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { useEditSkillForm } from '../useEditSkillForm';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

const queryClient = new QueryClient();

const wrapper = ({ children }: { children: React.ReactNode }) => (
  <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
);

describe('useEditSkillForm', () => {
    const mockSkill = {
        name: 'React',
        description: 'Lib',
        learningPath: [],
    };

    it('should initialize with skill data', () => {
        const { result } = renderHook(() => useEditSkillForm({ skill: mockSkill, onSave: vi.fn() }), { wrapper });
        expect(result.current.name).toBe('React');
        expect(result.current.description).toBe('Lib');
    });

    it('should update name', () => {
        const { result } = renderHook(() => useEditSkillForm({ skill: mockSkill, onSave: vi.fn() }), { wrapper });
        act(() => {
            result.current.setName('Vue');
        });
        expect(result.current.name).toBe('Vue');
    });

    it('should add link', () => {
        const { result } = renderHook(() => useEditSkillForm({ skill: mockSkill, onSave: vi.fn() }), { wrapper });
        act(() => {
            result.current.setNewLinkInput('http://example.com');
        });
        act(() => {
            result.current.handleAddLink();
        });
        expect(result.current.learningPath).toContain('http://example.com');
    });
});
