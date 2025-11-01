import Head from 'next/head';
import { useState, useEffect } from 'react';
import { ChartBarIcon, EyeIcon, MapIcon } from '@heroicons/react/24/outline';
import { getMockOpportunities } from '../lib/mock';
import PRSHeatmap from '../components/PRSHeatmap';
import SurfaceCard from '../components/SurfaceCard';

interface Opportunity {
  surface_id: string;
  title_id: string;
  shot_id: string;
  prs_score: number;
  surface_type: string;
  visibility_score: number;
  duration: number;
}

export default function SGI() {
  const [opportunities, setOpportunities] = useState<Opportunity[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedSurface, setSelectedSurface] = useState<string | null>(null);
  const [filters, setFilters] = useState({
    minPRS: 70,
    surfaceType: 'all',
    titleFilter: ''
  });

  useEffect(() => {
    loadOpportunities();
  }, [filters]);

  const loadOpportunities = async () => {
    setLoading(true);
    try {
      const data = await getMockOpportunities(filters);
      setOpportunities(data);
    } catch (error) {
      console.error('Error loading opportunities:', error);
    } finally {
      setLoading(false);
    }
  };

  const filteredOpportunities = opportunities.filter(opp => {
    if (filters.surfaceType !== 'all' && opp.surface_type !== filters.surfaceType) return false;
    if (filters.titleFilter && !opp.title_id.toLowerCase().includes(filters.titleFilter.toLowerCase())) return false;
    return opp.prs_score >= filters.minPRS;
  });

  const averagePRS = filteredOpportunities.reduce((sum, opp) => sum + opp.prs_score, 0) / filteredOpportunities.length || 0;

  return (
    <>
      <Head>
        <title>SGI Analysis - Inscenium CMS</title>
        <meta name="description" content="Scene Graph Intelligence analysis" />
      </Head>

      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Scene Graph Intelligence</h1>
            <p className="mt-2 text-gray-600">
              Analyze placement opportunities using computer vision
            </p>
          </div>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="bg-white overflow-hidden shadow rounded-lg">
            <div className="p-5">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <MapIcon className="h-6 w-6 text-blue-400" />
                </div>
                <div className="ml-5 w-0 flex-1">
                  <dl>
                    <dt className="text-sm font-medium text-gray-500 truncate">
                      Total Surfaces
                    </dt>
                    <dd className="text-lg font-medium text-gray-900">
                      {filteredOpportunities.length}
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
                  <ChartBarIcon className="h-6 w-6 text-green-400" />
                </div>
                <div className="ml-5 w-0 flex-1">
                  <dl>
                    <dt className="text-sm font-medium text-gray-500 truncate">
                      Average PRS
                    </dt>
                    <dd className="text-lg font-medium text-gray-900">
                      {averagePRS.toFixed(1)}
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
                  <EyeIcon className="h-6 w-6 text-purple-400" />
                </div>
                <div className="ml-5 w-0 flex-1">
                  <dl>
                    <dt className="text-sm font-medium text-gray-500 truncate">
                      High Quality (90+)
                    </dt>
                    <dd className="text-lg font-medium text-gray-900">
                      {filteredOpportunities.filter(o => o.prs_score >= 90).length}
                    </dd>
                  </dl>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Filters */}
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-lg font-medium text-gray-900 mb-4">Filters</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Minimum PRS Score
              </label>
              <input
                type="range"
                min="0"
                max="100"
                value={filters.minPRS}
                onChange={(e) => setFilters(prev => ({ ...prev, minPRS: Number(e.target.value) }))}
                className="w-full"
              />
              <div className="text-sm text-gray-500 mt-1">{filters.minPRS}</div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Surface Type
              </label>
              <select
                value={filters.surfaceType}
                onChange={(e) => setFilters(prev => ({ ...prev, surfaceType: e.target.value }))}
                className="w-full rounded-lg border-gray-300 shadow-sm focus:border-inscenium-500 focus:ring-inscenium-500"
              >
                <option value="all">All Types</option>
                <option value="wall">Wall</option>
                <option value="table">Table</option>
                <option value="screen">Screen</option>
                <option value="billboard">Billboard</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Title Filter
              </label>
              <input
                type="text"
                placeholder="Filter by title..."
                value={filters.titleFilter}
                onChange={(e) => setFilters(prev => ({ ...prev, titleFilter: e.target.value }))}
                className="w-full rounded-lg border-gray-300 shadow-sm focus:border-inscenium-500 focus:ring-inscenium-500"
              />
            </div>
          </div>
        </div>

        {/* PRS Heatmap */}
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-lg font-medium text-gray-900 mb-4">PRS Score Distribution</h2>
          <PRSHeatmap opportunities={filteredOpportunities} />
        </div>

        {/* Opportunities Grid */}
        <div className="bg-white rounded-lg shadow">
          <div className="px-6 py-4 border-b border-gray-200">
            <h2 className="text-lg font-medium text-gray-900">Placement Opportunities</h2>
          </div>
          
          {loading ? (
            <div className="p-8 text-center">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-inscenium-600 mx-auto"></div>
              <p className="mt-4 text-gray-600">Analyzing scenes...</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 p-6">
              {filteredOpportunities.map((opportunity) => (
                <SurfaceCard
                  key={opportunity.surface_id}
                  opportunity={opportunity}
                  selected={selectedSurface === opportunity.surface_id}
                  onClick={() => setSelectedSurface(opportunity.surface_id)}
                />
              ))}
            </div>
          )}
          
          {!loading && filteredOpportunities.length === 0 && (
            <div className="p-8 text-center">
              <MapIcon className="h-12 w-12 text-gray-400 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">No opportunities found</h3>
              <p className="text-gray-600">Try adjusting your filters.</p>
            </div>
          )}
        </div>
      </div>
    </>
  );
}