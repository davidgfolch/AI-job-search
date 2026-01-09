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

  it('loads existing learn list from localStorage', () => {
    localStorageMock.setItem('job-skills-learn-list', JSON.stringify(['React', 'TypeScript']));
    
    const { result } = renderHook(() => useLearnList());
    
    expect(result.current.learnList).toEqual(['React', 'TypeScript']);
  });

  it('adds skill to learn list when toggled', () => {
    const { result } = renderHook(() => useLearnList());
    
    act(() => {
      result.current.toggleSkill('JavaScript');
    });
    
    expect(result.current.learnList).toContain('JavaScript');
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
    localStorageMock.setItem('job-skills-learn-list', JSON.stringify(['Python', 'Django']));
    
    const { result } = renderHook(() => useLearnList());
    
    expect(result.current.isInLearnList('Python')).toBe(true);
    expect(result.current.isInLearnList('Flask')).toBe(false);
  });

  it('reorders skills correctly', () => {
    localStorageMock.setItem('job-skills-learn-list', JSON.stringify(['A', 'B', 'C']));
    const { result } = renderHook(() => useLearnList());
    
    act(() => {
      result.current.reorderSkills(['C', 'A', 'B']);
    });
    
    expect(result.current.learnList).toEqual(['C', 'A', 'B']);
    expect(JSON.parse(localStorageMock.getItem('job-skills-learn-list')!)).toEqual(['C', 'A', 'B']);
  });

  it('removes skill via removeSkill function', () => {
    localStorageMock.setItem('job-skills-learn-list', JSON.stringify(['A', 'B']));
    const { result } = renderHook(() => useLearnList());
    
    act(() => {
      result.current.removeSkill('A');
    });
    
    expect(result.current.learnList).toEqual(['B']);
  });
});
