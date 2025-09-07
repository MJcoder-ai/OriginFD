'use client'

import * as React from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import * as z from 'zod'
import { toast } from 'react-hot-toast'
import { 
  User, 
  Bell, 
  Shield, 
  Palette, 
  Globe, 
  CreditCard,
  Key,
  Users,
  Building,
  Save
} from 'lucide-react'

import {
  Button,
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
  Input,
  Label,
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
  Textarea,
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from '@originfd/ui'
import { useAuth } from '@/lib/auth/auth-provider'

const profileSchema = z.object({
  full_name: z.string().min(1, 'Full name is required'),
  email: z.string().email('Invalid email address'),
  phone: z.string().optional(),
  company: z.string().optional(),
  role: z.string().optional(),
  bio: z.string().optional(),
})

const preferencesSchema = z.object({
  theme: z.enum(['light', 'dark', 'system']),
  language: z.string(),
  timezone: z.string(),
  currency: z.string(),
  units: z.enum(['metric', 'imperial']),
})

const notificationSchema = z.object({
  email_notifications: z.boolean(),
  push_notifications: z.boolean(),
  project_updates: z.boolean(),
  system_alerts: z.boolean(),
  marketing_emails: z.boolean(),
})

type ProfileFormData = z.infer<typeof profileSchema>
type PreferencesFormData = z.infer<typeof preferencesSchema>
type NotificationFormData = z.infer<typeof notificationSchema>

export default function SettingsPage() {
  const { user } = useAuth()

  const profileForm = useForm<ProfileFormData>({
    resolver: zodResolver(profileSchema),
    defaultValues: {
      full_name: user?.full_name || '',
      email: user?.email || '',
      phone: '',
      company: '',
      role: '',
      bio: '',
    },
  })

  const preferencesForm = useForm<PreferencesFormData>({
    resolver: zodResolver(preferencesSchema),
    defaultValues: {
      theme: 'system',
      language: 'en',
      timezone: 'UTC',
      currency: 'USD',
      units: 'metric',
    },
  })

  const notificationForm = useForm<NotificationFormData>({
    resolver: zodResolver(notificationSchema),
    defaultValues: {
      email_notifications: true,
      push_notifications: false,
      project_updates: true,
      system_alerts: true,
      marketing_emails: false,
    },
  })

  const onProfileSubmit = (data: ProfileFormData) => {
    console.log('Profile update:', data)
    toast.success('Profile updated successfully!')
  }

  const onPreferencesSubmit = (data: PreferencesFormData) => {
    console.log('Preferences update:', data)
    toast.success('Preferences updated successfully!')
  }

  const onNotificationSubmit = (data: NotificationFormData) => {
    console.log('Notification settings update:', data)
    toast.success('Notification settings updated!')
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Settings</h1>
        <p className="text-muted-foreground">
          Manage your account settings and preferences
        </p>
      </div>

      {/* Settings Tabs */}
      <Tabs defaultValue="profile" className="space-y-6">
        <TabsList className="grid w-full grid-cols-6">
          <TabsTrigger value="profile" className="flex items-center gap-2">
            <User className="h-4 w-4" />
            Profile
          </TabsTrigger>
          <TabsTrigger value="preferences" className="flex items-center gap-2">
            <Palette className="h-4 w-4" />
            Preferences
          </TabsTrigger>
          <TabsTrigger value="notifications" className="flex items-center gap-2">
            <Bell className="h-4 w-4" />
            Notifications
          </TabsTrigger>
          <TabsTrigger value="security" className="flex items-center gap-2">
            <Shield className="h-4 w-4" />
            Security
          </TabsTrigger>
          <TabsTrigger value="team" className="flex items-center gap-2">
            <Users className="h-4 w-4" />
            Team
          </TabsTrigger>
          <TabsTrigger value="billing" className="flex items-center gap-2">
            <CreditCard className="h-4 w-4" />
            Billing
          </TabsTrigger>
        </TabsList>

        {/* Profile Tab */}
        <TabsContent value="profile" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Profile Information</CardTitle>
              <CardDescription>
                Update your personal information and profile details
              </CardDescription>
            </CardHeader>
            <CardContent>
              <form onSubmit={profileForm.handleSubmit(onProfileSubmit)} className="space-y-4">
                <div className="grid gap-4 md:grid-cols-2">
                  <div className="space-y-2">
                    <Label htmlFor="full_name">Full Name</Label>
                    <Input
                      id="full_name"
                      {...profileForm.register('full_name')}
                    />
                    {profileForm.formState.errors.full_name && (
                      <p className="text-sm text-red-600">
                        {profileForm.formState.errors.full_name.message}
                      </p>
                    )}
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="email">Email</Label>
                    <Input
                      id="email"
                      type="email"
                      {...profileForm.register('email')}
                    />
                    {profileForm.formState.errors.email && (
                      <p className="text-sm text-red-600">
                        {profileForm.formState.errors.email.message}
                      </p>
                    )}
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="phone">Phone Number</Label>
                    <Input
                      id="phone"
                      {...profileForm.register('phone')}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="company">Company</Label>
                    <Input
                      id="company"
                      {...profileForm.register('company')}
                    />
                  </div>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="role">Role</Label>
                  <Input
                    id="role"
                    {...profileForm.register('role')}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="bio">Bio</Label>
                  <Textarea
                    id="bio"
                    rows={3}
                    placeholder="Tell us about yourself"
                    {...profileForm.register('bio')}
                  />
                </div>
                <Button type="submit" className="gap-2">
                  <Save className="h-4 w-4" />
                  Save Profile
                </Button>
              </form>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Preferences Tab */}
        <TabsContent value="preferences" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Application Preferences</CardTitle>
              <CardDescription>
                Customize your application experience
              </CardDescription>
            </CardHeader>
            <CardContent>
              <form onSubmit={preferencesForm.handleSubmit(onPreferencesSubmit)} className="space-y-4">
                <div className="grid gap-4 md:grid-cols-2">
                  <div className="space-y-2">
                    <Label>Theme</Label>
                    <Select
                      value={preferencesForm.watch('theme')}
                      onValueChange={(value) => preferencesForm.setValue('theme', value as any)}
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="light">Light</SelectItem>
                        <SelectItem value="dark">Dark</SelectItem>
                        <SelectItem value="system">System</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-2">
                    <Label>Language</Label>
                    <Select
                      value={preferencesForm.watch('language')}
                      onValueChange={(value) => preferencesForm.setValue('language', value)}
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="en">English</SelectItem>
                        <SelectItem value="es">Spanish</SelectItem>
                        <SelectItem value="fr">French</SelectItem>
                        <SelectItem value="de">German</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-2">
                    <Label>Timezone</Label>
                    <Select
                      value={preferencesForm.watch('timezone')}
                      onValueChange={(value) => preferencesForm.setValue('timezone', value)}
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="UTC">UTC</SelectItem>
                        <SelectItem value="America/New_York">Eastern Time</SelectItem>
                        <SelectItem value="America/Chicago">Central Time</SelectItem>
                        <SelectItem value="America/Denver">Mountain Time</SelectItem>
                        <SelectItem value="America/Los_Angeles">Pacific Time</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-2">
                    <Label>Currency</Label>
                    <Select
                      value={preferencesForm.watch('currency')}
                      onValueChange={(value) => preferencesForm.setValue('currency', value)}
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="USD">USD ($)</SelectItem>
                        <SelectItem value="EUR">EUR (€)</SelectItem>
                        <SelectItem value="GBP">GBP (£)</SelectItem>
                        <SelectItem value="CAD">CAD (C$)</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>
                <div className="space-y-2">
                  <Label>Unit System</Label>
                  <Select
                    value={preferencesForm.watch('units')}
                    onValueChange={(value) => preferencesForm.setValue('units', value as any)}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="metric">Metric (SI)</SelectItem>
                      <SelectItem value="imperial">Imperial</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <Button type="submit" className="gap-2">
                  <Save className="h-4 w-4" />
                  Save Preferences
                </Button>
              </form>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Notifications Tab */}
        <TabsContent value="notifications" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Notification Settings</CardTitle>
              <CardDescription>
                Choose how you want to be notified about updates
              </CardDescription>
            </CardHeader>
            <CardContent>
              <form onSubmit={notificationForm.handleSubmit(onNotificationSubmit)} className="space-y-4">
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="font-medium">Email Notifications</p>
                      <p className="text-sm text-muted-foreground">Receive notifications via email</p>
                    </div>
                    {/* TODO: Add Switch component */}
                    <Button variant="outline" size="sm">Toggle</Button>
                  </div>
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="font-medium">Push Notifications</p>
                      <p className="text-sm text-muted-foreground">Receive push notifications in your browser</p>
                    </div>
                    <Button variant="outline" size="sm">Toggle</Button>
                  </div>
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="font-medium">Project Updates</p>
                      <p className="text-sm text-muted-foreground">Get notified about project changes</p>
                    </div>
                    <Button variant="outline" size="sm">Toggle</Button>
                  </div>
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="font-medium">System Alerts</p>
                      <p className="text-sm text-muted-foreground">Important system notifications</p>
                    </div>
                    <Button variant="outline" size="sm">Toggle</Button>
                  </div>
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="font-medium">Marketing Emails</p>
                      <p className="text-sm text-muted-foreground">Product updates and news</p>
                    </div>
                    <Button variant="outline" size="sm">Toggle</Button>
                  </div>
                </div>
                <Button type="submit" className="gap-2">
                  <Save className="h-4 w-4" />
                  Save Notification Settings
                </Button>
              </form>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Placeholder tabs */}
        <TabsContent value="security" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Key className="h-5 w-5" />
                Security Settings
              </CardTitle>
              <CardDescription>
                Manage your account security and authentication
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="text-center py-12">
                <Shield className="mx-auto h-12 w-12 text-muted-foreground" />
                <h3 className="mt-2 text-sm font-semibold text-gray-900">Security Settings</h3>
                <p className="mt-1 text-sm text-muted-foreground">
                  Security features are coming soon.
                </p>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="team" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Building className="h-5 w-5" />
                Team Management
              </CardTitle>
              <CardDescription>
                Manage your team members and organization
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="text-center py-12">
                <Users className="mx-auto h-12 w-12 text-muted-foreground" />
                <h3 className="mt-2 text-sm font-semibold text-gray-900">Team Features</h3>
                <p className="mt-1 text-sm text-muted-foreground">
                  Team management features are coming soon.
                </p>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="billing" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <CreditCard className="h-5 w-5" />
                Billing & Subscription
              </CardTitle>
              <CardDescription>
                Manage your subscription and billing information
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="text-center py-12">
                <CreditCard className="mx-auto h-12 w-12 text-muted-foreground" />
                <h3 className="mt-2 text-sm font-semibold text-gray-900">Billing Features</h3>
                <p className="mt-1 text-sm text-muted-foreground">
                  Billing and subscription features are coming soon.
                </p>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}
