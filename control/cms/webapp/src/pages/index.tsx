import Head from 'next/head';
import { useState } from 'react';
import { Chart as ChartJS, CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend } from 'chart.js';
import { Line } from 'react-chartjs-2';
import { CalendarDaysIcon, EyeIcon, CurrencyDollarIcon, ChartBarIcon } from '@heroicons/react/24/outline';

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend);

// Mock data for dashboard
const mockStats = {
  totalImpressions: 2847392,
  totalRevenue: 15432.50,
  averagePRS: 87.3,
  activeBookings: 127,
};

const mockChartData = {
  labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
  datasets: [
    {
      label: 'PRS Score',
      data: [82.1, 85.4, 87.2, 89.1, 87.8, 90.2],
      borderColor: 'rgb(59, 130, 246)',
      backgroundColor: 'rgba(59, 130, 246, 0.1)',
      tension: 0.3,
    },
    {
      label: 'Impressions (K)',
      data: [145, 178, 201, 234, 267, 298],
      borderColor: 'rgb(16, 185, 129)',
      backgroundColor: 'rgba(16, 185, 129, 0.1)',
      tension: 0.3,
      yAxisID: 'y1',
    },
  ],
};

const chartOptions = {
  responsive: true,
  plugins: {
    legend: {
      position: 'top' as const,
    },
    title: {
      display: true,
      text: 'Performance Overview',
    },
  },
  scales: {
    y: {
      type: 'linear' as const,
      display: true,
      position: 'left' as const,
      title: {
        display: true,
        text: 'PRS Score',
      },
    },
    y1: {
      type: 'linear' as const,
      display: true,
      position: 'right' as const,
      title: {
        display: true,
        text: 'Impressions (K)',
      },
      grid: {
        drawOnChartArea: false,
      },
    },
  },
};

export default function Dashboard() {
  const [timeRange, setTimeRange] = useState('7d');

  return (
    <>
      <Head>
        <title>Dashboard - Inscenium CMS</title>
        <meta name="description" content="Inscenium placement opportunities dashboard" />
      </Head>

      <div className="space-y-8">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>
            <p className="mt-2 text-gray-600">
              Overview of your placement performance and opportunities
            </p>
          </div>
          
          <div className="flex items-center space-x-4">
            <select
              value={timeRange}
              onChange={(e) => setTimeRange(e.target.value)}
              className="rounded-lg border-gray-300 shadow-sm focus:border-inscenium-500 focus:ring-inscenium-500"
            >
              <option value="24h">Last 24 hours</option>
              <option value="7d">Last 7 days</option>
              <option value="30d">Last 30 days</option>
              <option value="90d">Last 90 days</option>
            </select>
          </div>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4">
          <div className="bg-white overflow-hidden shadow rounded-lg">
            <div className="p-5">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <EyeIcon className="h-6 w-6 text-gray-400" />
                </div>
                <div className="ml-5 w-0 flex-1">
                  <dl>
                    <dt className="text-sm font-medium text-gray-500 truncate">
                      Total Impressions
                    </dt>
                    <dd className="text-lg font-medium text-gray-900">
                      {mockStats.totalImpressions.toLocaleString()}
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
                  <CurrencyDollarIcon className="h-6 w-6 text-gray-400" />
                </div>
                <div className="ml-5 w-0 flex-1">
                  <dl>
                    <dt className="text-sm font-medium text-gray-500 truncate">
                      Revenue
                    </dt>
                    <dd className="text-lg font-medium text-gray-900">
                      ${mockStats.totalRevenue.toLocaleString()}
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
                  <ChartBarIcon className="h-6 w-6 text-gray-400" />
                </div>
                <div className="ml-5 w-0 flex-1">
                  <dl>
                    <dt className="text-sm font-medium text-gray-500 truncate">
                      Average PRS Score
                    </dt>
                    <dd className="text-lg font-medium text-gray-900">
                      {mockStats.averagePRS}
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
                  <CalendarDaysIcon className="h-6 w-6 text-gray-400" />
                </div>
                <div className="ml-5 w-0 flex-1">
                  <dl>
                    <dt className="text-sm font-medium text-gray-500 truncate">
                      Active Bookings
                    </dt>
                    <dd className="text-lg font-medium text-gray-900">
                      {mockStats.activeBookings}
                    </dd>
                  </dl>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Chart */}
        <div className="bg-white shadow rounded-lg p-6">
          <h2 className="text-lg font-medium text-gray-900 mb-4">Performance Trends</h2>
          <div className="h-80">
            <Line data={mockChartData} options={chartOptions} />
          </div>
        </div>

        {/* Recent Activity */}
        <div className="bg-white shadow rounded-lg">
          <div className="px-6 py-4 border-b border-gray-200">
            <h2 className="text-lg font-medium text-gray-900">Recent Activity</h2>
          </div>
          <div className="divide-y divide-gray-200">
            {[
              {
                id: 1,
                type: 'booking',
                message: 'New booking for Movie Trailer - Surface #247',
                time: '2 minutes ago',
                status: 'success',
              },
              {
                id: 2,
                type: 'opportunity',
                message: 'High PRS opportunity detected in Sports Highlight',
                time: '15 minutes ago',
                status: 'info',
              },
              {
                id: 3,
                type: 'quality',
                message: 'PRS score improved to 92.1 for Campaign #45',
                time: '1 hour ago',
                status: 'success',
              },
            ].map((activity) => (
              <div key={activity.id} className="px-6 py-4">
                <div className="flex items-center space-x-3">
                  <div
                    className={`w-2 h-2 rounded-full ${
                      activity.status === 'success'
                        ? 'bg-green-400'
                        : activity.status === 'info'
                        ? 'bg-blue-400'
                        : 'bg-yellow-400'
                    }`}
                  />
                  <div className="flex-1">
                    <p className="text-sm text-gray-900">{activity.message}</p>
                    <p className="text-xs text-gray-500">{activity.time}</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </>
  );
}