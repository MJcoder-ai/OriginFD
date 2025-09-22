import * as React from "react";

const forward = (Tag: keyof JSX.IntrinsicElements, displayName: string) => {
  const Component = React.forwardRef<any, any>(
    ({ children, ...props }, ref) =>
      React.createElement(Tag, { ref, ...props }, children),
  );
  Component.displayName = displayName;
  return Component;
};

export const Button = forward("button", "Button");
export const Card = forward("div", "Card");
export const CardContent = forward("div", "CardContent");
export const CardDescription = forward("p", "CardDescription");
export const CardHeader = forward("div", "CardHeader");
export const CardTitle = forward("h3", "CardTitle");
export const Dialog = ({ children }: any) => (
  <div data-testid="dialog">{children}</div>
);
export const DialogContent = forward("div", "DialogContent");
export const DialogDescription = forward("p", "DialogDescription");
export const DialogFooter = forward("div", "DialogFooter");
export const DialogHeader = forward("div", "DialogHeader");
export const DialogTitle = forward("h2", "DialogTitle");
export const Input = forward("input", "Input");
export const Label = forward("label", "Label");
export const Tabs = forward("div", "Tabs");
export const TabsContent = forward("div", "TabsContent");
export const TabsList = forward("div", "TabsList");
export const TabsTrigger = forward("button", "TabsTrigger");
