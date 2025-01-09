import { Routes, Route, Navigate } from 'react-router-dom';
import Dashboard from './pages/Dashboard';
import TechnicianSelect from './pages/TechnicianSelect';
import WorkOrders from './pages/WorkOrders';
import WorkOrderNotes from './pages/WorkOrderNotes';
import Inventory from './pages/Inventory';
import Travel from './pages/Travel';

function App() {
  return (
    <Routes>
      <Route path="/" element={<TechnicianSelect />} />
      <Route path="/dashboard" element={<Dashboard />} />
      <Route path="/work-orders" element={<WorkOrders />} />
      <Route path="/work-orders/:orderId/notes" element={<WorkOrderNotes />} />
      <Route path="/inventory" element={<Inventory />} />
      <Route path="/travel" element={<Travel />} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

export default App; 