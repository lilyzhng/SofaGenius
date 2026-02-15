import type { QueryResult } from "../types";

const MAX_DISPLAY_ROWS = 100;

function formatCell(value: unknown): string {
  if (value === null || value === undefined) return "null";
  if (typeof value === "number") {
    return Number.isInteger(value) ? String(value) : value.toFixed(4);
  }
  return String(value);
}

interface Props {
  result: QueryResult;
}

export default function DataTable({ result }: Props) {
  const displayRows = result.rows.slice(0, MAX_DISPLAY_ROWS);
  const showing = displayRows.length;
  const total = result.row_count;

  return (
    <div>
      <div className="overflow-x-auto rounded-lg border border-stone-200">
        <table className="w-full text-xs">
          <thead>
            <tr className="bg-stone-50">
              {result.columns.map((col) => (
                <th
                  key={col}
                  className="px-3 py-2 text-left font-bold text-stone-600 uppercase tracking-wider border-b border-stone-200"
                >
                  {col}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {displayRows.map((row, i) => (
              <tr
                key={i}
                className="border-b border-stone-100 hover:bg-stone-50 transition-colors"
              >
                {row.map((cell, j) => (
                  <td
                    key={j}
                    className={`px-3 py-1.5 text-stone-700 ${
                      cell === null || cell === undefined
                        ? "italic text-stone-400"
                        : ""
                    }`}
                  >
                    {formatCell(cell)}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {(showing < total || result.truncated) && (
        <p className="mt-2 text-xs text-stone-400">
          Showing {showing} of {total} rows
          {result.truncated && " (query results truncated at 1,000 rows)"}
        </p>
      )}
    </div>
  );
}
