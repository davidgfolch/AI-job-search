import { useState, useEffect, useCallback } from 'react';
import { persistenceApi } from '../api/CommonPersistenceApi';

export function useDefaultComment() {
  const [comment, setComment] = useState<string>('');
  const [isLoading, setIsLoading] = useState<boolean>(true);

  useEffect(() => {
    const loadDefaultComment = async () => {
      try {
        const stored = await persistenceApi.getValue<string>('default_comment_text');
        setComment(stored || '- applied by 45k');
      } catch (error) {
        console.error('Failed to load default comment:', error);
        setComment('- applied by 45k');
      } finally {
        setIsLoading(false);
      }
    };

    loadDefaultComment();
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