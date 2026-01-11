import { renderHook, act, waitFor } from '@testing-library/react';
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { useLearnList } from '../useLearnList';
import { skillsApi } from '../../../api/skills';

// Mock skillsApi
vi.mock('../../../api/skills', () => ({
  skillsApi: {
    getSkills: vi.fn(),
    createSkill: vi.fn(),
    deleteSkill: vi.fn(),
    updateSkill: vi.fn(),
  },
}));

describe('useLearnList', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('initializes with empty list and fetches skills', async () => {
    (skillsApi.getSkills as any).mockResolvedValue([]);
    const { result } = renderHook(() => useLearnList());

    await waitFor(() => expect(result.current.isLoading).toBe(false));
    expect(result.current.learnList).toEqual([]);
    expect(skillsApi.getSkills).toHaveBeenCalled();
  });

  it('adds skill via API when toggled if not exists', async () => {
     (skillsApi.getSkills as any).mockResolvedValue([]);
     const { result } = renderHook(() => useLearnList());
     
     await waitFor(() => expect(result.current.isLoading).toBe(false));

     (skillsApi.createSkill as any).mockResolvedValue('ok');
     (skillsApi.getSkills as any).mockResolvedValueOnce([{ name: 'JavaScript', description: '', learningPath: [], disabled: false }]);

     await act(async () => {
       await result.current.toggleSkill('JavaScript');
     });

     expect(skillsApi.createSkill).toHaveBeenCalledWith(expect.objectContaining({ name: 'JavaScript' }));
     // Should re-fetch
     expect(skillsApi.getSkills).toHaveBeenCalledTimes(2);
  });

  it('removes skill via API (soft or hard depending on content) when toggled if exists', async () => {
    const existing = [{ name: 'Node.js', description: '', learningPath: [], disabled: false }];
    (skillsApi.getSkills as any).mockResolvedValue(existing);
    
    const { result } = renderHook(() => useLearnList());
    await waitFor(() => expect(result.current.isLoading).toBe(false));

    (skillsApi.deleteSkill as any).mockResolvedValue('ok');
    
    await act(async () => {
      await result.current.toggleSkill('Node.js');
    });

    // Content is empty, so should be hard delete
    expect(skillsApi.deleteSkill).toHaveBeenCalledWith('Node.js');
    expect(skillsApi.getSkills).toHaveBeenCalledTimes(2); // Initial + after delete
  });

  it('checks if skill is in learn list correctly', async () => {
    const existing = [
        { name: 'Python', description: '', learningPath: [], disabled: false },
        { name: 'Django', description: '', learningPath: [], disabled: true }
    ];
    (skillsApi.getSkills as any).mockResolvedValue(existing);
    
    const { result } = renderHook(() => useLearnList());
    await waitFor(() => expect(result.current.isLoading).toBe(false));
    
    expect(result.current.isInLearnList('Python')).toBe(true);
    expect(result.current.isInLearnList('Django')).toBe(false);
  });

  it('reorders skills (client side only for now)', async () => {
     // Implementation just sets state
     const initial = [
         { name: 'A', description: '', learningPath: [], disabled: false },
         { name: 'B', description: '', learningPath: [], disabled: false }
     ];
     (skillsApi.getSkills as any).mockResolvedValue(initial);

     const { result } = renderHook(() => useLearnList());
     await waitFor(() => expect(result.current.isLoading).toBe(false));

     const reordered = [initial[1], initial[0]];
     
     act(() => {
         result.current.reorderSkills(reordered);
     });

     expect(result.current.learnList).toEqual(reordered);
  });

  it('updates skill details via API', async () => {
     (skillsApi.getSkills as any).mockResolvedValue([]);
     const { result } = renderHook(() => useLearnList());
     await waitFor(() => expect(result.current.isLoading).toBe(false));

     (skillsApi.updateSkill as any).mockResolvedValue('ok');

     await act(async () => {
         await result.current.updateSkill('React', { description: 'New' });
     });

     expect(skillsApi.updateSkill).toHaveBeenCalledWith('React', { description: 'New' });
     expect(skillsApi.getSkills).toHaveBeenCalledTimes(2);
  });

  it('soft deletes skill with content', async () => {
     const existing = [{ name: 'Rich', description: 'Has info', learningPath: [], disabled: false }];
     (skillsApi.getSkills as any).mockResolvedValue(existing);

     const { result } = renderHook(() => useLearnList());
     await waitFor(() => expect(result.current.isLoading).toBe(false));

     (skillsApi.updateSkill as any).mockResolvedValue('ok');

     await act(async () => {
         await result.current.removeSkill('Rich');
     });

     // Should be update with disabled: true
     expect(skillsApi.updateSkill).toHaveBeenCalledWith('Rich', { disabled: true });
     expect(skillsApi.deleteSkill).not.toHaveBeenCalled();
  });
});
