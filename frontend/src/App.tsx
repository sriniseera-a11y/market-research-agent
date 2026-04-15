import { useCallback, useEffect, useRef, useState } from 'react'
import {
  ResearchJob,
  getResearchJob,
  listResearchJobs,
  submitResearch,
} from './api'
import { PastReports } from './components/PastReports'
import { ProgressTracker } from './components/ProgressTracker'
import { ReportViewer } from './components/ReportViewer'
import { ResearchForm } from './components/ResearchForm'

const POLL_INTERVAL_MS = 2000

export default function App() {
  const [jobs, setJobs] = useState<ResearchJob[]>([])
  const [activeJob, setActiveJob] = useState<ResearchJob | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [submitError, setSubmitError] = useState<string | null>(null)
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null)

  const loadJobs = useCallback(async () => {
    try {
      const data = await listResearchJobs()
      setJobs(data)
    } catch {
      // silently ignore list errors
    }
  }, [])

  useEffect(() => {
    loadJobs()
  }, [loadJobs])

  const startPolling = useCallback(
    (jobId: string) => {
      if (pollRef.current) clearInterval(pollRef.current)
      pollRef.current = setInterval(async () => {
        try {
          const job = await getResearchJob(jobId)
          setActiveJob(job)
          setJobs((prev) =>
            prev.map((j) => (j.id === job.id ? job : j))
          )
          if (job.status === 'done' || job.status === 'error') {
            clearInterval(pollRef.current!)
            pollRef.current = null
          }
        } catch {
          clearInterval(pollRef.current!)
          pollRef.current = null
        }
      }, POLL_INTERVAL_MS)
    },
    []
  )

  useEffect(() => {
    return () => {
      if (pollRef.current) clearInterval(pollRef.current)
    }
  }, [])

  async function handleSubmit(topic: string) {
    setIsSubmitting(true)
    setSubmitError(null)
    try {
      const { job_id } = await submitResearch(topic)
      const job = await getResearchJob(job_id)
      setActiveJob(job)
      setJobs((prev) => [job, ...prev])
      startPolling(job_id)
    } catch (err) {
      setSubmitError(err instanceof Error ? err.message : 'Submission failed')
    } finally {
      setIsSubmitting(false)
    }
  }

  function handleSelectJob(job: ResearchJob) {
    // Clear any in-flight poll so selecting a completed job doesn't get overwritten
    if (pollRef.current) {
      clearInterval(pollRef.current)
      pollRef.current = null
    }
    setActiveJob(job)
    setSubmitError(null)
    if (job.status === 'pending' || job.status === 'running') {
      startPolling(job.id)
    }
  }

  const isRunning =
    isSubmitting ||
    activeJob?.status === 'pending' ||
    activeJob?.status === 'running'

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="border-b border-gray-200 bg-white px-6 py-4 shadow-sm">
        <h1 className="text-xl font-bold text-gray-900">Market Research Agent</h1>
        <p className="text-sm text-gray-500">
          AI-powered market research reports in minutes
        </p>
      </header>

      <main className="mx-auto max-w-6xl px-6 py-8 grid grid-cols-3 gap-8">
        {/* Left panel: form + past reports */}
        <aside className="col-span-1 flex flex-col gap-6">
          <section className="rounded-xl border border-gray-200 bg-white p-5 shadow-sm">
            <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-gray-500">
              New Research
            </h2>
            <ResearchForm onSubmit={handleSubmit} isLoading={!!isRunning} />
            {submitError && (
              <p className="mt-2 text-xs text-red-600">{submitError}</p>
            )}
          </section>

          <section className="rounded-xl border border-gray-200 bg-white p-5 shadow-sm">
            <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-gray-500">
              Past Reports
            </h2>
            <PastReports
              jobs={jobs}
              onSelect={handleSelectJob}
              selectedJobId={activeJob?.id ?? null}
            />
          </section>
        </aside>

        {/* Right panel: progress + report */}
        <section className="col-span-2 flex flex-col gap-6">
          {activeJob && (
            <>
              <div className="rounded-xl border border-gray-200 bg-white p-5 shadow-sm">
                <h2 className="mb-1 text-sm font-semibold text-gray-700">
                  {activeJob.topic}
                </h2>
                <p className="mb-4 text-xs text-gray-400">
                  {activeJob.status === 'running'
                    ? 'Research in progress…'
                    : activeJob.status === 'done'
                      ? 'Complete'
                      : activeJob.status === 'error'
                        ? 'Failed'
                        : 'Queued'}
                </p>
                <ProgressTracker
                  currentStage={activeJob.current_stage}
                  status={activeJob.status}
                />
                {activeJob.status === 'error' && (
                  <p className="mt-3 rounded-lg bg-red-50 px-4 py-2 text-sm text-red-700">
                    Error: {activeJob.error_message}
                  </p>
                )}
              </div>

              {activeJob.status === 'done' && activeJob.report_markdown && (
                <ReportViewer
                  topic={activeJob.topic}
                  markdown={activeJob.report_markdown}
                />
              )}
            </>
          )}

          {!activeJob && (
            <div className="flex flex-col items-center justify-center rounded-xl border-2 border-dashed border-gray-200 py-24 text-center">
              <p className="text-gray-400">
                Submit a topic on the left to generate a report.
              </p>
            </div>
          )}
        </section>
      </main>
    </div>
  )
}
