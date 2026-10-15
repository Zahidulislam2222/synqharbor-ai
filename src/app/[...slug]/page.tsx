import type { Metadata } from "next";
import { notFound } from "next/navigation";
import pages from "@/content/pages.json";
import { PublicPage } from "@/components/public-page";

export const dynamicParams = false;
export function generateStaticParams() {
  return pages.map((page) => ({ slug: page.slug.split("/") }));
}
type Props = { params: Promise<{ slug: string[] }> };
export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { slug } = await params;
  const page = pages.find((item) => item.slug === slug.join("/"));
  return {
    title: page?.label,
    description: page?.description,
    alternates: { canonical: `/${slug.join("/")}/` },
  };
}
export default async function Page({ params }: Props) {
  const { slug } = await params;
  const page = pages.find((item) => item.slug === slug.join("/"));
  if (!page) notFound();
  return <PublicPage page={page} />;
}
