// Kurzlebige Hinweise mit optionalem "Rückgängig". Geteilter reaktiver Zustand.

export interface ToastEintrag {
  id: number
  text: string
  undo?: () => void | Promise<void>
}

let zaehler = 0

export const toasts = $state<ToastEintrag[]>([])

export function zeigeToast(text: string, undo?: () => void | Promise<void>): void {
  const id = ++zaehler
  toasts.push({ id, text, undo })
  setTimeout(() => entferne(id), 6000)
}

export function entferne(id: number): void {
  const i = toasts.findIndex((t) => t.id === id)
  if (i >= 0) toasts.splice(i, 1)
}
