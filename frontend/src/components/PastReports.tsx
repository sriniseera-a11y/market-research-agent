import { ResearchJob } from '../api'

interface PastReportsProps {
  jobs: ResearchJob[]
  onSelect: (job: ResearchJob) => void
  selectedJobId: string | null
}

function formatDate(iso: string): string {
  return new Date(iso).toLocaleString(undefined, {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

const STATUS_BADGE: Record<ResearchJob['status'], string> = {
  pending: 'bg-gray-100 text-gray-600',
  running: 'bg-blue-100 text-blue-700',
  done: 'bg-green-100 text-green-700',
  error: 'bg-red-100 text-red-700',
}

export function PastReports({ jobs, onSelect, selectedJobId }: PastReportsProps) {
  if (jobs.length === 0) {
    return (
      <p className="text-sm text-gray-400 italic">No reports yet. Submit a topic above.</p>
    )
  }

  return (
    <ul className="divide-y divide-gray-100">
      {jobs.map((job) => (
        <li key={job.id}>
          <button
            onClick={() => onSelect(job)}
            className={`w-full text-left px-3 py-3 hover:bg-gray-50 transition-colors rounded-lg
              ${selectedJobId === job.id ? 'bg-blue-50' : ''}`}
          >
            <div className="flex items-start justify-between gap-2">
              <span className="text-sm font-medium text-gray-800 line-clamp-1">
                {job.topic}
              </span>
              <span
                className={`shrink-0 rounded-full px-2 py-0.5 text-xs font-medium
                  ${STATUS_BADGE[job.status]}`}
              >
                {job.status}
              </span>
            </div>
            <span className="text-xs text-gray-400">{formatDate(job.created_at)}</span>
          </button>
        </li>
      ))}
    </ul>
  )
}
