import { BrowserRouter, Routes, Route } from "react-router-dom";
import { Toaster } from "react-hot-toast";
import Dashboard from "./pages/Dashboard";


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
        <Route path="/" element={<Dashboard />}>
          
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;
