import { UploadedFile } from "@/types/upload.types";
import { uploadHistory } from "@/data/uploadsData";

export const uploadApi = {
  getHistory: async (): Promise<UploadedFile[]> => {
    await new Promise((r) => setTimeout(r, 400));
    return uploadHistory;
  },
  uploadFile: async (
    file: File,
    onProgress: (pct: number) => void
  ): Promise<UploadedFile> => {
    for (let pct = 0; pct <= 100; pct += 10) {
      await new Promise((r) => setTimeout(r, 90));
      onProgress(pct);
    }
    const riskLevels: UploadedFile["riskLevel"][] = ["safe", "low", "medium", "high", "critical"];
    return {
      id: `up-${Date.now()}`,
      name: file.name,
      size: `${(file.size / (1024 * 1024)).toFixed(2)} MB`,
      type: file.type || "application/octet-stream",
      progress: 100,
      status: "completed",
      riskLevel: riskLevels[Math.floor(Math.random() * riskLevels.length)],
      sha256: Array.from({ length: 64 })
        .map(() => "0123456789abcdef"[Math.floor(Math.random() * 16)])
        .join(""),
      md5: Array.from({ length: 32 })
        .map(() => "0123456789abcdef"[Math.floor(Math.random() * 16)])
        .join(""),
      uploadedAt: new Date().toISOString(),
    };
  },
};
