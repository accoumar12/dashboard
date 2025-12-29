import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Routes, Route } from 'react-router-dom';
import { HomePage } from './components/HomePage';
import { Dashboard } from './components/Dashboard';
import { DashboardWrapper } from './components/DashboardWrapper';
import './App.css';

const queryClient = new QueryClient();

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/playground" element={<Dashboard sessionId="playground" />} />
        <Route path="/db/:sessionId" element={<DashboardWrapper />} />
      </Routes>
    </QueryClientProvider>
  );
}

export default App;
