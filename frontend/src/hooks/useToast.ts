import { useAppDispatch } from "@/redux/hooks";
import { addToast, ToastItem } from "@/redux/slices/uiSlice";

export function useToast() {
  const dispatch = useAppDispatch();
  return {
    toast: (toast: Omit<ToastItem, "id">) => dispatch(addToast(toast)),
  };
}
