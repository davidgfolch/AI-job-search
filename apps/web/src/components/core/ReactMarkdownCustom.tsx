import React, { type ReactNode } from 'react';
import ReactMarkdown from 'react-markdown';

interface ReactMarkdownCustomProps {
    children: string | null | undefined;
}

const slugify = (text: string) => {
    return text
        .toLowerCase()
        .replace(/[^\w\s-]/g, '')
        .replace(/\s+/g, '-');
};

const getText = (node: ReactNode): string => {
    if (typeof node === 'string') return node;
    if (typeof node === 'number') return String(node);
    if (Array.isArray(node)) return node.map(getText).join('');
    if (React.isValidElement(node)) {
        const props = node.props as { children?: ReactNode };
        return getText(props.children);
    }
    return '';
};

const createHeadingRenderer = (level: number) => {
    return ({ children, ...props }: any) => {
        const text = getText(children);
        const slug = slugify(text);
        const Tag = `h${level}` as React.ElementType;
        return <Tag id={slug} {...props}>{children}</Tag>;
    };
};

export default function ReactMarkdownCustom({ children }: ReactMarkdownCustomProps) {
    if (!children) return null;

    // Transform :color[text] syntax to markdown links before rendering
    // This allows us to intercept them in the link renderer
    const processedContent = children.replace(/:(\w+)\[(.*?)\]/g, '[$2](#color-$1)');

    return (
        <ReactMarkdown
            components={{
                a: ({ href, children, ...props }) => {
                    if (href?.startsWith('#color-')) {
                        const color = href.replace('#color-', '');
                        return <span style={{ color }}>{children}</span>;
                    }
                    if (href?.startsWith('#')) {
                        const handleClick = (e: React.MouseEvent) => {
                            e.preventDefault();
                            const id = href.substring(1);
                            const element = document.getElementById(id);
                            if (element) {
                                element.scrollIntoView({ behavior: 'smooth' });
                                window.history.pushState(null, '', href);
                            }
                        };
                        return <a href={href} onClick={handleClick} {...props}>{children}</a>;
                    }
                    return <a href={href} {...props}>{children}</a>;
                },
                h1: createHeadingRenderer(1),
                h2: createHeadingRenderer(2),
                h3: createHeadingRenderer(3),
                h4: createHeadingRenderer(4),
                h5: createHeadingRenderer(5),
                h6: createHeadingRenderer(6),
            }}
        >
            {processedContent}
        </ReactMarkdown>
    );
}
