import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { downloadFile } from '../fileUtils';

describe('fileUtils', () => {
    describe('downloadFile', () => {
        let createObjectURLMock: ReturnType<typeof vi.fn>;
        let revokeObjectURLMock: ReturnType<typeof vi.fn>;
        let clickMock: ReturnType<typeof vi.fn>;
        let appendChildMock: ReturnType<typeof vi.fn>;
        let removeChildMock: ReturnType<typeof vi.fn>;
        let createElementMock: ReturnType<typeof vi.fn>;
        let linkMock: { href: string; download: string; click: ReturnType<typeof vi.fn> };

        beforeEach(() => {
            createObjectURLMock = vi.fn();
            revokeObjectURLMock = vi.fn();
            clickMock = vi.fn();
            appendChildMock = vi.fn();
            removeChildMock = vi.fn();
            
            linkMock = {
                href: '',
                download: '',
                click: clickMock
            };

            createElementMock = vi.fn().mockReturnValue(linkMock);

            vi.stubGlobal('URL', {
                createObjectURL: createObjectURLMock,
                revokeObjectURL: revokeObjectURLMock
            });
            
            vi.stubGlobal('document', {
                createElement: createElementMock,
                body: {
                    appendChild: appendChildMock,
                    removeChild: removeChildMock
                }
            });
        });

        afterEach(() => {
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

        describe.each([
            {
                name: 'JSON file',
                content: '{"key": "value"}',
                filename: 'data.json',
                mimeType: 'application/json'
            },
            {
                name: 'plain text file',
                content: 'Plain text content',
                filename: 'notes.txt',
                mimeType: 'text/plain'
            },
            {
                name: 'CSV file',
                content: 'name,age\nJohn,30',
                filename: 'users.csv',
                mimeType: 'text/csv'
            },
            {
                name: 'empty file',
                content: '',
                filename: 'empty.txt',
                mimeType: 'text/plain'
            }
        ])('$name', ({ content, filename, mimeType }) => {
            it('should create a blob and trigger download', () => {
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

        describe('edge cases', () => {
            it.each([
                {
                    name: 'special characters in filename',
                    content: 'test',
                    filename: 'file with spaces & symbols.txt',
                    mimeType: 'text/plain'
                },
                {
                    name: 'very long content',
                    content: 'A'.repeat(10000),
                    filename: 'large.txt',
                    mimeType: 'text/plain'
                },
                {
                    name: 'unicode content',
                    content: '测试内容 🚀',
                    filename: 'unicode.txt',
                    mimeType: 'text/plain'
                }
            ])('handles $name', ({ content, filename, mimeType }) => {
                expect(() => downloadFile(content, filename, mimeType)).not.toThrow();
            });
        });
    });
});