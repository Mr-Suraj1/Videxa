type Props = { className?: string; height?: string | number; width?: string | number };

export function Skeleton({ className = "", height, width }: Props) {
  return (
    <div
      className={`skeleton ${className}`}
      style={{ height, width }}
      aria-hidden="true"
    />
  );
}

export function SkeletonText({ lines = 3 }: { lines?: number }) {
  return (
    <div className="skeleton-text">
      {Array.from({ length: lines }).map((_, i) => (
        <Skeleton
          key={i}
          className="skeleton-text__line"
          width={i === lines - 1 ? "60%" : "100%"}
        />
      ))}
    </div>
  );
}

export function SkeletonCard() {
  return (
    <div className="skeleton-card">
      <Skeleton height={16} width="70%" />
      <Skeleton height={12} width="40%" />
    </div>
  );
}
