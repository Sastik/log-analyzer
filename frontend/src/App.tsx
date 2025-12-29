import { BrowserRouter, Routes, Route } from "react-router-dom";
import { Toaster } from "react-hot-toast";
import Layout from "./components/layout/Layout";
import Dashboard from "./components/dashboard/Dashboard";


const Logs = () => (
  <div style={{ padding: "2rem" }}>
    <h2>Logs Page - Coming Soon</h2>
  </div>
);
const Analytics = () => (
  <div style={{ padding: "2rem" }}>
    <h2>Analytics Page - Coming Soon</h2>
  </div>
);
const LiveView = () => (
  <div style={{ padding: "2rem" }}>
    <h2>Live View Page - Coming Soon</h2>
  </div>
);

function App() {
  return (
    <BrowserRouter>
      <Toaster
        position="top-right"
        toastOptions={{
          duration: 4000,
          style: {
            background: "#fff",
            color: "#212121",
            borderRadius: "12px",
            boxShadow: "0 10px 15px -3px rgba(0, 0, 0, 0.1)",
            border: "1px solid #e0e0e0",
          },
          success: {
            iconTheme: {
              primary: "#4caf50",
              secondary: "#fff",
            },
          },
          error: {
            iconTheme: {
              primary: "#f44336",
              secondary: "#fff",
            },
          },
        }}
      />
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<Dashboard />} />
          <Route path="logs" element={<Logs />} />
          <Route path="analytics" element={<Analytics />} />
          <Route path="live" element={<LiveView />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;
