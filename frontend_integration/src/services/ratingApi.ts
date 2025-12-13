import axios, { AxiosError } from 'axios';

// Environment variable for API Base URL (ensure this is set in your .env)
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 10000, // 10s timeout
});

export interface RatingPayload {
  // Product Logic
  product_code?: string; // e.g., 'BGRP', 'SFSP'
  product_name?: string; // Fallback
  
  // Occupancy
  occupancy_code?: string;
  occupancy?: string; // Text description for generic engine

  // Core Params
  policy_period_years: number; // 1 to 10
  rate?: number; // Manual rate override (per mille)

  // Sum Insureds
  building_si?: number;
  buildingSI?: number; // Helper for different component standards
  contents_si?: number;
  contentsSI?: number; // Helper
  terrorism_si?: number; // usually same as Total SI
  
  // Covers & Toggles
  terrorism_selected?: boolean; 
  terrorismCover?: string; // "Yes" | "No" (Frontend variant)
  
  pa_selected?: boolean;
  paProposer?: string; // "Yes" | "No"
  paSpouse?: string; // "Yes" | "No"
  
  // Adjustments
  discount_percent?: number;
  discountPercentage?: number;
  loading_percent?: number;
  
  // Additional structures (if generic)
  add_ons?: Array<{ code: string; rate?: number }>;
}

export interface RatingBreakdown {
  basePremium?: number;
  firePremium?: number; // BGRP specific (alias for base)
  terrorismPremium?: number;
  paPremium?: number;
  loadings?: number;
  discounts?: number;
  [key: string]: number | undefined;
}

export interface RatingResponse {
  success?: boolean;
  data?: {
    // Core
    net_premium?: number;
    netPremium?: number; // CamelCase variant
    gst: number;
    total_premium?: number; // Gross
    gross_premium?: number; // CamelCase variant
    
    // Details
    base_premium?: number;
    basic_premium?: number;
    breakdown: RatingBreakdown;
    
    // Echoed inputs usually
    product?: string;
    rate_applied?: number;
  };
  detail?: string | object; // Error details
}

/**
 * Maps frontend specific field names to the backend Expected Schema if needed.
 * This ensures compatibility whether components use 'buildingSI' or 'building_si'.
 */
function normalizePayload(payload: RatingPayload): any {
  // Determine if specific product endpoint or generic
  // For this example, we normalize towards the generic or specific BGRP/SFSP schemas defined in docs.
  
  const isBgrp = payload.product_code === 'BGRP';
  
  // Normalize snake_case vs camelCase
  const building = payload.building_si ?? payload.buildingSI ?? 0;
  const contents = payload.contents_si ?? payload.contentsSI ?? 0;
  
  // Toggles
  const terror = payload.terrorism_selected === true || payload.terrorismCover === 'Yes';
  const paProp = payload.paProposer === 'Yes';
  const paSpouse = payload.paSpouse === 'Yes';
  
  if (isBgrp) {
    // BGRP specific endpoint expects CamelCase loosely or mapped in backend.
    // Based on backend implementation 'bgrp/calculate':
    // Expects: buildingSI, contentsSI, terrorismCover, paProposer, paSpouse, discountPercentage
    return {
      buildingSI: building,
      contentsSI: contents,
      terrorismCover: terror ? 'Yes' : 'No',
      paProposer: paProp ? 'Yes' : 'No',
      paSpouse: paSpouse ? 'Yes' : 'No',
      discountPercentage: payload.discount_percent ?? payload.discountPercentage ?? 0
    };
  }
  
  // Default / Universal Normalization (SFSP, etc.)
  return {
    product_code: payload.product_code,
    occupancy: payload.occupancy || payload.occupancy_code, // passing raw string if needed
    building_si: building,
    contents_si: contents, // If supported by SFSP endpoint
    pa_selected: payload.pa_selected ?? false,
    terrorism_cover: terror, // Some endpoints might check this
    add_ons: payload.add_ons || [],
    ...payload // Passthrough others
  };
}

/**
 * Calculate Premium API Call
 */
export async function calculatePremium(payload: RatingPayload): Promise<RatingResponse> {
  try {
    let endpoint = '/api/rating/calculate'; // Default Generic
    
    // Route to specific endpoints for better accuracy if code is known
    if (payload.product_code) {
      if (payload.product_code === 'BGRP') endpoint = '/irisk/fire/uiic/bgrp/calculate';
      else if (['SFSP', 'IAR', 'BLUSP', 'BSUSP'].includes(payload.product_code)) {
        endpoint = `/irisk/fire/uiic/${payload.product_code.toLowerCase()}/calculate`;
      }
    }
    
    const body = normalizePayload(payload);
    
    console.log('Sending Rating Request:', endpoint, body);
    
    const response = await apiClient.post<RatingResponse>(endpoint, body);
    return response.data;
  } catch (error) {
    if (axios.isAxiosError(error)) {
      const axiosError = error as AxiosError<RatingResponse>;
      if (axiosError.response?.data) {
         // Return the backend error response structure to be handled by UI
         throw axiosError.response.data;
      }
      throw new Error(axiosError.message);
    }
    throw error;
  }
}
