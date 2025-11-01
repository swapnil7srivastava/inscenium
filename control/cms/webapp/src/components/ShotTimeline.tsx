import { useMemo } from 'react';

interface ShotEvent {
  timestamp: number;
  type: 'cut' | 'opportunity' | 'booking';
  surface_id?: string;
  prs_score?: number;
}

interface ShotTimelineProps {
  duration: number;
  events: ShotEvent[];
  currentTime?: number;
}

export default function ShotTimeline({ duration, events, currentTime = 0 }: ShotTimelineProps) {
  const timelineEvents = useMemo(() => {
    return events.map(event => ({
      ...event,
      position: (event.timestamp / duration) * 100
    }));
  }, [events, duration]);

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const getEventColor = (type: string) => {
    switch (type) {
      case 'cut':
        return 'bg-gray-400';
      case 'opportunity':
        return 'bg-blue-500';
      case 'booking':
        return 'bg-green-500';
      default:
        return 'bg-gray-300';
    }
  };

  const currentPosition = (currentTime / duration) * 100;

  return (
    <div className="w-full">
      {/* Timeline Header */}
      <div className="flex items-center justify-between mb-2 text-sm text-gray-600">
        <span>0:00</span>
        <span className="text-gray-900 font-medium">Shot Timeline</span>
        <span>{formatTime(duration)}</span>
      </div>

      {/* Timeline Track */}
      <div className="relative h-8 bg-gray-200 rounded-lg overflow-hidden">
        {/* Background segments */}
        <div className="absolute inset-0 bg-gradient-to-r from-gray-100 via-gray-50 to-gray-100"></div>

        {/* Events */}
        {timelineEvents.map((event, index) => (
          <div
            key={index}
            className={`absolute top-1 bottom-1 w-1 ${getEventColor(event.type)} rounded-full`}
            style={{ left: `${event.position}%` }}
            title={`${event.type} at ${formatTime(event.timestamp)}${event.surface_id ? ` - ${event.surface_id}` : ''}`}
          >
            {/* Event marker */}
            <div className={`w-3 h-3 ${getEventColor(event.type)} rounded-full -ml-1 -mt-1 border-2 border-white shadow-sm`}></div>
          </div>
        ))}

        {/* Current time indicator */}
        <div
          className="absolute top-0 bottom-0 w-0.5 bg-red-500 z-10"
          style={{ left: `${currentPosition}%` }}
        >
          <div className="w-3 h-3 bg-red-500 rounded-full -ml-1 -mt-1 border-2 border-white shadow"></div>
        </div>

        {/* Time markers */}
        {[...Array(5)].map((_, i) => {
          const position = (i / 4) * 100;
          const time = (i / 4) * duration;
          return (
            <div
              key={i}
              className="absolute top-0 bottom-0 w-px bg-gray-300"
              style={{ left: `${position}%` }}
            >
              <div className="absolute -bottom-5 -ml-4 text-xs text-gray-500 w-8 text-center">
                {formatTime(time)}
              </div>
            </div>
          );
        })}
      </div>

      {/* Legend */}
      <div className="flex items-center justify-center space-x-6 mt-4 text-xs">
        <div className="flex items-center space-x-1">
          <div className="w-2 h-2 bg-gray-400 rounded-full"></div>
          <span>Scene Cut</span>
        </div>
        <div className="flex items-center space-x-1">
          <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
          <span>Opportunity</span>
        </div>
        <div className="flex items-center space-x-1">
          <div className="w-2 h-2 bg-green-500 rounded-full"></div>
          <span>Booking</span>
        </div>
        <div className="flex items-center space-x-1">
          <div className="w-2 h-2 bg-red-500 rounded-full"></div>
          <span>Current Time</span>
        </div>
      </div>

      {/* Event Summary */}
      {events.length > 0 && (
        <div className="mt-4 p-3 bg-gray-50 rounded-lg">
          <div className="text-sm text-gray-700">
            <strong>{events.length}</strong> events in timeline:
          </div>
          <div className="flex space-x-4 mt-1 text-xs text-gray-600">
            <span>{events.filter(e => e.type === 'cut').length} cuts</span>
            <span>{events.filter(e => e.type === 'opportunity').length} opportunities</span>
            <span>{events.filter(e => e.type === 'booking').length} bookings</span>
          </div>
        </div>
      )}
    </div>
  );
}