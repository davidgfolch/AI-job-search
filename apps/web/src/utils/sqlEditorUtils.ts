
export interface Suggestion {
    text: string;
    type: 'table' | 'column' | 'keyword';
}

// Helper to get caret coordinates
export const getCaretCoordinates = (element: HTMLTextAreaElement, position: number) => {
    const div = document.createElement('div');
    const style = getComputedStyle(element);
    for (const prop of Array.from(style)) {
            div.style.setProperty(prop, style.getPropertyValue(prop));
    }
    div.style.position = 'absolute';
    div.style.visibility = 'hidden';
    div.style.whiteSpace = 'pre-wrap';
    div.textContent = element.value.substring(0, position);
    const span = document.createElement('span');
    span.textContent = element.value.substring(position) || '.';
    div.appendChild(span);
    document.body.appendChild(div);
    const { offsetLeft: spanLeft, offsetTop: spanTop } = span;
    document.body.removeChild(div);
    return {
        left: spanLeft + element.offsetLeft, // Approximation
        top: spanTop + element.offsetTop
    };
};

export const SQL_FUNCTIONS = [
    'count', 'sum', 'avg', 'min', 'max', 'date', 'date_sub', 'curdate', 
    'now', 'concat', 'coalesce', 'if', 'length', 'lower', 'upper', 'cast'
];

interface Token {
    text: string;
    type: 'string' | 'number' | 'function' | 'keyword' | 'table' | 'column' | 'default';
}

// Tokenizer and syntax highlighter logic
export const tokenizeSql = (
    text: string, 
    keywords: string[], 
    schema: Record<string, string[]>
): Token[] => {
    if (!text) return [];

    // Regex to separate strings (single/double quoted), numbers, words, and operators
    const regex = /('[^']*'|"[^"]*"|\d+|[a-zA-Z0-9_]+|[(),=<>!*])/g;
    const parts = text.split(regex);
    
    return parts.filter(part => part).map(part => {
        const lowerPart = part.toLowerCase();
        let type: Token['type'] = 'default';

        if (part.startsWith("'") || part.startsWith('"')) {
            type = 'string';
        } else if (!isNaN(Number(part))) {
            type = 'number';
        } else if (SQL_FUNCTIONS.includes(lowerPart)) {
            type = 'function';
        } else if (keywords.map(k => k.toLowerCase()).includes(lowerPart)) {
            type = 'keyword';
        } else if (Object.keys(schema).includes(part)) {
            type = 'table';
        } else {
             // Check if it's a known column in any table (simplified)
             const isColumn = Object.values(schema).flat().includes(part);
             if (isColumn) {
                 type = 'column';
             }
        }
        return { text: part, type };
    });
};
