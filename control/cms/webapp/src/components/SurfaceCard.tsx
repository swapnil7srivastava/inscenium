import { ClockIcon, EyeIcon, MapIcon } from '@heroicons/react/24/outline';

interface Opportunity {
  surface_id: string;
  title_id: string;
  shot_id: string;
  prs_score: number;
  surface_type: string;
  visibility_score: number;
  duration: number;
}

interface SurfaceCardProps {
  opportunity: Opportunity;
  selected?: boolean;
  onClick?: () => void;
}

export default function SurfaceCard({ opportunity, selected = false, onClick }: SurfaceCardProps) {
  const getPRSColor = (score: number) => {
    if (score >= 90) return 'text-green-700 bg-green-100';
    if (score >= 80) return 'text-blue-700 bg-blue-100';
    if (score >= 70) return 'text-yellow-700 bg-yellow-100';
    return 'text-red-700 bg-red-100';
  };

  const getSurfaceIcon = () => {
    switch (opportunity.surface_type) {
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
    <div
      className={`relative rounded-lg border-2 p-4 cursor-pointer transition-all hover:shadow-md ${
        selected 
          ? 'border-inscenium-500 bg-inscenium-50' 
          : 'border-gray-200 hover:border-gray-300'
      }`}
      onClick={onClick}
    >
      {/* Header */}
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center space-x-2">
          <div className="text-gray-500">
            {getSurfaceIcon()}
          </div>
          <h3 className="font-medium text-gray-900 truncate">
            {opportunity.surface_id}
          </h3>
        </div>
        
        <span className={`px-2 py-1 rounded-full text-xs font-medium ${getPRSColor(opportunity.prs_score)}`}>
          {opportunity.prs_score.toFixed(1)}
        </span>
      </div>

      {/* Content */}
      <div className="space-y-2">
        <p className="text-sm text-gray-600 truncate">
          {opportunity.title_id.replace(/_/g, ' ')}
        </p>
        
        <div className="flex items-center justify-between text-xs text-gray-500">
          <div className="flex items-center space-x-1">
            <ClockIcon className="h-3 w-3" />
            <span>{opportunity.duration.toFixed(1)}s</span>
          </div>
          
          <div className="flex items-center space-x-1">
            <EyeIcon className="h-3 w-3" />
            <span>{opportunity.visibility_score}%</span>
          </div>
          
          <div className="capitalize">
            {opportunity.surface_type}
          </div>
        </div>
      </div>

      {/* Visual indicator for high-quality surfaces */}
      {opportunity.prs_score >= 90 && (
        <div className="absolute top-2 right-2 w-2 h-2 bg-green-400 rounded-full"></div>
      )}
      
      {/* Selection indicator */}
      {selected && (
        <div className="absolute inset-0 ring-2 ring-inscenium-500 rounded-lg pointer-events-none"></div>
      )}
    </div>
  );
}