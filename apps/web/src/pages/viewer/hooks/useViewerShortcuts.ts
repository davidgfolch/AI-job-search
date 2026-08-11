import { useCallback } from 'react';
import type { RefObject } from 'react';
import type { Job } from '../api/ViewerApi';
import type { ShortcutAction } from '../shortcutsConfig';

export interface ViewerShortcutActions {
    ignoreJob: () => void;
    appliedJob: () => void;
    nextJob: () => void;
    previousJob: () => void;
}

export const useViewerShortcuts = (actions: ViewerShortcutActions, selectedJob: Job | null, jobListRef: RefObject<HTMLDivElement | null>, detailScrollRef: RefObject<HTMLDivElement | null>) => {
    return useCallback((action: ShortcutAction) => {
        switch (action) {
            case 'ignore': actions.ignoreJob(); break;
            case 'apply': actions.appliedJob(); break;
            case 'next': actions.nextJob(); break;
            case 'previous': actions.previousJob(); break;
            case 'openUrl': if (selectedJob?.url) window.open(selectedJob.url, '_blank'); break;
            case 'listFocus': jobListRef.current?.focus({ preventScroll: true }); break;
            case 'detailFocus': detailScrollRef.current?.focus({ preventScroll: true }); break;
        }
    }, [actions, selectedJob, jobListRef, detailScrollRef]);
};
