export interface ResearchJob {
  id: string
  topic: string
  status: 'pending' | 'running' | 'done' | 'error'
  current_stage: string | null
  report_markdown: string | null
  error_message: string | null
  created_at: string
  completed_at: string | null
}

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? ''

export async function submitResearch(topic: string): Promise<{ job_id: string }> {
  const res = await fetch(`${API_BASE}/research`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ topic }),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err.detail ?? `Request failed: ${res.status}`)
  }
  return res.json()
}

export async function getResearchJob(jobId: string): Promise<ResearchJob> {
  const res = await fetch(`${API_BASE}/research/${jobId}`)
  if (!res.ok) throw new Error(`Failed to fetch job: ${res.status}`)
  return res.json()
}

export async function listResearchJobs(): Promise<ResearchJob[]> {
  const res = await fetch(`${API_BASE}/research`)
  if (!res.ok) throw new Error(`Failed to list jobs: ${res.status}`)
  return res.json()
}
