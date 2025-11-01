import Head from 'next/head';
import { useState, useEffect } from 'react';
import { MagnifyingGlassIcon, FunnelIcon, EyeIcon, ClockIcon, MapIcon, ChartBarIcon } from '@heroicons/react/24/outline';
import { mockApiClient, PlacementOpportunity } from '../lib/api';

export default function Opportunities() {
  const [opportunities, setOpportunities] = useState<PlacementOpportunity[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [minPRS, setMinPRS] = useState<number>(0);
  const [surfaceType, setSurfaceType] = useState<string>('all');
  const [sortBy, setSortBy] = useState<'prs_score' | 'duration' | 'created_at'>('prs_score');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');

  useEffect(() => {
    loadOpportunities();
  }, [minPRS, surfaceType]);

  const loadOpportunities = async () => {
    setLoading(true);
    try {
      const response = await mockApiClient.getOpportunities({
        title_id: searchTerm || undefined,
        min_prs: minPRS || undefined,
      });
      
      if (response.data) {
        setOpportunities(response.data.opportunities);
      }
    } catch (error) {
      console.error('Error loading opportunities:', error);
    } finally {
      setLoading(false);
    }
  };

  const filteredAndSortedOpportunities = opportunities
    .filter(op => {
      if (surfaceType !== 'all' && op.surface_type !== surfaceType) return false;
      if (searchTerm && !op.title_id.toLowerCase().includes(searchTerm.toLowerCase())) return false;
      return true;
    })
    .sort((a, b) => {
      const aVal = a[sortBy];
      const bVal = b[sortBy];
      const multiplier = sortOrder === 'asc' ? 1 : -1;
      
      if (typeof aVal === 'number' && typeof bVal === 'number') {
        return (aVal - bVal) * multiplier;
      }
      return String(aVal).localeCompare(String(bVal)) * multiplier;
    });

  const getPRSColor = (score: number) => {
    if (score >= 90) return 'text-green-700 bg-green-100';
    if (score >= 80) return 'text-blue-700 bg-blue-100';
    if (score >= 70) return 'text-yellow-700 bg-yellow-100';
    return 'text-red-700 bg-red-100';
  };

  const getSurfaceTypeIcon = (type: string) => {
    switch (type) {
      case 'wall':
        return <MapIcon className="h-4 w-4" />;
      case 'table':
        return <div className="h-4 w-4 bg-current rounded-sm" />;
      case 'screen':
        return <div className="h-4 w-4 border-2 border-current" />;
      case 'billboard':
        return <div className="h-4 w-4 bg-current rounded" />;
      default:
        return <MapIcon className="h-4 w-4" />;
    }
  };

  return (
    <>
      <Head>
        <title>Opportunities - Inscenium CMS</title>
        <meta name="description" content="Browse placement opportunities" />
      </Head>

      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Placement Opportunities</h1>
            <p className="mt-2 text-gray-600">
              Discover high-quality placement opportunities across various content
            </p>
          </div>
          
          <button
            onClick={loadOpportunities}
            className="bg-inscenium-600 text-white px-4 py-2 rounded-lg hover:bg-inscenium-700 transition-colors"
          >
            Refresh
          </button>
        </div>

        {/* Filters */}
        <div className="bg-white rounded-lg shadow p-6">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            {/* Search */}
            <div className="relative">
              <MagnifyingGlassIcon className="h-5 w-5 absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" />
              <input
                type="text"
                placeholder="Search by title..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10 w-full rounded-lg border-gray-300 shadow-sm focus:border-inscenium-500 focus:ring-inscenium-500"
              />
            </div>

            {/* Min PRS Filter */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Min PRS Score
              </label>
              <input
                type="number"
                min="0"
                max="100"
                value={minPRS}
                onChange={(e) => setMinPRS(Number(e.target.value))}
                className="w-full rounded-lg border-gray-300 shadow-sm focus:border-inscenium-500 focus:ring-inscenium-500"
              />
            </div>

            {/* Surface Type Filter */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Surface Type
              </label>
              <select
                value={surfaceType}
                onChange={(e) => setSurfaceType(e.target.value)}
                className="w-full rounded-lg border-gray-300 shadow-sm focus:border-inscenium-500 focus:ring-inscenium-500"
              >
                <option value="all">All Types</option>
                <option value="wall">Wall</option>
                <option value="table">Table</option>
                <option value="screen">Screen</option>
                <option value="billboard">Billboard</option>
              </select>
            </div>

            {/* Sort */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Sort By
              </label>
              <div className="flex space-x-2">
                <select
                  value={sortBy}
                  onChange={(e) => setSortBy(e.target.value as any)}
                  className="flex-1 rounded-lg border-gray-300 shadow-sm focus:border-inscenium-500 focus:ring-inscenium-500"
                >
                  <option value="prs_score">PRS Score</option>
                  <option value="duration">Duration</option>
                  <option value="created_at">Created</option>
                </select>
                <button
                  onClick={() => setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc')}
                  className="px-3 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
                >
                  {sortOrder === 'asc' ? '↑' : '↓'}
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* Results */}
        <div className="bg-white rounded-lg shadow">
          {loading ? (
            <div className="p-8 text-center">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-inscenium-600 mx-auto"></div>
              <p className="mt-4 text-gray-600">Loading opportunities...</p>
            </div>
          ) : (
            <>
              <div className="px-6 py-4 border-b border-gray-200">
                <div className="flex items-center justify-between">
                  <h2 className="text-lg font-medium text-gray-900">
                    {filteredAndSortedOpportunities.length} opportunities found
                  </h2>
                  <div className="flex items-center space-x-2 text-sm text-gray-500">
                    <FunnelIcon className="h-4 w-4" />
                    <span>Filtered and sorted</span>
                  </div>
                </div>
              </div>
              
              <div className="divide-y divide-gray-200">
                {filteredAndSortedOpportunities.map((opportunity) => (
                  <div key={opportunity.surface_id} className="p-6 hover:bg-gray-50 transition-colors">
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center space-x-3 mb-2">
                          <h3 className="text-lg font-medium text-gray-900">
                            {opportunity.surface_id}
                          </h3>
                          <div className="flex items-center space-x-1 text-gray-500">
                            {getSurfaceTypeIcon(opportunity.surface_type)}
                            <span className="text-sm capitalize">{opportunity.surface_type}</span>
                          </div>
                          <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getPRSColor(opportunity.prs_score)}`}>
                            PRS {opportunity.prs_score}
                          </span>
                        </div>
                        
                        <p className="text-gray-600 mb-3">{opportunity.title_id.replace(/_/g, ' ')}</p>
                        
                        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 text-sm">
                          <div className="flex items-center space-x-2">
                            <ClockIcon className="h-4 w-4 text-gray-400" />
                            <span>{opportunity.duration.toFixed(1)}s duration</span>
                          </div>
                          <div className="flex items-center space-x-2">
                            <EyeIcon className="h-4 w-4 text-gray-400" />
                            <span>{opportunity.visibility_score}% visibility</span>
                          </div>
                          <div className="flex items-center space-x-2">
                            <ChartBarIcon className="h-4 w-4 text-gray-400" />
                            <span>{opportunity.area_pixels?.toLocaleString() || 'N/A'} pixels</span>
                          </div>
                          <div className="flex items-center space-x-2">
                            <MapIcon className="h-4 w-4 text-gray-400" />
                            <span>{opportunity.area_world_m2?.toFixed(1) || 'N/A'} m²</span>
                          </div>
                        </div>
                        
                        {opportunity.restrictions && (
                          <div className="mt-3">
                            <div className="flex flex-wrap gap-1">
                              {JSON.parse(opportunity.restrictions).map((restriction: string, idx: number) => (
                                <span
                                  key={idx}
                                  className="inline-flex items-center px-2 py-1 rounded-md text-xs font-medium bg-gray-100 text-gray-800"
                                >
                                  {restriction}
                                </span>
                              ))}
                            </div>
                          </div>
                        )}
                        
                        <div className="mt-3 text-xs text-gray-500">
                          Created: {new Date(opportunity.created_at).toLocaleString()}
                        </div>
                      </div>
                      
                      <div className="ml-6">
                        <button className="bg-inscenium-600 text-white px-4 py-2 rounded-lg hover:bg-inscenium-700 transition-colors text-sm">
                          Book Placement
                        </button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
              
              {filteredAndSortedOpportunities.length === 0 && (
                <div className="p-8 text-center">
                  <MagnifyingGlassIcon className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                  <h3 className="text-lg font-medium text-gray-900 mb-2">No opportunities found</h3>
                  <p className="text-gray-600">Try adjusting your filters or search criteria.</p>
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </>
  );
}