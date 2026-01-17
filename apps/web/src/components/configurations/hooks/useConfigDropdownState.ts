import { useState, useCallback } from 'react';

export const useConfigDropdownState = (savedConfigName: string) => {
  const [configName, setConfigName] = useState('');
  const [isOpen, setIsOpen] = useState(false);

  const handleChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    setConfigName(e.target.value);
    if (!isOpen) setIsOpen(true);
  }, [isOpen]);

  const handleFocus = useCallback(() => {
    if (savedConfigName && configName === savedConfigName) {
      setConfigName('');
    }
    setIsOpen(true);
  }, [savedConfigName, configName]);

  const handleBlur = useCallback(() => {
    setTimeout(() => {
      if (!configName && savedConfigName) {
        setConfigName(savedConfigName);
      }
      setIsOpen(false);
    }, 200);
  }, [configName, savedConfigName]);

  return {
    configName,
    setConfigName,
    isOpen,
    setIsOpen,
    handleChange,
    handleFocus,
    handleBlur,
  };
};
