import type { ButtonHTMLAttributes } from 'react'

type Props = ButtonHTMLAttributes<HTMLButtonElement>

export function Button({ className = '', type = 'button', ...props }: Props) {
  return (
    <button
      type={type}
      className={`rounded-md bg-slate-900 px-4 py-2 text-sm font-medium text-white hover:bg-slate-700 disabled:opacity-50 ${className}`}
      {...props}
    />
  )
}
