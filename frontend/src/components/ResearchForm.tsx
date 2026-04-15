import React, { useState } from 'react'

interface ResearchFormProps {
  onSubmit: (topic: string) => void
  isLoading: boolean
}

export function ResearchForm({ onSubmit, isLoading }: ResearchFormProps) {
  const [topic, setTopic] = useState('')

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    const trimmed = topic.trim()
    if (trimmed.length === 0 || trimmed.length > 500) return
    onSubmit(trimmed)
    setTopic('')
  }

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-3">
      <label htmlFor="topic" className="text-sm font-medium text-gray-700">
        Research Topic
      </label>
      <textarea
        id="topic"
        value={topic}
        onChange={(e) => setTopic(e.target.value)}
        placeholder="e.g. Global electric vehicle battery market 2025"
        rows={3}
        maxLength={500}
        disabled={isLoading}
        className="w-full rounded-lg border border-gray-300 px-4 py-2 text-sm
                   focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500
                   disabled:bg-gray-50 disabled:text-gray-400"
      />
      <div className="flex items-center justify-between">
        <span className="text-xs text-gray-400">{topic.length}/500</span>
        <button
          type="submit"
          disabled={isLoading || topic.trim().length === 0}
          className="rounded-lg bg-blue-600 px-6 py-2 text-sm font-medium text-white
                     hover:bg-blue-700 disabled:cursor-not-allowed disabled:bg-gray-300
                     transition-colors"
        >
          {isLoading ? 'Researching…' : 'Generate Report'}
        </button>
      </div>
    </form>
  )
}
