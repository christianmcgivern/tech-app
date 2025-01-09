import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:3000/api';

// Types
export interface Technician {
    id: number;
    name: string;
    phone: string;
    active: boolean;
}

export interface WorkOrder {
    id: number;
    customer_id: number;
    title: string;
    brief_description: string;
    full_summary: string;
    status: 'pending' | 'in_progress' | 'completed' | 'scheduled';
    assigned_technician_id: number;
    scheduled_for: string;
    customer?: Customer;
    technician?: Technician;
}

export interface Customer {
    id: number;
    name: string;
    address: string;
    phone: string;
    email: string;
    is_new_customer: boolean;
}

export interface TruckInventory {
    id: number;
    truck_id: number;
    item_id: number;
    quantity: number;
    item: InventoryItem;
}

export interface InventoryItem {
    id: number;
    name: string;
    description: string;
    category: string;
    unit: string;
    locations?: Array<{
        truck_id: number;
        truck_name: string;
        quantity: number;
    }>;
}

export interface TravelLog {
    id: number;
    work_order_id: number;
    technician_id: number;
    travel_start_time: string;
    travel_end_time: string;
}

export interface ClockRecord {
    id: number;
    technician_id: number;
    truck_id: number;
    clock_in_time: string;
    clock_out_time: string | null;
}

// API Functions
export const api = {
    // Work Orders
    async getWorkOrders() {
        const { data } = await axios.get<WorkOrder[]>(`${API_URL}/work-orders`);
        return data;
    },

    async getWorkOrdersByTechnician(techId: number) {
        const { data } = await axios.get<WorkOrder[]>(`${API_URL}/work-orders/technician/${techId}`);
        return data;
    },

    async createWorkOrder(workOrder: Omit<WorkOrder, 'id'>) {
        const { data } = await axios.post<WorkOrder>(`${API_URL}/work-orders`, workOrder);
        return data;
    },

    async updateWorkOrder(id: number, workOrder: Partial<WorkOrder>) {
        const { data } = await axios.put<WorkOrder>(`${API_URL}/work-orders/${id}`, workOrder);
        return data;
    },

    async deleteWorkOrder(id: number) {
        const { data } = await axios.delete<void>(`${API_URL}/work-orders/${id}`);
        return data;
    },

    async updateWorkOrderStatus(id: number, status: WorkOrder['status']) {
        const { data } = await axios.patch<WorkOrder>(`${API_URL}/work-orders/${id}`, { status });
        return data;
    },

    // Technicians
    async getTechnicians() {
        const { data } = await axios.get<Technician[]>(`${API_URL}/technicians`);
        return data;
    },

    async createTechnician(technician: Omit<Technician, 'id'>) {
        const { data } = await axios.post<Technician>(`${API_URL}/technicians`, technician);
        return data;
    },

    async updateTechnician(id: number, technician: Partial<Technician>) {
        const { data } = await axios.put<Technician>(`${API_URL}/technicians/${id}`, technician);
        return data;
    },

    async deleteTechnician(id: number) {
        const { data } = await axios.delete<void>(`${API_URL}/technicians/${id}`);
        return data;
    },

    async getTechnicianStatus() {
        const { data } = await axios.get<Array<{
            technician_id: number;
            name: string;
            status: 'active' | 'inactive';
            current_work_order?: WorkOrder;
            last_clock_record?: ClockRecord;
        }>>(`${API_URL}/technicians/status`);
        return data;
    },

    // Inventory
    async getTruckInventory(truckId: number) {
        const { data } = await axios.get<TruckInventory[]>(`${API_URL}/inventory/truck/${truckId}`);
        return data;
    },

    async updateInventoryQuantity(truckId: number, itemId: number, quantity: number) {
        const { data } = await axios.patch<TruckInventory>(
            `${API_URL}/inventory/truck/${truckId}/item/${itemId}`,
            { quantity }
        );
        return data;
    },

    // Inventory Items
    async getInventoryItems() {
        const { data } = await axios.get<InventoryItem[]>(`${API_URL}/inventory/items`);
        return data;
    },

    async createInventoryItem(item: Omit<InventoryItem, 'id'>) {
        const { data } = await axios.post<InventoryItem>(`${API_URL}/inventory/items`, item);
        return data;
    },

    async updateInventoryItem(id: number, item: Partial<InventoryItem>) {
        const { data } = await axios.put<InventoryItem>(`${API_URL}/inventory/items/${id}`, item);
        return data;
    },

    async deleteInventoryItem(id: number) {
        const { data } = await axios.delete<void>(`${API_URL}/inventory/items/${id}`);
        return data;
    },

    // Customers
    async getCustomers() {
        const { data } = await axios.get<Customer[]>(`${API_URL}/customers`);
        return data;
    },

    async createCustomer(customer: Omit<Customer, 'id'>) {
        const { data } = await axios.post<Customer>(`${API_URL}/customers`, customer);
        return data;
    },

    // Travel Logs
    async getTravelLogs(workOrderId: number) {
        const { data } = await axios.get<TravelLog[]>(`${API_URL}/travel-logs/work-order/${workOrderId}`);
        return data;
    },

    // Clock Records
    async getCurrentClockRecords() {
        const { data } = await axios.get<ClockRecord[]>(`${API_URL}/clock-records/current`);
        return data;
    },

    // Dashboard Stats
    async getDashboardStats() {
        const { data } = await axios.get<{
            active_work_orders: number;
            completed_today: number;
            technicians_active: number;
            pending_work_orders: number;
        }>(`${API_URL}/stats/dashboard`);
        return data;
    }
}; 