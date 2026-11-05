type Variant = "purple" | "cyan" | "green" | "amber" | "red" | "default";

type Props = { children: React.ReactNode; variant?: Variant; className?: string };

export function Badge({ children, variant = "default", className = "" }: Props) {
  return (
    <span className={`badge badge--${variant} ${className}`}>{children}</span>
  );
}
