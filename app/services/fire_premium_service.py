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
    get_occupancy_details,
    get_fire_eq_rate_per_mille
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
        STRICT MODE with crash-proof defaults.
        """
        logger.info(f"Calculating {request.productCode} Premium")
        logger.info(f"Payload: {request.dict()}")

        try:
            # 1. Normalize ALL numeric inputs with safety defaults
            discount_pct = Decimal(str(request.discountPercentage or 0.0))
            loading_pct = Decimal(str(request.loadingPercentage or 0.0))
            building_si = Decimal(str(request.buildingSI or 0.0))
            contents_si = Decimal(str(request.contentsSI or 0.0))
            
            # Policy period safety
            policy_period = request.policyPeriod
            if policy_period < 1:
                policy_period = 1
                
            # Product code normalization
            if request.productCode:
                product_code = request.productCode.upper()
            else:
                 raise ValueError("Product code is missing")
                 
            if product_code not in ['UBGR', 'UVGR', 'UVGS']:
                raise ValueError(f"Invalid product code: {request.productCode}")

            # Total SI
            total_si = building_si + contents_si
            logger.info(f"Total SI: {total_si}")

            # 2. Basic Rate Lookup (SAFE)
            try:
                basic_rate = get_basic_rate_per_mille(product_code, request.occupancyCode)
                if basic_rate is None or basic_rate <= 0:
                     raise ValueError("Rate resolved to None or Zero")
            except Exception as e:
                logger.error(f"Basic rate lookup failed: {e}")
                raise ValueError(f"Basic rate lookup failed for {product_code}/{request.occupancyCode}")
            
            logger.info(f"Basic Rate: {basic_rate} (Per Mille)")
            
            # 3. Basic Fire Premium Calc
            base_premium = total_si * basic_rate / Decimal("1000")
            base_premium = Decimal(str(round_currency(float(base_premium))))
            
            if base_premium < 0: # Should not happen but strict check
                base_premium = Decimal("0")
                
            # 4. Add-On Premium
            add_on_premium = Decimal("0")
            add_on_details = []
            
            # Allow addons check
            occ_details = get_occupancy_details(request.occupancyCode)
            allow_addons = True
            if occ_details and not occ_details.get("allow_addons", True):
                allow_addons = False
            
            if allow_addons:
                add_on_premium, add_on_details = FirePremiumCalculator._calculate_add_on_premium(
                    product_code=product_code,
                    occupancy_code=request.occupancyCode,
                    add_ons=request.addOns,
                    pa_proposer=request.paSelection.proposer,
                    pa_spouse=request.paSelection.spouse
                )
            
            logger.info(f"Add-On Premium: {add_on_premium}")
            
            # 5. Discount Calculation (On Base + AddOn)
            discount_base = base_premium + add_on_premium
            discount_amount = discount_base * discount_pct / Decimal("100")
            discount_amount = Decimal(str(round_currency(float(discount_amount))))
            
            # 6. Subtotal
            subtotal = discount_base - discount_amount
            subtotal = Decimal(str(round_currency(float(subtotal))))
            
            # 7. Loading (On Subtotal)
            loading_amount = subtotal * loading_pct / Decimal("100")
            loading_amount = Decimal(str(round_currency(float(loading_amount))))
            
            # 8. Terrorism Premium
            terrorism_premium = Decimal("0")
            terrorism_rate = Decimal("0")
            
            if product_code in ["UBGR", "BGR"]:
                terr_si = Decimal(str(request.terrorismSI or 0.0))
                if terr_si > 0:
                    try:
                        t_rate_val = get_terrorism_rate_per_mille(
                             product_code=product_code,
                             occupancy_code=request.occupancyCode,
                             tsi=float(terr_si)
                        )
                        terrorism_rate = t_rate_val if t_rate_val is not None else Decimal("0.0")
                        
                        terrorism_premium = terr_si * terrorism_rate / Decimal("1000")
                        terrorism_premium = Decimal(str(round_currency(float(terrorism_premium))))
                    except Exception as e:
                        logger.warning(f"Terrorism calc skipped due to lookup error: {e}")
                        terrorism_premium = Decimal("0")
            
            # --- EARTHQUAKE (EQ) PREMIUM CALCULATION ---
            # Rules:
            # - UBGR, BSUS: EQ Not applicable (0.0)
            # - Others (SFSP, UVGR, UVUS, BLUS, IAR): Applicable, Key = (IIB, Zone)
            
            eq_premium = Decimal("0")
            eq_rate = Decimal("0")
            
            # Whitelist products that REQUIRE EQ (or blacklist UBGR/BSUS)
            # Prompt says "EQ is NOT applicable to UBGR and BSUS"
            if product_code not in ["UBGR", "BSUS", "BGRP"]: # BGRP is alias for UBGR often
                 # Assume applicable for all others (SFSP, etc)
                 # Validate Zone
                 if not request.eqZone:
                      raise ValueError(f"EQ Zone is required for product {product_code}")
                 
                 # Fetch Rate
                 try:
                      eq_rate = get_fire_eq_rate_per_mille(request.occupancyCode, request.eqZone)
                      # Calc Premium
                      eq_si = total_si # Usually EQ SI = Total SI unless specified otherwise
                      eq_premium = eq_si * eq_rate / Decimal("1000")
                      eq_premium = Decimal(str(round_currency(float(eq_premium))))
                 except Exception as e:
                      logger.error(f"EQ Rate Lookup Failed: {e}")
                      # If logic is strict, we should raise. Prompt: "ERROR: If EQ required ... return HTTP 400" (handled by ValueError prop)
                      raise ValueError(f"Failed to calculate EQ Premium: {e}")
            
            # 9. Net Premium Aggregation
            # Prompt Step 3:
            # subtotal = base + add_on + pa
            # discount = subtotal * pct
            # loading = subtotal * pct
            # net = subtotal - discount + loading + terr
            
            # 9. Net Premium Aggregation
            # Define Subtotal (Excluding Terrorism)
            # Typically includes Base + AddOns + EQ (if applicable)
            total_before_adjustments = base_premium + add_on_premium + eq_premium
            
            # Recalculate Discount/Loading on this valid subtotal
            # Discount
            discount_amount = total_before_adjustments * discount_pct / Decimal("100")
            discount_amount = Decimal(str(round_currency(float(discount_amount))))
            
            # Loading
            loading_amount = total_before_adjustments * loading_pct / Decimal("100")
            loading_amount = Decimal(str(round_currency(float(loading_amount))))
            
            # Net Excl Terrorism
            net_premium_excl_terrorism = total_before_adjustments - discount_amount + loading_amount
            
            # Final Net
            annual_net = net_premium_excl_terrorism + terrorism_premium
            annual_net = Decimal(str(round_currency(float(annual_net))))
            
            # Policy Period
            final_net = annual_net * Decimal(str(policy_period))
            final_net = Decimal(str(round_currency(float(final_net))))
            
            if final_net <= 0 and total_si > 0:
                 logger.warning("Net premium is zero despite SI > 0")
                 # Check logic?
                 
            # Taxes
            cgst = final_net * Decimal("0.09")
            cgst = Decimal(str(round_currency(float(cgst))))
            sgst = final_net * Decimal("0.09")
            sgst = Decimal(str(round_currency(float(sgst))))
            stamp = Decimal("1.0")
            
            gross = final_net + cgst + sgst + stamp
            gross = Decimal(str(round_currency(float(gross))))
            
            # LOGGING
            logger.info(
              f"🔥 CALC BREAKDOWN | "
              f"base={base_premium}, add_on={add_on_premium}, terr={terrorism_premium}, "
              f"disc={discount_amount}, load={loading_amount}, "
              f"net={final_net}, gross={gross}"
            )
            
            return {
                "breakdown": PremiumBreakdown(
                    basic_premium=float(base_premium),
                    add_on_premium=float(add_on_premium),
                    discount_amount=float(discount_amount),
                    sub_total=float(total_before_adjustments), # Prompt called this subtotal
                    loading_amount=float(loading_amount),
                    terrorism_premium=float(terrorism_premium),
                    net_premium=float(final_net),
                    cgst=float(cgst),
                    sgst=float(sgst),
                    stamp_duty=float(stamp),
                    gross_premium=float(gross)
                ),
                "meta": CalculationMeta(
                    applied_rate=float(basic_rate),
                    risk_rate=float(basic_rate),
                    rate_source="product_basic_rates",
                    terrorism_rate=float(terrorism_rate),
                    occupancy_code=request.occupancyCode,
                    product_code=product_code
                )
            }

        except Exception as e:
            logger.error(f"CRITICAL CALC ERROR: {e}", exc_info=True)
            raise ValueError(f"Calculation failed: {str(e)}")
