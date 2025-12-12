import React from 'react';

interface SumInsuredBreakdownCardProps {
    buildingSI?: number;
    contentsSI?: number;
    terrorismSI?: number;
    addOnSI?: Record<string, number>; // Map of add-on name -> SI
    currencySymbol?: string;
    className?: string;
}

const SumInsuredBreakdownCard: React.FC<SumInsuredBreakdownCardProps> = ({
    buildingSI = 0,
    contentsSI = 0,
    terrorismSI,
    addOnSI = {},
    currencySymbol = '₹',
    className = ''
}) => {
    const totalSI = buildingSI + contentsSI;

    const styles = {
        container: {
            backgroundColor: '#f8fafc',
            borderRadius: '8px',
            border: '1px solid #e2e8f0',
            padding: '16px',
            marginBottom: '16px',
            fontFamily: '-apple-system, sans-serif'
        },
        title: {
            fontSize: '14px',
            textTransform: 'uppercase',
            letterSpacing: '0.05em',
            color: '#64748b',
            marginBottom: '12px',
            fontWeight: '600'
        },
        row: {
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            marginBottom: '8px'
        },
        label: {
            color: '#334155',
            fontSize: '15px'
        },
        value: {
            fontWeight: '600',
            color: '#0f172a',
            fontVariantNumeric: 'tabular-nums'
        },
        totalRow: {
            display: 'flex',
            justifyContent: 'space-between',
            marginTop: '12px',
            paddingTop: '12px',
            borderTop: '1px dashed #cbd5e1',
            fontWeight: 'bold',
            color: '#2563eb'
        }
    } as const;

    const format = (n: number) => n.toLocaleString('en-IN');

    return (
        <div style={styles.container} className={className}>
            <div style={styles.title as any}>Sum Insured Details</div>

            {buildingSI > 0 && (
                <div style={styles.row}>
                    <span style={styles.label}>Building</span>
                    <span style={styles.value}>{currencySymbol}{format(buildingSI)}</span>
                </div>
            )}

            {contentsSI > 0 && (
                <div style={styles.row}>
                    <span style={styles.label}>Contents</span>
                    <span style={styles.value}>{currencySymbol}{format(contentsSI)}</span>
                </div>
            )}

            {Object.entries(addOnSI).map(([name, si]) => (
                <div style={styles.row} key={name}>
                    <span style={styles.label}>{name}</span>
                    <span style={styles.value}>{currencySymbol}{format(si)}</span>
                </div>
            ))}

            {/* Total SI */}
            <div style={styles.totalRow}>
                <span>Total Sum Insured</span>
                <span>{currencySymbol}{format(totalSI)}</span>
            </div>

            {/* Terrorism usually matches Total but shown separately as info */}
            {terrorismSI !== undefined && terrorismSI > 0 && (
                <div style={{ ...styles.row, marginTop: '8px', fontSize: '13px', color: '#64748b' }}>
                    <span>(Terrorism Coverage Limit)</span>
                    <span>{currencySymbol}{format(terrorismSI)}</span>
                </div>
            )}
        </div>
    );
};

export default SumInsuredBreakdownCard;
