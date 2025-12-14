"""
Fire Premium Calculation Service
Implements authoritative premium calculation for UBGR/UVGR products.
"""
import logging
from decimal import Decimal
from typing import List, Dict, Tuple
from app.services.rating_engine import (
    get_basic_rate_per_mille,
    get_terrorism_rate_per_mille,
    get_add_on_rate,
    get_occupancy_details
)
from app.schemas.fire_premium import (
    UBGRUVGRRequest,
    PremiumBreakdown,
    CalculationMeta,
    AddOnItem
)
from app.utils.rating_engine import round_currency

logger = logging.getLogger(__name__)

class FirePremiumCalculator:
    """
    Authoritative premium calculator for Fire insurance products.
    Implements strict calculation rules as per business requirements.
    """
    
    @staticmethod
    def _calculate_add_on_premium(
        product_code: str,
        occupancy_code: str,
        add_ons: List[AddOnItem],
        pa_proposer: bool,
        pa_spouse: bool
    ) -> Tuple[Decimal, List[Dict]]:
        """
        Calculate total add-on premium including PA.
        
        Returns:
            (total_add_on_premium, add_on_details)
        """
        total_add_on = Decimal("0")
        details = []
        
        # Process each add-on
        for addon in add_ons:
            rate_type, rate_value = get_add_on_rate(
                product_code=product_code,
                add_on_code=addon.addOnCode,
                occupancy_code=occupancy_code
            )
            
            if rate_type.lower() == "per_mille":
                # Rate per 1000 of SI
                premium = Decimal(str(addon.sumInsured)) * rate_value / Decimal("1000")
            elif rate_type.lower() == "percentage":
                # Percentage of SI
                premium = Decimal(str(addon.sumInsured)) * rate_value / Decimal("100")
            else:
                # Fixed amount
                premium = rate_value
            
            premium = Decimal(str(round_currency(float(premium))))
            total_add_on += premium
            
            details.append({
                "addOnCode": addon.addOnCode,
                "sumInsured": addon.sumInsured,
                "rateType": rate_type,
                "rateValue": float(rate_value),
                "premium": float(premium)
            })
        
        # Add PA premiums (flat rates from DB)
        if pa_proposer:
            _, pa_rate = get_add_on_rate(product_code, "PA_PROPOSER", occupancy_code)
            pa_premium = Decimal(str(round_currency(float(pa_rate))))
            total_add_on += pa_premium
            details.append({
                "addOnCode": "PA_PROPOSER",
                "sumInsured": 0,
                "rateType": "fixed",
                "rateValue": float(pa_rate),
                "premium": float(pa_premium)
            })
        
        if pa_spouse:
            _, pa_rate = get_add_on_rate(product_code, "PA_SPOUSE", occupancy_code)
            pa_premium = Decimal(str(round_currency(float(pa_rate))))
            total_add_on += pa_premium
            details.append({
                "addOnCode": "PA_SPOUSE",
                "sumInsured": 0,
                "rateType": "fixed",
                "rateValue": float(pa_rate),
                "premium": float(pa_premium)
            })
        
        return total_add_on, details
    
    @staticmethod
    def calculate_ubgr_uvgr(request: UBGRUVGRRequest) -> PremiumBreakdown:
        """
        Calculate premium for UBGR/UVGR products.
        
        Calculation Flow:
        1. Basic Fire Premium = Total SI × Basic Rate / 1000
        2. Add-On Premium = Sum of all add-on premiums + PA premiums
        3. Discount Amount = (Basic Fire + Add-On) × Discount %
        4. Subtotal = (Basic Fire + Add-On) - Discount
        5. Loading Amount = Subtotal × Loading %
        6. Terrorism Premium = Total SI × Terrorism Rate / 1000
        7. Net Premium = Subtotal + Loading + Terrorism
        8. Taxes & Final
        """
        logger.info(f"Calculating {request.productCode} Premium")
        logger.info(f"Occupancy: {request.occupancyCode}, Building SI: {request.buildingSI}, Contents SI: {request.contentsSI}")
        
        # Validate product code
        if request.productCode.upper() not in ['UBGR', 'UVGR', 'UVGS']:
            raise ValueError(f"Invalid product code: {request.productCode}. Expected UBGR, UVGR, or UVGS")
        
        product_code = request.productCode.upper()
        
        # Total Sum Insured
        total_si = Decimal(str(request.buildingSI + request.contentsSI))
        logger.info(f"Total SI: {total_si}")
        
        # 1. Basic Fire Premium
        basic_rate = get_basic_rate_per_mille(product_code, request.occupancyCode)
        if basic_rate <= 0:
            raise ValueError(f"No basic rate found for {product_code}/{request.occupancyCode}")
        
        basic_fire_premium = total_si * basic_rate / Decimal("1000")
        basic_fire_premium = Decimal(str(round_currency(float(basic_fire_premium))))
        logger.info(f"Basic Fire Premium: {basic_fire_premium} (Rate: {basic_rate}‰)")
        
        # 2. Add-On Premium
        # 2. Add-On Premium
        add_on_premium = Decimal("0")
        add_on_details = []
        
        occ_details = get_occupancy_details(request.occupancyCode)
        allow_addons = True
        if occ_details and not occ_details.get("allow_addons", True):
            allow_addons = False
            logger.warning(f"Add-ons disabled for occupancy: {request.occupancyCode}")
        
        if allow_addons:
            add_on_premium, add_on_details = FirePremiumCalculator._calculate_add_on_premium(
                product_code=product_code,
                occupancy_code=request.occupancyCode,
                add_ons=request.addOns,
                pa_proposer=request.paSelection.proposer,
                pa_spouse=request.paSelection.spouse
            )
        else:
            logger.info("Skipping add-on calculation (restricted by occupancy rules)")
            
        logger.info(f"Add-On Premium: {add_on_premium}")
        
        # 3. Discount (applies ONLY to Basic Fire + Add-On)
        discount_base = basic_fire_premium + add_on_premium
        discount_amount = discount_base * Decimal(str(request.discountPercentage)) / Decimal("100")
        discount_amount = Decimal(str(round_currency(float(discount_amount))))
        logger.info(f"Discount Amount: {discount_amount} ({request.discountPercentage}% on {discount_base})")
        
        # 4. Subtotal (after discount)
        subtotal = discount_base - discount_amount
        subtotal = Decimal(str(round_currency(float(subtotal))))
        logger.info(f"Subtotal: {subtotal}")
        
        # 5. Loading (applies ONLY to Subtotal)
        loading_amount = subtotal * Decimal(str(request.loadingPercentage)) / Decimal("100")
        loading_amount = Decimal(str(round_currency(float(loading_amount))))
        logger.info(f"Loading Amount: {loading_amount} ({request.loadingPercentage}% on {subtotal})")
        
        # 6. Terrorism Premium (UBGR/BGR only, excluded from discount & loading)
        # Rule: UVGR → Terrorism NOT applicable
        terrorism_premium = None
        terrorism_rate = None
        
        if product_code in ['UBGR', 'BGR']:
            terr_si = Decimal(str(request.terrorismSI))
            
            if terr_si > 0:
                try:
                    terrorism_rate = get_terrorism_rate_per_mille(
                        product_code=product_code,
                        occupancy_code=request.occupancyCode,
                        tsi=float(terr_si) # Rate might depend on TSI slab
                    )
                    terrorism_premium = terr_si * terrorism_rate / Decimal("1000")
                    terrorism_premium = Decimal(str(round_currency(float(terrorism_premium))))
                    logger.info(f"Terrorism Premium: {terrorism_premium} (Rate: {terrorism_rate}‰ on SI: {terr_si})")
                except Exception as e:
                    logger.error(f"Terrorism rate lookup failed: {e}")
                    # Fail safe defaults? 
                    pass
            else:
                logger.info("Terrorism SI is 0. Calc skipped.")
                terrorism_premium = Decimal("0")
                terrorism_rate = Decimal("0")

        elif product_code in ['UVGR', 'UVGS']:
             logger.info(f"{product_code} -> Terrorism Premium NOT applicable")
             terrorism_premium = Decimal("0")
             terrorism_rate = Decimal("0")
        else:
            logger.info(f"{product_code} does not require terrorism premium")
        
        # 7. Net Premium (Annual)
        annual_net_premium = subtotal + loading_amount
        if terrorism_premium is not None:
            annual_net_premium += terrorism_premium
        annual_net_premium = Decimal(str(round_currency(float(annual_net_premium))))
        logger.info(f"Annual Net Premium: {annual_net_premium}")

        # 8. Apply Policy Period Multiplier
        policy_period = request.policyPeriod
        if policy_period < 1: 
            policy_period = 1 # Safety
            
        net_premium = annual_net_premium * Decimal(str(policy_period))
        net_premium = Decimal(str(round_currency(float(net_premium))))
        
        logger.info(f"Final Net Premium ({policy_period} Years): {net_premium}")
        
        # 9. Taxes
        cgst = net_premium * Decimal("0.09")
        cgst = Decimal(str(round_currency(float(cgst))))
        
        sgst = net_premium * Decimal("0.09")
        sgst = Decimal(str(round_currency(float(sgst))))
        
        stamp_duty = Decimal("1.0")  # Fixed stamp duty
        
        gross_premium = net_premium + cgst + sgst + stamp_duty
        gross_premium = Decimal(str(round_currency(float(gross_premium))))
        
        logger.info(f"Gross Premium: {gross_premium} (Net: {net_premium}, CGST: {cgst}, SGST: {sgst}, Stamp: {stamp_duty})")
        
        # Construct response
        # Construct response
        # Construct response
        breakdown = PremiumBreakdown(
            basic_premium=float(basic_fire_premium),
            add_on_premium=float(add_on_premium),
            discount_amount=float(discount_amount),
            sub_total=float(subtotal),
            loading_amount=float(loading_amount),
            terrorism_premium=float(terrorism_premium) if terrorism_premium is not None else 0.0,
            net_premium=float(net_premium),
            cgst=float(cgst),
            sgst=float(sgst),
            stamp_duty=float(stamp_duty),
            gross_premium=float(gross_premium)
        )
        
        meta = CalculationMeta(
            applied_rate=float(basic_rate),
            risk_rate=float(basic_rate),  # Same as applied_rate for UI clarity
            rate_source="product_basic_rates",
            terrorism_rate=float(terrorism_rate) if terrorism_rate is not None else None,
            occupancy_code=request.occupancyCode,
            product_code=product_code
        )
        
        return {
            "breakdown": breakdown,
            "meta": meta
        }
