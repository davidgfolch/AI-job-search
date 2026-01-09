
import { tokenizeSql, SQL_FUNCTIONS } from '../sqlEditorUtils';

describe('sqlEditorUtils', () => {
    describe('tokenizeSql', () => {
        const mockSchema = {
            'users': ['id', 'name', 'email'],
            'jobs': ['id', 'title', 'salary']
        };
        const mockKeywords = ['select', 'from', 'where'];

        it('should tokenize keywords correctly', () => {
            const tokens = tokenizeSql('SELECT * FROM users', mockKeywords, mockSchema);
            expect(tokens.find(t => t.text === 'SELECT')?.type).toBe('keyword');
            expect(tokens.find(t => t.text === 'FROM')?.type).toBe('keyword');
        });

        it('should tokenize tables correctly', () => {
            const tokens = tokenizeSql('users', mockKeywords, mockSchema);
            expect(tokens[0].type).toBe('table');
        });

        it('should tokenize columns correctly', () => {
            const tokens = tokenizeSql('salary', mockKeywords, mockSchema);
            expect(tokens[0].type).toBe('column');
        });

        it('should tokenize functions correctly', () => {
            const tokens = tokenizeSql('COUNT(*)', mockKeywords, mockSchema);
            expect(tokens.find(t => t.text.toLowerCase() === 'count')?.type).toBe('function');
        });

        it('should tokenize strings correctly', () => {
            const tokens = tokenizeSql("'hello'", mockKeywords, mockSchema);
            expect(tokens[0].type).toBe('string');
        });

        it('should tokenize numbers correctly', () => {
            const tokens = tokenizeSql("123", mockKeywords, mockSchema);
            expect(tokens[0].type).toBe('number');
        });
    });

    describe('tokenizeSql edge cases', () => {
        it('should return empty array for empty input', () => {
            expect(tokenizeSql('', [], {})).toEqual([]);
        });

        it('should tokenize double quoted strings', () => {
             const tokens = tokenizeSql('"hello"', [], {});
             expect(tokens[0].type).toBe('string');
        });
    });

    describe('getCaretCoordinates', () => {
        it('should return coordinates', () => {
             // Mock getComputedStyle
             const mockStyle = {
                 getPropertyValue: vi.fn(),
                 length: 0,
                 [Symbol.iterator]: function* () { yield* []; }
             };
             window.getComputedStyle = vi.fn().mockReturnValue(mockStyle);
             
             // Mock document.createElement
             const mockDiv = {
                 style: { setProperty: vi.fn() },
                 appendChild: vi.fn(),
                 textContent: ''
             };
             const mockSpan = {
                 textContent: '',
                 offsetLeft: 10,
                 offsetTop: 20
             };
             
             // Simple mock of createElement to return functional mocks
             vi.spyOn(document, 'createElement').mockImplementation((tag) => {
                 if (tag === 'div') return mockDiv as any;
                 if (tag === 'span') return mockSpan as any;
                 return document.createElement(tag);
             });
             
             // Mock document.body.appendChild/removeChild
             vi.spyOn(document.body, 'appendChild').mockImplementation(() => mockDiv as any);
             vi.spyOn(document.body, 'removeChild').mockImplementation(() => mockDiv as any);

             const mockTextarea = {
                 value: 'SELECT',
                 offsetLeft: 5,
                 offsetTop: 5
             } as HTMLTextAreaElement;

             import('../sqlEditorUtils').then(({ getCaretCoordinates }) => {
                 const coords = getCaretCoordinates(mockTextarea, 2);
                 expect(coords).toEqual({ left: 15, top: 25 }); // 5+10, 5+20
             });
        });
    });
});
