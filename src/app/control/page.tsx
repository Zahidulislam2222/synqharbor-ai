import type { Metadata } from "next";
import { Control } from "@/components/control";
import copy from "@/content/control.json";

export const metadata: Metadata = { title: copy.title, robots: { index: false, follow: false } };
export default function ControlPage() { return <Control />; }
