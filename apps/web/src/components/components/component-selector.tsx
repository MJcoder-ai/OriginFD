"use client";

import * as React from "react";
import { useQuery } from "@tanstack/react-query";
import {
  Check,
  ChevronsUpDown,
  Search,
  Package,
  Plus,
  X,
  AlertCircle,
  CheckCircle,
  Clock,
  Warehouse,
} from "lucide-react";

import {
  Button,
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  Input,
  Label,
} from "@originfd/ui";
import { cn } from "@/lib/utils";
import { componentAPI } from "@/lib/api-client";
import type { ComponentResponse } from "@/lib/types";

// Inline UI components for missing dependencies
const Badge = ({
  children,
  variant = "secondary",
  className = "",
}: {
  children: React.ReactNode;
  variant?: "secondary" | "outline";
  className?: string;
}) => (
  <span
    className={cn(
      "inline-flex items-center px-2 py-1 rounded-full text-xs font-medium border",
      variant === "outline"
        ? "bg-transparent border-gray-200"
        : "bg-gray-100 border-gray-200",
      className,
    )}
  >
    {children}
  </span>
);

const Separator = ({
  orientation = "horizontal",
  className = "",
}: {
  orientation?: "horizontal" | "vertical";
  className?: string;
}) => (
  <div
    className={cn(
      "bg-border",
      orientation === "vertical" ? "w-px h-full" : "h-px w-full",
      className,
    )}
  />
);

const Popover = ({ children }: { children: React.ReactNode }) => (
  <div className="relative">{children}</div>
);
const PopoverTrigger = ({
  children,
  asChild,
  ...props
}: {
  children: React.ReactNode;
  asChild?: boolean;
  [key: string]: any;
}) => <div {...props}>{children}</div>;
const PopoverContent = ({
  children,
  className = "",
}: {
  children: React.ReactNode;
  className?: string;
}) => (
  <div
    className={cn(
      "absolute z-50 min-w-[8rem] overflow-hidden rounded-md border bg-popover p-1 text-popover-foreground shadow-md",
      className,
    )}
  >
    {children}
  </div>
);

// Simplified Command components
const Command = ({ children }: { children: React.ReactNode }) => (
  <div>{children}</div>
);
const CommandList = ({ children }: { children: React.ReactNode }) => (
  <div>{children}</div>
);
const CommandGroup = ({ children }: { children: React.ReactNode }) => (
  <div className="space-y-1">{children}</div>
);
const CommandItem = ({
  children,
  onSelect,
}: {
  children: React.ReactNode;
  onSelect: () => void;
}) => (
  <div
    className="cursor-pointer px-2 py-1 hover:bg-accent rounded text-sm"
    onClick={onSelect}
  >
    {children}
  </div>
);

// Helper functions for ODL-SD v4.1 component display
const getODLStatusDisplay = (status?: string) => {
  const statuses = {
    draft: {
      icon: Clock,
      color: "text-yellow-600",
      bg: "bg-yellow-50",
      label: "Draft",
    },
    parsed: {
      icon: Clock,
      color: "text-blue-600",
      bg: "bg-blue-50",
      label: "Parsed",
    },
    enriched: {
      icon: CheckCircle,
      color: "text-blue-600",
      bg: "bg-blue-50",
      label: "Enriched",
    },
    approved: {
      icon: CheckCircle,
      color: "text-green-600",
      bg: "bg-green-50",
      label: "Approved",
    },
    available: {
      icon: CheckCircle,
      color: "text-green-600",
      bg: "bg-green-50",
      label: "Available",
    },
    rfq_open: {
      icon: Clock,
      color: "text-purple-600",
      bg: "bg-purple-50",
      label: "RFQ Open",
    },
    operational: {
      icon: CheckCircle,
      color: "text-emerald-600",
      bg: "bg-emerald-50",
      label: "Operational",
    },
    archived: {
      icon: Package,
      color: "text-gray-600",
      bg: "bg-gray-50",
      label: "Archived",
    },
  };
  return statuses[status as keyof typeof statuses] || statuses.draft;
};

const getComplianceDisplay = (
  certificates?: Array<{ standard: string; valid_until: string }>,
) => {
  if (!certificates || certificates.length === 0) {
    return {
      icon: AlertCircle,
      color: "text-red-600",
      label: "No Certificates",
    };
  }

  const now = new Date();
  const expiringSoon = certificates.some((cert) => {
    const validUntil = new Date(cert.valid_until);
    const monthsUntilExpiry =
      (validUntil.getTime() - now.getTime()) / (1000 * 60 * 60 * 24 * 30);
    return monthsUntilExpiry < 6;
  });

  if (expiringSoon) {
    return {
      icon: AlertCircle,
      color: "text-orange-600",
      label: "Expiring Soon",
    };
  }

  return {
    icon: CheckCircle,
    color: "text-green-600",
    label: `${certificates.length} Certs`,
  };
};

interface ComponentSelectorProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onComponentsSelected: (components: SelectedComponent[]) => void;
  projectDomain?: string;
  projectScale?: string;
  multiSelect?: boolean;
  title?: string;
  description?: string;
}

interface SelectedComponent {
  component: ComponentResponse;
  quantity: number;
  placement?: {
    location?: string;
    coordinates?: { x: number; y: number; z?: number };
    orientation?: string;
  };
  configuration?: Record<string, any>;
  notes?: string;
}

export function ComponentSelector({
  open,
  onOpenChange,
  onComponentsSelected,
  projectDomain,
  projectScale,
  multiSelect = true,
  title = "Select Components",
  description = "Choose components to add to your project",
}: ComponentSelectorProps) {
  const [searchQuery, setSearchQuery] = React.useState("");
  const [selectedComponents, setSelectedComponents] = React.useState<
    SelectedComponent[]
  >([]);
  const [categoryFilter, setCategoryFilter] = React.useState<string>("");
  const [domainFilter, setDomainFilter] = React.useState<string>(
    projectDomain || "",
  );
  const [lifecycleFilter, setLifecycleFilter] = React.useState<string>("");
  const [showInventoryOnly, setShowInventoryOnly] =
    React.useState<boolean>(false);

  // Fetch components with filters
  const { data: componentsData, isLoading } = useQuery({
    queryKey: [
      "components",
      searchQuery,
      categoryFilter,
      domainFilter,
      lifecycleFilter,
      showInventoryOnly,
    ],
    queryFn: () =>
      componentAPI.listComponents({
        search: searchQuery || undefined,
        category: categoryFilter || undefined,
        domain: domainFilter || undefined,
        status: lifecycleFilter || undefined,
        page_size: 50,
      }),
    enabled: open,
  });

  const components = componentsData?.components || [];

  const handleComponentToggle = (component: ComponentResponse) => {
    if (!multiSelect) {
      setSelectedComponents([{ component, quantity: 1 }]);
      return;
    }

    const existingIndex = selectedComponents.findIndex(
      (sc) => sc.component.id === component.id,
    );

    if (existingIndex >= 0) {
      // Remove component
      setSelectedComponents((prev) =>
        prev.filter((_, i) => i !== existingIndex),
      );
    } else {
      // Add component
      setSelectedComponents((prev) => [...prev, { component, quantity: 1 }]);
    }
  };

  const updateComponentQuantity = (componentId: string, quantity: number) => {
    setSelectedComponents((prev) =>
      prev.map((sc) =>
        sc.component.id === componentId
          ? { ...sc, quantity: Math.max(1, quantity) }
          : sc,
      ),
    );
  };

  const updateComponentPlacement = (
    componentId: string,
    placement: SelectedComponent["placement"],
  ) => {
    setSelectedComponents((prev) =>
      prev.map((sc) =>
        sc.component.id === componentId ? { ...sc, placement } : sc,
      ),
    );
  };

  const updateComponentNotes = (componentId: string, notes: string) => {
    setSelectedComponents((prev) =>
      prev.map((sc) =>
        sc.component.id === componentId ? { ...sc, notes } : sc,
      ),
    );
  };

  const handleConfirm = () => {
    onComponentsSelected(selectedComponents);
    onOpenChange(false);
    setSelectedComponents([]);
    setSearchQuery("");
  };

  const handleCancel = () => {
    onOpenChange(false);
    setSelectedComponents([]);
    setSearchQuery("");
  };

  const isComponentSelected = (component: ComponentResponse) => {
    return selectedComponents.some((sc) => sc.component.id === component.id);
  };

  const getSelectedComponent = (componentId: string) => {
    return selectedComponents.find((sc) => sc.component.id === componentId);
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[900px] max-h-[90vh] overflow-hidden flex flex-col">
        <DialogHeader>
          <DialogTitle>{title}</DialogTitle>
          <DialogDescription>{description}</DialogDescription>
        </DialogHeader>

        <div className="flex-1 flex gap-6 overflow-hidden">
          {/* Component Library */}
          <div className="flex-1 flex flex-col min-h-0">
            <div className="space-y-4 mb-4">
              {/* Search */}
              <div className="relative">
                <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
                <Input
                  placeholder="Search components..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pl-8"
                />
              </div>

              {/* Filters */}
              <div className="flex gap-2 flex-wrap">
                <Popover>
                  <PopoverTrigger asChild>
                    <Button
                      variant="outline"
                      size="sm"
                      className="w-[120px] justify-between"
                    >
                      {categoryFilter || "Category"}
                      <ChevronsUpDown className="ml-2 h-4 w-4 shrink-0 opacity-50" />
                    </Button>
                  </PopoverTrigger>
                  <PopoverContent className="w-[120px] p-0">
                    <Command>
                      <CommandList>
                        <CommandGroup>
                          <CommandItem onSelect={() => setCategoryFilter("")}>
                            All Categories
                          </CommandItem>
                          <CommandItem
                            onSelect={() => setCategoryFilter("pv_modules")}
                          >
                            PV Modules
                          </CommandItem>
                          <CommandItem
                            onSelect={() => setCategoryFilter("inverters")}
                          >
                            Inverters
                          </CommandItem>
                          <CommandItem
                            onSelect={() => setCategoryFilter("batteries")}
                          >
                            Batteries
                          </CommandItem>
                        </CommandGroup>
                      </CommandList>
                    </Command>
                  </PopoverContent>
                </Popover>

                <Popover>
                  <PopoverTrigger asChild>
                    <Button
                      variant="outline"
                      size="sm"
                      className="w-[100px] justify-between"
                    >
                      {domainFilter || "Domain"}
                      <ChevronsUpDown className="ml-2 h-4 w-4 shrink-0 opacity-50" />
                    </Button>
                  </PopoverTrigger>
                  <PopoverContent className="w-[100px] p-0">
                    <Command>
                      <CommandList>
                        <CommandGroup>
                          <CommandItem onSelect={() => setDomainFilter("")}>
                            All Domains
                          </CommandItem>
                          <CommandItem onSelect={() => setDomainFilter("PV")}>
                            PV
                          </CommandItem>
                          <CommandItem onSelect={() => setDomainFilter("BESS")}>
                            BESS
                          </CommandItem>
                          <CommandItem
                            onSelect={() => setDomainFilter("HYBRID")}
                          >
                            Hybrid
                          </CommandItem>
                          <CommandItem onSelect={() => setDomainFilter("GRID")}>
                            Grid
                          </CommandItem>
                        </CommandGroup>
                      </CommandList>
                    </Command>
                  </PopoverContent>
                </Popover>

                <Popover>
                  <PopoverTrigger asChild>
                    <Button
                      variant="outline"
                      size="sm"
                      className="w-[110px] justify-between"
                    >
                      {lifecycleFilter || "Lifecycle"}
                      <ChevronsUpDown className="ml-2 h-4 w-4 shrink-0 opacity-50" />
                    </Button>
                  </PopoverTrigger>
                  <PopoverContent className="w-[110px] p-0">
                    <Command>
                      <CommandList>
                        <CommandGroup>
                          <CommandItem onSelect={() => setLifecycleFilter("")}>
                            All Statuses
                          </CommandItem>
                          <CommandItem
                            onSelect={() => setLifecycleFilter("draft")}
                          >
                            Draft
                          </CommandItem>
                          <CommandItem
                            onSelect={() => setLifecycleFilter("approved")}
                          >
                            Approved
                          </CommandItem>
                          <CommandItem
                            onSelect={() => setLifecycleFilter("available")}
                          >
                            Available
                          </CommandItem>
                          <CommandItem
                            onSelect={() => setLifecycleFilter("operational")}
                          >
                            Operational
                          </CommandItem>
                          <CommandItem
                            onSelect={() => setLifecycleFilter("archived")}
                          >
                            Archived
                          </CommandItem>
                        </CommandGroup>
                      </CommandList>
                    </Command>
                  </PopoverContent>
                </Popover>

                <Button
                  variant={showInventoryOnly ? "default" : "outline"}
                  size="sm"
                  onClick={() => setShowInventoryOnly(!showInventoryOnly)}
                  className="gap-2"
                >
                  <Warehouse className="h-4 w-4" />
                  {showInventoryOnly ? "In Stock" : "Stock"}
                </Button>
              </div>
            </div>

            {/* Component List */}
            <div className="flex-1 overflow-y-auto space-y-2">
              {isLoading ? (
                <div className="flex items-center justify-center py-8">
                  <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-primary"></div>
                </div>
              ) : components.length === 0 ? (
                <div className="text-center py-8">
                  <Package className="mx-auto h-8 w-8 text-muted-foreground" />
                  <p className="mt-2 text-sm text-muted-foreground">
                    No components found
                  </p>
                </div>
              ) : (
                components.map((component: any) => {
                  const statusDisplay = getODLStatusDisplay(
                    component.component_management.status,
                  );
                  const complianceDisplay = getComplianceDisplay(
                    component.component_management.compliance.certificates,
                  );
                  const StatusIcon = statusDisplay.icon;
                  const ComplianceIcon = complianceDisplay.icon;
                  const identity =
                    component.component_management.component_identity;
                  const hasInventory =
                    component.component_management.inventory.stocks.length > 0;
                  const inventoryQty = hasInventory
                    ? component.component_management.inventory.stocks[0]
                        .on_hand_qty
                    : 0;

                  return (
                    <Card
                      key={component.id}
                      className={cn(
                        "cursor-pointer transition-colors",
                        isComponentSelected(component) && "ring-2 ring-primary",
                      )}
                      onClick={() => handleComponentToggle(component)}
                    >
                      <CardContent className="p-3">
                        <div className="flex items-start justify-between">
                          <div className="flex items-start space-x-3 flex-1">
                            <div className="p-2 rounded bg-muted flex-shrink-0">
                              <Package className="h-4 w-4" />
                            </div>
                            <div className="flex-1 min-w-0">
                              <p className="font-medium text-sm truncate">
                                {identity.brand} {identity.part_number}
                              </p>
                              <p className="text-xs text-muted-foreground">
                                {identity.rating_w}W •{" "}
                                {identity.classification?.unspsc
                                  ? identity.classification.unspsc ===
                                    "26111704"
                                    ? "PV Modules"
                                    : identity.classification.unspsc ===
                                        "26111705"
                                      ? "Inverters"
                                      : identity.classification.unspsc ===
                                          "26111706"
                                        ? "Batteries"
                                        : "Component"
                                  : "Component"}
                              </p>

                              {/* ODL-SD v4.1 status indicators */}
                              <div className="flex items-center gap-2 mt-1">
                                <div
                                  className={cn(
                                    "flex items-center gap-1 px-1.5 py-0.5 rounded text-xs",
                                    statusDisplay.bg,
                                  )}
                                >
                                  <StatusIcon
                                    className={cn(
                                      "h-3 w-3",
                                      statusDisplay.color,
                                    )}
                                  />
                                  <span className={statusDisplay.color}>
                                    {statusDisplay.label}
                                  </span>
                                </div>

                                <div className="flex items-center gap-1">
                                  <ComplianceIcon
                                    className={cn(
                                      "h-3 w-3",
                                      complianceDisplay.color,
                                    )}
                                  />
                                  <span
                                    className={cn(
                                      "text-xs",
                                      complianceDisplay.color,
                                    )}
                                  >
                                    {complianceDisplay.label}
                                  </span>
                                </div>

                                {hasInventory && (
                                  <div className="flex items-center gap-1">
                                    <Warehouse className="h-3 w-3 text-blue-600" />
                                    <span className="text-xs text-blue-600">
                                      {inventoryQty} pcs
                                    </span>
                                  </div>
                                )}
                              </div>
                            </div>
                          </div>

                          <div className="flex items-center space-x-2 flex-shrink-0 ml-2">
                            {component.component_management.warranty.terms
                              .duration_years > 0 && (
                              <Badge variant="outline" className="text-xs">
                                {
                                  component.component_management.warranty.terms
                                    .duration_years
                                }
                                yr warranty
                              </Badge>
                            )}
                            {isComponentSelected(component) && (
                              <div className="w-5 h-5 rounded-full bg-primary flex items-center justify-center">
                                <Check className="h-3 w-3 text-primary-foreground" />
                              </div>
                            )}
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  );
                })
              )}
            </div>
          </div>

          {/* Selected Components */}
          {selectedComponents.length > 0 && (
            <>
              <Separator orientation="vertical" className="h-full" />
              <div className="w-80 flex flex-col min-h-0">
                <div className="mb-4">
                  <h3 className="font-medium">
                    Selected Components ({selectedComponents.length})
                  </h3>
                  <p className="text-sm text-muted-foreground">
                    Configure placement and quantities
                  </p>
                </div>

                <div className="flex-1 overflow-y-auto space-y-3">
                  {selectedComponents.map((selectedComponent) => (
                    <Card key={selectedComponent.component.id}>
                      <CardHeader className="pb-2">
                        <div className="flex items-start justify-between">
                          <div>
                            <CardTitle className="text-sm">
                              {
                                selectedComponent.component.component_management
                                  ?.component_identity?.brand
                              }{" "}
                              {
                                selectedComponent.component.component_management
                                  ?.component_identity?.part_number
                              }
                            </CardTitle>
                            <CardDescription className="text-xs">
                              {
                                selectedComponent.component.component_management
                                  ?.component_identity?.rating_w
                              }
                              W
                            </CardDescription>
                          </div>
                          <Button
                            variant="ghost"
                            size="sm"
                            className="h-6 w-6 p-0"
                            onClick={() =>
                              handleComponentToggle(selectedComponent.component)
                            }
                          >
                            <X className="h-3 w-3" />
                          </Button>
                        </div>
                      </CardHeader>
                      <CardContent className="pt-0 space-y-3">
                        <div>
                          <Label className="text-xs">Quantity</Label>
                          <Input
                            type="number"
                            min="1"
                            value={selectedComponent.quantity}
                            onChange={(e) =>
                              updateComponentQuantity(
                                selectedComponent.component.id,
                                parseInt(e.target.value) || 1,
                              )
                            }
                            className="mt-1 h-8"
                          />
                        </div>
                        <div>
                          <Label className="text-xs">Location</Label>
                          <Input
                            placeholder="e.g., Roof Section A"
                            value={selectedComponent.placement?.location || ""}
                            onChange={(e) =>
                              updateComponentPlacement(
                                selectedComponent.component.id,
                                {
                                  ...selectedComponent.placement,
                                  location: e.target.value,
                                },
                              )
                            }
                            className="mt-1 h-8"
                          />
                        </div>
                        <div>
                          <Label className="text-xs">Notes</Label>
                          <Input
                            placeholder="Additional notes..."
                            value={selectedComponent.notes || ""}
                            onChange={(e) =>
                              updateComponentNotes(
                                selectedComponent.component.id,
                                e.target.value,
                              )
                            }
                            className="mt-1 h-8"
                          />
                        </div>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              </div>
            </>
          )}
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={handleCancel}>
            Cancel
          </Button>
          <Button
            onClick={handleConfirm}
            disabled={selectedComponents.length === 0}
          >
            Add {selectedComponents.length} Component
            {selectedComponents.length !== 1 ? "s" : ""}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
