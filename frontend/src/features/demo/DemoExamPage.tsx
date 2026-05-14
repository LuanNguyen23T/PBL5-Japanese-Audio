import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { AlertCircle, Loader2, PlayCircle } from 'lucide-react'

import { Button } from '@/components/ui/Button'
import { TakeExamContent } from '@/features/test/TakeExamPage'
import type { TestExamDetail } from '@/features/test/types'
import { demoClient } from './demoClient'

export default function DemoExamPage() {
  const [exam, setExam] = useState<TestExamDetail | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    demoClient
      .getDemoExam()
      .then((data) => setExam(data))
      .catch((err: Error) => setError(err.message || 'Không tải được đề mẫu'))
      .finally(() => setLoading(false))
  }, [])

  if (loading) {
    return (
      <div className="flex min-h-[60vh] items-center justify-center">
        <Loader2 className="h-10 w-10 animate-spin text-blue-500" />
      </div>
    )
  }

  if (error || !exam) {
    return (
      <div className="mx-auto flex min-h-[60vh] max-w-xl flex-col items-center justify-center text-center">
        <div className="mb-5 inline-flex h-14 w-14 items-center justify-center rounded-2xl bg-amber-100 text-amber-700">
          <AlertCircle className="h-7 w-7" />
        </div>
        <h1 className="text-2xl font-bold text-foreground">Chưa có đề mẫu sẵn sàng</h1>
        <p className="mt-3 text-sm leading-6 text-muted-foreground">
          {error || 'Hệ thống chưa có đề thi đã xuất bản để dùng thử.'}
        </p>
        <div className="mt-6 flex flex-wrap justify-center gap-3">
          <Link to="/">
            <Button variant="outline">Về trang chủ</Button>
          </Link>
          <Link to="/register">
            <Button>Đăng ký tài khoản</Button>
          </Link>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <section className="rounded-2xl border border-blue-100 bg-blue-50 px-5 py-4 text-blue-950">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex items-start gap-3">
            <span className="mt-0.5 inline-flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-blue-600 text-white">
              <PlayCircle className="h-5 w-5" />
            </span>
            <div>
              <h1 className="text-base font-bold">Làm thử đề mẫu miễn phí</h1>
              <p className="mt-1 text-sm leading-6 text-blue-800">
                Bạn có thể nghe audio, chọn đáp án và xem điểm tạm thời. Kết quả demo không lưu vào lịch sử.
              </p>
            </div>
          </div>
          <Link to="/register" className="shrink-0">
            <Button variant="outline" className="border-blue-200 bg-white text-blue-700 hover:bg-blue-100">
              Đăng ký để lưu kết quả
            </Button>
          </Link>
        </div>
      </section>

      <TakeExamContent
        examId={exam.exam_id}
        initialExam={exam}
        submitExam={(payload) => demoClient.submitDemoExam(exam.exam_id, payload)}
        standalone
        variant="demo"
        returnPath="/"
      />
    </div>
  )
}
