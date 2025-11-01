import Head from 'next/head';
import { useState, useEffect } from 'react';
import { CheckCircleIcon, ExclamationTriangleIcon, XCircleIcon } from '@heroicons/react/24/outline';
import { getMockQCResults } from '../lib/mock';

interface QCResult {
  surface_id: string;
  title_id: string;
  prs_score: number;
  quality_score: number;
  issues: string[];
  status: 'passed' | 'warning' | 'failed';
  checked_at: string;
}

export default function QC() {
  const [results, setResults] = useState<QCResult[]>([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState('all');

  useEffect(() => {
    loadQCResults();
  }, []);

  const loadQCResults = async () => {
    setLoading(true);
    try {
      const data = await getMockQCResults();
      setResults(data);
    } catch (error) {
      console.error('Error loading QC results:', error);
    } finally {
      setLoading(false);
    }
  };

  const filteredResults = results.filter(result => {
    if (statusFilter === 'all') return true;
    return result.status === statusFilter;
  });

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'passed':
        return <CheckCircleIcon className="h-5 w-5 text-green-500" />;
      case 'warning':
        return <ExclamationTriangleIcon className="h-5 w-5 text-yellow-500" />;
      case 'failed':
        return <XCircleIcon className="h-5 w-5 text-red-500" />;
      default:
        return null;
    }
  };

  const getStatusBadge = (status: string) => {
    const styles = {
      passed: 'bg-green-100 text-green-800',
      warning: 'bg-yellow-100 text-yellow-800',
      failed: 'bg-red-100 text-red-800'
    };
    return `px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${styles[status as keyof typeof styles]}`;
  };

  const passRate = (results.filter(r => r.status === 'passed').length / results.length * 100) || 0;
  const averageQuality = results.reduce((sum, r) => sum + r.quality_score, 0) / results.length || 0;

  return (
    <>
      <Head>
        <title>Quality Control - Inscenium CMS</title>
        <meta name="description" content="Quality control and validation" />
      </Head>

      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Quality Control</h1>
            <p className="mt-2 text-gray-600">
              Monitor placement quality and validation results
            </p>
          </div>
          <button
            onClick={loadQCResults}
            className="bg-inscenium-600 text-white px-4 py-2 rounded-lg hover:bg-inscenium-700"
          >
            Run QC Check
          </button>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          <div className="bg-white overflow-hidden shadow rounded-lg">
            <div className="p-5">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <CheckCircleIcon className="h-6 w-6 text-green-400" />
                </div>
                <div className="ml-5 w-0 flex-1">
                  <dl>
                    <dt className="text-sm font-medium text-gray-500 truncate">
                      Pass Rate
                    </dt>
                    <dd className="text-lg font-medium text-gray-900">
                      {passRate.toFixed(1)}%
                    </dd>
                  </dl>
                </div>
              </div>
            </div>
          </div>

          <div className="bg-white overflow-hidden shadow rounded-lg">
            <div className="p-5">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <ExclamationTriangleIcon className="h-6 w-6 text-yellow-400" />
                </div>
                <div className="ml-5 w-0 flex-1">
                  <dl>
                    <dt className="text-sm font-medium text-gray-500 truncate">
                      Warnings
                    </dt>
                    <dd className="text-lg font-medium text-gray-900">
                      {results.filter(r => r.status === 'warning').length}
                    </dd>
                  </dl>
                </div>
              </div>
            </div>
          </div>

          <div className="bg-white overflow-hidden shadow rounded-lg">
            <div className="p-5">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <XCircleIcon className="h-6 w-6 text-red-400" />
                </div>
                <div className="ml-5 w-0 flex-1">
                  <dl>
                    <dt className="text-sm font-medium text-gray-500 truncate">
                      Failed
                    </dt>
                    <dd className="text-lg font-medium text-gray-900">
                      {results.filter(r => r.status === 'failed').length}
                    </dd>
                  </dl>
                </div>
              </div>
            </div>
          </div>

          <div className="bg-white overflow-hidden shadow rounded-lg">
            <div className="p-5">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <div className="h-6 w-6 bg-blue-400 rounded"></div>
                </div>
                <div className="ml-5 w-0 flex-1">
                  <dl>
                    <dt className="text-sm font-medium text-gray-500 truncate">
                      Avg Quality
                    </dt>
                    <dd className="text-lg font-medium text-gray-900">
                      {averageQuality.toFixed(1)}
                    </dd>
                  </dl>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Filters */}
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center space-x-4">
            <label className="text-sm font-medium text-gray-700">Filter by status:</label>
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="rounded-lg border-gray-300 shadow-sm focus:border-inscenium-500 focus:ring-inscenium-500"
            >
              <option value="all">All Results</option>
              <option value="passed">Passed</option>
              <option value="warning">Warning</option>
              <option value="failed">Failed</option>
            </select>
          </div>
        </div>

        {/* QC Results Table */}
        <div className="bg-white shadow overflow-hidden sm:rounded-lg">
          <div className="px-4 py-5 sm:px-6">
            <h3 className="text-lg leading-6 font-medium text-gray-900">
              Quality Check Results
            </h3>
            <p className="mt-1 max-w-2xl text-sm text-gray-500">
              {filteredResults.length} results found
            </p>
          </div>
          
          {loading ? (
            <div className="p-8 text-center">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-inscenium-600 mx-auto"></div>
              <p className="mt-4 text-gray-600">Running quality checks...</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Surface
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Status
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      PRS Score
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Quality Score
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Issues
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Checked At
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {filteredResults.map((result) => (
                    <tr key={result.surface_id} className="hover:bg-gray-50">
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm font-medium text-gray-900">
                          {result.surface_id}
                        </div>
                        <div className="text-sm text-gray-500">
                          {result.title_id}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="flex items-center">
                          {getStatusIcon(result.status)}
                          <span className={`ml-2 ${getStatusBadge(result.status)}`}>
                            {result.status}
                          </span>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {result.prs_score.toFixed(1)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {result.quality_score.toFixed(1)}
                      </td>
                      <td className="px-6 py-4">
                        <div className="text-sm text-gray-900">
                          {result.issues.length > 0 ? (
                            <ul className="list-disc list-inside space-y-1">
                              {result.issues.slice(0, 2).map((issue, index) => (
                                <li key={index}>{issue}</li>
                              ))}
                              {result.issues.length > 2 && (
                                <li className="text-gray-500">+{result.issues.length - 2} more</li>
                              )}
                            </ul>
                          ) : (
                            <span className="text-gray-500">No issues</span>
                          )}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {new Date(result.checked_at).toLocaleString()}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
          
          {!loading && filteredResults.length === 0 && (
            <div className="p-8 text-center">
              <CheckCircleIcon className="h-12 w-12 text-gray-400 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">No QC results found</h3>
              <p className="text-gray-600">Run a quality check to see results.</p>
            </div>
          )}
        </div>
      </div>
    </>
  );
}