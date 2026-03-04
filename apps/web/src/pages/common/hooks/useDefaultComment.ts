import { useState, useEffect, useCallback, useRef } from 'react';
import { settingsApi } from '../../settings/api/SettingsApi';
import { useEnvSettings } from './useEnvSettings';

export function useDefaultComment() {
  const [comment, setComment] = useState<string>('');
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const isMounted = useRef(true);
  const { data: envSettings } = useEnvSettings();

  useEffect(() => {
    isMounted.current = true;
    if (envSettings) {
      try {
        if (isMounted.current && envSettings.UI_APPLY_MODAL_DEFAULT_TEXT) {
          setComment(envSettings.UI_APPLY_MODAL_DEFAULT_TEXT);
        }
      } catch (e) {
          console.error(e);
      } finally {
        setIsLoading(false);
      }
    }
    return () => { isMounted.current = false; };
  }, [envSettings]);

  const saveComment = useCallback(async (newText: string) => {
    if (!newText.trim()) return;
    setComment(newText);
    await settingsApi.updateEnvSetting('UI_APPLY_MODAL_DEFAULT_TEXT', newText);
  }, []);

  return { 
    comment, 
    saveComment, 
    isLoading 
  };
}