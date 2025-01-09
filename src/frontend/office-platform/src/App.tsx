import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import MainLayout from './layouts/MainLayout';
import Dashboard from './pages/Dashboard';
import WorkOrders from './pages/WorkOrders';
import Technicians from './pages/Technicians';
import Equipment from './pages/Equipment';

function App() {
  return (
    <Router>
      <MainLayout>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/work-orders" element={<WorkOrders />} />
          <Route path="/technicians" element={<Technicians />} />
          <Route path="/equipment" element={<Equipment />} />
        </Routes>
      </MainLayout>
    </Router>
  );
}

export default App;
