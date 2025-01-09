import React from 'react';
import { useDashboard } from '../hooks/useDashboard';
import { ClipboardDocumentListIcon, UserGroupIcon, BellAlertIcon, CheckCircleIcon } from '@heroicons/react/24/outline';

export default function Dashboard() {
  const { stats, workOrders, technicianStatus } = useDashboard();

  const stats_items = [
    {
      name: 'Active Work Orders',
      value: stats.data.active_work_orders,
      icon: ClipboardDocumentListIcon,
      color: 'text-blue-600',
    },
    {
      name: 'Active Technicians',
      value: stats.data.technicians_active,
      icon: UserGroupIcon,
      color: 'text-green-600',
    },
    {
      name: 'Pending Work Orders',
      value: stats.data.pending_work_orders,
      icon: BellAlertIcon,
      color: 'text-yellow-600',
    },
    {
      name: 'Completed Today',
      value: stats.data.completed_today,
      icon: CheckCircleIcon,
      color: 'text-indigo-600',
    },
  ];

  return (
    <div className="min-h-screen bg-gray-100">
      <main className="py-10">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          {/* Stats */}
          <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4">
            {stats_items.map((item) => (
              <div
                key={item.name}
                className="relative overflow-hidden rounded-lg bg-white px-4 pb-12 pt-5 shadow sm:px-6 sm:pt-6"
              >
                <dt>
                  <div className={`absolute rounded-md p-3 ${item.color} bg-opacity-10`}>
                    <item.icon className={`h-6 w-6 ${item.color}`} aria-hidden="true" />
                  </div>
                  <p className="ml-16 truncate text-sm font-medium text-gray-500">{item.name}</p>
                </dt>
                <dd className="ml-16 flex items-baseline pb-6 sm:pb-7">
                  <p className="text-2xl font-semibold text-gray-900">{item.value}</p>
                </dd>
              </div>
            ))}
          </div>

          {/* Work Orders Table */}
          <div className="mt-8">
            <div className="sm:flex sm:items-center">
              <div className="sm:flex-auto">
                <h1 className="text-base font-semibold leading-6 text-gray-900">Active Work Orders</h1>
                <p className="mt-2 text-sm text-gray-700">
                  A list of all active work orders including customer details and assigned technician.
                </p>
              </div>
            </div>
            <div className="mt-8 flow-root">
              <div className="-mx-4 -my-2 overflow-x-auto sm:-mx-6 lg:-mx-8">
                <div className="inline-block min-w-full py-2 align-middle sm:px-6 lg:px-8">
                  <table className="min-w-full divide-y divide-gray-300">
                    <thead>
                      <tr>
                        <th className="py-3.5 pl-4 pr-3 text-left text-sm font-semibold text-gray-900 sm:pl-0">
                          Customer
                        </th>
                        <th className="px-3 py-3.5 text-left text-sm font-semibold text-gray-900">
                          Description
                        </th>
                        <th className="px-3 py-3.5 text-left text-sm font-semibold text-gray-900">
                          Technician
                        </th>
                        <th className="px-3 py-3.5 text-left text-sm font-semibold text-gray-900">
                          Status
                        </th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-200">
                      {workOrders.data
                        .filter(wo => wo.status === 'in_progress' || wo.status === 'pending')
                        .map((workOrder) => (
                          <tr key={workOrder.id}>
                            <td className="whitespace-nowrap py-4 pl-4 pr-3 text-sm font-medium text-gray-900 sm:pl-0">
                              {workOrder.customer?.name}
                            </td>
                            <td className="whitespace-nowrap px-3 py-4 text-sm text-gray-500">
                              {workOrder.brief_description}
                            </td>
                            <td className="whitespace-nowrap px-3 py-4 text-sm text-gray-500">
                              {workOrder.technician?.name}
                            </td>
                            <td className="whitespace-nowrap px-3 py-4 text-sm text-gray-500">
                              <span className={`inline-flex items-center rounded-md px-2 py-1 text-xs font-medium
                                ${workOrder.status === 'in_progress' ? 'bg-green-50 text-green-700' : 
                                  workOrder.status === 'pending' ? 'bg-yellow-50 text-yellow-700' : 
                                  'bg-gray-50 text-gray-700'}`}>
                                {workOrder.status}
                              </span>
                            </td>
                          </tr>
                        ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          </div>

          {/* Technician Status */}
          <div className="mt-8">
            <div className="sm:flex sm:items-center">
              <div className="sm:flex-auto">
                <h1 className="text-base font-semibold leading-6 text-gray-900">Technician Status</h1>
                <p className="mt-2 text-sm text-gray-700">
                  Current status and location of all technicians.
                </p>
              </div>
            </div>
            <div className="mt-8 flow-root">
              <div className="-mx-4 -my-2 overflow-x-auto sm:-mx-6 lg:-mx-8">
                <div className="inline-block min-w-full py-2 align-middle sm:px-6 lg:px-8">
                  <table className="min-w-full divide-y divide-gray-300">
                    <thead>
                      <tr>
                        <th className="py-3.5 pl-4 pr-3 text-left text-sm font-semibold text-gray-900 sm:pl-0">
                          Technician
                        </th>
                        <th className="px-3 py-3.5 text-left text-sm font-semibold text-gray-900">
                          Status
                        </th>
                        <th className="px-3 py-3.5 text-left text-sm font-semibold text-gray-900">
                          Current Work Order
                        </th>
                        <th className="px-3 py-3.5 text-left text-sm font-semibold text-gray-900">
                          Clock In Time
                        </th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-200">
                      {technicianStatus.data.map((tech) => (
                        <tr key={tech.technician_id}>
                          <td className="whitespace-nowrap py-4 pl-4 pr-3 text-sm font-medium text-gray-900 sm:pl-0">
                            {tech.name}
                          </td>
                          <td className="whitespace-nowrap px-3 py-4 text-sm text-gray-500">
                            <span className={`inline-flex items-center rounded-md px-2 py-1 text-xs font-medium
                              ${tech.status === 'active' ? 'bg-green-50 text-green-700' : 'bg-gray-50 text-gray-700'}`}>
                              {tech.status}
                            </span>
                          </td>
                          <td className="whitespace-nowrap px-3 py-4 text-sm text-gray-500">
                            {tech.current_work_order?.title || 'None'}
                          </td>
                          <td className="whitespace-nowrap px-3 py-4 text-sm text-gray-500">
                            {tech.last_clock_record ? 
                              new Date(tech.last_clock_record.clock_in_time).toLocaleTimeString() : 
                              'Not clocked in'}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
} 