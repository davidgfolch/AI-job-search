import { renderHook, act } from '@testing-library/react';
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { useLearnList } from '../useLearnList';

// Mock localStorage
const localStorageMock = (() => {
  let store: Record<string, string> = {};

  return {
    getItem: (key: string) => store[key] || null,
    setItem: (key: string, value: string) => {
      store[key] = value;
    },
    clear: () => {
      store = {};
    },
  };
})();

// Define strict types for our expected data shapes
interface TestSkill {
  name: string;
  description: string;
  learningPath: string[];
  disabled?: boolean;
}

Object.defineProperty(window, 'localStorage', {
  value: localStorageMock,
});

describe('useLearnList', () => {
  beforeEach(() => {
    localStorageMock.clear();
    vi.clearAllMocks();
  });

  it('initializes with empty list', () => {
    const { result } = renderHook(() => useLearnList());
    
    expect(result.current.learnList).toEqual([]);
  });

  it('loads existing learn list from localStorage and migrates strings', () => {
    // Store legacy string data
    localStorageMock.setItem('job-skills-learn-list', JSON.stringify(['React', 'TypeScript']));
    
    const { result } = renderHook(() => useLearnList());
    
    expect(result.current.learnList).toHaveLength(2);
    expect(result.current.learnList[0]).toEqual({ name: 'React', description: '', learningPath: [], disabled: false });
    expect(result.current.learnList[1]).toEqual({ name: 'TypeScript', description: '', learningPath: [], disabled: false });
  });

  it('adds skill to learn list when toggled', () => {
    const { result } = renderHook(() => useLearnList());
    
    act(() => {
      result.current.toggleSkill('JavaScript');
    });
    
    expect(result.current.learnList).toHaveLength(1);
    expect(result.current.learnList[0].name).toBe('JavaScript');
    expect(result.current.isInLearnList('JavaScript')).toBe(true);
  });

  it('removes skill from learn list when toggled twice', () => {
    const { result } = renderHook(() => useLearnList());
    
    act(() => {
      result.current.toggleSkill('Node.js');
    });
    
    expect(result.current.isInLearnList('Node.js')).toBe(true);
    
    act(() => {
      result.current.toggleSkill('Node.js');
    });
    
    expect(result.current.isInLearnList('Node.js')).toBe(false);
  });

  it('checks if skill is in learn list correctly', () => {
    const initialData = [
      { name: 'Python', description: '', learningPath: [] },
      { name: 'Django', description: '', learningPath: [] }
    ];
    localStorageMock.setItem('job-skills-learn-list', JSON.stringify(initialData));
    
    const { result } = renderHook(() => useLearnList());
    
    expect(result.current.isInLearnList('Python')).toBe(true);
    expect(result.current.isInLearnList('Flask')).toBe(false);
  });

  it('reorders skills correctly', () => {
    const initialData = [
      { name: 'A', description: '', learningPath: [] },
      { name: 'B', description: '', learningPath: [] },
      { name: 'C', description: '', learningPath: [] }
    ];
    localStorageMock.setItem('job-skills-learn-list', JSON.stringify(initialData));
    const { result } = renderHook(() => useLearnList());
    
    const reordered = [initialData[2], initialData[0], initialData[1]]; // C, A, B
    
    act(() => {
      result.current.reorderSkills(reordered);
    });
    
    expect(result.current.learnList).toEqual(reordered);
    expect(JSON.parse(localStorageMock.getItem('job-skills-learn-list')!)).toEqual(reordered);
  });

  it('removes skill via removeSkill function', () => {
    const initialData = [
      { name: 'A', description: '', learningPath: [] },
      { name: 'B', description: '', learningPath: [] }
    ];
    localStorageMock.setItem('job-skills-learn-list', JSON.stringify(initialData));
    const { result } = renderHook(() => useLearnList());
    
    act(() => {
      result.current.removeSkill('A');
    });
    
    expect(result.current.learnList).toHaveLength(1);
    expect(result.current.learnList[0].name).toBe('B');
  });

  it('updates skill details', () => {
    const initialData = [
      { name: 'React', description: '', learningPath: [] }
    ];
    localStorageMock.setItem('job-skills-learn-list', JSON.stringify(initialData));
    const { result } = renderHook(() => useLearnList());
    
    act(() => {
      result.current.updateSkill('React', { description: 'UI Lib', learningPath: ['https://react.dev'] });
    });
    
    expect(result.current.learnList[0].description).toBe('UI Lib');
    expect(result.current.learnList[0].learningPath).toEqual(['https://react.dev']);
  });

  it('soft deletes skill with content', () => {
    const { result } = renderHook(() => useLearnList());
    
    // Add skill and content
    act(() => {
      result.current.toggleSkill('RichSkill');
    });
    act(() => {
      result.current.updateSkill('RichSkill', { description: 'Has info' });
    });

    // Remove it
    act(() => {
      result.current.removeSkill('RichSkill');
    });
    
    // Should still be in list but disabled
    const stored = JSON.parse(localStorageMock.getItem('job-skills-learn-list')!) as TestSkill[];
    expect(stored).toHaveLength(1);
    expect(stored[0].name).toBe('RichSkill');
    expect(stored[0].disabled).toBe(true);

    // Should NOT be considered "in learn list" for UI purposes check
    expect(result.current.isInLearnList('RichSkill')).toBe(false);
  });

  it('re-enables disabled skill when added again', () => {
    const { result } = renderHook(() => useLearnList());
    
    // Setup disabled skill
    const initialData = [
      { name: 'DisabledSkill', description: 'Info', learningPath: [], disabled: true }
    ];
    localStorageMock.setItem('job-skills-learn-list', JSON.stringify(initialData));

    // Verify initially disabled
    expect(result.current.isInLearnList('DisabledSkill')).toBe(false);

    // Toggle (add equivalent)
    act(() => {
      result.current.toggleSkill('DisabledSkill');
    });

    // Verify enabled
    expect(result.current.isInLearnList('DisabledSkill')).toBe(true);
    
    const stored = JSON.parse(localStorageMock.getItem('job-skills-learn-list')!) as TestSkill[];
    expect(stored[0].disabled).toBe(false);
  });

});
