"use client";

import * as React from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "react-hot-toast";
import {
  Loader2,
  ChevronLeft,
  ChevronRight,
  Check,
  Upload,
  Zap,
  Battery,
  Sun,
  Grid3x3,
  Cpu,
  Shield,
  Activity,
  Package,
} from "lucide-react";

import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  Button,
  Input,
  Label,
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
  Textarea,
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from "@originfd/ui";
import { componentAPI } from "@/lib/api-client";

const componentSchema = z.object({
  brand: z
    .string()
    .min(1, "Brand is required")
    .max(64, "Brand must be less than 64 characters"),
  part_number: z
    .string()
    .min(1, "Part number is required")
    .max(64, "Part number must be less than 64 characters"),
  rating_w: z
    .number()
    .min(1, "Rating must be at least 1W")
    .max(1000000, "Rating must be less than 1MW"),
  category: z
    .enum([
      "generation",
      "storage",
      "conversion",
      "protection",
      "monitoring",
      "structural",
      "other",
    ])
    .optional(),
  subcategory: z.string().max(50).optional(),
  domain: z.enum(["PV", "BESS", "HYBRID", "GRID", "MICROGRID"]).optional(),
  scale: z
    .enum(["RESIDENTIAL", "COMMERCIAL", "INDUSTRIAL", "UTILITY", "HYPERSCALE"])
    .optional(),
  description: z.string().max(500).optional(),
  datasheet_url: z.string().url().optional().or(z.literal("")),
  classification: z
    .object({
      unspsc: z
        .string()
        .regex(/^\d{8}$/)
        .optional()
        .or(z.literal("")),
      eclass: z.string().max(32).optional(),
      hs_code: z
        .string()
        .regex(/^\d{6}(\d{2,4})?$/)
        .optional()
        .or(z.literal("")),
      gtin: z
        .string()
        .regex(/^(?:\d{8}|\d{12}|\d{13}|\d{14})$/)
        .optional()
        .or(z.literal("")),
    })
    .optional(),
});

type ComponentFormData = z.infer<typeof componentSchema>;

interface ComponentCreationWizardProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

const categoryOptions = [
  {
    value: "generation",
    label: "Generation",
    description: "Power generation equipment",
    icon: Sun,
  },
  {
    value: "storage",
    label: "Storage",
    description: "Energy storage systems",
    icon: Battery,
  },
  {
    value: "conversion",
    label: "Conversion",
    description: "Power conversion equipment",
    icon: Zap,
  },
  {
    value: "protection",
    label: "Protection",
    description: "Safety and protection devices",
    icon: Shield,
  },
  {
    value: "monitoring",
    label: "Monitoring",
    description: "Monitoring and control systems",
    icon: Activity,
  },
  {
    value: "structural",
    label: "Structural",
    description: "Mounting and structural components",
    icon: Package,
  },
  {
    value: "other",
    label: "Other",
    description: "Other components",
    icon: Grid3x3,
  },
];

const domainOptions = [
  { value: "PV", label: "Solar PV", icon: Sun, color: "text-yellow-600" },
  {
    value: "BESS",
    label: "Battery Storage",
    icon: Battery,
    color: "text-green-600",
  },
  {
    value: "HYBRID",
    label: "Hybrid System",
    icon: Zap,
    color: "text-purple-600",
  },
  {
    value: "GRID",
    label: "Grid Integration",
    icon: Grid3x3,
    color: "text-blue-600",
  },
  {
    value: "MICROGRID",
    label: "Microgrid",
    icon: Cpu,
    color: "text-indigo-600",
  },
];

const scaleOptions = [
  {
    value: "RESIDENTIAL",
    label: "Residential",
    description: "Single-family homes",
    range: "< 10 kW",
  },
  {
    value: "COMMERCIAL",
    label: "Commercial",
    description: "Office buildings, retail",
    range: "10 kW - 1 MW",
  },
  {
    value: "INDUSTRIAL",
    label: "Industrial",
    description: "Manufacturing facilities",
    range: "1 MW - 10 MW",
  },
  {
    value: "UTILITY",
    label: "Utility Scale",
    description: "Large-scale power generation",
    range: "10 MW - 100 MW",
  },
  {
    value: "HYPERSCALE",
    label: "Hyperscale",
    description: "Massive installations",
    range: "> 100 MW",
  },
];

export function ComponentCreationWizard({
  open,
  onOpenChange,
}: ComponentCreationWizardProps) {
  const [currentStep, setCurrentStep] = React.useState(0);
  const [isAIProcessing, setIsAIProcessing] = React.useState(false);
  const queryClient = useQueryClient();

  const form = useForm<ComponentFormData>({
    resolver: zodResolver(componentSchema),
    defaultValues: {
      brand: "",
      part_number: "",
      rating_w: 0,
      description: "",
      datasheet_url: "",
      classification: {
        unspsc: "",
        eclass: "",
        hs_code: "",
        gtin: "",
      },
    },
  });

  const createComponentMutation = useMutation({
    mutationFn: async (data: ComponentFormData) => {
      const request: any = {
        brand: data.brand,
        part_number: data.part_number,
        rating_w: data.rating_w,
        category: data.category,
        subcategory: data.subcategory,
        domain: data.domain,
        scale: data.scale,
        classification: data.classification,
      };
      return componentAPI.createComponent(request);
    },
    onSuccess: (data) => {
      toast.success("Component created successfully!");
      queryClient.invalidateQueries({ queryKey: ["components"] });
      onOpenChange(false);
      form.reset();
      setCurrentStep(0);
    },
    onError: (error: any) => {
      console.error("Failed to create component:", error);
      toast.error(error.message || "Failed to create component");
    },
  });

  const steps = [
    {
      title: "Basic Information",
      description: "Component identity and basic details",
    },
    {
      title: "Classification",
      description: "Category and technical classification",
    },
    {
      title: "Documentation",
      description: "Datasheets and additional information",
    },
    {
      title: "Review & Create",
      description: "Review all details and create component",
    },
  ];

  const nextStep = () => {
    if (currentStep < steps.length - 1) {
      setCurrentStep(currentStep + 1);
    }
  };

  const prevStep = () => {
    if (currentStep > 0) {
      setCurrentStep(currentStep - 1);
    }
  };

  const onSubmit = (data: ComponentFormData) => {
    createComponentMutation.mutate(data);
  };

  const handleAIDatasheetParse = async () => {
    const datasheetUrl = form.getValues("datasheet_url");
    if (!datasheetUrl) {
      toast.error("Please enter a datasheet URL first");
      return;
    }

    setIsAIProcessing(true);
    try {
      // TODO: Integrate with AI orchestrator for datasheet parsing
      await new Promise((resolve) => setTimeout(resolve, 3000)); // Mock delay

      // Mock AI-extracted data
      form.setValue("rating_w", 400);
      form.setValue("category", "generation");
      form.setValue("subcategory", "pv_module");
      form.setValue("classification.unspsc", "26111701");

      toast.success(
        "Datasheet parsed successfully! Review the extracted information.",
      );
    } catch (error) {
      toast.error("Failed to parse datasheet");
    } finally {
      setIsAIProcessing(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[800px] max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Create New Component</DialogTitle>
          <DialogDescription>
            Add a new component to your library following ODL-SD v4.1 standards
          </DialogDescription>
        </DialogHeader>

        {/* Progress Steps */}
        <div className="flex items-center justify-between mb-6">
          {steps.map((step, index) => (
            <div key={index} className="flex items-center">
              <div
                className={`flex items-center justify-center w-8 h-8 rounded-full border-2 ${
                  index <= currentStep
                    ? "bg-primary border-primary text-primary-foreground"
                    : "border-muted-foreground text-muted-foreground"
                }`}
              >
                {index < currentStep ? (
                  <Check className="w-4 h-4" />
                ) : (
                  index + 1
                )}
              </div>
              {index < steps.length - 1 && (
                <div
                  className={`w-12 h-0.5 mx-2 ${
                    index < currentStep ? "bg-primary" : "bg-muted"
                  }`}
                />
              )}
            </div>
          ))}
        </div>

        <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
          {/* Step 1: Basic Information */}
          {currentStep === 0 && (
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="brand">Brand *</Label>
                  <Input
                    id="brand"
                    placeholder="e.g., Tesla, Jinko Solar"
                    {...form.register("brand")}
                  />
                  {form.formState.errors.brand && (
                    <p className="text-sm text-red-600">
                      {form.formState.errors.brand.message}
                    </p>
                  )}
                </div>
                <div className="space-y-2">
                  <Label htmlFor="part_number">Part Number *</Label>
                  <Input
                    id="part_number"
                    placeholder="e.g., JKM400M-54HL4-V"
                    {...form.register("part_number")}
                  />
                  {form.formState.errors.part_number && (
                    <p className="text-sm text-red-600">
                      {form.formState.errors.part_number.message}
                    </p>
                  )}
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="rating_w">Power Rating (Watts) *</Label>
                <Input
                  id="rating_w"
                  type="number"
                  placeholder="e.g., 400"
                  {...form.register("rating_w", { valueAsNumber: true })}
                />
                {form.formState.errors.rating_w && (
                  <p className="text-sm text-red-600">
                    {form.formState.errors.rating_w.message}
                  </p>
                )}
              </div>

              <div className="space-y-2">
                <Label htmlFor="description">Description</Label>
                <Textarea
                  id="description"
                  placeholder="Brief description of the component..."
                  rows={3}
                  {...form.register("description")}
                />
              </div>
            </div>
          )}

          {/* Step 2: Classification */}
          {currentStep === 1 && (
            <div className="space-y-6">
              <div className="space-y-3">
                <Label>Category</Label>
                <div className="grid grid-cols-2 gap-3">
                  {categoryOptions.map((option) => {
                    const Icon = option.icon;
                    const isSelected = form.watch("category") === option.value;
                    return (
                      <Card
                        key={option.value}
                        className={`cursor-pointer transition-colors ${
                          isSelected
                            ? "ring-2 ring-primary"
                            : "hover:bg-muted/50"
                        }`}
                        onClick={() =>
                          form.setValue("category", option.value as any)
                        }
                      >
                        <CardContent className="p-3">
                          <div className="flex items-center space-x-2">
                            <Icon className="h-4 w-4" />
                            <div>
                              <div className="font-medium text-sm">
                                {option.label}
                              </div>
                              <div className="text-xs text-muted-foreground">
                                {option.description}
                              </div>
                            </div>
                          </div>
                        </CardContent>
                      </Card>
                    );
                  })}
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="subcategory">Subcategory</Label>
                <Input
                  id="subcategory"
                  placeholder="e.g., pv_module, string_inverter"
                  {...form.register("subcategory")}
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-3">
                  <Label>Domain</Label>
                  <Select
                    value={form.watch("domain") || ""}
                    onValueChange={(value) =>
                      form.setValue("domain", value as any)
                    }
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Select domain" />
                    </SelectTrigger>
                    <SelectContent>
                      {domainOptions.map((option) => {
                        const Icon = option.icon;
                        return (
                          <SelectItem key={option.value} value={option.value}>
                            <div className="flex items-center space-x-2">
                              <Icon className={`h-4 w-4 ${option.color}`} />
                              <span>{option.label}</span>
                            </div>
                          </SelectItem>
                        );
                      })}
                    </SelectContent>
                  </Select>
                </div>

                <div className="space-y-3">
                  <Label>Scale</Label>
                  <Select
                    value={form.watch("scale") || ""}
                    onValueChange={(value) =>
                      form.setValue("scale", value as any)
                    }
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Select scale" />
                    </SelectTrigger>
                    <SelectContent>
                      {scaleOptions.map((option) => (
                        <SelectItem key={option.value} value={option.value}>
                          <div className="flex items-center justify-between w-full">
                            <div>
                              <div className="font-medium">{option.label}</div>
                              <div className="text-xs text-muted-foreground">
                                {option.description}
                              </div>
                            </div>
                            <div className="text-xs text-muted-foreground ml-2">
                              {option.range}
                            </div>
                          </div>
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>

              {/* Classification Codes */}
              <div className="space-y-4">
                <Label>Classification Codes</Label>
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="unspsc">UNSPSC Code</Label>
                    <Input
                      id="unspsc"
                      placeholder="e.g., 26111701"
                      {...form.register("classification.unspsc")}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="hs_code">HS Code</Label>
                    <Input
                      id="hs_code"
                      placeholder="e.g., 854140"
                      {...form.register("classification.hs_code")}
                    />
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="eclass">eCl@ss Code</Label>
                    <Input
                      id="eclass"
                      placeholder="e.g., 27-02-26-01"
                      {...form.register("classification.eclass")}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="gtin">GTIN</Label>
                    <Input
                      id="gtin"
                      placeholder="e.g., 1234567890123"
                      {...form.register("classification.gtin")}
                    />
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Step 3: Documentation */}
          {currentStep === 2 && (
            <div className="space-y-6">
              <div className="space-y-4">
                <Label htmlFor="datasheet_url">Datasheet URL</Label>
                <div className="flex space-x-2">
                  <Input
                    id="datasheet_url"
                    placeholder="https://example.com/datasheet.pdf"
                    {...form.register("datasheet_url")}
                    className="flex-1"
                  />
                  <Button
                    type="button"
                    variant="outline"
                    onClick={handleAIDatasheetParse}
                    disabled={isAIProcessing}
                  >
                    {isAIProcessing ? (
                      <Loader2 className="h-4 w-4 animate-spin" />
                    ) : (
                      <Upload className="h-4 w-4" />
                    )}
                    AI Parse
                  </Button>
                </div>
                <p className="text-sm text-muted-foreground">
                  Our AI will extract technical specifications from the
                  datasheet automatically
                </p>
              </div>

              {isAIProcessing && (
                <Card>
                  <CardContent className="p-4">
                    <div className="flex items-center space-x-2">
                      <Loader2 className="h-4 w-4 animate-spin" />
                      <span>AI is processing your datasheet...</span>
                    </div>
                  </CardContent>
                </Card>
              )}

              <div className="space-y-4">
                <Label>File Upload</Label>
                <div className="border-2 border-dashed border-muted-foreground/25 rounded-lg p-6">
                  <div className="text-center">
                    <Upload className="mx-auto h-12 w-12 text-muted-foreground" />
                    <div className="mt-2">
                      <Button type="button" variant="outline">
                        Upload Datasheet
                      </Button>
                    </div>
                    <p className="text-sm text-muted-foreground mt-2">
                      PDF, DOC, or image files up to 10MB
                    </p>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Step 4: Review */}
          {currentStep === 3 && (
            <div className="space-y-6">
              <Card>
                <CardHeader>
                  <CardTitle>Review Component Details</CardTitle>
                  <CardDescription>
                    Please review all information before creating the component
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <Label className="text-sm font-medium text-muted-foreground">
                        Component ID
                      </Label>
                      <p className="font-mono text-sm">
                        CMP:{form.watch("brand")}:{form.watch("part_number")}:
                        {form.watch("rating_w")}W:REV1
                      </p>
                    </div>
                    <div>
                      <Label className="text-sm font-medium text-muted-foreground">
                        Name
                      </Label>
                      <p className="font-mono text-sm">
                        {form.watch("brand")}_{form.watch("part_number")}_
                        {form.watch("rating_w")}W
                      </p>
                    </div>
                  </div>

                  <div className="grid grid-cols-3 gap-4">
                    <div>
                      <Label className="text-sm font-medium text-muted-foreground">
                        Category
                      </Label>
                      <p>{form.watch("category") || "Not specified"}</p>
                    </div>
                    <div>
                      <Label className="text-sm font-medium text-muted-foreground">
                        Domain
                      </Label>
                      <p>{form.watch("domain") || "Not specified"}</p>
                    </div>
                    <div>
                      <Label className="text-sm font-medium text-muted-foreground">
                        Scale
                      </Label>
                      <p>{form.watch("scale") || "Not specified"}</p>
                    </div>
                  </div>

                  {form.watch("description") && (
                    <div>
                      <Label className="text-sm font-medium text-muted-foreground">
                        Description
                      </Label>
                      <p className="text-sm">{form.watch("description")}</p>
                    </div>
                  )}
                </CardContent>
              </Card>
            </div>
          )}

          <DialogFooter className="flex justify-between">
            <div>
              {currentStep > 0 && (
                <Button type="button" variant="outline" onClick={prevStep}>
                  <ChevronLeft className="w-4 h-4 mr-2" />
                  Previous
                </Button>
              )}
            </div>
            <div className="flex space-x-2">
              <Button
                type="button"
                variant="outline"
                onClick={() => onOpenChange(false)}
                disabled={createComponentMutation.isPending}
              >
                Cancel
              </Button>
              {currentStep < steps.length - 1 ? (
                <Button type="button" onClick={nextStep}>
                  Next
                  <ChevronRight className="w-4 h-4 ml-2" />
                </Button>
              ) : (
                <Button
                  type="submit"
                  disabled={createComponentMutation.isPending}
                >
                  {createComponentMutation.isPending && (
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  )}
                  Create Component
                </Button>
              )}
            </div>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
