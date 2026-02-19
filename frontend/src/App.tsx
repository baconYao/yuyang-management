import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import Layout from './components/Layout';
import Dashboard from './pages/Dashboard';
import Customers from './pages/Customers';
import Contracts from './pages/Contracts';
import BillsDraft from './pages/BillsDraft';
import BillsProcessing from './pages/BillsProcessing';
import BillsProcessed from './pages/BillsProcessed';

function App() {
  return (
    <BrowserRouter>
      <Layout>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/customers" element={<Customers />} />
          <Route path="/contracts" element={<Contracts />} />
          <Route path="/bills/draft" element={<BillsDraft />} />
          <Route path="/bills/processing" element={<BillsProcessing />} />
          <Route path="/bills/processed" element={<BillsProcessed />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </Layout>
    </BrowserRouter>
  );
}

export default App;
