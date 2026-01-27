import { describe, it, expect, vi, afterEach } from 'vitest';
import { downloadFile } from '../fileUtils';

describe('fileUtils', () => {
    describe('downloadFile', () => {
        const createObjectURLMock = vi.fn();
        const revokeObjectURLMock = vi.fn();
        const clickMock = vi.fn();
        const appendChildMock = vi.fn();
        const removeChildMock = vi.fn();

        vi.stubGlobal('URL', {
            createObjectURL: createObjectURLMock,
            revokeObjectURL: revokeObjectURLMock
        });
        
        // Mock document.createElement
        const linkMock = {
            href: '',
            download: '',
            click: clickMock
        } as unknown as HTMLAnchorElement;

        const createElementMock = vi.fn().mockReturnValue(linkMock);

        vi.stubGlobal('document', {
            createElement: createElementMock,
            body: {
                appendChild: appendChildMock,
                removeChild: removeChildMock
            }
        });

        afterEach(() => {
            vi.clearAllMocks();
            vi.unstubAllGlobals();
        });

        it('should create a blob and trigger download', () => {
            const content = '# Test';
            const filename = 'test.md';
            const mimeType = 'text/markdown';

            downloadFile(content, filename, mimeType);

            expect(createObjectURLMock).toHaveBeenCalled();
            expect(createElementMock).toHaveBeenCalledWith('a');
            expect(linkMock.download).toBe(filename);
            expect(appendChildMock).toHaveBeenCalled();
            expect(clickMock).toHaveBeenCalled();
            expect(removeChildMock).toHaveBeenCalled();
            expect(revokeObjectURLMock).toHaveBeenCalled();
        });
    });
});
