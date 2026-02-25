import { useEffect, useState, useRef } from 'react';
import Editor from 'react-simple-code-editor';
import Prism from 'prismjs';
import 'prismjs/components/prism-json';
import 'prismjs/themes/prism-tomorrow.css';
import PageHeader from '../common/components/PageHeader';
import { settingsApi } from './api/SettingsApi';
import { groupSettingsByKey, getSubgroupTitle } from './utils/SettingsUtils';
import MessageContainer from '../common/components/core/MessageContainer';
import { FormField } from '../common/components/core/FormField';
import './Settings.css';

export default function Settings() {
    const [envSettings, setEnvSettings] = useState<Record<string, string>>({});
    const [scrapperState, setScrapperState] = useState<string>('');
    const [message, setMessage] = useState<{ text: string; type: 'success' | 'error' } | null>(null);
    const [isLoading, setIsLoading] = useState(true);

    const effectRan = useRef(false);

    useEffect(() => {
        if (!effectRan.current) {
            loadData();
            effectRan.current = true;
        }
    }, []);

    const loadScrapperState = async () => {
        const scrapper = await settingsApi.getScrapperState();
        setScrapperState(JSON.stringify(scrapper, null, 2));
    };

    const loadData = async () => {
        try {
            setIsLoading(true);
            const [env] = await Promise.all([
                settingsApi.getEnvSettings(),
                loadScrapperState()
            ]);
            setEnvSettings(env);
        } catch (error) {
            setMessage({ text: 'Failed to load settings', type: 'error' });
        } finally {
            setIsLoading(false);
        }
    };

    const handleScrapperStateRefresh = async () => {
        try {
            await loadScrapperState();
            setMessage({ text: 'Scrapper state refreshed', type: 'success' });
            setTimeout(() => setMessage(null), 3000);
        } catch (error) {
            setMessage({ text: 'Failed to refresh scrapper state', type: 'error' });
        }
    };

    const handleEnvUpdateBulk = async (groupName: string, keys: string[]) => {
        try {
            const updates: Record<string, string> = {};
            keys.forEach(k => updates[k] = envSettings[k]);
            const updated = await settingsApi.updateEnvSettingsBulk(updates);
            setEnvSettings(updated);
            setMessage({ text: `${groupName} settings saved successfully`, type: 'success' });
            
            setTimeout(() => setMessage(null), 3000);
        } catch (error) {
            setMessage({ text: `Failed to update ${groupName} settings`, type: 'error' });
        }
    };

    const handleScrapperStateSave = async () => {
        try {
            const parsed = JSON.parse(scrapperState);
            const updated = await settingsApi.updateScrapperState(parsed);
            setScrapperState(JSON.stringify(updated, null, 2));
            setMessage({ text: 'Scrapper state saved successfully', type: 'success' });
            
            setTimeout(() => setMessage(null), 3000);
        } catch (error) {
            setMessage({ text: 'Invalid JSON format for scrapper state', type: 'error' });
        }
    };

    const groupedSettings = groupSettingsByKey(envSettings);

    if (isLoading) {
        return <div className="settings-loading">Loading settings...</div>;
    }

    return (
        <>
            <PageHeader title="Settings" />
            <main className="settings-main">
                <MessageContainer message={message} error={null} onDismissMessage={() => setMessage(null)} />
                
                <div className="settings-container">
                    <div className="settings-section env-variables-section">
                        <div className="env-section-header">
                            <h2>Environment Variables (.env)</h2>
                            <button
                                className="env-save-btn"
                                onClick={() => Object.entries(groupedSettings).forEach(([g, k]) => handleEnvUpdateBulk(g, k))}
                            >
                                Save
                            </button>
                        </div>
                        <div className="env-groups-container">
                            {Object.entries(groupedSettings).map(([groupName, keys]) => {
                                // Group keys by internal prefix
                                const subGroups = keys.reduce((acc, key) => {
                                    const sub = getSubgroupTitle(key);
                                    if (!acc[sub]) acc[sub] = [];
                                    acc[sub].push(key);
                                    return acc;
                                }, {} as Record<string, string[]>);

                                return (
                                    <div key={groupName} className="env-group">
                                        <div className="env-group-header">
                                            <h3>{groupName}</h3>
                                        </div>
                                        <div className="env-items-scrollable">
                                            {Object.entries(subGroups).sort().map(([subTitle, subKeys]) => {
                                                if (subKeys.length === 1) {
                                                    const key = subKeys[0];
                                                    return (
                                                        <FormField key={key} id={`env-${key}`} label={<span className="env-key-label">{key}</span>} className="env-item inline-item">
                                                            <input
                                                                id={`env-${key}`}
                                                                name={key}
                                                                className="env-input compact-input"
                                                                type={key.includes('PWD') || key.includes('PASSWORD') || key.includes('EMAIL') ? "password" : "text"}
                                                                value={envSettings[key] || ''}
                                                                onChange={(e) => setEnvSettings({ ...envSettings, [key]: e.target.value })}
                                                            />
                                                        </FormField>
                                                    );
                                                }
                                                return (
                                                    <div key={subTitle} className="env-subgroup">
                                                        <h4 className="env-subgroup-title">{subTitle}</h4>
                                                        <div className="env-items">
                                                            {subKeys.map(key => (
                                                                <FormField key={key} id={`env-${key}`} label={<span className="env-key-label">{key}</span>} className="env-item inline-item">
                                                                    <input
                                                                        id={`env-${key}`}
                                                                        name={key}
                                                                        className="env-input compact-input"
                                                                        type={key.includes('PWD') || key.includes('PASSWORD') || key.includes('EMAIL') ? "password" : "text"}
                                                                        value={envSettings[key] || ''}
                                                                        onChange={(e) => setEnvSettings({ ...envSettings, [key]: e.target.value })}
                                                                    />
                                                                </FormField>
                                                            ))}
                                                        </div>
                                                    </div>
                                                );
                                            })}
                                        </div>
                                    </div>
                                );
                            })}
                        </div>
                        <div className="env-section-footer">
                            <button
                                className="env-save-btn"
                                onClick={() => Object.entries(groupedSettings).forEach(([g, k]) => handleEnvUpdateBulk(g, k))}
                            >
                                Save
                            </button>
                        </div>
                    </div>

                    <div className="settings-section">
                        <h2>Scrapper State (scrapper_state.json)</h2>
                        <div className="scrapper-editor-wrapper">
                            <Editor
                                value={scrapperState}
                                onValueChange={code => setScrapperState(code)}
                                highlight={code => Prism.highlight(code, Prism.languages.json, 'json')}
                                padding={12}
                                className="scrapper-editor"
                            />
                        </div>
                        <div className="scrapper-actions">
                            <button className="scrapper-refresh-btn" onClick={handleScrapperStateRefresh}>↻ Refresh</button>
                            <button className="scrapper-save-btn" onClick={handleScrapperStateSave}>Save</button>
                        </div>
                    </div>
                </div>
            </main>
        </>
    );
}
