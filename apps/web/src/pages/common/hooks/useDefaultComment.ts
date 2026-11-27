import { useState, useCallback } from 'react';
import { settingsApi } from '../../settings/api/SettingsApi';
import { useEnvSettings } from './useEnvSettings';

export function useDefaultComment() {
  const { data: envSettings } = useEnvSettings();
  const envComment = envSettings?.UI_APPLY_MODAL_DEFAULT_TEXT ?? '';
  const [commentState, setCommentState] = useState({ envComment, override: null as string | null });
  if (commentState.envComment !== envComment) {
    setCommentState({ envComment, override: null });
  }

  const saveComment = useCallback(async (newText: string) => {
    if (!newText.trim()) return;
    setCommentState(prev => ({ ...prev, override: newText }));
    await settingsApi.updateEnvSetting('UI_APPLY_MODAL_DEFAULT_TEXT', newText);
  }, []);

  return {
    comment: commentState.override ?? commentState.envComment,
    saveComment,
    isLoading: !envSettings
  };
}
