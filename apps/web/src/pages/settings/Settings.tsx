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

type SetStateAction<T> = React.Dispatch<React.SetStateAction<T>>;

export default function Settings() {
    const [envSettings, setEnvSettings] = useState<Record<string, string>>({});
    const [scrapperState, setScrapperState] = useState<string>('');
    const [message, setMessage] = useState<{ text: string; type: 'success' | 'error' } | null>(null);
    const [isLoading, setIsLoading] = useState(true);
    const effectRan = useRef(false);

    useEffect(() => { if (!effectRan.current) { loadData(); effectRan.current = true; } }, []);

    const loadScrapperState = async () => setScrapperState(JSON.stringify(await settingsApi.getScrapperState(), null, 2));

    const loadData = async () => {
        try {
            setIsLoading(true);
            const [env] = await Promise.all([settingsApi.getEnvSettings(), loadScrapperState()]);
            setEnvSettings(env);
        } catch { setMessage({ text: 'Failed to load settings', type: 'error' }); }
        finally { setIsLoading(false); }
    };

    const handleScrapperStateRefresh = async () => {
        try { await loadScrapperState(); setMessage({ text: 'Scrapper state refreshed', type: 'success' }); setTimeout(() => setMessage(null), 3000); }
        catch { setMessage({ text: 'Failed to refresh scrapper state', type: 'error' }); }
    };

    const handleEnvUpdateAll = async () => {
        try { const updated = await settingsApi.updateEnvSettingsBulk(envSettings); setEnvSettings(updated); setMessage({ text: `Settings saved successfully`, type: 'success' }); setTimeout(() => setMessage(null), 3000); }
        catch { setMessage({ text: `Failed to update settings`, type: 'error' }); }
    };

    const handleScrapperStateSave = async () => {
        try { const parsed = JSON.parse(scrapperState); const updated = await settingsApi.updateScrapperState(parsed); setScrapperState(JSON.stringify(updated, null, 2)); setMessage({ text: 'Scrapper state saved successfully', type: 'success' }); setTimeout(() => setMessage(null), 3000); }
        catch { setMessage({ text: 'Invalid JSON format for scrapper state', type: 'error' }); }
    };

    if (isLoading) return <div className="settings-loading">Loading settings...</div>;

    const groupedSettings = groupSettingsByKey(envSettings);
    const sortedGroupNames = Object.keys(groupedSettings).sort((a, b) => {
        const order = ['System & Base', 'UI Frontend', 'Scrapper', 'AI Enrichment', 'Other'];
        const getIdx = (k: string) => (i => i === -1 ? order.length : i)(order.indexOf(k));
        return getIdx(a) - getIdx(b);
    });
    const leftGroups = sortedGroupNames.filter(g => g === 'System & Base' || g === 'UI Frontend');
    const middleGroups = sortedGroupNames.filter(g => g === 'Scrapper');
    const rightGroups = sortedGroupNames.filter(g => g === 'AI Enrichment' || g === 'Other');

    return (
        <>
            <PageHeader title="Settings" />
            <main className="settings-main">
                <MessageContainer message={message} error={null} onDismissMessage={() => setMessage(null)} />
                <div className="settings-container">
                    <div className="settings-section env-variables-section">
                        <div className="env-section-header"><h2>Environment Variables (.env)</h2><button className="env-save-btn" onClick={handleEnvUpdateAll}>Save</button></div>
                        <div className="env-groups-container">
                            <div className="env-groups-column">{leftGroups.map(g => renderGroup(g, groupedSettings, envSettings, setEnvSettings, scrapperState, setScrapperState, handleScrapperStateRefresh, handleScrapperStateSave))}</div>
                            <div className="env-groups-column">{middleGroups.map(g => renderGroup(g, groupedSettings, envSettings, setEnvSettings, scrapperState, setScrapperState, handleScrapperStateRefresh, handleScrapperStateSave))}</div>
                            <div className="env-groups-column">{rightGroups.map(g => renderGroup(g, groupedSettings, envSettings, setEnvSettings, scrapperState, setScrapperState, handleScrapperStateRefresh, handleScrapperStateSave))}</div>
                        </div>
                        <div className="env-section-footer"><button className="env-save-btn" onClick={handleEnvUpdateAll}>Save</button></div>
                    </div>
                </div>
            </main>
        </>
    );
}

function renderGroup(groupName: string, groupedSettings: Record<string, string[]>, envSettings: Record<string, string>, setEnvSettings: SetStateAction<Record<string, string>>, scrapperState: string, setScrapperState: SetStateAction<string>, handleRefresh: () => void, handleSave: () => void) {
    if (!groupedSettings[groupName]) return null;
    const keys = groupedSettings[groupName];
    const subGroups = keys.reduce((acc, key) => { const sub = getSubgroupTitle(key); (acc[sub] ??= []).push(key); return acc; }, {} as Record<string, string[]>);
    return (
        <div key={groupName} className="env-group">
            <div className="env-group-header"><h3>{groupName}</h3></div>
            <div className="env-items-scrollable">
                {Object.entries(subGroups).sort(([a], [b]) => sortSubGroups(a, b, groupName)).map(([subTitle, subKeys]) => subKeys.length === 1 ? renderInlineItem(subKeys[0], envSettings, setEnvSettings) : renderSubgroup(subTitle, subKeys, envSettings, setEnvSettings))}
                {groupName === 'Scrapper' && renderScrapperEditor(scrapperState, setScrapperState, handleRefresh, handleSave)}
            </div>
        </div>
    );
}

function sortSubGroups(a: string, b: string, groupName: string) {
    if (groupName !== 'Scrapper') return a.localeCompare(b);
    const top = ['SCRAPPER_JOBS', 'SCRAPPER_RUN', 'SCRAPPER_USE'];
    const aIdx = top.findIndex(t => a.startsWith(t)), bIdx = top.findIndex(t => b.startsWith(t));
    if (aIdx !== -1 && bIdx !== -1 && aIdx !== bIdx) return aIdx - bIdx;
    if (aIdx !== -1 && bIdx === -1) return -1;
    if (bIdx !== -1 && aIdx === -1) return 1;
    return a.localeCompare(b);
}

function renderInlineItem(key: string, envSettings: Record<string, string>, setEnvSettings: SetStateAction<Record<string, string>>) {
    const isPassword = key.includes('PWD') || key.includes('PASSWORD') || key.includes('EMAIL');
    return (<FormField key={key} id={`env-${key}`} label={<span className="env-key-label">{key}</span>} className="env-item inline-item"><input id={`env-${key}`} name={key} className="env-input compact-input" type={isPassword ? "password" : "text"} value={envSettings[key] || ''} onChange={(e) => setEnvSettings({ ...envSettings, [key]: e.target.value })} /></FormField>);
}

function renderSubgroup(subTitle: string, subKeys: string[], envSettings: Record<string, string>, setEnvSettings: SetStateAction<Record<string, string>>) {
    return (<div key={subTitle} className="env-subgroup"><h4 className="env-subgroup-title">{subTitle}</h4><div className="env-items">{subKeys.map(key => renderInlineItem(key, envSettings, setEnvSettings))}</div></div>);
}

function renderScrapperEditor(scrapperState: string, setScrapperState: SetStateAction<string>, handleRefresh: () => void, handleSave: () => void) {
    return (<div className="env-subgroup"><h4 className="env-subgroup-title">scrapper_state.json</h4><div className="scrapper-editor-wrapper"><Editor value={scrapperState} onValueChange={code => setScrapperState(code)} highlight={code => Prism.highlight(code, Prism.languages.json, 'json')} padding={12} className="scrapper-editor" /></div><div className="scrapper-actions"><button className="scrapper-refresh-btn" onClick={handleRefresh}>↻ Refresh</button><button className="scrapper-save-btn" onClick={handleSave}>Save</button></div></div>);
}
