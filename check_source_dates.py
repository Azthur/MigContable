from sqlalchemy import create_engine, text
from backend.app.core.config import get_settings

def check_dates():
    settings = get_settings()
    engine = create_engine(settings.POSTGRES_CONNECTION_STRING)
    with engine.connect() as conn:
        try:
            # Check vtaritem columns to find a date field
            res = conn.execute(text("SELECT * FROM vtaritem LIMIT 0"))
            cols = list(res.keys())
            print(f"vtaritem columns: {cols}")
            
            # Look for typical date column names (fch, fec, ffecha, etc.)
            date_col = next((c for c in cols if 'fec' in c.lower() or 'fch' in c.lower() or 'fecha' in c.lower() or 'pdv' in c.lower()), None)
            
            if date_col:
                print(f"Using date column: {date_col}")
                # Get year/month range
                range_query = text(f"SELECT min({date_col}), max({date_col}) FROM vtaritem")
                vmin, vmax = conn.execute(range_query).fetchone()
                print(f"vtaritem date range: {vmin} to {vmax}")
            else:
                print("No obvious date column found in vtaritem.")

            # Check ccbrgdoc
            res = conn.execute(text("SELECT * FROM ccbrgdoc LIMIT 0"))
            cols = list(res.keys())
            date_col = next((c for c in cols if 'fec' in c.lower() or 'fch' in c.lower() or 'fecha' in c.lower()), None)
            if date_col:
                print(f"ccbrgdoc using date column: {date_col}")
                vmin, vmax = conn.execute(text(f"SELECT min({date_col}), max({date_col}) FROM ccbrgdoc")).fetchone()
                print(f"ccbrgdoc date range: {vmin} to {vmax}")

        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    check_dates()
