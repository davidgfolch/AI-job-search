import ReactMarkdown from 'react-markdown';

interface ReactMarkdownCustomProps {
    children: string | null | undefined;
}

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
                    return <a href={href} {...props}>{children}</a>;
                }
            }}
        >
            {processedContent}
        </ReactMarkdown>
    );
}
