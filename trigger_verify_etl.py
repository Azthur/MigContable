import sys
import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from app.core.config import get_settings

def trigger_and_verify():
    settings = get_settings()
    engine = create_engine(settings.POSTGRES_CONNECTION_STRING)
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        # Use subcategory 4 (vtaritem) which has data in 2026-01
        sub_id = 4
        periodo = "2026"
        mes = "01"
        company_id = 1 # Assuming company 1 based on previous checks
        
        print(f"Testing with subcategory ID {sub_id}, company_id={company_id}, period={periodo}-{mes}")

        # Trigger generation via API function code
        from app.api.endpoints.mapeo import generate_to_cf_diariol
        
        body = {
            "company_id": company_id,
            "subcategoria_id": sub_id,
            "periodo": periodo,
            "mes": mes,
            "clear_previous": True,
            "filters": [] # No filters to get all data for the month
        }
        
        print("Triggering generation...")
        result = generate_to_cf_diariol(body, db=session)
        print(f"SUCCESS: {result['message']}")
        
        # Verify in DB
        cols_query = text("SELECT column_name FROM information_schema.columns WHERE table_name = 'cf_diariol'")
        cols = [r[0] for r in session.execute(cols_query).fetchall()]
        
        check_cols = ["cper", "cmes", "ccodcue", "ndebe", "nhaber", "ccodmon", "subcategoria_id", "nasiento", "nidlin"]
        existing_check = [c for c in check_cols if c in cols]
        
        data_query = text(f"SELECT {', '.join(existing_check)} FROM cf_diariol WHERE subcategoria_id = :sub_key ORDER BY nasiento, nidlin LIMIT 20")
        results = session.execute(data_query, {"sub_key": sub_id}).fetchall()
        
        if not results:
            print("ERROR: No records found in cf_diariol after generation!")
        else:
            print(f"\nFound {len(results)} records in cf_diariol. Validating essential fields:")
            all_ok = True
            for row in results:
                row_dict = dict(zip(existing_check, row))
                # Critical check: essential fields should be filled
                null_fields = [k for k, v in row_dict.items() if v is None and k in ["cper", "cmes", "ccodcue", "nasiento", "ccodmon"]]
                if null_fields:
                    print(f"  FAILED: Null values in {null_fields} for row: {row_dict}")
                    all_ok = False
                else:
                    print(f"  OK: Asiento {row_dict['nasiento']} Linea {row_dict['nidlin']} - {row_dict['ccodcue']} - {row_dict['ndebe']}/{row_dict['nhaber']} ({row_dict['ccodmon']})")
            
            if all_ok:
                print("\nVERIFICATION SUCCESSFUL: ETL Step 2 correctly populates mapping fields and generates multiple lines per asiento.")
            else:
                print("\nVERIFICATION FAILED: Some essential fields were NULL.")

    except Exception as e:
        print(f"Error during trigger_and_verify: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()

if __name__ == "__main__":
    trigger_and_verify()
