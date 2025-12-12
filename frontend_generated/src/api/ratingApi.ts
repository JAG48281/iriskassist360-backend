import httpClient from './httpClient';

// --- Types ---

export interface AddOnPayload {
    code: string;
    rate?: number; // Override rate if needed
}

export interface RatingPayload {
    product_code?: string; // e.g., 'BGRP'
    product_name?: string;
    occupancy_code?: string;
    occupancy?: string;

    policy_period_years: number;
    rate?: number;

    building_si?: number;
    buildingSI?: number;
    contents_si?: number;
    contentsSI?: number;
    terrorism_si?: number;

    terrorism_selected?: boolean;
    terrorismCover?: string; // "Yes" | "No"

    pa_selected?: boolean;
    paProposer?: string;
    paSpouse?: string;

    discount_percent?: number;
    discountPercentage?: number;
    loading_percent?: number;

    add_ons?: AddOnPayload[];
}

export interface RatingBreakdown {
    basePremium?: number;   // or 'base'
    base?: number;
    firePremium?: number;
    terrorismPremium?: number;
    paPremium?: number;
    loadings?: number;
    discounts?: number;
    [key: string]: number | undefined; // For dynamic add-ons
}

export interface RatingResponseData {
    net_premium?: number;
    netPremium?: number;
    gst: number;
    total_premium?: number;
    gross_premium?: number;

    base_premium?: number;
    basic_premium?: number;

    breakdown: RatingBreakdown;
    product?: string;
    rate_applied?: number;
}

export interface RatingResponse {
    success: boolean;
    data: RatingResponseData;
    detail?: any;
}

export interface AddOnRate {
    code: string;
    name: string;
    rate_per_mille: number;
    is_fixed: boolean;
}

export interface OccupancyInfo {
    code: string;
    name: string;
    risk_code?: string;
}

// --- API Service ---

/**
 * Calculates the insurance premium based on the payload.
 */
export const calculatePremium = async (payload: RatingPayload): Promise<RatingResponseData> => {
    try {
        let endpoint = '/api/rating/calculate';

        // Legacy routing support (optional, can stick to generic if backend supports it fully)
        if (payload.product_code === 'BGRP') endpoint = '/irisk/fire/uiic/bgrp/calculate';
        else if (payload.product_code && ['SFSP', 'IAR', 'BLUSP'].includes(payload.product_code)) {
            endpoint = `/irisk/fire/uiic/${payload.product_code.toLowerCase()}/calculate`;
        }

        const { data } = await httpClient.post<RatingResponse>(endpoint, payload);

        if (!data.success && !data.data) {
            throw new Error((data.detail as string) || 'Calculation failed');
        }

        return data.data;
    } catch (error) {
        throw error; // Propagate to caller handling/toast
    }
};

/**
 * Fetches valid occupancies for a product.
 * (Assumes a backend endpoint exists or returns mocked list)
 */
export const getOccupancies = async (productCode: string): Promise<OccupancyInfo[]> => {
    // Placeholder implementation - replace with actual endpoint when available
    // const { data } = await httpClient.get(`/api/products/${productCode}/occupancies`);
    // return data;

    // Return mock for now to prevent breakage
    return [
        { code: '1001', name: 'Residential', risk_code: 'R1' },
        { code: '2001', name: 'Shop/Office', risk_code: 'C1' },
        { code: '3001', name: 'Wellness/Hospital', risk_code: 'H1' },
        { code: '4001', name: 'Industrial', risk_code: 'I1' },
    ];
};

/**
 * Fetches available add-ons for a product.
 */
export const getAddOns = async (productCode: string): Promise<AddOnRate[]> => {
    // const { data } = await httpClient.get(`/api/products/${productCode}/addons`);
    // return data;

    // Mock fallback
    return [
        { code: 'STFI', name: 'Storm, Tempest, Flood, Inundation', rate_per_mille: 0.15, is_fixed: false },
        { code: 'EQ', name: 'Earthquake', rate_per_mille: 0.10, is_fixed: false },
        { code: 'TERROR', name: 'Terrorism Damage', rate_per_mille: 0.08, is_fixed: false },
    ];
};

export default {
    calculatePremium,
    getOccupancies,
    getAddOns
};
