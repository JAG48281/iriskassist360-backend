import React from 'react';

// --- Types ---
import { RatingBreakdown, RatingResponseData } from '../api/ratingApi';

interface PremiumBreakdownCardProps {
    data: RatingResponseData;
    currencySymbol?: string;
    className?: string; // Allow external class injection
}

/**
 * PremiumBreakdownCard
 * 
 * Displays the detailed premium breakdown including Base, Add-ons, Loadings, Discounts, Net, and GST.
 * Designed with a "Mobile-First" card aesthetic.
 */
const PremiumBreakdownCard: React.FC<PremiumBreakdownCardProps> = ({
    data,
    currencySymbol = '₹',
    className = ''
}) => {
    const {
        breakdown,
        base_premium, basic_premium,
        gross_premium, total_premium,
        net_premium, netPremium,
        gst
    } = data;

    const base = base_premium || basic_premium || breakdown.base || breakdown.firePremium || 0;
    const net = net_premium || netPremium || 0;
    const gross = gross_premium || total_premium || 0;

    // Extract specific known components to keep order clean
    const terrorism = breakdown.terrorismPremium || 0;
    const pa = breakdown.paPremium || 0;
    const loading = breakdown.loadings || 0;
    const discount = breakdown.discounts || 0;

    // Filter out keys we've already handled to show dynamic add-ons
    const handledKeys = ['base', 'firePremium', 'basic_premium', 'terrorismPremium', 'paPremium', 'loadings', 'discounts', 'gst', 'net_premium', 'gross_premium'];
    const extraAddons = Object.entries(breakdown).filter(([key]) => !handledKeys.includes(key));

    // --- Styles (Vanilla JS Objects for Portability) ---
    const styles = {
        card: {
            backgroundColor: '#ffffff',
            borderRadius: '12px',
            boxShadow: '0 4px 12px rgba(0, 0, 0, 0.08)',
            padding: '20px',
            maxWidth: '400px',
            width: '100%',
            fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif',
            margin: '0 auto',
            ...((className.includes && className.includes('dark')) ? { backgroundColor: '#1e293b', color: '#f8fafc' } : {})
        },
        header: {
            fontSize: '18px',
            fontWeight: '600',
            marginBottom: '16px',
            borderBottom: '1px solid #e2e8f0',
            paddingBottom: '12px',
            color: '#334155'
        },
        row: {
            display: 'flex',
            justifyContent: 'space-between',
            marginBottom: '8px',
            fontSize: '14px',
            color: '#64748b'
        },
        rowHighlight: {
            display: 'flex',
            justifyContent: 'space-between',
            marginBottom: '8px',
            fontSize: '14px',
            color: '#0f172a',
            fontWeight: '500'
        },
        amount: {
            fontVariantNumeric: 'tabular-nums',
            fontWeight: '500'
        },
        divider: {
            height: '1px',
            backgroundColor: '#e2e8f0',
            margin: '12px 0'
        },
        totalRow: {
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            marginTop: '12px',
            fontSize: '20px',
            fontWeight: '700',
            color: '#2563eb' // Brand Primary Blue
        },
        discount: {
            color: '#16a34a' // Green
        },
        loading: {
            color: '#dc2626' // Red
        }
    } as const;

    const formatMoney = (val: number) =>
        val.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 });

    return (
        <div style={styles.card} className={`premium-card ${className}`}>
            <div style={styles.header}>Premium Breakdown</div>

            {/* Base */}
            <div style={styles.row}>
                <span>Base Premium</span>
                <span style={styles.amount}>{currencySymbol}{formatMoney(base)}</span>
            </div>

            {/* Basic Covers (Terrorism, PA) */}
            {terrorism > 0 && (
                <div style={styles.row}>
                    <span>Terrorism Premium</span>
                    <span style={styles.amount}>{currencySymbol}{formatMoney(terrorism)}</span>
                </div>
            )}
            {pa > 0 && (
                <div style={styles.row}>
                    <span>P.A. Cover</span>
                    <span style={styles.amount}>{currencySymbol}{formatMoney(pa)}</span>
                </div>
            )}

            {/* Dynamic Add-ons */}
            {extraAddons.map(([key, val]) => (
                <div style={styles.row} key={key}>
                    <span style={{ textTransform: 'capitalize' }}>{key.replace(/_/g, ' ')}</span>
                    <span style={styles.amount}>{currencySymbol}{formatMoney(val as number)}</span>
                </div>
            ))}

            {/* Loading & Discount */}
            {loading > 0 && (
                <div style={{ ...styles.row, ...styles.loading }}>
                    <span>Loading (+)</span>
                    <span style={styles.amount}>{currencySymbol}{formatMoney(loading)}</span>
                </div>
            )}
            {discount > 0 && (
                <div style={{ ...styles.row, ...styles.discount }}>
                    <span>Discount (-)</span>
                    <span style={styles.amount}>-{currencySymbol}{formatMoney(discount)}</span>
                </div>
            )}

            <div style={styles.divider} />

            {/* Net & GST */}
            <div style={styles.rowHighlight}>
                <span>Net Premium</span>
                <span style={styles.amount}>{currencySymbol}{formatMoney(net)}</span>
            </div>
            <div style={styles.row}>
                <span>GST (18%)</span>
                <span style={styles.amount}>{currencySymbol}{formatMoney(gst)}</span>
            </div>

            <div style={styles.divider} />

            {/* Gross Total */}
            <div style={styles.totalRow}>
                <span>Total Payable</span>
                <span>{currencySymbol}{formatMoney(gross)}</span>
            </div>
        </div>
    );
};

export default PremiumBreakdownCard;
