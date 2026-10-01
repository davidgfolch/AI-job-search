import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { CompanySynonymsTable } from '../CompanySynonymsTable';
import type { SynonymGroup } from '../../api/CompanySynonymsManagerApi';

describe('CompanySynonymsTable', () => {
    const groups: SynonymGroup[] = [
        { group_id: 7, names: ['Acme', 'Acme Inc'] },
        { group_id: 9, names: ['Globex'] },
    ];
    let onAddToGroup: ReturnType<typeof vi.fn>;
    let onRemoveName: ReturnType<typeof vi.fn>;
    let onRemoveGroup: ReturnType<typeof vi.fn>;

    beforeEach(() => {
        onAddToGroup = vi.fn();
        onRemoveName = vi.fn();
        onRemoveGroup = vi.fn();
    });

    const renderTable = (data: SynonymGroup[] = groups) =>
        render(<CompanySynonymsTable groups={data} onAddToGroup={onAddToGroup} onRemoveName={onRemoveName} onRemoveGroup={onRemoveGroup} />);

    it('renders one row per group with all its names', () => {
        renderTable();
        expect(screen.getAllByRole('row')).toHaveLength(3);
        expect(screen.getByText('7')).toBeInTheDocument();
        expect(screen.getByText('Acme')).toBeInTheDocument();
        expect(screen.getByText('Acme Inc')).toBeInTheDocument();
        expect(screen.getByText('Globex')).toBeInTheDocument();
    });

    it('shows an empty message when there are no groups', () => {
        renderTable([]);
        expect(screen.getByText('No synonym groups defined yet.')).toBeInTheDocument();
        expect(screen.getAllByRole('row')).toHaveLength(2);
    });

    it('calls onAddToGroup with the group id when + Add is clicked', () => {
        renderTable();
        fireEvent.click(screen.getAllByRole('button', { name: '+ Add' })[1]);
        expect(onAddToGroup).toHaveBeenCalledTimes(1);
        expect(onAddToGroup).toHaveBeenCalledWith(9);
    });

    it('calls onRemoveName with the clicked name', () => {
        renderTable();
        fireEvent.click(screen.getAllByTitle('Remove this name')[1]);
        expect(onRemoveName).toHaveBeenCalledWith('Acme Inc');
    });

    it('calls onRemoveGroup with the whole group when Remove All is clicked', () => {
        renderTable();
        fireEvent.click(screen.getAllByRole('button', { name: '× Remove All' })[0]);
        expect(onRemoveGroup).toHaveBeenCalledWith(groups[0]);
    });
});