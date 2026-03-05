import type { ReactNode } from 'react'

interface BulkActionBarProps {
  count: number
  onClear: () => void
  children: ReactNode
}

export default function BulkActionBar({ count, onClear, children }: BulkActionBarProps) {
  if (count === 0) return null

  return (
    <div className="fixed bottom-4 left-1/2 -translate-x-1/2 bg-gray-900 text-white rounded-lg px-4 py-3 shadow-lg flex items-center gap-3 z-50">
      <span className="text-sm font-medium">{count} selected</span>
      <div className="w-px h-5 bg-gray-600" />
      {children}
      <div className="w-px h-5 bg-gray-600" />
      <button
        onClick={onClear}
        className="text-sm text-gray-300 hover:text-white cursor-pointer"
      >
        Clear
      </button>
    </div>
  )
}
