import React from 'react';

// --- Types ---
import { AddOnRate } from '../api/ratingApi';

interface RateInfoCardProps {
    basicRatePerMille: number;
    terrorismRatePerMille?: number;
    addOnRates?: AddOnRate[];
    policyPeriod: number;
    className?: string;
}

const RateInfoCard: React.FC<RateInfoCardProps> = ({
    basicRatePerMille,
    terrorismRatePerMille = 0,
    addOnRates = [],
    policyPeriod,
    className = ''
}) => {
    const styles = {
        container: {
            backgroundColor: '#f0fdf4', // Light green bg
            border: '1px solid #bbf7d0',
            borderRadius: '8px',
            padding: '12px',
            fontSize: '13px',
            color: '#166534',
            marginTop: '12px',
            fontFamily: '-apple-system, sans-serif'
        },
        header: {
            fontWeight: 'bold',
            marginBottom: '6px'
        },
        item: {
            marginBottom: '4px',
            display: 'flex',
            justifyContent: 'space-between'
        }
    } as const;

    return (
        <div style={styles.container} className={className}>
            <div style={styles.header}>Rate Information (Per Mille / ‰)</div>

            <div style={styles.item}>
                <span>Basic Fire Rate:</span>
                <span>{basicRatePerMille.toFixed(3)}‰</span>
            </div>

            {terrorismRatePerMille > 0 && (
                <div style={styles.item}>
                    <span>Terrorism Rate:</span>
                    <span>{terrorismRatePerMille.toFixed(3)}‰</span>
                </div>
            )}

            {/* Display simple count of active add-on rates if specific breakdown is verbose */}
            {addOnRates.length > 0 && (
                <div style={{ marginTop: '6px', paddingTop: '6px', borderTop: '1px dashed #bbf7d0' }}>
                    <strong>Active Add-ons:</strong>
                    {addOnRates.map(addon => (
                        <div style={styles.item} key={addon.code}>
                            <span>{addon.name}</span>
                            <span>{addon.rate_per_mille.toFixed(3)}‰</span>
                        </div>
                    ))}
                </div>
            )}

            <div style={{ marginTop: '8px', fontSize: '12px', color: '#15803d' }}>
                Policy Tenure: {policyPeriod} Year(s)
            </div>
        </div>
    );
};

export default RateInfoCard;
