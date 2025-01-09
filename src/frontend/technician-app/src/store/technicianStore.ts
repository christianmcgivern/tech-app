import { create } from 'zustand';

interface TechnicianState {
  technicianId: string | null;
  truckId: string | null;
  setTechnician: (id: string) => void;
  setTruck: (id: string) => void;
  clear: () => void;
}

export const useTechnicianStore = create<TechnicianState>((set) => ({
  technicianId: localStorage.getItem('selectedTechnician'),
  truckId: localStorage.getItem('selectedTruck'),
  setTechnician: (id) => {
    localStorage.setItem('selectedTechnician', id);
    set({ technicianId: id });
  },
  setTruck: (id) => {
    localStorage.setItem('selectedTruck', id);
    set({ truckId: id });
  },
  clear: () => {
    localStorage.removeItem('selectedTechnician');
    localStorage.removeItem('selectedTruck');
    set({ technicianId: null, truckId: null });
  },
})); 