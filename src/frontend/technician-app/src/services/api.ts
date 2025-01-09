import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:3000/api';

interface Activity {
  id: number;
  type: string;
  description: string;
  time: string;
}

interface Technician {
  id: number;
  name: string;
  phone: string;
  active: boolean;
}

interface Truck {
  id: number;
  name: string;
  status: string;
}

interface Note {
  id: number;
  note: string;
  technician_name: string;
  created_at: string;
  alert_office: boolean;
  is_read: boolean;
}

interface WorkOrder {
  id: number;
  title: string;
  status: string;
  scheduled_for: string;
  brief_description: string;
  notes?: Note[];
  technician_name?: string;
  customer_name?: string;
}

interface WorkOrderResponse extends WorkOrder {
  notes: Note[];
}

interface InventoryItem {
  id: number;
  name: string;
  category: string;
  quantity: number;
  description?: string;
  unit?: string;
}

interface ActivityLog {
  id: number;
  type: string;
  time: string;
  description: string;
}

interface TechnicianProfile {
  id: number;
  name: string;
  phone: string;
  active: boolean;
}

interface ManualNotification {
  technician_id: number;
  work_order_id: number;
  message: string;
  priority: 'high' | 'normal' | 'low';
}

export type WorkflowState = 
  | 'CLOCKED_IN'
  | 'TRAVELING_TO_FIRST_JOB'
  | 'AT_JOBSITE'
  | 'WORKING_ON_JOB'
  | 'JOB_COMPLETED'
  | 'TRAVELING_TO_NEXT_JOB'
  | 'TRAVELING_TO_OFFICE'
  | 'DAY_COMPLETED';

export interface ClockRecord {
    id: number;
    technician_id: number;
    truck_id: number;
    clock_in_time: string;
    clock_out_time: string | null;
    workflow_state: WorkflowState;
    current_work_order_id: number | null;
    next_work_order_id: number | null;
    is_locked: boolean;
}

export const api = {
  // Get all active technicians
  getActiveTechnicians: async (): Promise<Technician[]> => {
    const response = await axios.get(`${API_URL}/technicians?active=true`);
    return response.data;
  },

  // Get all available trucks
  getAvailableTrucks: async (): Promise<Truck[]> => {
    const response = await axios.get(`${API_URL}/trucks?available=true`);
    return response.data;
  },

  // Clock in a technician with a truck
  clockIn: async (technicianId: string, data: { truck_id: number }) => {
    const response = await axios.post(`${API_URL}/technicians/${technicianId}/clock-in`, data);
    return response.data;
  },

  // Clock out a technician
  clockOut: async (technicianId: string) => {
    const response = await axios.post(`${API_URL}/technicians/${technicianId}/clock-out`);
    return response.data;
  },

  // Fetch technician's recent activity
  getTechnicianActivity: async (technicianId: string): Promise<ActivityLog[]> => {
    const response = await axios.get(`${API_URL}/technicians/${technicianId}/activity`);
    return response.data;
  },

  // Fetch work orders for a technician
  getTechnicianWorkOrders: async (technicianId: string): Promise<WorkOrder[]> => {
    const response = await axios.get(`${API_URL}/technicians/${technicianId}/work-orders`);
    return response.data;
  },

  // Fetch inventory for a truck
  getTruckInventory: async (truckId: string): Promise<InventoryItem[]> => {
    const response = await axios.get(`${API_URL}/trucks/${truckId}/inventory`);
    return response.data;
  },

  // Update truck inventory quantity
  updateTruckInventory: async (truckId: string, itemId: number, quantity: number): Promise<void> => {
    await axios.patch(`${API_URL}/trucks/${truckId}/inventory/${itemId}`, { quantity });
  },

  // Get technician profile
  getTechnicianProfile: async (technicianId: string): Promise<TechnicianProfile> => {
    const response = await axios.get(`${API_URL}/technicians/${technicianId}`);
    return response.data;
  },

  // Get work order details
  getWorkOrder: async (orderId: number): Promise<WorkOrder> => {
    const response = await axios.get(`${API_URL}/work-orders/${orderId}`);
    return response.data;
  },

  // Update work order notes
  updateWorkOrderNotes: async (orderId: number, notes: string, alertOffice: boolean = false) => {
    const technicianId = localStorage.getItem('selectedTechnician');
    const response = await axios.put(`${API_URL}/work-orders/${orderId}/notes`, {
      notes,
      alert_office: alertOffice,
      technician_id: technicianId
    });
    return response.data;
  },

  createManualNotification: async (notification: ManualNotification) => {
    const response = await axios.post(`${API_URL}/notifications/manual`, notification);
    return response.data;
  },

  getTechnicianStatus: async (technicianId: string) => {
    const response = await axios.get(`${API_URL}/technicians/${technicianId}/status`);
    return response.data;
  },

  // Start job timing
  startJobTiming: async (orderId: number, technicianId: string) => {
    const response = await axios.post(`${API_URL}/work-orders/${orderId}/timing/start`, {
      technician_id: technicianId
    });
    return response.data;
  },

  // End job timing
  endJobTiming: async (orderId: number, technicianId: string, notes?: string) => {
    const response = await axios.post(`${API_URL}/work-orders/${orderId}/timing/end`, {
      technician_id: technicianId,
      notes: notes
    });
    return response.data;
  },

  // Update workflow state
  updateWorkflowState: async (technicianId: string, state: WorkflowState, currentWorkOrderId?: number, nextWorkOrderId?: number) => {
    const response = await axios.patch(`${API_URL}/technicians/${technicianId}/workflow-state`, {
      state,
      current_work_order_id: currentWorkOrderId,
      next_work_order_id: nextWorkOrderId
    });
    return response.data;
  },

  // Get current workflow state
  getCurrentWorkflowState: async (technicianId: string): Promise<ClockRecord> => {
    const response = await axios.get(`${API_URL}/technicians/${technicianId}/current-clock-record`);
    return response.data;
  },
}; 