import { api } from './api';

export const tools = [
  {
    name: 'get_work_orders',
    description: 'Get the list of work orders assigned to a technician',
    parameters: {
      type: 'object',
      properties: {
        technician_id: {
          type: 'string',
          description: 'The ID of the technician'
        }
      },
      required: ['technician_id']
    }
  },
  {
    name: 'get_technician_status',
    description: 'Get the current status of a technician including active work orders and assigned truck',
    parameters: {
      type: 'object',
      properties: {
        technician_id: {
          type: 'string',
          description: 'The ID of the technician'
        }
      },
      required: ['technician_id']
    }
  },
  {
    name: 'start_travel',
    description: 'Start travel to a work order location',
    parameters: {
      type: 'object',
      properties: {
        work_order_id: {
          type: 'string',
          description: 'The ID of the work order'
        },
        technician_id: {
          type: 'string',
          description: 'The ID of the technician'
        }
      },
      required: ['work_order_id', 'technician_id']
    }
  },
  {
    name: 'end_travel',
    description: 'End travel at a work order location',
    parameters: {
      type: 'object',
      properties: {
        work_order_id: {
          type: 'string',
          description: 'The ID of the work order'
        },
        technician_id: {
          type: 'string',
          description: 'The ID of the technician'
        }
      },
      required: ['work_order_id', 'technician_id']
    }
  },
  {
    name: 'update_work_order_notes',
    description: 'Update notes for a work order',
    parameters: {
      type: 'object',
      properties: {
        work_order_id: {
          type: 'string',
          description: 'The ID of the work order'
        },
        notes: {
          type: 'string',
          description: 'Notes to add to the work order'
        },
        alert_office: {
          type: 'boolean',
          description: 'Whether to alert the office about these notes'
        }
      },
      required: ['work_order_id', 'notes']
    }
  },
  {
    name: 'check_inventory',
    description: 'Check the current inventory of a truck',
    parameters: {
      type: 'object',
      properties: {
        truck_id: {
          type: 'string',
          description: 'The ID of the truck'
        }
      },
      required: ['truck_id']
    }
  },
  {
    name: 'update_inventory',
    description: 'Update the inventory count for an item in a truck',
    parameters: {
      type: 'object',
      properties: {
        truck_id: {
          type: 'string',
          description: 'The ID of the truck'
        },
        item_id: {
          type: 'string',
          description: 'The ID of the inventory item'
        },
        quantity: {
          type: 'number',
          description: 'The new quantity of the item'
        }
      },
      required: ['truck_id', 'item_id', 'quantity']
    }
  },
  {
    name: 'create_manual_notification',
    description: 'Create a manual notification for the office',
    parameters: {
      type: 'object',
      properties: {
        message: {
          type: 'string',
          description: 'The notification message'
        },
        priority: {
          type: 'string',
          enum: ['low', 'medium', 'high'],
          description: 'The priority level of the notification'
        }
      },
      required: ['message', 'priority']
    }
  }
];

export const functionMap = {
  get_work_orders: api.getTechnicianWorkOrders,
  get_technician_status: api.getTechnicianStatus,
  start_travel: async (work_order_id: string, technician_id: string) => {
    return await api.updateWorkOrderNotes(
      parseInt(work_order_id),
      'Started traveling to work order location',
      true
    );
  },
  end_travel: async (work_order_id: string, technician_id: string) => {
    return await api.updateWorkOrderNotes(
      parseInt(work_order_id),
      'Arrived at work order location',
      true
    );
  },
  update_work_order_notes: async (work_order_id: string, notes: string, alert_office: boolean = false) => {
    return await api.updateWorkOrderNotes(parseInt(work_order_id), notes, alert_office);
  },
  check_inventory: api.getTruckInventory,
  update_inventory: api.updateTruckInventory,
  create_manual_notification: api.createManualNotification
}; 