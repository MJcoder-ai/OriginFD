import * as React from "react";
import { cn } from "../../lib/utils";

interface Column<T extends Record<string, any>> {
  key: keyof T;
  header: React.ReactNode;
  priority?: number;
  render?: (value: any, row: T) => React.ReactNode;
}

interface ResponsiveTableProps<T extends Record<string, any>> {
  columns: Column<T>[];
  data: T[];
  className?: string;
}

const priorityClasses: Record<number, string> = {
  2: "hidden md:table-cell",
  3: "hidden lg:table-cell",
  4: "hidden xl:table-cell",
  5: "hidden 2xl:table-cell",
};

export function ResponsiveTable<T extends Record<string, any>>({
  columns,
  data,
  className,
}: ResponsiveTableProps<T>) {
  const renderCell = (col: Column<T>, row: T) =>
    col.render
      ? col.render(row[col.key], row)
      : (row[col.key] as React.ReactNode);

  const getPriorityClass = (p?: number) =>
    p ? (priorityClasses[p] ?? "") : "";

  return (
    <div className={cn("w-full overflow-x-auto", className)}>
      {/* Table for screens >=640px */}
      <table className="hidden w-full border-collapse text-sm sm:table">
        <thead>
          <tr>
            {columns.map((col, index) => (
              <th
                key={String(col.key)}
                className={cn(
                  "border-b px-3 py-2 text-left font-medium",
                  index === 0 && "sticky left-0 z-10 bg-background",
                  getPriorityClass(col.priority),
                )}
              >
                {col.header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {data.map((row, rowIndex) => (
            <tr key={rowIndex} className="border-b">
              {columns.map((col, index) => (
                <td
                  key={String(col.key)}
                  className={cn(
                    "px-3 py-2",
                    index === 0 && "sticky left-0 z-0 bg-background",
                    getPriorityClass(col.priority),
                  )}
                >
                  {renderCell(col, row)}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>

      {/* Card layout for screens <640px */}
      <div className="grid gap-4 sm:hidden">
        {data.map((row, rowIndex) => (
          <div key={rowIndex} className="rounded-lg border p-4">
            <div className="font-medium">{renderCell(columns[0], row)}</div>
            {columns.slice(1).map((col) => (
              <div
                key={String(col.key)}
                className="mt-2 flex justify-between text-sm"
              >
                <span className="font-medium">{col.header}</span>
                <span>{renderCell(col, row)}</span>
              </div>
            ))}
          </div>
        ))}
      </div>
    </div>
  );
}

export default ResponsiveTable;
