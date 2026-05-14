export class ApiError extends Error {
  constructor(public status: number, message: string) { super(message) }
}

export async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const isFormData = init?.body instanceof FormData
  const res = await fetch(path, {
    ...init,
    headers: isFormData ? init?.headers : { 'Content-Type': 'application/json', ...init?.headers },
  })
  if (!res.ok) {
    const t = await res.text().catch(() => res.statusText)
    throw new ApiError(res.status, t)
  }
  if (res.status === 204) return undefined as T
  return res.json()
}
