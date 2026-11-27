import { useState, type Dispatch, type SetStateAction } from 'react';
import { FormField } from '../common/components/core/FormField';
import { useProviderModels } from '../common/hooks/useProviderModels';
import { API_KEY_FIELDS, LLM_PROVIDERS, MODEL_OPTIONS, PROVIDER_KEY_LINKS, type LlmProviderGroup } from './llmProviders';

type EnvSettings = Record<string, string>;
type Props = { envSettings: EnvSettings; setEnvSettings: Dispatch<SetStateAction<EnvSettings>>; onSave: (key: string, value: string) => Promise<void> };

export default function LlmProviders({ envSettings, setEnvSettings, onSave }: Props) {
    return (
        <div className="settings-section llm-providers-section">
            <h2>LLM Providers</h2>
            <div className="llm-providers-flex">
                {LLM_PROVIDERS.map(group => <ProviderCard key={group.key} group={group} envSettings={envSettings} onSave={onSave} />)}
            </div>
            <div className="llm-provider-related">
                <h3 className="llm-subtitle">API keys</h3>
                <div className="env-items">
                    {API_KEY_FIELDS.map(key => <ApiKeyField key={key} envKey={key} envSettings={envSettings} setEnvSettings={setEnvSettings} />)}
                </div>
            </div>
            <p className="llm-providers-hint">Selectors apply on the next worker cycle — no Save click needed. API keys are saved with the Settings Save button.</p>
        </div>
    );
}

type CardProps = { group: LlmProviderGroup; envSettings: EnvSettings; onSave: Props['onSave'] };

function ProviderCard({ group, envSettings, onSave }: CardProps) {
    const [search, setSearch] = useState('');
    const provider = envSettings[group.key] || group.options[0].value;
    const modelKey = group.modelKeys[provider] || '';
    const { data, isFetching, refresh } = useProviderModels(provider);
    const liveModels = data?.models ?? [];
    const models = liveModels.length ? liveModels : (MODEL_OPTIONS[provider] ?? []).map(id => ({ id, label: id, free: false }));
    const current = envSettings[modelKey] || '';
    const matches = models.filter(m => `${m.id} ${m.label}`.toLowerCase().includes(search.toLowerCase()));
    const keepCurrent = current && !search && !matches.some(m => m.id === current);
    const value = keepCurrent ? current : (matches[0]?.id || '');
    const free = matches.filter(m => m.free);
    const other = matches.filter(m => !m.free);
    const showFreeGroups = liveModels.length > 0 && provider !== 'ollama';

    return (
        <div className="llm-provider-group">
            <FormField id={`llm-provider-${group.key}`} label={<span className="env-key-label">{group.label}</span>} className="env-item inline-item">
                <select id={`llm-provider-${group.key}`} name={group.key} className="env-input compact-input" value={provider} onChange={e => { setSearch(''); void onSave(group.key, e.target.value); }}>
                    {group.options.map(option => <option key={option.value} value={option.value}>{option.label}</option>)}
                </select>
            </FormField>
            <FormField id={`llm-model-search-${group.key}`} label={<span className="env-key-label">Search models</span>} className="env-item inline-item">
                <input id={`llm-model-search-${group.key}`} type="text" className="env-input compact-input" placeholder="Search models…" value={search} onChange={e => setSearch(e.target.value)} />
            </FormField>
            <FormField id={`llm-model-${group.key}`} label={<span className="env-key-label">{modelKey}</span>} className="env-item inline-item">
                <select id={`llm-model-${group.key}`} name={modelKey} className="env-input compact-input" value={value} onChange={e => void onSave(modelKey, e.target.value)}>
                    {keepCurrent && <option value={current}>{current}</option>}
                    {showFreeGroups ? <>
                        {free.length > 0 && <optgroup label="Free models">{free.map(m => <option key={m.id} value={m.id}>{m.label}</option>)}</optgroup>}
                        <optgroup label="All models">{other.map(m => <option key={m.id} value={m.id}>{m.label}</option>)}</optgroup>
                    </> : <optgroup label={provider === 'ollama' ? 'Installed locally' : 'All models'}>{matches.map(m => <option key={m.id} value={m.id}>{m.label}</option>)}</optgroup>}
                </select>
            </FormField>
            <button type="button" className="llm-refresh-btn" disabled={isFetching} onClick={() => void refresh()}>↻ Refresh models</button>
            {data?.source === 'fallback' && <small className="llm-fallback-note">Live list unavailable — showing suggested models.</small>}
        </div>
    );
}

type KeyProps = { envKey: string; envSettings: EnvSettings; setEnvSettings: Props['setEnvSettings'] };

function ApiKeyField({ envKey, envSettings, setEnvSettings }: KeyProps) {
    const link = PROVIDER_KEY_LINKS[envKey];
    return (
        <FormField id={`env-${envKey}`} label={<span className="env-key-label">{envKey}{link && <> <a className="llm-key-link" href={link.url} target="_blank" rel="noopener noreferrer">{link.label} ↗</a></>}</span>} className="env-item inline-item">
            <input id={`env-${envKey}`} name={envKey} className="env-input compact-input" type="password" value={envSettings[envKey] || ''} onChange={e => setEnvSettings({ ...envSettings, [envKey]: e.target.value })} />
        </FormField>
    );
}
