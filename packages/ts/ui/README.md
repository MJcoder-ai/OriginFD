# OriginFD UI

Shared React component library for OriginFD. Components are built with Tailwind CSS and follow shadcn/ui conventions.

## ResponsiveTable

`ResponsiveTable` displays tabular data while adapting to different screen sizes.

- Columns collapse based on their `priority` value.
- The left-most column stays visible during horizontal scrolling.
- Below `640px` each row renders as a stacked card for readability on mobile devices.

### Usage

```tsx
import { ResponsiveTable } from "@originfd/ui"

const columns = [
  { key: "name", header: "Name", priority: 1 },
  { key: "email", header: "Email", priority: 3 },
  { key: "role", header: "Role", priority: 2 }
]

const data = [
  { name: "Alice", email: "alice@example.com", role: "Admin" },
  { name: "Bob", email: "bob@example.com", role: "User" }
]

<ResponsiveTable columns={columns} data={data} />
```

`priority` determines when a column hides as the viewport shrinks: `1` stays visible the longest while higher numbers hide sooner.
