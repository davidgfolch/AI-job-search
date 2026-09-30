import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import CompanySynonymsManager from '../CompanySynonymsManager';
import type { SynonymGroup } from '../api/CompanySynonymsManagerApi';

const mockSynonyms = vi.hoisted(() => ({
    createGroup: vi.fn(),
    addToGroup: vi.fn(),
    removeName: vi.fn(),
    state: { groups: [] as SynonymGroup[], isLoading: false, error: null as unknown },
}));

vi.mock('../hooks/useCompanySynonyms', () => ({
    useCompanySynonyms: () => ({
        groups: mockSynonyms.state.groups,
        isLoading: mockSynonyms.state.isLoading,
        error: mockSynonyms.state.error,
        createGroup: mockSynonyms.createGroup,
        addToGroup: mockSynonyms.addToGroup,
        removeName: mockSynonyms.removeName,
    }),
}));

vi.mock('../components/EditSynonymGroupModal', () => ({
    EditSynonymGroupModal: ({ onSave, onClose, groupId, existingNames }: { onSave: (names: string[]) => void; onClose: () => void; groupId?: number; existingNames?: string[] }) => (
        <div data-testid="modal" data-group-id={groupId ?? 'new'}>
            <span data-testid="modal-existing">{existingNames?.join(',') ?? ''}</span>
            <button onClick={() => onSave(['New Corp', 'New Corp Ltd'])}>mock-save</button>
            <button onClick={onClose}>mock-close</button>
        </div>
    ),
}));

const groups: SynonymGroup[] = [
    { group_id: 1, names: ['Acme', 'Acme Inc'] },
    { group_id: 2, names: ['Globex'] },
];

describe('CompanySynonymsManager', () => {
    beforeEach(() => {
        vi.clearAllMocks();
        mockSynonyms.createGroup.mockResolvedValue(undefined);
        mockSynonyms.addToGroup.mockResolvedValue(undefined);
        mockSynonyms.removeName.mockResolvedValue(undefined);
        mockSynonyms.state = { groups, isLoading: false, error: null };
        vi.stubGlobal('confirm', vi.fn(() => true));
    });

    it('renders the page header and the groups table', () => {
        render(<CompanySynonymsManager />);
        expect(screen.getByRole('heading', { name: 'AI Job Search - Company Synonyms' })).toBeInTheDocument();
        expect(screen.getByText('Acme')).toBeInTheDocument();
        expect(screen.queryByText('Loading synonym groups...')).not.toBeInTheDocument();
    });

    it('hides the table and shows the indicator while loading', () => {
        mockSynonyms.state = { groups: [], isLoading: true, error: null };
        render(<CompanySynonymsManager />);
        expect(screen.getByText('Loading synonym groups...')).toBeInTheDocument();
        expect(screen.queryByRole('table')).not.toBeInTheDocument();
    });

    it('renders the error message when the query fails', () => {
        mockSynonyms.state = { groups: [], isLoading: false, error: new Error('backend down') };
        render(<CompanySynonymsManager />);
        expect(screen.getByText('Error: backend down')).toBeInTheDocument();
    });

    it('creates a group and closes the create modal on save', async () => {
        render(<CompanySynonymsManager />);
        fireEvent.click(screen.getByRole('button', { name: '+ Add Synonym Group' }));
        expect(screen.getByTestId('modal')).toHaveAttribute('data-group-id', 'new');
        fireEvent.click(screen.getByRole('button', { name: 'mock-save' }));
        await waitFor(() => expect(mockSynonyms.createGroup).toHaveBeenCalledWith(['New Corp', 'New Corp Ltd']));
        await waitFor(() => expect(screen.queryByTestId('modal')).not.toBeInTheDocument());
    });

    it('closes the create modal without creating when dismissed', async () => {
        render(<CompanySynonymsManager />);
        fireEvent.click(screen.getByRole('button', { name: '+ Add Synonym Group' }));
        fireEvent.click(screen.getByRole('button', { name: 'mock-close' }));
        expect(screen.queryByTestId('modal')).not.toBeInTheDocument();
        expect(mockSynonyms.createGroup).not.toHaveBeenCalled();
    });

    it('opens the add-to-group modal pre-filled with the target group names', () => {
        render(<CompanySynonymsManager />);
        fireEvent.click(screen.getAllByRole('button', { name: '+ Add' })[1]);
        expect(screen.getByTestId('modal')).toHaveAttribute('data-group-id', '2');
        expect(screen.getByTestId('modal-existing')).toHaveTextContent('Globex');
    });

    it('adds the first saved name to the selected group and closes the modal', async () => {
        render(<CompanySynonymsManager />);
        fireEvent.click(screen.getAllByRole('button', { name: '+ Add' })[0]);
        fireEvent.click(screen.getByRole('button', { name: 'mock-save' }));
        await waitFor(() => expect(mockSynonyms.addToGroup).toHaveBeenCalledWith({ groupId: 1, name: 'New Corp' }));
        await waitFor(() => expect(screen.queryByTestId('modal')).not.toBeInTheDocument());
    });

    it('removes a single name after confirmation', async () => {
        render(<CompanySynonymsManager />);
        fireEvent.click(screen.getAllByTitle('Remove this name')[1]);
        await waitFor(() => expect(mockSynonyms.removeName).toHaveBeenCalledTimes(1));
        expect(mockSynonyms.removeName).toHaveBeenCalledWith('Acme Inc');
    });

    it('does not remove a name when the confirmation is declined', async () => {
        vi.stubGlobal('confirm', vi.fn(() => false));
        render(<CompanySynonymsManager />);
        fireEvent.click(screen.getAllByTitle('Remove this name')[0]);
        await Promise.resolve();
        expect(mockSynonyms.removeName).not.toHaveBeenCalled();
    });

    it('removes every name of a group one by one after confirmation', async () => {
        render(<CompanySynonymsManager />);
        fireEvent.click(screen.getAllByRole('button', { name: '× Remove All' })[0]);
        await waitFor(() => expect(mockSynonyms.removeName).toHaveBeenCalledTimes(2));
        expect(mockSynonyms.removeName).toHaveBeenNthCalledWith(1, 'Acme');
        expect(mockSynonyms.removeName).toHaveBeenNthCalledWith(2, 'Acme Inc');
    });

    it('does not remove a group when the confirmation is declined', async () => {
        vi.stubGlobal('confirm', vi.fn(() => false));
        render(<CompanySynonymsManager />);
        fireEvent.click(screen.getAllByRole('button', { name: '× Remove All' })[1]);
        await Promise.resolve();
        expect(mockSynonyms.removeName).not.toHaveBeenCalled();
    });
});