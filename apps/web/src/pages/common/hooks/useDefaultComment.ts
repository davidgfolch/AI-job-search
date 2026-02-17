import { useState, useEffect, useCallback, useRef } from 'react';
import { persistenceApi } from '../api/CommonPersistenceApi';

export function useDefaultComment() {
  const [comment, setComment] = useState<string>('');
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const isMounted = useRef(true);

  useEffect(() => {
    isMounted.current = true;
    const loadDefaultComment = async () => {
      if (isMounted.current) {
        try {
          const stored = await persistenceApi.getValue<string>('default_comment_text');
          if (isMounted.current && stored) {
            setComment(stored);
          }
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
      await persistenceApi.setValue('default_comment_text', newText);
  }, [comment]);

  return { 
    comment, 
    saveComment, 
    isLoading 
  };
}