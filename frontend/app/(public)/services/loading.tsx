import { PageSkeleton } from "@/components/layout/Skeleton";

export default function Loading() {
  return <PageSkeleton label="Loading services" cards={6} />;
}
