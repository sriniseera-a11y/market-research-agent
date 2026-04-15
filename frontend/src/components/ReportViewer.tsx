import ReactMarkdown from 'react-markdown'

interface ReportViewerProps {
  topic: string
  markdown: string
}

export function ReportViewer({ topic, markdown }: ReportViewerProps) {
  function handleDownload() {
    const blob = new Blob([markdown], { type: 'text/markdown' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `${topic.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '')}-report.md`
    a.click()
    URL.revokeObjectURL(url)
  }

  return (
    <div className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm">
      <div className="mb-4 flex items-center justify-between">
        <h2 className="text-lg font-semibold text-gray-900">Report</h2>
        <button
          onClick={handleDownload}
          className="rounded-lg border border-gray-300 px-4 py-1.5 text-sm
                     text-gray-700 hover:bg-gray-50 transition-colors"
        >
          Download .md
        </button>
      </div>
      <div
        className="prose prose-sm max-w-none
                   prose-headings:font-semibold prose-h1:text-2xl prose-h2:text-xl
                   prose-h2:border-b prose-h2:border-gray-100 prose-h2:pb-1
                   prose-ul:my-1 prose-li:my-0.5"
      >
        <ReactMarkdown>{markdown}</ReactMarkdown>
      </div>
    </div>
  )
}
