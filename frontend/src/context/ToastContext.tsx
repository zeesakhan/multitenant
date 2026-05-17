import { createContext, useCallback, useContext, useState, ReactNode } from 'react'
import { CheckCircle, AlertCircle, Info, X } from 'lucide-react'
import clsx from 'clsx'

export type ToastType = 'success' | 'error' | 'info'

interface ToastItem {
  id: number
  message: string
  type: ToastType
}

interface ToastCtx {
  toast: (message: string, type?: ToastType) => void
}

const ToastContext = createContext<ToastCtx>({ toast: () => {} })

let _nextId = 0

const STYLES: Record<ToastType, string> = {
  success: 'bg-green-50 border-green-200 text-green-800',
  error:   'bg-red-50 border-red-200 text-red-800',
  info:    'bg-blue-50 border-blue-200 text-blue-800',
}

const ICONS = {
  success: CheckCircle,
  error:   AlertCircle,
  info:    Info,
}

function ToastBanner({ item, onDismiss }: { item: ToastItem; onDismiss: () => void }) {
  const Icon = ICONS[item.type]
  return (
    <div className={clsx('flex items-start gap-3 p-3 rounded-lg border shadow-md text-sm', STYLES[item.type])}>
      <Icon className="w-4 h-4 mt-0.5 shrink-0" />
      <span className="flex-1">{item.message}</span>
      <button onClick={onDismiss} className="opacity-60 hover:opacity-100 transition-opacity">
        <X className="w-4 h-4" />
      </button>
    </div>
  )
}

export function ToastProvider({ children }: { children: ReactNode }) {
  const [items, setItems] = useState<ToastItem[]>([])

  const toast = useCallback((message: string, type: ToastType = 'success') => {
    const id = ++_nextId
    setItems(prev => [...prev, { id, message, type }])
    setTimeout(() => setItems(prev => prev.filter(t => t.id !== id)), 3500)
  }, [])

  return (
    <ToastContext.Provider value={{ toast }}>
      {children}
      {items.length > 0 && (
        <div className="fixed bottom-4 right-4 z-[100] flex flex-col gap-2 w-80 pointer-events-none">
          {items.map(item => (
            <div key={item.id} className="pointer-events-auto">
              <ToastBanner
                item={item}
                onDismiss={() => setItems(prev => prev.filter(t => t.id !== item.id))}
              />
            </div>
          ))}
        </div>
      )}
    </ToastContext.Provider>
  )
}

export function useToast() {
  return useContext(ToastContext)
}
