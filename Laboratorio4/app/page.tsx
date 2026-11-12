import Dashboard from "@/components/dashboard";
import { loadDashboardData } from "@/lib/data";

export default function Home() {
  return <Dashboard data={loadDashboardData()} />;
}
