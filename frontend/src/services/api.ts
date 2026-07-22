import axios from 'axios';
import type {
  PredictionRequest,
  PredictionResponse,
  DashboardSummary,
  OwnerFeedbackCreate,
  OwnerFeedbackItem,
  SlotRule,
  ModelMetric
} from '../types';

const API_BASE_URL = 'http://localhost:8000/api';

const client = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export interface ColumnMappingPayload {
  temp_filename: string;
  price_col: string;
  date_col: string;
  slot_col?: string;
  guests_col?: string;
  lead_col?: string;
  competitor_col?: string;
}

export interface ValidationReport {
  temp_filename: string;
  total_rows: number;
  clean_rows: number;
  duplicate_rows: number;
  missing_count: number;
  price_mean: number;
  price_median: number;
  price_min: number;
  price_max: number;
  is_price_suspicious: boolean;
  warning_message?: string;
  date_start: string;
  date_end: string;
  slot_distribution: Record<string, number>;
  preview_data: Array<Record<string, any>>;
}

export const api = {
  getDashboard: async (): Promise<DashboardSummary> => {
    const res = await client.get('/dashboard');
    return res.data;
  },

  predictPrice: async (req: PredictionRequest): Promise<PredictionResponse> => {
    const res = await client.post('/predict', req);
    return res.data;
  },

  getWeatherPreview: async (bookingDate: string): Promise<any> => {
    const res = await client.get('/predict/weather-preview', {
      params: { booking_date: bookingDate },
    });
    return res.data;
  },

  logFeedback: async (feedback: OwnerFeedbackCreate): Promise<{ status: string; message: string }> => {
    const res = await client.post('/feedback', feedback);
    return res.data;
  },

  getFeedbackHistory: async (): Promise<OwnerFeedbackItem[]> => {
    const res = await client.get('/feedback/history');
    return res.data;
  },

  previewUpload: async (file: File): Promise<any> => {
    const formData = new FormData();
    formData.append('file', file);
    const res = await client.post('/upload/preview', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return res.data;
  },

  validateMapping: async (payload: ColumnMappingPayload): Promise<ValidationReport> => {
    const res = await client.post('/upload/validate', payload);
    return res.data;
  },

  confirmAndTrain: async (payload: ColumnMappingPayload): Promise<any> => {
    const res = await client.post('/upload/confirm-and-train', payload);
    return res.data;
  },

  uploadDataset: async (file: File): Promise<any> => {
    const formData = new FormData();
    formData.append('file', file);
    const res = await client.post('/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return res.data;
  },

  getSampleExcelUrl: (): string => {
    return `${API_BASE_URL}/upload/sample-excel`;
  },

  getModelVersions: async (): Promise<any> => {
    const res = await client.get('/models/versions');
    return res.data;
  },

  rollbackVersion: async (versionId: string): Promise<any> => {
    const res = await client.post('/models/rollback', { version_id: versionId });
    return res.data;
  },

  getSlots: async (): Promise<SlotRule[]> => {
    const res = await client.get('/slots');
    return res.data;
  },

  getModelMetrics: async (): Promise<ModelMetric[]> => {
    const res = await client.get('/model-info');
    return res.data;
  }
};
