import { useMemo } from 'react';

interface Opportunity {
  surface_id: string;
  prs_score: number;
  surface_type: string;
}

interface PRSHeatmapProps {
  opportunities: Opportunity[];
}

export default function PRSHeatmap({ opportunities }: PRSHeatmapProps) {
  const heatmapData = useMemo(() => {
    // Create bins for PRS scores
    const bins = [
      { min: 90, max: 100, label: '90-100', color: 'bg-green-500' },
      { min: 80, max: 89.9, label: '80-89', color: 'bg-blue-500' },
      { min: 70, max: 79.9, label: '70-79', color: 'bg-yellow-500' },
      { min: 60, max: 69.9, label: '60-69', color: 'bg-orange-500' },
      { min: 0, max: 59.9, label: '0-59', color: 'bg-red-500' },
    ];

    return bins.map(bin => {
      const count = opportunities.filter(opp => 
        opp.prs_score >= bin.min && opp.prs_score <= bin.max
      ).length;
      
      const percentage = opportunities.length > 0 ? (count / opportunities.length) * 100 : 0;
      
      return {
        ...bin,
        count,
        percentage
      };
    });
  }, [opportunities]);

  const maxCount = Math.max(...heatmapData.map(d => d.count));

  return (
    <div className="space-y-4">
      {/* Legend */}
      <div className="flex items-center space-x-4 text-sm text-gray-600">
        <span>PRS Score Distribution:</span>
        <div className="flex items-center space-x-2">
          <span>Low</span>
          <div className="flex">
            <div className="w-3 h-3 bg-red-500"></div>
            <div className="w-3 h-3 bg-orange-500"></div>
            <div className="w-3 h-3 bg-yellow-500"></div>
            <div className="w-3 h-3 bg-blue-500"></div>
            <div className="w-3 h-3 bg-green-500"></div>
          </div>
          <span>High</span>
        </div>
      </div>

      {/* Heatmap Bars */}
      <div className="space-y-3">
        {heatmapData.map((bin) => (
          <div key={bin.label} className="flex items-center space-x-4">
            <div className="w-16 text-sm font-medium text-gray-700">
              {bin.label}
            </div>
            
            <div className="flex-1 relative">
              <div className="h-8 bg-gray-100 rounded-lg overflow-hidden">
                <div
                  className={`h-full ${bin.color} transition-all duration-300`}
                  style={{
                    width: maxCount > 0 ? `${(bin.count / maxCount) * 100}%` : '0%',
                    opacity: bin.count === 0 ? 0.1 : 0.8
                  }}
                ></div>
              </div>
              
              <div className="absolute inset-y-0 left-2 flex items-center">
                <span className="text-sm font-medium text-white drop-shadow">
                  {bin.count} ({bin.percentage.toFixed(1)}%)
                </span>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Summary Stats */}
      <div className="grid grid-cols-3 gap-4 pt-4 border-t">
        <div className="text-center">
          <div className="text-2xl font-bold text-green-600">
            {heatmapData.filter(d => d.min >= 80).reduce((sum, d) => sum + d.count, 0)}
          </div>
          <div className="text-sm text-gray-600">High Quality (80+)</div>
        </div>
        
        <div className="text-center">
          <div className="text-2xl font-bold text-blue-600">
            {opportunities.length > 0 ? (
              (opportunities.reduce((sum, opp) => sum + opp.prs_score, 0) / opportunities.length).toFixed(1)
            ) : (
              '0.0'
            )}
          </div>
          <div className="text-sm text-gray-600">Average PRS</div>
        </div>
        
        <div className="text-center">
          <div className="text-2xl font-bold text-purple-600">
            {opportunities.length}
          </div>
          <div className="text-sm text-gray-600">Total Surfaces</div>
        </div>
      </div>
    </div>
  );
}