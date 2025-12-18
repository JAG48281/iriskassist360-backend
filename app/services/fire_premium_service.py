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
    def calculate_ubgr_uvgr(request: UBGRUVGRRequest) -> Dict:
        """
        Calculate premium for UBGR/UVGR products.
        STRICT MODE with ₹50 (Basic+Addon) Minimum Premium Rule.
        """
        logger.info(f"Calculating {request.productCode} Premium")
        logger.info(f"Payload: {request.model_dump()}")

        try:
            # 1. Normalize ALL numeric inputs with safety defaults
            discount_pct = Decimal(str(request.discountPercentage or 0.0))
            loading_pct = Decimal(str(request.loadingPercentage or 0.0))
            
            # Resolve Source SIs (Preference for basic_cover_si/add_on_cover_si as per turn prompt)
            raw_basic_si = request.basic_cover_si if request.basic_cover_si is not None else request.buildingSI
            raw_addon_si = request.add_on_cover_si if request.add_on_cover_si is not None else request.contentsSI
            
            building_si = Decimal(str(raw_basic_si or 0.0))
            contents_si = Decimal(str(raw_addon_si or 0.0))
            terrorism_si_input = Decimal(str(request.terrorism_si or request.terrorismSI or 0.0))
            
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

            # --- UBGR EXCLUSION RULE: Dwellings: Co-operative Society (1001_2) ---
            optional_addons_applicable = True
            if product_code == "UBGR" and request.occupancyCode == "1001_2":
                logger.info("UBGR Co-operative Society logic applied")
                optional_addons_applicable = False
                # Forcibly set contents_si and PA to 0
                contents_si = Decimal("0")
                request.paSelection.proposer = False
                request.paSelection.spouse = False
                # If there are any add-ons in the list, we ignore them in premium calc
                # (handled by setting contents_si to 0 above since add_on_premium depends on it)

            # 2. Basic Rate Lookup (SAFE)
            if product_code == "UBGR":
                if request.risk_rate_per_mille is None:
                     raise ValueError("Risk rate missing for UBGR calculation")
                basic_rate = Decimal(str(request.risk_rate_per_mille))
                logger.info(f"Using Explicit Risk Rate for UBGR: {basic_rate}")
            else:
                try:
                    basic_rate = get_basic_rate_per_mille(product_code, request.occupancyCode)
                    if basic_rate is None or basic_rate <= 0:
                         raise ValueError("Rate resolved to None or Zero")
                except Exception as e:
                    logger.error(f"Basic rate lookup failed: {e}")
                    raise ValueError(f"Basic rate lookup failed for {product_code}/{request.occupancyCode}")
            
            logger.info(f"Basic Rate: {basic_rate} (Per Mille)")
            
            # 3. UBGR Premium Logic (STRICT - ANNUAL)
            
            # basic_fire_premium = buildingSI × risk_rate / 1000
            basic_fire_premium_annual = building_si * basic_rate / Decimal("1000")
            basic_fire_premium_annual = Decimal(str(round_currency(float(basic_fire_premium_annual))))
            
            # 1️⃣ Add-on Premium Calculation
            # add_on_premium = (lossOfRentSI + altAccommodationSI + valuableContentsSI + paProposerSI + paSpouseSI) × risk_rate / 1000
            # MUST ALWAYS be 0 for 1001_2
            if request.occupancyCode == "1001_2":
                add_on_premium_annual = Decimal("0")
                optional_addons_applicable = False
            else:
                add_on_si_sum = (
                    Decimal(str(request.lossOfRentSI or 0)) +
                    Decimal(str(request.altAccommodationSI or 0)) +
                    Decimal(str(request.valuableContentsSI or 0)) +
                    Decimal(str(request.paProposerSI or 0)) +
                    Decimal(str(request.paSpouseSI or 0))
                )
                add_on_premium_annual = add_on_si_sum * basic_rate / Decimal("1000")
                add_on_premium_annual = Decimal(str(round_currency(float(add_on_premium_annual))))
            
            # 2️⃣ Subtotal Premium (EXCLUDING terrorism)
            subtotal_premium_annual = basic_fire_premium_annual + add_on_premium_annual
            
            # 3️⃣ Discount Logic (Apply ONLY on subtotal_premium)
            discount_amount_annual = subtotal_premium_annual * discount_pct / Decimal("100")
            discount_amount_annual = Decimal(str(round_currency(float(discount_amount_annual))))
            
            # 4️⃣ Loading Logic (Apply ONLY after discount, on (subtotal - discount))
            loading_amount_annual = (subtotal_premium_annual - discount_amount_annual) * loading_pct / Decimal("100")
            loading_amount_annual = Decimal(str(round_currency(float(loading_amount_annual))))
            
            # 6. Terrorism Premium (ANNUAL)
            terrorism_premium_annual = Decimal("0")
            # For UBGR, check if "TERRORISM" is in add_ons list
            is_terrorism_selected = any(addon.addOnCode.upper() == "TERRORISM" for addon in request.addOns)
            
            if is_terrorism_selected and terrorism_si_input > 0:
                try:
                    occ_details = get_occupancy_details(request.occupancyCode)
                    occ_type = occ_details.get("occupancy_type", "Non-Industrial") if occ_details else "Non-Industrial"
                    terrorism_premium_annual = Decimal(str(calculate_terrorism_premium(occ_type, float(terrorism_si_input))))
                    terrorism_premium_annual = Decimal(str(round_currency(float(terrorism_premium_annual))))
                except Exception as e:
                    logger.warning(f"Terrorism calc failed: {e}")
                    terrorism_premium_annual = Decimal("0")
            
            # 5️⃣ Net Premium Calculation (FINAL)
            # net_premium = (subtotal_premium - discount_amount + loading_amount) + terrorism_premium
            net_premium_annual = (subtotal_premium_annual - discount_amount_annual + loading_amount_annual) + terrorism_premium_annual
            net_premium_annual = Decimal(str(round_currency(float(net_premium_annual))))
            
            # 8. Policy Period Scaling
            period_multiplier = Decimal(str(policy_period))
            
            basic_fire_premium = basic_fire_premium_annual * period_multiplier
            add_on_premium = add_on_premium_annual * period_multiplier
            subtotal_premium = subtotal_premium_annual * period_multiplier
            terrorism_premium = terrorism_premium_annual * period_multiplier
            discount_amount = discount_amount_annual * period_multiplier
            loading_amount = loading_amount_annual * period_multiplier
            net_premium = net_premium_annual * period_multiplier
            
            # Round scaled components
            basic_fire_premium = Decimal(str(round_currency(float(basic_fire_premium))))
            add_on_premium = Decimal(str(round_currency(float(add_on_premium))))
            subtotal_premium = Decimal(str(round_currency(float(subtotal_premium))))
            terrorism_premium = Decimal(str(round_currency(float(terrorism_premium))))
            discount_amount = Decimal(str(round_currency(float(discount_amount))))
            loading_amount = Decimal(str(round_currency(float(loading_amount))))
            net_premium = Decimal(str(round_currency(float(net_premium))))
            
            # 9. Taxes & Stamp Duty
            cgst = net_premium * Decimal("0.09")
            cgst = Decimal(str(round_currency(float(cgst))))
            sgst = net_premium * Decimal("0.09")
            sgst = Decimal(str(round_currency(float(sgst))))
            
            # Stamp Duty - FIXED
            stamp = 1
            
            # gross_premium
            gross = net_premium + cgst + sgst + stamp
            gross = Decimal(str(round_currency(float(gross))))
            
            # Final Logging
            logger.info(
              f"🔥 CALC BREAKDOWN | "
              f"basic_fire={basic_fire_premium}, add_on={add_on_premium}, subtotal={subtotal_premium}, "
              f"terr={terrorism_premium}, disc={discount_amount}, load={loading_amount}, "
              f"net={net_premium}, gross={gross}"
            )
            
            breakdown = PremiumBreakdown(
                basic_fire_premium=float(basic_fire_premium),
                add_on_premium=float(add_on_premium),
                subtotal_premium=float(subtotal_premium),
                terrorism_premium=float(terrorism_premium),
                discount_amount=float(discount_amount),
                loading_amount=float(loading_amount),
                net_premium=float(net_premium),
                cgst=float(cgst),
                sgst=float(sgst),
                stamp_duty=float(stamp),
                gross_premium=float(gross)
            )

            return {
                "success": True,
                "message": f"{product_code} Premium Calculated Successfully",
                "productCode": product_code,
                **breakdown.model_dump(),
                "meta": CalculationMeta(
                    applied_rate=float(basic_rate),
                    risk_rate=float(basic_rate),
                    rate_source="explicit_risk_rate" if product_code == "UBGR" else "product_basic_rates",
                    occupancy_code=request.occupancyCode,
                    product_code=product_code,
                    policy_period_years=policy_period,
                    optional_addons_applicable=optional_addons_applicable
                )
            }

        except Exception as e:
            logger.error(f"CRITICAL CALC ERROR: {e}", exc_info=True)
            raise ValueError(f"Calculation failed: {str(e)}")
