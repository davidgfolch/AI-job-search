import { screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import Settings from '../Settings';
import { settingsApi } from '../api/SettingsApi';
import { renderWithClient, setupSettingsMocks } from './Settings.mocks';
import { CLOUD_OPTIONS, MODEL_OPTIONS } from '../llmProviders';

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

    const card = (label: string) => screen.getByLabelText(label).closest('.llm-provider-group') as HTMLElement;

    it('renders all three provider selectors with their own options and current values', async () => {
        await renderSelectors();
        const enrich = screen.getByLabelText('aiEnrich') as HTMLSelectElement;
        const skill = screen.getByLabelText('aiEnrichSkill') as HTMLSelectElement;
        const formFiller = screen.getByLabelText('aiFormFiller') as HTMLSelectElement;
        expect([enrich.value, skill.value, formFiller.value]).toEqual(['ollama', 'ollama', 'local']);
        const cloud = CLOUD_OPTIONS.map(o => o.value);
        expect([...enrich.options].map(o => o.value)).toEqual(['ollama', ...cloud]);
        expect([...skill.options].map(o => o.value)).toEqual(['ollama', 'huggingface', ...cloud]);
        expect([...formFiller.options].map(o => o.value)).toEqual(['local', ...cloud, 'openai']);
    });

    it.each([
        ['aiEnrich', 'AI_ENRICH_OLLAMA_MODEL', 'ollama'],
        ['aiEnrichSkill', 'AI_ENRICHSKILL_OLLAMA_MODEL', 'ollama'],
        ['aiFormFiller', 'AI_FORM_HF_MODEL', 'local'],
    ])('shows the model selector bound to %s (%s)', async (label, key, provider) => {
        await renderSelectors();
        const model = within(card(label)).getByLabelText(key) as HTMLSelectElement;
        expect(model.value).toBeTruthy();
        expect([...model.options].map(o => o.value)).toContain(MODEL_OPTIONS[provider][0]);
    });

    it('shows the API keys in one masked block with setup links', async () => {
        await renderSelectors();
        const section = screen.getByText('LLM Providers').closest('.llm-providers-section') as HTMLElement;
        const keys = ['OPENROUTER_API_KEY', 'GEMINI_API_KEY', 'GROQ_API_KEY', 'CEREBRAS_API_KEY', 'HF_TOKEN', 'OPENAI_API_KEY'];
        for (const key of keys) {
            const input = document.getElementById(`env-${key}`) as HTMLInputElement;
            expect(section).toContainElement(input);
            expect(input).toHaveAttribute('type', 'password');
            expect(document.querySelectorAll(`#env-${key}`)).toHaveLength(1);
        }
        const geminiField = document.getElementById('env-GEMINI_API_KEY')!.closest('.env-item') as HTMLElement;
        expect(within(geminiField).getByRole('link', { name: /get a key/i })).toHaveAttribute('href', 'https://aistudio.google.com/apikey');
        expect(card('aiFormFiller')).not.toContainElement(document.getElementById('env-OPENAI_API_KEY')!);
    });

    it.each([
        ['aiEnrich', 'AI_ENRICH_LLM_BACKEND', 'openrouter', 'AI_ENRICH_OPENROUTER_MODEL'],
        ['aiEnrichSkill', 'AI_ENRICHSKILL_BACKEND', 'huggingface', 'AI_ENRICHSKILL_HF_MODEL_ID'],
        ['aiFormFiller', 'AI_FORM_PROVIDER', 'openai', 'AI_FORM_OPENAI_MODEL'],
    ])('saves %s provider independently and retargets its model key', async (label, providerKey, provider, modelKey) => {
        await renderSelectors();
        await userEvent.selectOptions(screen.getByLabelText(label), provider);
        expect(settingsApi.updateEnvSetting).toHaveBeenCalledWith(providerKey, provider);
        expect(settingsApi.updateEnvSettingsBulk).not.toHaveBeenCalled();
        expect(within(card(label)).getByLabelText(modelKey)).toBeInTheDocument();
    });

    it('saves a model change immediately under the module key', async () => {
        await renderSelectors();
        const model = within(card('aiEnrich')).getByLabelText('AI_ENRICH_OLLAMA_MODEL') as HTMLSelectElement;
        await userEvent.selectOptions(model, 'ollama/phi3.5:3b');
        expect(settingsApi.updateEnvSetting).toHaveBeenCalledWith('AI_ENRICH_OLLAMA_MODEL', 'ollama/phi3.5:3b');
        expect(settingsApi.updateEnvSettingsBulk).not.toHaveBeenCalled();
    });

    it('filters the model options with the search input', async () => {
        await renderSelectors();
        await userEvent.type(within(card('aiEnrich')).getByLabelText('Search models'), 'phi3.5');
        const model = within(card('aiEnrich')).getByLabelText('AI_ENRICH_OLLAMA_MODEL') as HTMLSelectElement;
        expect([...model.options].map(o => o.value)).toEqual(['ollama/phi3.5:3b']);
    });

    it('forces a live reload when refresh is clicked', async () => {
        await renderSelectors();
        await userEvent.selectOptions(screen.getByLabelText('aiEnrich'), 'gemini');
        await userEvent.click(within(card('aiEnrich')).getByRole('button', { name: /refresh models/i }));
        await waitFor(() => expect(settingsApi.getProviderModels).toHaveBeenCalledWith('gemini', true));
    });

    it('rolls back and reports an error when the switch fails', async () => {
        vi.mocked(settingsApi.updateEnvSetting).mockRejectedValueOnce(new Error('Save Error'));
        await renderSelectors();
        await userEvent.selectOptions(screen.getByLabelText('aiEnrichSkill'), 'huggingface');
        await waitFor(() => expect(screen.getByTestId('message-container')).toHaveTextContent('Failed to switch AI_ENRICHSKILL_BACKEND'));
        expect((screen.getByLabelText('aiEnrichSkill') as HTMLSelectElement).value).toBe('ollama');
    });
});
