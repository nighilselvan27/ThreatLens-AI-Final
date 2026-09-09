import { useEffect } from "react";
import AppRoutes from "@/routes/AppRoutes";
import { useAppSelector } from "@/redux/hooks";
import ToastViewport from "@/components/ui/Toast";

function App() {
  const darkMode = useAppSelector((s) => s.ui.darkMode);

  useEffect(() => {
    document.documentElement.classList.toggle("dark", darkMode);
  }, [darkMode]);

  return (
    <>
      <AppRoutes />
      <ToastViewport />
    </>
  );
}

export default App;
