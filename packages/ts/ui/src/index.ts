/**
 * OriginFD UI Component Library
 * Shared components based on shadcn/ui and Radix UI primitives
 */

// Base components
export * from './components/ui/button'
export * from './components/ui/card'
export * from './components/ui/input'
export * from './components/ui/label'
export * from './components/ui/select'
export * from './components/ui/textarea'
export * from './components/ui/dialog'
export * from './components/ui/sheet'
export * from './components/ui/tabs'
export * from './components/ui/avatar'
export * from './components/ui/badge'
export * from './components/ui/progress'
export * from './components/ui/separator'
export * from './components/ui/switch'
export * from './components/ui/tooltip'
export * from './components/ui/dropdown-menu'
export * from './components/ui/toast'
export * from './components/ui/alert-dialog'

// Composite components
export * from './components/layout/header'
export * from './components/layout/sidebar'
export * from './components/layout/page-layout'
export * from './components/data-display/data-table'
export * from './components/data-display/status-badge'
export * from './components/data-display/metric-card'
export * from './components/feedback/loading-spinner'
export * from './components/feedback/error-boundary'
export * from './components/feedback/empty-state'
export * from './components/forms/form-field'
export * from './components/forms/search-input'

// OriginFD specific components
export * from './components/originfd/document-card'
export * from './components/originfd/project-selector'
export * from './components/originfd/task-status'
export * from './components/originfd/patch-viewer'

// Utilities
export * from './lib/utils'
export * from './lib/cn'

// Hooks
export * from './hooks/use-toast'
export * from './hooks/use-local-storage'