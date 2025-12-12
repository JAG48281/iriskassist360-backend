from app.database import engine
from sqlalchemy import text
from seed import get_product_map, upsert
from app.models.fire_models import AddOnRate

def seed_one_failure():
    # NOIV, SFSP
    p_code = "SFSP"
    a_code = "NOIV"
    
    with engine.begin() as conn:
        prod_map = {row[0]: row[1] for row in conn.execute(text("SELECT product_code, id FROM product_master")).fetchall()}
        ao_map = {row[0]: row[1] for row in conn.execute(text("SELECT add_on_code, id FROM add_on_master")).fetchall()}
        
        p_id = prod_map.get(p_code)
        a_id = ao_map.get(a_code)
        
        print(f"P: {p_id}, A: {a_id}")
        
        data = {
             "add_on_id": a_id,
             "product_code": p_code,
             "product_id": p_id,
             "rate_type": "policy_rate",
             "rate_value": 1.0,
             "si_min": None,
             "si_max": None,
             "occupancy_type": None,
             "active": True
         }
         
        try:
             conn.execute(text("INSERT INTO add_on_rates (add_on_id, product_code, product_id, rate_type, rate_value, si_min, si_max, occupancy_type, active) VALUES (:aid, :pc, :pid, :rt, :rv, :smin, :smax, :occ, :act)"), 
                {"aid": a_id, "pc": p_code, "pid": p_id, "rt": "policy_rate", "rv": 1.0, "smin": None, "smax": None, "occ": None, "act": True})
             print("Success.")
        except Exception as e:
             print(f"FAILED: {e}")

if __name__ == "__main__":
    seed_one_failure()
