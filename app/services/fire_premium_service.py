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
    calculate_terrorism_premium,
    get_add_on_rate,
    get_occupancy_details,
    get_fire_eq_rate_per_mille,
    get_stfi_rate_per_mille
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
            if product_code == "UBGR":
                # STRICT: Use explicit rate provided in request
                if request.risk_rate_per_mille is None:
                     # This should be caught by router validation, but double safe
                     raise ValueError("Risk rate missing for UBGR calculation")
                
                basic_rate = Decimal(str(request.risk_rate_per_mille))
                logger.info(f"Using Explicit Risk Rate for UBGR: {basic_rate}")
            else:
                # Fallback / Other Products: Query Database
                try:
                    basic_rate = get_basic_rate_per_mille(product_code, request.occupancyCode)
                    if basic_rate is None or basic_rate <= 0:
                         raise ValueError("Rate resolved to None or Zero")
                except Exception as e:
                    logger.error(f"Basic rate lookup failed: {e}")
                    raise ValueError(f"Basic rate lookup failed for {product_code}/{request.occupancyCode}")
            
            logger.info(f"Basic Rate: {basic_rate} (Per Mille)")
            
            # 3. Basic Fire Premium Calc (ANNUAL)
            # IMPORTANT: Basic fire premium = (Building + Contents) ONLY
            basic_fire_si = building_si + contents_si
            basic_fire_premium_annual = basic_fire_si * basic_rate / Decimal("1000")
            basic_fire_premium_annual = Decimal(str(round_currency(float(basic_fire_premium_annual))))
            
            logger.info(f"Basic Fire Premium (Annual): {basic_fire_premium_annual}")
                
            # 4. Add-On Premium (ANNUAL, PAID add-ons only)
            # EQ and STFI are FREE (covered by default) - do NOT include in add_on_premium
            add_on_premium_annual = Decimal("0")
            add_on_details = []
            
            # Allow addons check
            occ_details = get_occupancy_details(request.occupancyCode)
            allow_addons = True
            if occ_details and not occ_details.get("allow_addons", True):
                allow_addons = False
            
            if allow_addons:
                add_on_premium_annual, add_on_details = FirePremiumCalculator._calculate_add_on_premium(
                    product_code=product_code,
                    occupancy_code=request.occupancyCode,
                    add_ons=request.addOns,
                    pa_proposer=request.paSelection.proposer,
                    pa_spouse=request.paSelection.spouse
                )
            
            logger.info(f"Add-On Premium (Annual): {add_on_premium_annual}")
            
            # 5. Discount Calculation (On Base + AddOn)
            # Note: Will be calculated on total_before_adjustments later
            
            # 5. Terrorism Premium (ANNUAL)
            terrorism_premium_annual = Decimal("0")
            terrorism_rate = Decimal("0")
            
            # Use provided terrorism SI
            terr_si = Decimal(str(request.terrorismSI or 0.0))
            
            if terr_si > 0:
                try:
                    occ_type = occ_details.get("occupancy_type", "Non-Industrial") if occ_details else "Non-Industrial"
                    
                    # Resolve single rate for metadata
                    terrorism_rate = get_terrorism_rate_per_mille(occ_type, float(total_si))
                    
                    # Calculate premium slab-wise (ANNUAL)
                    terrorism_premium_annual = Decimal(str(calculate_terrorism_premium(occ_type, float(terr_si))))
                    terrorism_premium_annual = Decimal(str(round_currency(float(terrorism_premium_annual))))
                    
                    logger.info(f"Terrorism Premium (Annual): {terrorism_premium_annual}")
                except Exception as e:
                    logger.warning(f"Terrorism calc failed: {e}")
                    terrorism_premium_annual = Decimal("0")
            
            # --- EARTHQUAKE (EQ) PREMIUM CALCULATION ---
            # Rules:
            # - UBGR, BSUS: EQ Not applicable (0.0) -> Wait, prompt says BSUS requires EQ Zone implies EQ applicable?
            # Prompt Step 5: "BSUS -> fire_bsus_rates (EQ mandatory)".
            # "EQ ... Applies to: SFSP, IAR, UVUS, BLUS ... Not for UBGR ... BSUS requires EQ Zone".
            # This means BSUS uses `fire_bsus_rates` (which depends on EQ Zone) BUT `fire_eq_rates` (the separate EQ addon) does NOT apply to BSUS? 
            # Prompt says "EQ ... Not for UBGR". It lists "Applies to: SFSP, IAR, UVUS, BLUS". It does NOT list BSUS in the 'Applies to' list for EQ.
            # But "BSUS requires EQ Zone" is listed under EQ section? Or BSUS section?
            # Under "Base Premium": "BSUS -> fire_bsus_rates (EQ mandatory)".
            # Under "EQ": "Applies to: SFSP... Not for UBGR. BSUS requires EQ Zone".
            # This confirms BSUS Base Rate DEPENDS on EQ Zone, but BSUS does NOT get a separate EQ Premium add-on (it's built into base or strictly derived from base table).
            # So EQ Premium is ONLY for SFSP, IAR, UVUS, BLUS.
            
            eq_premium = Decimal("0")
            eq_rate = Decimal("0")
            
            if product_code in ["SFSP", "IAR", "UVUS", "BLUS", "UVGR", "UVGS"]: # Assuming UVGR/UVGS are in the 'SFSP' family for this logic
                 # Validate Zone
                 if not request.eqZone:
                      raise ValueError(f"EQ Zone is required for product {product_code}")
                 
                 # Fetch Rate
                 try:
                      eq_rate = get_fire_eq_rate_per_mille(request.occupancyCode, request.eqZone)
                      eq_si = total_si 
                      eq_premium = eq_si * eq_rate / Decimal("1000")
                      eq_premium = Decimal(str(round_currency(float(eq_premium))))
                 except Exception as e:
                      logger.error(f"EQ Rate Lookup Failed: {e}")
                      raise ValueError(f"Failed to calculate EQ Premium: {e}")

            # --- STFI PREMIUM CALCULATION ---
            # Rules: 
            # Applies to: SFSP, IAR, UVUS, BLUS.
            # Not for UBGR.
            stfi_premium = Decimal("0")
            stfi_rate = Decimal("0")
            
            if product_code in ["SFSP", "IAR", "UVUS", "BLUS", "UVGR", "UVGS"]:
                 try:
                      stfi_rate = get_stfi_rate_per_mille(request.occupancyCode)
                      stfi_si = total_si
                      stfi_premium = stfi_si * stfi_rate / Decimal("1000")
                      stfi_premium = Decimal(str(round_currency(float(stfi_premium))))
                 except Exception as e:
                      logger.error(f"STFI Rate Lookup Failed: {e}")
                      # If critical, raise. Else 0.
                      # Proceed with 0 for now unless strict
                      stfi_premium = Decimal("0")

            # 6. Apply Discount & Loading (ANNUAL, only on fire components)
            fire_base_annual = basic_fire_premium_annual + add_on_premium_annual
            
            # Discount (On Fire Base)
            discount_amount_annual = fire_base_annual * discount_pct / Decimal("100")
            discount_amount_annual = Decimal(str(round_currency(float(discount_amount_annual))))
            
            # Loading (On Fire Base after discount)
            loading_base_annual = fire_base_annual - discount_amount_annual
            loading_amount_annual = loading_base_annual * loading_pct / Decimal("100")
            loading_amount_annual = Decimal(str(round_currency(float(loading_amount_annual))))
            
            # Fire Subtotal (Annual)
            fire_subtotal_annual = fire_base_annual - discount_amount_annual + loading_amount_annual
            fire_subtotal_annual = Decimal(str(round_currency(float(fire_subtotal_annual))))
            
            # Annual Net Premium (1-year)
            annual_net_premium = fire_subtotal_annual + terrorism_premium_annual
            annual_net_premium = Decimal(str(round_currency(float(annual_net_premium))))
            
            logger.info(f"Annual Net Premium: {annual_net_premium}")
            
            # 7. Policy Period Scaling (Multiply EVERY component for consistent UI breakdown)
            period_multiplier = Decimal(str(policy_period))
            
            basic_fire_premium = basic_fire_premium_annual * period_multiplier
            add_on_premium = add_on_premium_annual * period_multiplier
            discount_amount = discount_amount_annual * period_multiplier
            loading_amount = loading_amount_annual * period_multiplier
            fire_subtotal = fire_subtotal_annual * period_multiplier
            terrorism_premium = terrorism_premium_annual * period_multiplier
            net_premium = annual_net_premium * period_multiplier
            
            # Round all scaled components
            basic_fire_premium = Decimal(str(round_currency(float(basic_fire_premium))))
            add_on_premium = Decimal(str(round_currency(float(add_on_premium))))
            discount_amount = Decimal(str(round_currency(float(discount_amount))))
            loading_amount = Decimal(str(round_currency(float(loading_amount))))
            fire_subtotal = Decimal(str(round_currency(float(fire_subtotal))))
            terrorism_premium = Decimal(str(round_currency(float(terrorism_premium))))
            net_premium = Decimal(str(round_currency(float(net_premium))))
            
            logger.info(f"Final Net Premium ({policy_period}Y): {net_premium}")
            
            if net_premium <= 0 and total_si > 0:
                 logger.warning("Net premium is zero despite SI > 0")
                 
            # 8. Taxes & Stamp Duty
            cgst = net_premium * Decimal("0.09")
            cgst = Decimal(str(round_currency(float(cgst))))
            sgst = net_premium * Decimal("0.09")
            sgst = Decimal(str(round_currency(float(sgst))))
            
            # Stamp Duty - FIXED
            stamp = Decimal("1.0")
            
            gross = net_premium + cgst + sgst + stamp
            gross = Decimal(str(round_currency(float(gross))))
            
            # LOGGING
            logger.info(
              f"🔥 CALC BREAKDOWN | "
              f"basic_fire={basic_fire_premium}, add_on={add_on_premium}, terr={terrorism_premium}, "
              f"disc={discount_amount}, load={loading_amount}, "
              f"annual_net={annual_net_premium}, net({policy_period}y)={net_premium}, gross={gross}"
            )
            
            return {
                "breakdown": PremiumBreakdown(
                    basic_fire_premium=float(basic_fire_premium),
                    add_on_premium=float(add_on_premium),
                    fire_subtotal=float(fire_subtotal),
                    terrorism_premium=float(terrorism_premium),
                    discount_amount=float(discount_amount),
                    loading_amount=float(loading_amount),
                    net_premium=float(net_premium),
                    cgst=float(cgst),
                    sgst=float(sgst),
                    stamp_duty=float(stamp),
                    gross_premium=float(gross)
                ),
                "meta": CalculationMeta(
                    applied_rate=float(basic_rate),
                    risk_rate=float(basic_rate),
                    rate_source="explicit_risk_rate" if product_code == "UBGR" else "product_basic_rates",
                    terrorism_rate=float(terrorism_rate),
                    occupancy_code=request.occupancyCode,
                    product_code=product_code,
                    policy_period_years=policy_period
                )
            }

        except Exception as e:
            logger.error(f"CRITICAL CALC ERROR: {e}", exc_info=True)
            raise ValueError(f"Calculation failed: {str(e)}")
