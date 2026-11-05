import type { InputHTMLAttributes, ReactNode, SelectHTMLAttributes, TextareaHTMLAttributes } from "react";
import { Icon } from "@/components/icon";
import { cn } from "@/lib/cn";

/*
 * Form controls on the design system's classes (Figma: Field, Select, Textarea, Checkbox, Radio). Each control takes
 * an id; its label, help line and error are tied to it for assistive technology. An error replaces the help line, as
 * the Figma State=Error variants do. These hold no state themselves, so a form keeps its values and errors.
 */

type FieldShellProps = {
  id: string;
  label: ReactNode;
  help?: ReactNode;
  error?: string;
  className?: string;
  /** Something beside the label, such as a "Sample times" tag. */
  labelAside?: ReactNode;
  children: ReactNode;
};

/** The label, the control and the help or error line, 8px apart (Figma: Field). */
function FieldShell({ id, label, help, error, className, labelAside, children }: FieldShellProps) {
  return (
    <div className={cn("aap-field", className)}>
      {labelAside ? (
        <div className="flex items-center justify-between gap-3">
          <label htmlFor={id} className="aap-field__label">
            {label}
          </label>
          {labelAside}
        </div>
      ) : (
        <label htmlFor={id} className="aap-field__label">
          {label}
        </label>
      )}
      {children}
      <FieldMessage id={id} help={help} error={error} />
    </div>
  );
}

/** The help line or, when there is one, the error (with its icon) under a control. */
export function FieldMessage({ id, help, error }: { id: string; help?: ReactNode; error?: string }) {
  if (error) {
    return (
      <p id={`${id}-error`} className="aap-field__error">
        <Icon name="x-circle" className="mt-px size-4 shrink-0" />
        {error}
      </p>
    );
  }
  return help ? (
    <p id={`${id}-help`} className="aap-field__help">
      {help}
    </p>
  ) : null;
}

/** The ids that describe a control: its error if it has one, otherwise its help line. */
export function describedBy(id: string, help?: ReactNode, error?: string) {
  if (error) return `${id}-error`;
  return help ? `${id}-help` : undefined;
}

type TextFieldProps = Omit<InputHTMLAttributes<HTMLInputElement>, "id"> & Omit<FieldShellProps, "children">;

export function TextField({ id, label, help, error, className, labelAside, ...input }: TextFieldProps) {
  return (
    <FieldShell id={id} label={label} help={help} error={error} className={className} labelAside={labelAside}>
      <input
        id={id}
        className="aap-input"
        aria-invalid={error ? true : undefined}
        aria-describedby={describedBy(id, help, error)}
        {...input}
      />
    </FieldShell>
  );
}

type SelectFieldProps = Omit<SelectHTMLAttributes<HTMLSelectElement>, "id"> & Omit<FieldShellProps, "children"> & {
  children: ReactNode;
};

export function SelectField({ id, label, help, error, className, labelAside, children, ...select }: SelectFieldProps) {
  return (
    <FieldShell id={id} label={label} help={help} error={error} className={className} labelAside={labelAside}>
      <select
        id={id}
        className="aap-select"
        aria-invalid={error ? true : undefined}
        aria-describedby={describedBy(id, help, error)}
        {...select}
      >
        {children}
      </select>
    </FieldShell>
  );
}

type TextareaFieldProps = Omit<TextareaHTMLAttributes<HTMLTextAreaElement>, "id"> & Omit<FieldShellProps, "children">;

export function TextareaField({ id, label, help, error, className, labelAside, ...textarea }: TextareaFieldProps) {
  return (
    <FieldShell id={id} label={label} help={help} error={error} className={className} labelAside={labelAside}>
      <textarea
        id={id}
        className="aap-textarea"
        aria-invalid={error ? true : undefined}
        aria-describedby={describedBy(id, help, error)}
        {...textarea}
      />
    </FieldShell>
  );
}

type CheckboxProps = Omit<InputHTMLAttributes<HTMLInputElement>, "id" | "type"> & {
  id: string;
  /** The label, which may hold a link (for example to the privacy policy). */
  children: ReactNode;
  error?: string;
  className?: string;
};

/** A checkbox with its label beside it (Figma: Checkbox, Body/SM). */
export function Checkbox({ id, children, error, className, ...input }: CheckboxProps) {
  return (
    <div className={cn("flex flex-col gap-2", className)}>
      <div className="aap-check">
        <input
          id={id}
          type="checkbox"
          aria-invalid={error ? true : undefined}
          aria-describedby={error ? `${id}-error` : undefined}
          {...input}
        />
        <label htmlFor={id}>{children}</label>
      </div>
      <FieldMessage id={id} error={error} />
    </div>
  );
}

type RadioOptionProps = Omit<InputHTMLAttributes<HTMLInputElement>, "id" | "type"> & {
  id: string;
  label: ReactNode;
  className?: string;
};

/** One radio button and its label (Figma: Radio, Body/SM). Group them in a fieldset with a legend. */
export function RadioOption({ id, label, className, ...input }: RadioOptionProps) {
  return (
    <span className={cn("aap-check", className)}>
      <input id={id} type="radio" {...input} />
      <label htmlFor={id}>{label}</label>
    </span>
  );
}
