// Mocks a way to obtain the authoritative ODL document for a project
// Replace with your real bridge/service call.
import { apiClient } from "@/lib/api-client";

export async function getProjectDoc(projectId: string): Promise<any> {
  try {
    return await apiClient.getPrimaryProjectDocument(projectId);
  } catch {
    return null;
  }
}
