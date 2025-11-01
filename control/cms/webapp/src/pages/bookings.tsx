import Head from 'next/head';
import { useState, useEffect } from 'react';
import { CalendarDaysIcon, CurrencyDollarIcon, EyeIcon, CheckCircleIcon, ClockIcon, XCircleIcon } from '@heroicons/react/24/outline';
import { mockApiClient, Booking } from '../lib/api';

// Mock booking data
const mockBookings: Booking[] = [
  {
    booking_id: 'booking_surface_001_1705320900',
    surface_id: 'surface_001',
    advertiser_id: 'advertiser_nike',
    campaign_id: 'campaign_swoosh_2024',
    bid_amount_cpm: 5.50,
    final_cpm_rate: 5.50,
    estimated_impressions: 1000,
    actual_impressions: 847,
    status: 'active',
    booking_time: '2024-01-15T10:35:00Z',
    confirmation_time: '2024-01-15T10:35:30Z'
  },
  {
    booking_id: 'booking_surface_002_1705320800',
    surface_id: 'surface_002',
    advertiser_id: 'advertiser_cocacola',
    campaign_id: 'campaign_refresh_2024',
    bid_amount_cpm: 7.25,
    final_cpm_rate: 7.00,
    estimated_impressions: 1500,
    actual_impressions: 1342,
    status: 'completed',
    booking_time: '2024-01-15T09:20:00Z',
    confirmation_time: '2024-01-15T09:20:15Z'
  },
  {
    booking_id: 'booking_surface_003_1705321000',
    surface_id: 'surface_003',
    advertiser_id: 'advertiser_apple',
    campaign_id: 'campaign_iphone_2024',
    bid_amount_cpm: 12.00,
    final_cpm_rate: 11.75,
    estimated_impressions: 800,
    actual_impressions: 0,
    status: 'pending',
    booking_time: '2024-01-15T11:45:00Z'
  },
  {
    booking_id: 'booking_surface_004_1705320700',
    surface_id: 'surface_004',
    advertiser_id: 'advertiser_tesla',
    campaign_id: 'campaign_model_y_2024',
    bid_amount_cpm: 9.80,
    final_cmp_rate: 9.50,
    estimated_impressions: 1200,
    actual_impressions: 1156,
    status: 'completed',
    booking_time: '2024-01-15T08:15:00Z',
    confirmation_time: '2024-01-15T08:15:20Z'
  },
  {
    booking_id: 'booking_surface_005_1705321100',
    surface_id: 'surface_005',
    advertiser_id: 'advertiser_amazon',
    campaign_id: 'campaign_prime_2024',
    bid_amount_cpm: 6.30,
    final_cpm_rate: 6.30,
    estimated_impressions: 900,
    actual_impressions: 0,
    status: 'cancelled',
    booking_time: '2024-01-15T12:30:00Z'
  }
];

export default function Bookings() {
  const [bookings, setBookings] = useState<Booking[]>([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedBooking, setSelectedBooking] = useState<Booking | null>(null);
  const [showDetails, setShowDetails] = useState(false);

  useEffect(() => {
    loadBookings();
  }, []);

  const loadBookings = async () => {
    setLoading(true);
    try {
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 800));
      setBookings(mockBookings);
    } catch (error) {
      console.error('Error loading bookings:', error);
    } finally {
      setLoading(false);
    }
  };

  const filteredBookings = bookings.filter(booking => {
    if (statusFilter !== 'all' && booking.status !== statusFilter) return false;
    if (searchTerm && !booking.booking_id.toLowerCase().includes(searchTerm.toLowerCase()) && 
        !booking.advertiser_id.toLowerCase().includes(searchTerm.toLowerCase())) return false;
    return true;
  });

  const getStatusBadge = (status: Booking['status']) => {
    const badges = {
      pending: 'bg-yellow-100 text-yellow-800',
      confirmed: 'bg-blue-100 text-blue-800', 
      active: 'bg-green-100 text-green-800',
      completed: 'bg-gray-100 text-gray-800',
      cancelled: 'bg-red-100 text-red-800'
    };
    
    const icons = {
      pending: <ClockIcon className="h-4 w-4" />,
      confirmed: <CheckCircleIcon className="h-4 w-4" />,
      active: <CheckCircleIcon className="h-4 w-4" />,
      completed: <CheckCircleIcon className="h-4 w-4" />,
      cancelled: <XCircleIcon className="h-4 w-4" />
    };

    return (
      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${badges[status]}`}>
        {icons[status]}
        <span className="ml-1 capitalize">{status}</span>
      </span>
    );
  };

  const calculateROI = (booking: Booking) => {
    if (!booking.actual_impressions || booking.actual_impressions === 0) return 'N/A';
    const actualCost = (booking.actual_impressions / 1000) * (booking.final_cpm_rate || booking.bid_amount_cpm);
    const estimatedCost = (booking.estimated_impressions / 1000) * booking.bid_amount_cpm;
    const savings = estimatedCost - actualCost;
    const roi = (savings / estimatedCost) * 100;
    return roi.toFixed(1) + '%';
  };

  const openBookingDetails = (booking: Booking) => {
    setSelectedBooking(booking);
    setShowDetails(true);
  };

  const closeBookingDetails = () => {
    setSelectedBooking(null);
    setShowDetails(false);
  };

  const totalSpent = bookings
    .filter(b => b.actual_impressions && b.actual_impressions > 0)
    .reduce((sum, b) => sum + ((b.actual_impressions! / 1000) * (b.final_cmp_rate || b.bid_amount_cpm)), 0);

  const totalImpressions = bookings.reduce((sum, b) => sum + (b.actual_impressions || 0), 0);

  return (
    <>
      <Head>
        <title>Bookings - Inscenium CMS</title>
        <meta name="description" content="Manage placement bookings" />
      </Head>

      <div className="space-y-6">
        {/* Header with Stats */}
        <div>
          <div className="flex items-center justify-between mb-6">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">Placement Bookings</h1>
              <p className="mt-2 text-gray-600">
                Track and manage your placement bookings
              </p>
            </div>
            
            <button
              onClick={loadBookings}
              className="bg-inscenium-600 text-white px-4 py-2 rounded-lg hover:bg-inscenium-700 transition-colors"
            >
              Refresh
            </button>
          </div>

          {/* Summary Stats */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
            <div className="bg-white p-4 rounded-lg shadow">
              <div className="flex items-center">
                <CalendarDaysIcon className="h-8 w-8 text-blue-500" />
                <div className="ml-3">
                  <p className="text-sm font-medium text-gray-500">Total Bookings</p>
                  <p className="text-2xl font-bold text-gray-900">{bookings.length}</p>
                </div>
              </div>
            </div>
            
            <div className="bg-white p-4 rounded-lg shadow">
              <div className="flex items-center">
                <EyeIcon className="h-8 w-8 text-green-500" />
                <div className="ml-3">
                  <p className="text-sm font-medium text-gray-500">Total Impressions</p>
                  <p className="text-2xl font-bold text-gray-900">{totalImpressions.toLocaleString()}</p>
                </div>
              </div>
            </div>
            
            <div className="bg-white p-4 rounded-lg shadow">
              <div className="flex items-center">
                <CurrencyDollarIcon className="h-8 w-8 text-yellow-500" />
                <div className="ml-3">
                  <p className="text-sm font-medium text-gray-500">Total Spent</p>
                  <p className="text-2xl font-bold text-gray-900">${totalSpent.toLocaleString(undefined, {maximumFractionDigits: 2})}</p>
                </div>
              </div>
            </div>
            
            <div className="bg-white p-4 rounded-lg shadow">
              <div className="flex items-center">
                <CheckCircleIcon className="h-8 w-8 text-purple-500" />
                <div className="ml-3">
                  <p className="text-sm font-medium text-gray-500">Active Bookings</p>
                  <p className="text-2xl font-bold text-gray-900">
                    {bookings.filter(b => b.status === 'active' || b.status === 'confirmed').length}
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Filters */}
        <div className="bg-white rounded-lg shadow p-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Search
              </label>
              <input
                type="text"
                placeholder="Search by booking ID or advertiser..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full rounded-lg border-gray-300 shadow-sm focus:border-inscenium-500 focus:ring-inscenium-500"
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Status Filter
              </label>
              <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                className="w-full rounded-lg border-gray-300 shadow-sm focus:border-inscenium-500 focus:ring-inscenium-500"
              >
                <option value="all">All Statuses</option>
                <option value="pending">Pending</option>
                <option value="confirmed">Confirmed</option>
                <option value="active">Active</option>
                <option value="completed">Completed</option>
                <option value="cancelled">Cancelled</option>
              </select>
            </div>
          </div>
        </div>

        {/* Bookings Table */}
        <div className="bg-white rounded-lg shadow overflow-hidden">
          {loading ? (
            <div className="p-8 text-center">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-inscenium-600 mx-auto"></div>
              <p className="mt-4 text-gray-600">Loading bookings...</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Booking
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Advertiser
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Status
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Impressions
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      CPM
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Created
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {filteredBookings.map((booking) => (
                    <tr key={booking.booking_id} className="hover:bg-gray-50">
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div>
                          <div className="text-sm font-medium text-gray-900">
                            {booking.booking_id}
                          </div>
                          <div className="text-sm text-gray-500">
                            {booking.surface_id}
                          </div>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm text-gray-900">{booking.advertiser_id.replace('advertiser_', '')}</div>
                        <div className="text-sm text-gray-500">{booking.campaign_id.replace('campaign_', '')}</div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        {getStatusBadge(booking.status)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        <div>{booking.actual_impressions?.toLocaleString() || 0} / {booking.estimated_impressions.toLocaleString()}</div>
                        <div className="text-xs text-gray-500">
                          {booking.actual_impressions ? 
                            `${((booking.actual_impressions / booking.estimated_impressions) * 100).toFixed(1)}% of estimate` : 
                            'Not started'
                          }
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        <div>${booking.final_cmp_rate || booking.final_cpm_rate || booking.bid_amount_cpm}</div>
                        {booking.final_cpm_rate && booking.final_cpm_rate !== booking.bid_amount_cpm && (
                          <div className="text-xs text-green-600">
                            Saved ${(booking.bid_amount_cpm - booking.final_cpm_rate).toFixed(2)}
                          </div>
                        )}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {new Date(booking.booking_time).toLocaleDateString()}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                        <button
                          onClick={() => openBookingDetails(booking)}
                          className="text-inscenium-600 hover:text-inscenium-900 mr-3"
                        >
                          View Details
                        </button>
                        {booking.status === 'active' && (
                          <button className="text-red-600 hover:text-red-900">
                            Cancel
                          </button>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
              
              {filteredBookings.length === 0 && (
                <div className="p-8 text-center">
                  <CalendarDaysIcon className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                  <h3 className="text-lg font-medium text-gray-900 mb-2">No bookings found</h3>
                  <p className="text-gray-600">Try adjusting your search or filter criteria.</p>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Booking Details Modal */}
        {showDetails && selectedBooking && (
          <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
            <div className="relative top-20 mx-auto p-5 border w-11/12 md:w-3/4 lg:w-1/2 shadow-lg rounded-md bg-white">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-medium text-gray-900">Booking Details</h3>
                <button
                  onClick={closeBookingDetails}
                  className="text-gray-400 hover:text-gray-600"
                >
                  <XCircleIcon className="h-6 w-6" />
                </button>
              </div>
              
              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-500">Booking ID</label>
                    <p className="mt-1 text-sm text-gray-900">{selectedBooking.booking_id}</p>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-500">Status</label>
                    <div className="mt-1">{getStatusBadge(selectedBooking.status)}</div>
                  </div>
                </div>
                
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-500">Surface ID</label>
                    <p className="mt-1 text-sm text-gray-900">{selectedBooking.surface_id}</p>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-500">Advertiser</label>
                    <p className="mt-1 text-sm text-gray-900">{selectedBooking.advertiser_id.replace('advertiser_', '')}</p>
                  </div>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-500">Campaign</label>
                  <p className="mt-1 text-sm text-gray-900">{selectedBooking.campaign_id.replace('campaign_', '')}</p>
                </div>
                
                <div className="grid grid-cols-3 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-500">Bid CPM</label>
                    <p className="mt-1 text-sm text-gray-900">${selectedBooking.bid_amount_cpm}</p>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-500">Final CPM</label>
                    <p className="mt-1 text-sm text-gray-900">
                      ${selectedBooking.final_cmp_rate || selectedBooking.final_cpm_rate || selectedBooking.bid_amount_cpm}
                    </p>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-500">ROI</label>
                    <p className="mt-1 text-sm text-gray-900">{calculateROI(selectedBooking)}</p>
                  </div>
                </div>
                
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-500">Estimated Impressions</label>
                    <p className="mt-1 text-sm text-gray-900">{selectedBooking.estimated_impressions.toLocaleString()}</p>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-500">Actual Impressions</label>
                    <p className="mt-1 text-sm text-gray-900">
                      {selectedBooking.actual_impressions?.toLocaleString() || 0}
                    </p>
                  </div>
                </div>
                
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-500">Booking Time</label>
                    <p className="mt-1 text-sm text-gray-900">
                      {new Date(selectedBooking.booking_time).toLocaleString()}
                    </p>
                  </div>
                  {selectedBooking.confirmation_time && (
                    <div>
                      <label className="block text-sm font-medium text-gray-500">Confirmation Time</label>
                      <p className="mt-1 text-sm text-gray-900">
                        {new Date(selectedBooking.confirmation_time).toLocaleString()}
                      </p>
                    </div>
                  )}
                </div>
              </div>
              
              <div className="mt-6 flex justify-end space-x-3">
                <button
                  onClick={closeBookingDetails}
                  className="px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 hover:bg-gray-50"
                >
                  Close
                </button>
                {selectedBooking.status === 'active' && (
                  <button className="px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-red-600 hover:bg-red-700">
                    Cancel Booking
                  </button>
                )}
              </div>
            </div>
          </div>
        )}
      </div>
    </>
  );
}