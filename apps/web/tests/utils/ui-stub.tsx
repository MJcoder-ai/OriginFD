import type { ButtonHTMLAttributes, HTMLAttributes, PropsWithChildren } from "react";

export function Button({ children, ...props }: PropsWithChildren<ButtonHTMLAttributes<HTMLButtonElement>>) {
  return (
    <button type="button" {...props}>
      {children}
    </button>
  );
}

export function Card({ children, ...props }: PropsWithChildren<HTMLAttributes<HTMLDivElement>>) {
  return (
    <div {...props}>
      {children}
    </div>
  );
}

export function CardHeader({ children, ...props }: PropsWithChildren<HTMLAttributes<HTMLDivElement>>) {
  return (
    <div {...props}>
      {children}
    </div>
  );
}

export function CardTitle({ children, ...props }: PropsWithChildren<HTMLAttributes<HTMLHeadingElement>>) {
  return (
    <h3 {...props}>
      {children}
    </h3>
  );
}

export function CardDescription({ children, ...props }: PropsWithChildren<HTMLAttributes<HTMLParagraphElement>>) {
  return (
    <p {...props}>
      {children}
    </p>
  );
}

export function CardContent({ children, ...props }: PropsWithChildren<HTMLAttributes<HTMLDivElement>>) {
  return (
    <div {...props}>
      {children}
    </div>
  );
}
