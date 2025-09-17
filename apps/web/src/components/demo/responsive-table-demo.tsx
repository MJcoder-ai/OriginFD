"use client";

import { ResponsiveTable } from "@originfd/ui";

interface User {
  name: string;
  email: string;
  role: string;
  status: string;
}

const columns: Array<{key: keyof User; header: string; priority: number}> = [
  { key: "name", header: "Name", priority: 1 },
  { key: "email", header: "Email", priority: 3 },
  { key: "role", header: "Role", priority: 2 },
  { key: "status", header: "Status", priority: 2 },
];

const data: User[] = [
  {
    name: "Alice Johnson",
    email: "alice@example.com",
    role: "Admin",
    status: "Active",
  },
  {
    name: "Bob Smith",
    email: "bob@example.com",
    role: "User",
    status: "Pending",
  },
  {
    name: "Carol Lee",
    email: "carol@example.com",
    role: "Manager",
    status: "Active",
  },
];

export function ResponsiveTableDemo() {
  return <ResponsiveTable<User> columns={columns} data={data} />;
}

export default ResponsiveTableDemo;
