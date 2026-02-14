import { useState, useEffect, useCallback, useRef } from 'react';
import { persistenceApi } from '../api/CommonPersistenceApi';

export function useDefaultComment() {
  const [comment, setComment] = useState<string>('');
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const isMounted = useRef(true);

  useEffect(() => {
    isMounted.current = true;
    const loadDefaultComment = async () => {
      try {
        const stored = await persistenceApi.getValue<string>('default_comment_text');
        if (isMounted.current) {
          setComment(stored || '- applied by 45k');
        }
      } catch (error) {
        console.error('Failed to load default comment:', error);
        if (isMounted.current) {
          setComment('- applied by 45k');
        }
      } finally {
        if (isMounted.current) {
          setIsLoading(false);
        }
      }
    };

    loadDefaultComment();
    return () => { isMounted.current = false; };
  }, []);

  const saveComment = useCallback(async (newText: string) => {
    if (!newText.trim()) return;
    
    try {
      setComment(newText);
      await persistenceApi.setValue('default_comment_text', newText);
    } catch (error) {
      console.error('Failed to save default comment:', error);
      // Revert on error
      const previousComment = comment;
      setComment(previousComment);
    }
  }, [comment]);

  return { 
    comment, 
    saveComment, 
    isLoading 
  };
}