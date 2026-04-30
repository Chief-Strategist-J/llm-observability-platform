import { Routes, Route } from 'react-router-dom';
import { Layout } from './components/layout/Layout';
import { Dashboard } from './pages/Dashboard';
import { Services } from './pages/Services';
import { ServiceDetail } from './pages/ServiceDetail';
import { Clusters } from './pages/Clusters';
import { ClusterDetail } from './pages/ClusterDetail';
import { TraceExplorer } from './pages/TraceExplorer';
import { Incidents } from './pages/Incidents';
import { Settings } from './pages/Settings';
import TestPage from './TestPage';

export function App() {
  return (
    <Routes>
      <Route path="/test" element={<TestPage />} />
      <Route path="/" element={<Layout />}>
        <Route index element={<Dashboard />} />
        <Route path="services" element={<Services />} />
        <Route path="services/:id" element={<ServiceDetail />} />
        <Route path="clusters" element={<Clusters />} />
        <Route path="clusters/:id" element={<ClusterDetail />} />
        <Route path="traces" element={<TraceExplorer />} />
        <Route path="incidents" element={<Incidents />} />
        <Route path="settings" element={<Settings />} />
      </Route>
    </Routes>
  );
}
