
interface LoadingSkeletonProps {
  rows?: number;
  className?: string;
}

export function LoadingSkeleton({ rows = 3, className = "" }: LoadingSkeletonProps) {
  const rowList = Array.from({ length: rows });

  return (
    <div className={`space-y-3 ${className}`}>
      {rowList.map((_, index) => (
        <div
          key={index}
          className="h-4 bg-gray-700 rounded animate-pulse w-full"
          style={{
            opacity: 1 - (index * 0.15), // Create a clean visual fade out effect
          }}
        />
      ))}
    </div>
  );
}
export default LoadingSkeleton;
