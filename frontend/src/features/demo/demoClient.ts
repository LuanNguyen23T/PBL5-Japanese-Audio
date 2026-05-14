import type { TestExamDetail, TestSubmitPayload, TestSubmitResult } from '@/features/test/types'

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000'

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText }))
    throw new Error(error.detail || 'API request failed')
  }
  return response.json()
}

export const demoClient = {
  getDemoExam: () =>
    fetch(`${API_BASE}/api/demo/exam`, {
      headers: { 'Content-Type': 'application/json' },
    }).then((response) => handleResponse<TestExamDetail>(response)),

  submitDemoExam: (examId: string, payload: TestSubmitPayload) =>
    fetch(`${API_BASE}/api/demo/exams/${examId}/submit`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    }).then((response) => handleResponse<TestSubmitResult>(response)),
}
