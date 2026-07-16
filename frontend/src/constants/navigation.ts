import {
  LayoutDashboard,
  Database,
  BarChart3,
  BrainCircuit,
  MessageSquare,
  FileText,
  Settings,
} from "lucide-react";
import type { LucideIcon } from "lucide-react";

export interface NavItem {
  label: string;
  href: string;
  icon: LucideIcon;
  disabled?: boolean;
}

export const navigationItems: NavItem[] = [
  {
    label: "Dashboard",
    href: "/",
    icon: LayoutDashboard,
  },
  {
    label: "Datasets",
    href: "/datasets",
    icon: Database,
  },
  {
    label: "Visualize",
    href: "/visualize",
    icon: BarChart3,
  },
  {
    label: "Reports",
    href: "/reports",
    icon: FileText,
  },
  {
    label: "Settings",
    href: "/settings",
    icon: Settings,
    disabled: true,
  },
];
