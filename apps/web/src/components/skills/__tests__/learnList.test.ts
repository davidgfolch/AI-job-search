import { describe, it, expect, beforeEach } from 'vitest';
import { getLearnList, addToLearnList, removeFromLearnList } from '../learnList';

describe('learnList', () => {
    beforeEach(() => {
        localStorage.clear();
    });

    it('should add to learn list', () => {
        addToLearnList('React');
        expect(getLearnList()).toHaveLength(1);
        expect(getLearnList()[0].name).toBe('React');
    });

    it('should remove from learn list (hard delete if empty)', () => {
        addToLearnList('React');
        removeFromLearnList('React');
        expect(getLearnList()).toHaveLength(0);
    });

    it('should soft delete if has content', () => {
        addToLearnList('React');
        // Manually manipulate for test or assume addToLearnList init empty.
        // We need to modify it. But learnList.ts doesn't export internal update.
        // We can use default params or mock. 
        // Actually, let's just test basic add/remove for now.
        // For soft delete, we'd need to add description which is not in the API unless we hack localStorage.
        const list = [{ name: 'React', description: 'desc', learningPath: [], disabled: false }];
        localStorage.setItem('job-skills-learn-list', JSON.stringify(list));
        
        removeFromLearnList('React');
        const updated = getLearnList();
        expect(updated).toHaveLength(1);
        expect(updated[0].disabled).toBe(true);
    });
});
