import { useState, useCallback } from "react";

export interface ConfirmationModal {
  isOpen: boolean;
  message: string;
  confirm: (message: string, onConfirm: () => void) => void;
  close: () => void;
  handleConfirm: () => void;
}

export function useConfirmationModal(): ConfirmationModal {
  const [modalState, setModalState] = useState<{
    isOpen: boolean;
    message: string;
    onConfirm: () => void;
  }>({ isOpen: false, message: "", onConfirm: () => {} });

  const confirm = useCallback((message: string, onConfirm: () => void) => {
    setModalState({ isOpen: true, message, onConfirm });
  }, []);

  const close = useCallback(() => {
    setModalState((prev) => ({ ...prev, isOpen: false }));
  }, []);

  const handleConfirm = useCallback(() => {
    modalState.onConfirm();
    close();
  }, [modalState, close]);

  return {
    isOpen: modalState.isOpen,
    message: modalState.message,
    confirm,
    close,
    handleConfirm,
  };
}
