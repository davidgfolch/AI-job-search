import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import Settings from '../Settings';
import { settingsApi } from '../api/SettingsApi';
import { renderWithClient, setupSettingsMocks } from './Settings.mocks';

vi.mock('../api/SettingsApi');
vi.mock('../utils/SettingsUtils');
vi.mock('../../common/components/PageHeader', () => ({ default: () => <div /> }));
vi.mock('../../common/components/core/MessageContainer', () => ({
    default: ({ message }: { message: { text: string } | null }) => message ? <div data-testid="message-container">{message.text}</div> : null
}));

describe('Settings LLM provider selectors', () => {
    beforeEach(() => setupSettingsMocks());

    const renderSelectors = async () => {
        renderWithClient(<Settings />);
        await waitFor(() => expect(screen.getByText('LLM Providers')).toBeInTheDocument());
    };

    it('renders all three selectors with their own options and current values', async () => {
        await renderSelectors();
        const enrich = screen.getByLabelText('aiEnrich') as HTMLSelectElement;
        const skill = screen.getByLabelText('aiEnrichSkill') as HTMLSelectElement;
        const formFiller = screen.getByLabelText('aiFormFiller') as HTMLSelectElement;
        expect(enrich.value).toBe('ollama');
        expect(skill.value).toBe('ollama');
        expect(formFiller.value).toBe('local');
        expect([...enrich.options].map(o => o.value)).toEqual(['ollama', 'openrouter']);
        expect([...skill.options].map(o => o.value)).toEqual(['ollama', 'huggingface']);
        expect([...formFiller.options].map(o => o.value)).toEqual(['local', 'openrouter', 'openai']);
    });

    it('keeps API keys beside the selectors and the form-filler fields with aiFormFiller', async () => {
        await renderSelectors();
        const section = screen.getByText('LLM Providers').closest('.llm-providers-section');
        expect(section).toContainElement(document.getElementById('env-OPENAI_API_KEY')!);
        expect(section).toContainElement(document.getElementById('env-OPENROUTER_API_KEY')!);
        expect(section).toContainElement(document.getElementById('env-OPENROUTER_MODEL')!);
        const formFillerGroup = screen.getByLabelText('aiFormFiller').closest('.llm-provider-group');
        expect(formFillerGroup).toContainElement(document.getElementById('env-OPENAI_API_KEY')!);
        expect(formFillerGroup).toContainElement(document.getElementById('env-OPENROUTER_MODEL')!);
        expect(formFillerGroup).not.toContainElement(document.getElementById('env-OPENROUTER_API_KEY')!);
        expect(document.querySelectorAll('#env-OPENAI_API_KEY')).toHaveLength(1);
        expect(document.querySelectorAll('#env-OPENROUTER_API_KEY')).toHaveLength(1);
        expect(document.querySelectorAll('#env-OPENROUTER_MODEL')).toHaveLength(1);
        expect(document.getElementById('env-OPENAI_API_KEY')).toHaveAttribute('type', 'password');
        expect(document.getElementById('env-OPENROUTER_API_KEY')).toHaveAttribute('type', 'password');
    });

    it('saves aiEnrich immediately without saving the whole env or the other selector', async () => {
        await renderSelectors();
        await userEvent.selectOptions(screen.getByLabelText('aiEnrich'), 'openrouter');
        expect(settingsApi.updateEnvSetting).toHaveBeenCalledWith('AI_ENRICH_LLM_BACKEND', 'openrouter');
        expect(settingsApi.updateEnvSettingsBulk).not.toHaveBeenCalled();
        expect((screen.getByLabelText('aiEnrichSkill') as HTMLSelectElement).value).toBe('ollama');
        await waitFor(() => expect(screen.getByTestId('message-container')).toHaveTextContent('AI_ENRICH_LLM_BACKEND switched to openrouter'));
    });

    it('saves aiEnrichSkill independently from aiEnrich', async () => {
        await renderSelectors();
        await userEvent.selectOptions(screen.getByLabelText('aiEnrichSkill'), 'huggingface');
        expect(settingsApi.updateEnvSetting).toHaveBeenCalledTimes(1);
        expect(settingsApi.updateEnvSetting).toHaveBeenCalledWith('AI_ENRICHSKILL_BACKEND', 'huggingface');
        expect((screen.getByLabelText('aiEnrich') as HTMLSelectElement).value).toBe('ollama');
    });

    it('saves aiFormFiller independently from the enrichment selectors', async () => {
        await renderSelectors();
        await userEvent.selectOptions(screen.getByLabelText('aiFormFiller'), 'openrouter');
        expect(settingsApi.updateEnvSetting).toHaveBeenCalledTimes(1);
        expect(settingsApi.updateEnvSetting).toHaveBeenCalledWith('AI_FORM_PROVIDER', 'openrouter');
        expect((screen.getByLabelText('aiEnrich') as HTMLSelectElement).value).toBe('ollama');
        expect((screen.getByLabelText('aiEnrichSkill') as HTMLSelectElement).value).toBe('ollama');
    });

    it('rolls back and reports an error when the switch fails', async () => {
        vi.mocked(settingsApi.updateEnvSetting).mockRejectedValueOnce(new Error('Save Error'));
        await renderSelectors();
        await userEvent.selectOptions(screen.getByLabelText('aiEnrichSkill'), 'huggingface');
        await waitFor(() => expect(screen.getByTestId('message-container')).toHaveTextContent('Failed to switch AI_ENRICHSKILL_BACKEND'));
        expect((screen.getByLabelText('aiEnrichSkill') as HTMLSelectElement).value).toBe('ollama');
    });
});
