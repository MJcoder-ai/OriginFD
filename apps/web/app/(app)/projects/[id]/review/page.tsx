import ReviewActions from '@/components/projects/review-actions';
import { diffWithKpi } from '@/lib/diff';

interface Props {
  params: { id: string };
}

export default function ReviewPage({ params }: Props) {
  const projectId = params.id;
  // Placeholder documents for demonstration
  const source = { finance: { capex: 100, opex: 50 }, esg: { metrics: { metrics: [{ name: 'co2', value: 10 }] } } };
  const target = { finance: { capex: 120, opex: 45 }, esg: { metrics: { metrics: [{ name: 'co2', value: 8 }] } } };
  const diff = diffWithKpi(source, target);

  return (
    <div className="p-4 space-y-4">
      <h1 className="text-xl font-bold">Project Review</h1>
      {Object.entries(diff.grouped_diffs).map(([section, ops]) => (
        <div key={section}>
          <h2 className="font-semibold">{section}</h2>
          <pre className="bg-gray-100 p-2 text-sm overflow-x-auto">{JSON.stringify(ops, null, 2)}</pre>
        </div>
      ))}
      <div>
        <h2 className="font-semibold">KPI Deltas</h2>
        <ul>
          {Object.entries(diff.kpi_deltas).map(([k, v]) => (
            <li key={k}>{k}: {v}</li>
          ))}
        </ul>
      </div>
      <ReviewActions projectId={projectId} source={source} target={target} />
    </div>
  );
}
