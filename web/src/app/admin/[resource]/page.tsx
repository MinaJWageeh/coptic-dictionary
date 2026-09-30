import { notFound } from "next/navigation";
import { ResourcePage } from "@/components/resource-page";
import { getResource } from "@/lib/resource-config";

export default async function AdminResourcePage({ params }: { params: Promise<{ resource: string }> }) {
  const { resource: key } = await params;
  const resource = getResource(key);
  if (!resource) notFound();
  return <ResourcePage resource={resource} />;
}
