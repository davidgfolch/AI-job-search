import React, { type ReactNode } from 'react';

export interface FormFieldProps {
    id?: string;
    label?: ReactNode;
    children: ReactNode;
    className?: string;
    layout?: 'vertical' | 'horizontal';
}

export const FormField: React.FC<FormFieldProps> = ({ id, label, children, className = 'form-field', layout = 'vertical' }) => {
    const layoutClass = layout === 'horizontal' ? 'form-field-horizontal' : '';
    const combinedClassName = `${className} ${layoutClass}`.trim();

    return (
        <div className={combinedClassName}>
            {label && (id ? <label htmlFor={id}>{label}</label> : <label>{label}</label>)}
            {children}
        </div>
    );
};
