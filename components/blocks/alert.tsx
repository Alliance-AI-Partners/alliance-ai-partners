import type { ReactNode } from "react";
import { Icon, type IconName } from "@/components/icon";
import { cn } from "@/lib/cn";

const types: Record<"info" | "success" | "warning" | "error", { icon: IconName; className: string }> = {
  info: { icon: "info", className: "" },
  success: { icon: "check-circle", className: "aap-alert--success" },
  warning: { icon: "alert-triangle", className: "aap-alert--warning" },
  error: { icon: "x-circle", className: "aap-alert--error" },
};

type AlertProps = {
  type?: keyof typeof types;
  title: ReactNode;
  children?: ReactNode;
  className?: string;
  /** "status" for a confirmation that appears after an action, so screen readers announce it; "alert" for errors. */
  role?: "status" | "alert";
};

/**
 * A message box (Figma: Alert): the type's icon, a Body/Strong title and a Body/SM line, on the type's tinted surface.
 */
export function Alert({ type = "info", title, children, className, role }: AlertProps) {
  const { icon, className: typeClass } = types[type];
  return (
    <div className={cn("aap-alert", typeClass, className)} role={role}>
      <Icon name={icon} />
      <div className="flex flex-col gap-1">
        <p className="text-body font-semibold">{title}</p>
        {children ? <div className="text-body-sm">{children}</div> : null}
      </div>
    </div>
  );
}
