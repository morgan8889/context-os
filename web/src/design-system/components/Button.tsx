import { type ButtonHTMLAttributes, forwardRef } from 'react';

type Variant = 'default' | 'outline' | 'ghost' | 'destructive';
type Size = 'sm' | 'md' | 'lg';

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant;
  size?: Size;
}

const variantClasses: Record<Variant, string> = {
  default: 'bg-blue-600 text-white hover:bg-blue-700 focus-visible:ring-blue-500',
  outline: 'border border-current bg-transparent hover:bg-black/5 focus-visible:ring-blue-500',
  ghost: 'bg-transparent hover:bg-black/5 focus-visible:ring-blue-500',
  destructive: 'bg-red-600 text-white hover:bg-red-700 focus-visible:ring-red-500',
};

const sizeClasses: Record<Size, string> = {
  sm: 'h-7 px-3 text-xs',
  md: 'h-9 px-4 text-sm',
  lg: 'h-11 px-6 text-base',
};

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ variant = 'default', size = 'md', className = '', ...props }, ref) => (
    <button
      ref={ref}
      className={[
        'inline-flex items-center justify-center gap-2 rounded-md font-medium',
        'transition-colors duration-[var(--motion-duration-everyday)]',
        'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-1',
        'disabled:pointer-events-none disabled:opacity-50',
        variantClasses[variant],
        sizeClasses[size],
        className,
      ].join(' ')}
      {...props}
    />
  )
);
Button.displayName = 'Button';
