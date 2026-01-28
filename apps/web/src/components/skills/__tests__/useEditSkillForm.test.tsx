import { renderHook, act } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { useEditSkillForm } from '../useEditSkillForm';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { skillsApi } from '../../../api/skills';

vi.mock('../../../api/skills', () => ({
    skillsApi: {
        getSkill: vi.fn(),
    }
}));

const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
});

const wrapper = ({ children }: { children: React.ReactNode }) => (
  <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
);

describe('useEditSkillForm', () => {
    const mockSkill = {
        name: 'React',
        description: 'Lib',
        learningPath: ['link1'],
        category: 'Frontend',
    };

    beforeEach(() => {
        vi.clearAllMocks();
        queryClient.clear();
    });

    it('should initialize with skill data', () => {
        const { result } = renderHook(() => useEditSkillForm({ skill: mockSkill, onSave: vi.fn() }), { wrapper });
        expect(result.current.name).toBe('React');
        expect(result.current.description).toBe('Lib');
        expect(result.current.learningPath).toEqual(['link1']);
        expect(result.current.category).toBe('Frontend');
    });

    it('should update basic state fields', () => {
        const { result } = renderHook(() => useEditSkillForm({ skill: mockSkill, onSave: vi.fn() }), { wrapper });
        act(() => {
            result.current.setName('Vue');
            result.current.setCategory('Framework');
            result.current.setDescription('Vue Lib');
        });
        expect(result.current.name).toBe('Vue');
        expect(result.current.category).toBe('Framework');
        expect(result.current.description).toBe('Vue Lib');
    });

    it('should manage links correctly', () => {
        const { result } = renderHook(() => useEditSkillForm({ skill: mockSkill, onSave: vi.fn() }), { wrapper });
        act(() => { result.current.setNewLinkInput('link2'); });
        act(() => { result.current.handleAddLink(); });
        expect(result.current.learningPath).toEqual(['link1', 'link2']);
        act(() => { result.current.handleRemoveLink(0); });
        expect(result.current.learningPath).toEqual(['link2']);
    });

    it('should call onSave with mapped data and handle validation', () => {
        const onSave = vi.fn();
        const alertSpy = vi.spyOn(window, 'alert').mockImplementation(() => {});
        const { result } = renderHook(() => useEditSkillForm({ skill: mockSkill, onSave }), { wrapper });
        
        act(() => { result.current.handleSave(); });
        expect(onSave).toHaveBeenCalledWith(expect.objectContaining({ name: 'React' }));

        act(() => { result.current.setName(''); });
        act(() => { result.current.handleSave(); });
        expect(alertSpy).toHaveBeenCalledWith("Skill name is required");
        alertSpy.mockRestore();
    });

    it.each([
        { ctrlKey: true, metaKey: false },
        { ctrlKey: false, metaKey: true },
    ])('should call handleSave on Ctrl/Meta + Enter', ({ ctrlKey, metaKey }) => {
        const onSave = vi.fn();
        renderHook(() => useEditSkillForm({ skill: mockSkill, onSave }), { wrapper });
        window.dispatchEvent(new KeyboardEvent('keydown', { key: 'Enter', ctrlKey, metaKey }));
        expect(onSave).toHaveBeenCalled();
    });

    it('should handle auto-fill and polling', async () => {
        vi.useFakeTimers();
        const onUpdate = vi.fn();
        const enrichedSkill = { ...mockSkill, description: 'AI Content', ai_enriched: true };
        vi.mocked(skillsApi.getSkill).mockResolvedValue(enrichedSkill);
        
        const { result } = renderHook(() => useEditSkillForm({ skill: mockSkill, onSave: vi.fn(), onUpdate }), { wrapper });
        await act(async () => { await result.current.handleAutoFill(); });
        expect(result.current.isPolling).toBe(true);

        await act(async () => { vi.advanceTimersByTime(10000); });
        expect(result.current.description).toBe('AI Content');
        expect(result.current.isPolling).toBe(false);
        vi.useRealTimers();
    });

    it('should handle reload and keyboard events', async () => {
        vi.mocked(skillsApi.getSkill).mockResolvedValueOnce({ ...mockSkill, description: 'Reloaded' });
        const { result } = renderHook(() => useEditSkillForm({ skill: mockSkill, onSave: vi.fn() }), { wrapper });
        
        await act(async () => { await result.current.handleReload(); });
        expect(result.current.description).toBe('Reloaded');

        act(() => { result.current.setNewLinkInput('k-link'); });
        act(() => { result.current.handleLinkInputKeyDown({ key: 'Enter' } as any); });
        expect(result.current.learningPath).toContain('k-link');
    });
});
