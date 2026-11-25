// B1-15 설정 화면 API (LSH)
import { apiFetch } from "../client";
import type { CustomerSetting, SourceSetting } from "../../types/b1";

export const getSources = () => apiFetch<SourceSetting[]>("/b1/settings/sources");

export const saveSources = (rows: SourceSetting[]) =>
  apiFetch<SourceSetting[]>("/b1/settings/sources", { method: "PUT", body: JSON.stringify(rows) });

export const getCustomers = () => apiFetch<CustomerSetting[]>("/b1/settings/customers");
