
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
});
