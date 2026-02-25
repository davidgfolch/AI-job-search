import { useState, useEffect, useCallback, useRef } from 'react';
import { settingsApi } from '../../settings/api/SettingsApi';

export function useDefaultComment() {
  const [comment, setComment] = useState<string>('');
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const isMounted = useRef(true);

  useEffect(() => {
    isMounted.current = true;
    const loadDefaultComment = async () => {
      if (isMounted.current) {
        try {
          const envSettings = await settingsApi.getEnvSettings();
          if (isMounted.current && envSettings.APPLY_MODAL_DEFAULT_TEXT) {
            setComment(envSettings.APPLY_MODAL_DEFAULT_TEXT);
          }
        } catch (e) {
            console.error(e);
        } finally {
          setIsLoading(false);
        }
      }
    };

    loadDefaultComment();
    return () => { isMounted.current = false; };
  }, []);

  const saveComment = useCallback(async (newText: string) => {
    if (!newText.trim()) return;
    setComment(newText);
    await settingsApi.updateEnvSetting('APPLY_MODAL_DEFAULT_TEXT', newText);
  }, []);

  return { 
    comment, 
    saveComment, 
    isLoading 
  };
}