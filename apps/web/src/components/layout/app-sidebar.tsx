"use client";

import * as React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { cn } from "@/lib/utils";
import {
  LayoutDashboard,
  FolderOpen,
  Zap,
  Settings,
  HelpCircle,
  ChevronLeft,
  ChevronRight,
  Sun,
  Battery,
  Grid3x3,
  BarChart3,
  Users,
  Bell,
  BookOpen,
  Building,
  Database,
  CheckSquare,
  FileText,
  Layers,
} from "lucide-react";
import { apiClient } from "@/lib/api-client";

interface SidebarItem {
  name: string;
  href: string;
  icon: React.ElementType;
  badge?: string;
  children?: SidebarItem[];
}

const staticNavigation: SidebarItem[] = [
  {
    name: "Dashboard",
    href: "/dashboard",
    icon: LayoutDashboard,
  },
  {
    name: "AI Assistant",
    href: "/ai",
    icon: Zap,
    badge: "New",
  },
  {
    name: "Components",
    href: "/components",
    icon: Grid3x3,
  },
  {
    name: "Missions",
    href: "/missions",
    icon: CheckSquare,
  },
  {
    name: "Suppliers",
    href: "/suppliers",
    icon: Building,
  },
  {
    name: "Model Registry",
    href: "/model-registry",
    icon: Database,
  },
  {
    name: "Analytics",
    href: "/analytics",
    icon: BarChart3,
  },
  {
    name: "Transparency",
    href: "/transparency-dashboard",
    icon: BarChart3,
  },
  {
    name: "Team",
    href: "/team",
    icon: Users,
  },
];

const getDomainIcon = (domain: string) => {
  switch (domain) {
    case "PV":
      return Sun;
    case "BESS":
      return Battery;
    case "HYBRID":
      return Zap;
    default:
      return FolderOpen;
  }
};

const createProjectSubItems = (projectId: string): SidebarItem[] => [
  { name: "Canvases", href: `/projects/${projectId}/canvases`, icon: Layers },
  { name: "Models", href: `/projects/${projectId}/models`, icon: Database },
  {
    name: "Documents",
    href: `/projects/${projectId}/documents`,
    icon: FileText,
  },
  {
    name: "Reviews & Approvals",
    href: `/projects/${projectId}/reviews`,
    icon: CheckSquare,
  },
];

const bottomNavigation: SidebarItem[] = [
  {
    name: "Documentation",
    href: "/docs",
    icon: BookOpen,
  },
  {
    name: "Help & Support",
    href: "/support",
    icon: HelpCircle,
  },
  {
    name: "Settings",
    href: "/settings",
    icon: Settings,
  },
];

interface AppSidebarProps {
  className?: string;
}

export function AppSidebar({ className }: AppSidebarProps) {
  const pathname = usePathname();
  const [isCollapsed, setIsCollapsed] = React.useState(false);
  const [hoverOpen, setHoverOpen] = React.useState(false);
  const [expandedItems, setExpandedItems] = React.useState<string[]>([]);

  // Load projects dynamically
  const { data: projects = [], isLoading } = useQuery({
    queryKey: ["projects"],
    queryFn: () => apiClient.listProjects(),
  });

  // Filter out legacy projects and create dynamic navigation
  const uniqueProjects = projects.filter(
    (project: any) => !project.project_name.includes("(Legacy)"),
  );

  // Create dynamic navigation with projects
  const navigation = React.useMemo(() => {
    const projectsItem = {
      name: "Projects",
      href: "/projects",
      icon: FolderOpen,
      children: [
        ...uniqueProjects.map((project: any) => ({
          name: project.project_name,
          href: `/projects/${project.id}`,
          icon: FolderOpen,
          children: createProjectSubItems(project.id),
        })),
      ],
    };

    return [
      staticNavigation[0], // Dashboard
      projectsItem,
      ...staticNavigation.slice(1), // Rest of the navigation
    ];
  }, [uniqueProjects]);

  const toggleExpanded = (itemName: string) => {
    setExpandedItems((prev) =>
      prev.includes(itemName)
        ? prev.filter((name) => name !== itemName)
        : [...prev, itemName],
    );
  };

  const isActive = (href: string) => {
    if (href === "/dashboard") {
      return pathname === "/dashboard";
    }
    return pathname.startsWith(href);
  };

  const SidebarLink = ({
    item,
    level = 0,
  }: {
    item: SidebarItem;
    level?: number;
  }) => {
    const Icon = item.icon;
    const isItemActive = isActive(item.href);
    const hasChildren = item.children && item.children.length > 0;
    const isExpanded = expandedItems.includes(item.name);

    return (
      <div>
        <Link
          href={item.href}
          className={cn(
            "group flex items-center justify-between py-1.5 text-sm font-medium rounded-lg transition-colors w-full",
            level === 0 && "px-3",
            level === 1 && "px-3",
            level === 2 && "px-3",
            isItemActive
              ? "bg-primary text-primary-foreground shadow-sm"
              : "text-muted-foreground hover:text-foreground hover:bg-muted",
            isCollapsed && level === 0 && "justify-center px-3",
          )}
          onClick={(e) => {
            if (hasChildren && !isCollapsed) {
              e.preventDefault();
              toggleExpanded(item.name);
            }
          }}
        >
          <div
            className="flex items-center min-w-0 flex-1"
            style={{
              paddingLeft: level === 1 ? "1rem" : level === 2 ? "1.75rem" : "0",
            }}
          >
            <Icon className="h-4 w-4 flex-shrink-0 mr-2" />
            {!isCollapsed && (
              <span className="truncate text-sm">{item.name}</span>
            )}
          </div>
          {!isCollapsed && (
            <div className="flex items-center gap-2 flex-shrink-0">
              {item.badge && (
                <span className="bg-primary/10 text-primary text-xs font-medium px-2 py-0.5 rounded-full whitespace-nowrap">
                  {item.badge}
                </span>
              )}
              {hasChildren && (
                <ChevronRight
                  className={cn(
                    "h-3 w-3 transition-transform flex-shrink-0",
                    isExpanded && "rotate-90",
                  )}
                />
              )}
            </div>
          )}
        </Link>

        {/* Children */}
        {hasChildren && isExpanded && !isCollapsed && (
          <div className="space-y-0.5">
            {item.children!.map((child) => (
              <SidebarLink key={child.name} item={child} level={level + 1} />
            ))}
          </div>
        )}
      </div>
    );
  };

  return (
    <div
      onMouseEnter={() => setHoverOpen(true)}
      onMouseLeave={() => setHoverOpen(false)}
      className={cn(
        "flex flex-col h-full bg-card border-r border-border transition-[width] duration-200 overflow-hidden",
        isCollapsed && !hoverOpen ? "w-16" : "w-64",
        className,
      )}
    >
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-border">
        {(!isCollapsed || hoverOpen) && (
          <div className="flex items-center gap-2">
            <div className="h-8 w-8 bg-gradient-to-r from-originfd-blue-600 to-originfd-green-600 rounded-lg flex items-center justify-center">
              <span className="text-white font-bold text-sm">OF</span>
            </div>
            <span className="font-bold text-lg">OriginFD</span>
          </div>
        )}
        <button
          onClick={() => setIsCollapsed(!isCollapsed)}
          className="p-1.5 rounded-md hover:bg-muted transition-colors"
          aria-label={isCollapsed ? "Expand sidebar" : "Collapse sidebar"}
        >
          {isCollapsed ? (
            <ChevronRight className="h-4 w-4" />
          ) : (
            <ChevronLeft className="h-4 w-4" />
          )}
        </button>
      </div>

      {/* Navigation */}
      <nav className="flex-1 p-4 overflow-y-auto">
        <div className="space-y-1">
          {isLoading ? (
            <div className="px-3 py-2 text-sm text-muted-foreground">
              Loading navigation...
            </div>
          ) : (
            navigation.map((item) => (
              <SidebarLink key={item.name} item={item} />
            ))
          )}
        </div>
      </nav>

      {/* Bottom Navigation */}
      <div className="p-4 border-t border-border">
        <div className="space-y-1">
          {bottomNavigation.map((item) => (
            <SidebarLink key={item.name} item={item} />
          ))}
        </div>
      </div>

      {/* Notifications (when expanded) */}
      {(!isCollapsed || hoverOpen) && (
        <div className="p-4 border-t border-border">
          <div className="flex items-center gap-3 p-3 bg-muted/50 rounded-lg">
            <div className="p-2 bg-originfd-blue-100 rounded-lg">
              <Bell className="h-4 w-4 text-originfd-blue-600" />
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-xs font-medium text-foreground">
                3 active tasks
              </p>
              <p className="text-xs text-muted-foreground truncate">
                AI analysis in progress
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
