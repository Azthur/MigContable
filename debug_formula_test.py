import pandas as pd
import numpy as np
from backend.app.core.formula_parser import evaluate_formula_on_df
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

def test():
    df = pd.DataFrame({'CODMON': [1, 2, 3]})
    formula_str = 'SI.CONJUNTO(codmon="1","S", codmon="2", "D")'
    engine = create_engine('sqlite:///:memory:')
    Session = sessionmaker(bind=engine)
    db = Session()
    res = evaluate_formula_on_df(df, formula_str, db, company_id=1, default="")
    print(res)

test()
