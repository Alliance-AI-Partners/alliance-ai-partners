/** Joins class names, skipping empty values: cn("a", flag && "b"). */
export function cn(...classes: (string | false | null | undefined)[]) {
  return classes.filter(Boolean).join(" ");
}
