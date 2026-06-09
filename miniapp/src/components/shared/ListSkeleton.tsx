import { Skeleton } from '@/components/ui/skeleton';

interface ListSkeletonProps {
  count?: number;
  itemHeight?: number;
}

export function ListSkeleton({ count = 4, itemHeight = 76 }: ListSkeletonProps) {
  return (
    <div className="space-y-3">
      {Array.from({ length: count }).map((_, i) => (
        <Skeleton key={i} style={{ height: itemHeight }} />
      ))}
    </div>
  );
}
