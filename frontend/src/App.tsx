import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import Layout from "@/components/Layout";
import UploadPage from "@/pages/UploadPage";
import InvoiceListPage from "@/pages/InvoiceListPage";
import InvoiceDetailPage from "@/pages/InvoiceDetailPage";
import StatsPage from "@/pages/StatsPage";

export default function App() {
  return (
    <Router>
      <Routes>
        <Route element={<Layout />}>
          <Route path="/" element={<UploadPage />} />
          <Route path="/invoices" element={<InvoiceListPage />} />
          <Route path="/invoices/:id" element={<InvoiceDetailPage />} />
          <Route path="/stats" element={<StatsPage />} />
        </Route>
      </Routes>
    </Router>
  );
}
