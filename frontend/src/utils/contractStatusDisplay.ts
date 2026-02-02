import type { Contract } from "../types";

const DAYS_NEAR_END = 60;

export function getContractStatusDisplay(
  contract: Pick<Contract, "status" | "end_date">
): { label: string; className: string } {
  const status = contract.status;
  if (status === "ACTIVE") {
    const endDate = contract.end_date ? new Date(contract.end_date) : null;
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    if (endDate) {
      endDate.setHours(0, 0, 0, 0);
      const diffMs = endDate.getTime() - today.getTime();
      const diffDays = Math.ceil(diffMs / (1000 * 60 * 60 * 24));
      if (diffDays >= 0 && diffDays <= DAYS_NEAR_END) {
        return { label: "即將到期", className: "bg-red-100 text-red-800" };
      }
    }
    return { label: "生效", className: "bg-green-100 text-green-800" };
  }
  if (status === "ENDED") {
    return { label: "結束", className: "bg-gray-200 text-gray-700" };
  }
  if (status === "TERMINATED") {
    return { label: "終止", className: "bg-gray-200 text-gray-700" };
  }
  if (status === "PENDING") {
    return { label: "合約待簽署", className: "bg-blue-200 text-blue-700" };
  }
  if (status === "TRIAL") {
    return { label: "試用", className: "bg-amber-100 text-amber-800" };
  }
  return { label: status, className: "bg-blue-100 text-blue-800" };
}
