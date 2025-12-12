import axios, {
    AxiosInstance,
    AxiosError,
    InternalAxiosRequestConfig,
    AxiosResponse
} from 'axios';

// --- Configuration ---
// Usually set in .env: VITE_API_BASE_URL
const BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
const DEFAULT_TIMEOUT = 10000;
const MAX_RETRIES = 2;

// --- Notification Placeholder ---
// Replace this with your actual toast library (e.g., react-hot-toast, react-toastify)
const notifyError = (message: string) => {
    console.error(`[UI TOAST] ${message}`);
    // if (window.toast) window.toast.error(message);
};

// --- Type Definitions ---
interface RetryConfig extends InternalAxiosRequestConfig {
    _retryCount?: number;
}

// --- Client Creation ---
const httpClient: AxiosInstance = axios.create({
    baseURL: BASE_URL,
    timeout: DEFAULT_TIMEOUT,
    headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
    },
});

// --- Request Interceptor ---
httpClient.interceptors.request.use(
    (config) => {
        // Log request in dev mode
        if (import.meta.env.DEV) {
            console.info(`[API REQ] ${config.method?.toUpperCase()} ${config.url}`, config.data || '');
        }

        // Future: Token injection
        const token = localStorage.getItem('authToken');
        if (token && config.headers) {
            config.headers.Authorization = `Bearer ${token}`;
        }

        return config;
    },
    (error) => {
        return Promise.reject(error);
    }
);

// --- Response Interceptor ---
httpClient.interceptors.response.use(
    (response: AxiosResponse) => {
        // Log response in dev mode
        if (import.meta.env.DEV) {
            console.info(`[API RES] ${response.status} ${response.config.url}`, response.data);
        }
        return response;
    },
    async (error: AxiosError) => {
        const config = error.config as RetryConfig;

        // 1. Network / Offline Handling
        if (!error.response) {
            notifyError('Network error. Please check your connection.');
            return Promise.reject(error);
        }

        // 2. Server Errors (5xx) - Retry Logic
        if (error.response.status >= 500 && config) {
            config._retryCount = config._retryCount || 0;

            if (config._retryCount < MAX_RETRIES) {
                config._retryCount += 1;
                const delay = config._retryCount * 1000; // Linear backoff: 1s, 2s

                console.warn(`[API RETRY] Attempt ${config._retryCount} for ${config.url}`);
                await new Promise(resolve => setTimeout(resolve, delay));
                return httpClient(config);
            } else {
                notifyError('Server error. Please try again later.');
            }
        }

        // 3. Client Errors (4xx)
        if (error.response.status === 422) {
            // Validation error
            const detail = (error.response.data as any).detail;
            const msg = Array.isArray(detail)
                ? detail.map(d => d.msg).join(', ')
                : (detail || 'Validation failed');
            notifyError(`Validation Error: ${msg}`);
        } else if (error.response.status === 401) {
            notifyError('Session expired. Please login again.');
            // window.location.href = '/login'; 
        } else if (error.response.status === 403) {
            notifyError('Access denied.');
        } else if (error.response.status === 404) {
            // 404 might be expected in some checks, so maybe strictly log
            console.warn('Resource not found:', config?.url);
        } else {
            notifyError(`Request failed: ${error.message}`);
        }

        return Promise.reject(error);
    }
);

export default httpClient;
