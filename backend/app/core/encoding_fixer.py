"""
Módulo para corrección de caracteres corruptos UTF-8 antes de migrar a WIN1252.
Basado en el diccionario de patrones de corrupción identificados.
"""

def fix_encoding(value):
    """
    Corrige el encoding de un valor aplicando patrones específicos confirmados.
    Esta función debe aplicarse a todos los campos de texto antes de migrar
    desde staging (UTF-8) hacia Contasis (WIN1252).
    
    Args:
        value: Valor a corregir (str o None)
    
    Returns:
        Valor corregido con caracteres UTF-8 válidos para conversión a WIN1252
    """
    if value is None or not isinstance(value, str):
        return value
    
    try:
        # Patrones de corrección confirmados (ordenados por longitud descendente)
        # Los patrones más largos deben procesarse primero para evitar reemplazos parciales
        replacements = [
            # Patrones complejos (más largos primero)
            ('├â┬▒', 'ñ'),
            ('├â┬í', 'á'),
            ('├âí', 'á'),
            ('├é┬á', 'á'),
            ('├éí', 'í'),
            ('├ÂÍ', 'Á'),
            ('├ÌA', 'ÍA'),
            # Patrones simples específicos
            ('├®', 'é'),
            ('├æ', 'Ñ'),
            ('├ü', 'ú'),
            ('├ë', 'é'),
            ('├ô', 'ó'),
            ('├á', 'á'),
            ('├▒', 'ñ'),
            ('├¡', 'í'),
            ('├Ü', 'ú'),
            ('├í', 'í'),
            ('├ì', 'í'),
            ('Dé', "D'"),
        ]
        
        for corrupt, correct in replacements:
            value = value.replace(corrupt, correct)
        
        # Re-encode como UTF-8 para asegurar encoding correcto
        return value.encode('utf-8', errors='replace').decode('utf-8')
    
    except Exception:
        # En caso de error, retornar el valor original
        return str(value)


def fix_row_encoding(row_dict, text_columns=None):
    """
    Aplica corrección de encoding a todas las columnas de texto de un registro.
    
    Args:
        row_dict: Diccionario con los datos del registro
        text_columns: Lista de columnas que son de texto (opcional, si no se provee
                     se asumen todas las columnas de tipo str)
    
    Returns:
        Diccionario con los valores corregidos
    """
    if text_columns is None:
        # Si no se especifican columnas, corregir todos los valores string
        text_columns = [k for k, v in row_dict.items() if isinstance(v, str)]
    
    for col in text_columns:
        if col in row_dict and row_dict[col] is not None:
            row_dict[col] = fix_encoding(row_dict[col])
    
    return row_dict


def fix_dataframe_encoding(df, text_columns=None):
    """
    Aplica corrección de encoding a un DataFrame pandas.
    
    Args:
        df: DataFrame pandas
        text_columns: Lista de columnas de texto a corregir (opcional)
    
    Returns:
        DataFrame con los valores corregidos
    """
    import pandas as pd
    
    if text_columns is None:
        # Detectar columnas de tipo object/string
        text_columns = df.select_dtypes(include=['object']).columns.tolist()
    
    for col in text_columns:
        if col in df.columns:
            df[col] = df[col].apply(lambda x: fix_encoding(x) if x is not None else x)
    
    return df
