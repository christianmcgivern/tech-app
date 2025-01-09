import { api } from './api';
import { WorkflowState } from './api';

export const tools = [
  {
    type: "function",
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
    type: "function",
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
    type: "function",
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
    type: "function",
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
    type: "function",
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
    type: "function",
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
    type: "function",
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
    type: "function",
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
  },
  {
    type: "function",
    name: 'start_job',
    description: 'Start timing a job for a work order',
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
    type: "function",
    name: 'end_job',
    description: 'End timing a job for a work order',
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
        },
        notes: {
          type: 'string',
          description: 'Optional notes about the job completion'
        }
      },
      required: ['work_order_id', 'technician_id']
    }
  },
  {
    type: "function",
    name: 'update_workflow_state',
    description: 'Update the technician\'s current workflow state',
    parameters: {
      type: 'object',
      properties: {
        technician_id: {
          type: 'string',
          description: 'The ID of the technician'
        },
        state: {
          type: 'string',
          description: 'The new workflow state',
          enum: [
            'CLOCKED_IN',
            'TRAVELING_TO_FIRST_JOB',
            'AT_JOBSITE',
            'WORKING_ON_JOB',
            'JOB_COMPLETED',
            'TRAVELING_TO_NEXT_JOB',
            'TRAVELING_TO_OFFICE',
            'DAY_COMPLETED'
          ]
        },
        current_work_order_id: {
          type: 'string',
          description: 'The ID of the current work order'
        },
        next_work_order_id: {
          type: 'string',
          description: 'The ID of the next work order in queue'
        }
      },
      required: ['technician_id', 'state']
    }
  }
];

export const functionMap = {
  get_work_orders: api.getTechnicianWorkOrders,
  get_technician_status: api.getTechnicianStatus,
  start_travel: async (work_order_id: string, technician_id: string) => {
    await api.updateWorkflowState(
      technician_id,
      'TRAVELING_TO_FIRST_JOB',
      parseInt(work_order_id),
      undefined
    );
    return await api.updateWorkOrderNotes(
      parseInt(work_order_id),
      'Started traveling to work order location',
      true
    );
  },
  end_travel: async (work_order_id: string, technician_id: string) => {
    await api.updateWorkflowState(
      technician_id,
      'AT_JOBSITE',
      parseInt(work_order_id),
      undefined
    );
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
  create_manual_notification: api.createManualNotification,
  start_job: async (work_order_id: string, technician_id: string) => {
    await api.updateWorkflowState(
      technician_id,
      'WORKING_ON_JOB',
      parseInt(work_order_id),
      undefined
    );
    return await api.startJobTiming(parseInt(work_order_id), technician_id);
  },
  end_job: async (work_order_id: string, technician_id: string, notes?: string) => {
    await api.updateWorkflowState(
      technician_id,
      'JOB_COMPLETED',
      parseInt(work_order_id),
      undefined
    );
    const response = await api.endJobTiming(parseInt(work_order_id), technician_id);
    if (notes) {
      await api.updateWorkOrderNotes(parseInt(work_order_id), notes, true);
    }
    return response;
  },
  update_workflow_state: async (
    technician_id: string,
    state: string,
    current_work_order_id?: string,
    next_work_order_id?: string
  ) => {
    return await api.updateWorkflowState(
      technician_id,
      state as WorkflowState,
      current_work_order_id ? parseInt(current_work_order_id) : undefined,
      next_work_order_id ? parseInt(next_work_order_id) : undefined
    );
  }
}; 