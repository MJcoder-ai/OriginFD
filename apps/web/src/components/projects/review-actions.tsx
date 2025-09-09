'use client';

import { useState } from 'react';

interface Props {
  projectId: string;
  source: any;
  target: any;
}

export default function ReviewActions({ projectId, source, target }: Props) {
  const [status, setStatus] = useState<string | null>(null);

  async function send(decision: 'approve' | 'reject') {
    const res = await fetch('/approvals', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ project_id: projectId, decision, source, target }),
    });
    const data = await res.json();
    setStatus(data.decision);
  }

  return (
    <div className="space-x-2 mt-4">
      <button onClick={() => send('approve')} className="px-2 py-1 bg-green-600 text-white rounded">Approve</button>
      <button onClick={() => send('reject')} className="px-2 py-1 bg-red-600 text-white rounded">Reject</button>
      {status && <span className="ml-2">Last decision: {status}</span>}
    </div>
  );
}
