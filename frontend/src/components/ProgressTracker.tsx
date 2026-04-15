type Stage = 'plan' | 'search' | 'synthesize' | 'write'

const STAGES: { key: Stage; label: string; description: string }[] = [
  { key: 'plan', label: 'Plan', description: 'Generating search queries' },
  { key: 'search', label: 'Search', description: 'Searching the web' },
  { key: 'synthesize', label: 'Synthesize', description: 'Analyzing results' },
  { key: 'write', label: 'Write', description: 'Writing report' },
]

const STAGE_ORDER: Stage[] = ['plan', 'search', 'synthesize', 'write']

interface ProgressTrackerProps {
  currentStage: string | null
  status: 'pending' | 'running' | 'done' | 'error'
}

export function ProgressTracker({ currentStage, status }: ProgressTrackerProps) {
  const currentIndex = currentStage
    ? STAGE_ORDER.indexOf(currentStage as Stage)
    : -1

  return (
    <div className="flex items-start gap-0">
      {STAGES.map((stage, index) => {
        const isCompleted =
          status === 'done' ||
          ((status === 'running' || status === 'error') && index < currentIndex)
        const isActive = status === 'running' && index === currentIndex
        const isPending = index > currentIndex || status === 'pending'

        return (
          <div key={stage.key} className="flex flex-1 flex-col items-center">
            <div className="flex w-full items-center">
              <div
                className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-full
                  text-sm font-semibold
                  ${isCompleted ? 'bg-green-500 text-white' : ''}
                  ${isActive ? 'bg-blue-600 text-white animate-pulse' : ''}
                  ${isPending ? 'bg-gray-200 text-gray-500' : ''}`}
              >
                {isCompleted ? '✓' : index + 1}
              </div>
              {index < STAGES.length - 1 && (
                <div
                  className={`h-1 flex-1 ${isCompleted ? 'bg-green-400' : 'bg-gray-200'}`}
                />
              )}
            </div>
            <div className="mt-1 text-center">
              <p className={`text-xs font-medium ${isActive ? 'text-blue-600' : 'text-gray-600'}`}>
                {stage.label}
              </p>
              {isActive && (
                <p className="text-xs text-gray-400">{stage.description}</p>
              )}
            </div>
          </div>
        )
      })}
    </div>
  )
}
