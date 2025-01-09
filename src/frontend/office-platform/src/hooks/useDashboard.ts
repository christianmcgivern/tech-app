import { useQuery } from '@tanstack/react-query';
import { api } from '../services/api';

export function useDashboard() {
    const workOrders = useQuery({
        queryKey: ['workOrders'],
        queryFn: api.getWorkOrders
    });

    const technicians = useQuery({
        queryKey: ['technicians'],
        queryFn: api.getTechnicians
    });

    const technicianStatus = useQuery({
        queryKey: ['technicianStatus'],
        queryFn: api.getTechnicianStatus
    });

    const dashboardStats = useQuery({
        queryKey: ['dashboardStats'],
        queryFn: api.getDashboardStats
    });

    return {
        workOrders: {
            data: workOrders.data ?? [],
            isLoading: workOrders.isLoading,
            error: workOrders.error
        },
        technicians: {
            data: technicians.data ?? [],
            isLoading: technicians.isLoading,
            error: technicians.error
        },
        technicianStatus: {
            data: technicianStatus.data ?? [],
            isLoading: technicianStatus.isLoading,
            error: technicianStatus.error
        },
        stats: {
            data: dashboardStats.data ?? {
                active_work_orders: 0,
                completed_today: 0,
                technicians_active: 0,
                pending_work_orders: 0
            },
            isLoading: dashboardStats.isLoading,
            error: dashboardStats.error
        }
    };
} 