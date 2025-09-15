'use client'

import { useState } from 'react'
import { useMutation, useQueryClient, useQuery } from '@tanstack/react-query'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  Button,
  Input,
  Label,
  Textarea,
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  Badge,
  Separator,
  Progress
} from '@originfd/ui'
import { RFQRequest, RFQSpecification, EvaluationCriteria, ComponentResponse } from '@/lib/types'
import { Plus, Trash2, Calendar, DollarSign, FileText, Users } from 'lucide-react'

interface RFQCreationWizardProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  selectedComponent?: ComponentResponse
}

interface RFQFormData {
  title: string
  description: string
  component_id: string
  quantity: number
  unit_of_measure: string
  delivery_location: string
  required_delivery_date: string
  response_deadline: string
  budget_range?: {
    min: number
    max: number
    currency: string
  }
  specifications: RFQSpecification[]
  evaluation_criteria: EvaluationCriteria
}

const initialFormData: RFQFormData = {
  title: '',
  description: '',
  component_id: '',
  quantity: 1,
  unit_of_measure: 'pcs',
  delivery_location: '',
  required_delivery_date: '',
  response_deadline: '',
  specifications: [
    {
      category: 'Power Rating',
      requirement: '',
      mandatory: true,
      measurement_unit: 'W'
    }
  ],
  evaluation_criteria: {
    price_weight: 40,
    delivery_weight: 20,
    quality_weight: 25,
    experience_weight: 10,
    sustainability_weight: 5,
    total_weight: 100
  }
}

export default function RFQCreationWizard({ open, onOpenChange, selectedComponent }: RFQCreationWizardProps) {
  const queryClient = useQueryClient()
  const [currentStep, setCurrentStep] = useState(1)
  const [formData, setFormData] = useState<RFQFormData>(() => ({
    ...initialFormData,
    component_id: selectedComponent?.id || '',
    title: selectedComponent
      ? `RFQ for ${selectedComponent.component_management?.component_identity?.brand} ${selectedComponent.component_management?.component_identity?.part_number}`
      : ''
  }))

  // Fetch available components for selection
  const { data: components } = useQuery({
    queryKey: ['components-available'],
    queryFn: async () => {
      const response = await fetch('/api/bridge/components?status=available')
      if (!response.ok) throw new Error('Failed to fetch components')
      return response.json()
    },
    enabled: !selectedComponent
  })

  // Create RFQ mutation
  const createRFQMutation = useMutation({
    mutationFn: async (data: RFQFormData) => {
      const response = await fetch('/api/bridge/rfq', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ...data,
          requester_id: 'current_user',
          status: 'draft'
        })
      })
      if (!response.ok) throw new Error('Failed to create RFQ')
      return response.json()
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['rfqs'] })
      onOpenChange(false)
      setCurrentStep(1)
      setFormData(initialFormData)
    }
  })

  const updateFormData = (field: string, value: any) => {
    setFormData(prev => ({ ...prev, [field]: value }))
  }

  const addSpecification = () => {
    setFormData(prev => ({
      ...prev,
      specifications: [...prev.specifications, {
        category: '',
        requirement: '',
        mandatory: false,
        measurement_unit: ''
      }]
    }))
  }

  const removeSpecification = (index: number) => {
    setFormData(prev => ({
      ...prev,
      specifications: prev.specifications.filter((_, i) => i !== index)
    }))
  }

  const updateSpecification = (index: number, field: string, value: any) => {
    setFormData(prev => ({
      ...prev,
      specifications: prev.specifications.map((spec, i) =>
        i === index ? { ...spec, [field]: value } : spec
      )
    }))
  }

  const updateEvaluationCriteria = (field: string, value: number) => {
    setFormData(prev => ({
      ...prev,
      evaluation_criteria: {
        ...prev.evaluation_criteria,
        [field]: value,
        total_weight: Object.values({
          ...prev.evaluation_criteria,
          [field]: value
        }).reduce((sum, weight) => field === 'total_weight' ? sum : sum + weight, 0)
      }
    }))
  }

  const validateStep = (step: number) => {
    switch (step) {
      case 1:
        return !!(formData.title && formData.component_id && formData.quantity > 0)
      case 2:
        return !!(formData.delivery_location && formData.required_delivery_date && formData.response_deadline)
      case 3:
        return formData.specifications.every(spec => spec.category && spec.requirement)
      case 4:
        return Math.abs(formData.evaluation_criteria.total_weight - 100) < 0.01
      default:
        return true
    }
  }

  const nextStep = () => {
    if (validateStep(currentStep) && currentStep < 5) {
      setCurrentStep(currentStep + 1)
    }
  }

  const prevStep = () => {
    if (currentStep > 1) {
      setCurrentStep(currentStep - 1)
    }
  }

  const handleSubmit = () => {
    if (validateStep(4)) {
      createRFQMutation.mutate(formData)
    }
  }

  const selectedComponentData = components?.find((comp: ComponentResponse) => comp.id === formData.component_id) || selectedComponent

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-4xl max-h-[80vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Create New RFQ - Step {currentStep} of 4</DialogTitle>
        </DialogHeader>

        {/* Progress */}
        <div className="mb-6">
          <Progress value={(currentStep / 4) * 100} className="h-2" />
          <div className="flex justify-between mt-2 text-sm text-muted-foreground">
            <span>Basic Information</span>
            <span>Delivery Details</span>
            <span>Specifications</span>
            <span>Evaluation</span>
          </div>
        </div>

        {/* Step 1: Basic Information */}
        {currentStep === 1 && (
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label htmlFor="title">RFQ Title *</Label>
                <Input
                  id="title"
                  value={formData.title}
                  onChange={(e) => updateFormData('title', e.target.value)}
                  placeholder="Enter RFQ title"
                />
              </div>
              <div>
                <Label htmlFor="component">Component *</Label>
                {selectedComponent ? (
                  <div className="p-2 border rounded-md bg-muted">
                    <div className="text-sm font-medium">
                      {selectedComponent.component_management?.component_identity?.brand} {selectedComponent.component_management?.component_identity?.part_number}
                    </div>
                    <div className="text-xs text-muted-foreground">
                      {selectedComponent.component_management?.component_identity?.name}
                    </div>
                  </div>
                ) : (
                  <Select value={formData.component_id} onValueChange={(value) => updateFormData('component_id', value)}>
                    <SelectTrigger>
                      <SelectValue placeholder="Select component" />
                    </SelectTrigger>
                    <SelectContent>
                      {components?.map((comp: ComponentResponse) => (
                        <SelectItem key={comp.id} value={comp.id}>
                          {comp.component_management?.component_identity?.brand} {comp.component_management?.component_identity?.part_number}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                )}
              </div>
            </div>

            <div>
              <Label htmlFor="description">Description</Label>
              <Textarea
                id="description"
                value={formData.description}
                onChange={(e) => updateFormData('description', e.target.value)}
                placeholder="Describe the requirements and context for this RFQ"
                rows={3}
              />
            </div>

            <div className="grid grid-cols-3 gap-4">
              <div>
                <Label htmlFor="quantity">Quantity *</Label>
                <Input
                  id="quantity"
                  type="number"
                  value={formData.quantity}
                  onChange={(e) => updateFormData('quantity', parseInt(e.target.value) || 0)}
                  min="1"
                />
              </div>
              <div>
                <Label htmlFor="uom">Unit of Measure</Label>
                <Select value={formData.unit_of_measure} onValueChange={(value) => updateFormData('unit_of_measure', value)}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="pcs">Pieces</SelectItem>
                    <SelectItem value="m">Meters</SelectItem>
                    <SelectItem value="kg">Kilograms</SelectItem>
                    <SelectItem value="set">Sets</SelectItem>
                    <SelectItem value="roll">Rolls</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div>
                <Label>Budget Range (Optional)</Label>
                <div className="flex space-x-2">
                  <Input
                    type="number"
                    placeholder="Min"
                    value={formData.budget_range?.min || ''}
                    onChange={(e) => updateFormData('budget_range', {
                      ...formData.budget_range,
                      min: parseFloat(e.target.value) || 0,
                      currency: 'USD'
                    })}
                  />
                  <Input
                    type="number"
                    placeholder="Max"
                    value={formData.budget_range?.max || ''}
                    onChange={(e) => updateFormData('budget_range', {
                      ...formData.budget_range,
                      max: parseFloat(e.target.value) || 0,
                      currency: 'USD'
                    })}
                  />
                </div>
              </div>
            </div>

            {selectedComponentData && (
              <Card>
                <CardHeader>
                  <CardTitle className="text-sm">Selected Component Details</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <span className="text-muted-foreground">Brand:</span> {selectedComponentData.component_management?.component_identity?.brand}
                    </div>
                    <div>
                      <span className="text-muted-foreground">Part Number:</span> {selectedComponentData.component_management?.component_identity?.part_number}
                    </div>
                    <div>
                      <span className="text-muted-foreground">Rating:</span> {selectedComponentData.component_management?.component_identity?.rating_w}W
                    </div>
                    <div>
                      <span className="text-muted-foreground">Status:</span>
                      <Badge variant="outline" className="ml-2">
                        {selectedComponentData.component_management?.status}
                      </Badge>
                    </div>
                  </div>
                </CardContent>
              </Card>
            )}
          </div>
        )}

        {/* Step 2: Delivery Details */}
        {currentStep === 2 && (
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label htmlFor="delivery_location">Delivery Location *</Label>
                <Input
                  id="delivery_location"
                  value={formData.delivery_location}
                  onChange={(e) => updateFormData('delivery_location', e.target.value)}
                  placeholder="Enter delivery address"
                />
              </div>
              <div>
                <Label htmlFor="required_delivery_date">Required Delivery Date *</Label>
                <Input
                  id="required_delivery_date"
                  type="date"
                  value={formData.required_delivery_date}
                  onChange={(e) => updateFormData('required_delivery_date', e.target.value)}
                />
              </div>
            </div>

            <div>
              <Label htmlFor="response_deadline">Response Deadline *</Label>
              <Input
                id="response_deadline"
                type="datetime-local"
                value={formData.response_deadline}
                onChange={(e) => updateFormData('response_deadline', e.target.value)}
              />
              <div className="text-xs text-muted-foreground mt-1">
                When suppliers must submit their bids by
              </div>
            </div>
          </div>
        )}

        {/* Step 3: Specifications */}
        {currentStep === 3 && (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-medium">Technical Specifications</h3>
              <Button onClick={addSpecification} size="sm" variant="outline">
                <Plus className="h-4 w-4 mr-2" />
                Add Specification
              </Button>
            </div>

            <div className="space-y-3">
              {formData.specifications.map((spec, index) => (
                <Card key={index}>
                  <CardContent className="p-4">
                    <div className="flex items-start space-x-4">
                      <div className="flex-1 grid grid-cols-2 gap-4">
                        <div>
                          <Label>Category *</Label>
                          <Input
                            value={spec.category}
                            onChange={(e) => updateSpecification(index, 'category', e.target.value)}
                            placeholder="e.g., Power Rating"
                          />
                        </div>
                        <div>
                          <Label>Measurement Unit</Label>
                          <Input
                            value={spec.measurement_unit || ''}
                            onChange={(e) => updateSpecification(index, 'measurement_unit', e.target.value)}
                            placeholder="e.g., W, V, A"
                          />
                        </div>
                        <div className="col-span-2">
                          <Label>Requirement *</Label>
                          <Textarea
                            value={spec.requirement}
                            onChange={(e) => updateSpecification(index, 'requirement', e.target.value)}
                            placeholder="Describe the specific requirement"
                            rows={2}
                          />
                        </div>
                        <div className="flex items-center space-x-2">
                          <input
                            type="checkbox"
                            id={`mandatory-${index}`}
                            checked={spec.mandatory}
                            onChange={(e) => updateSpecification(index, 'mandatory', e.target.checked)}
                          />
                          <Label htmlFor={`mandatory-${index}`}>Mandatory requirement</Label>
                        </div>
                      </div>
                      {formData.specifications.length > 1 && (
                        <Button
                          onClick={() => removeSpecification(index)}
                          size="sm"
                          variant="ghost"
                          className="text-destructive hover:text-destructive"
                        >
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      )}
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </div>
        )}

        {/* Step 4: Evaluation Criteria */}
        {currentStep === 4 && (
          <div className="space-y-4">
            <h3 className="text-lg font-medium">Bid Evaluation Criteria</h3>
            <div className="text-sm text-muted-foreground">
              Set the weights for evaluating bids. Total must equal 100%.
            </div>

            <div className="grid gap-4">
              {[
                { key: 'price_weight', label: 'Price', description: 'Cost competitiveness' },
                { key: 'delivery_weight', label: 'Delivery', description: 'Timeline and logistics' },
                { key: 'quality_weight', label: 'Quality', description: 'Product quality and certifications' },
                { key: 'experience_weight', label: 'Experience', description: 'Supplier track record' },
                { key: 'sustainability_weight', label: 'Sustainability', description: 'Environmental impact' }
              ].map(({ key, label, description }) => (
                <div key={key} className="flex items-center space-x-4">
                  <div className="flex-1">
                    <Label>{label}</Label>
                    <div className="text-xs text-muted-foreground">{description}</div>
                  </div>
                  <div className="w-20">
                    <Input
                      type="number"
                      min="0"
                      max="100"
                      value={formData.evaluation_criteria[key as keyof EvaluationCriteria] as number}
                      onChange={(e) => updateEvaluationCriteria(key, parseInt(e.target.value) || 0)}
                    />
                  </div>
                  <div className="w-12 text-sm text-muted-foreground">%</div>
                </div>
              ))}
            </div>

            <Separator />

            <div className="flex items-center justify-between text-sm">
              <span>Total Weight:</span>
              <span className={formData.evaluation_criteria.total_weight === 100 ? 'text-green-600' : 'text-red-600'}>
                {formData.evaluation_criteria.total_weight}%
              </span>
            </div>

            {formData.evaluation_criteria.total_weight !== 100 && (
              <div className="text-sm text-red-600">
                Total weight must equal 100% to proceed
              </div>
            )}
          </div>
        )}

        {/* Navigation */}
        <div className="flex items-center justify-between pt-4 border-t">
          <Button
            variant="outline"
            onClick={prevStep}
            disabled={currentStep === 1}
          >
            Previous
          </Button>

          <div className="text-sm text-muted-foreground">
            Step {currentStep} of 4
          </div>

          {currentStep < 4 ? (
            <Button
              onClick={nextStep}
              disabled={!validateStep(currentStep)}
            >
              Next
            </Button>
          ) : (
            <Button
              onClick={handleSubmit}
              disabled={!validateStep(4) || createRFQMutation.isPending}
            >
              {createRFQMutation.isPending ? 'Creating...' : 'Create RFQ'}
            </Button>
          )}
        </div>
      </DialogContent>
    </Dialog>
  )
}