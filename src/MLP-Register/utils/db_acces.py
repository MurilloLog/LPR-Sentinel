import pandas as pd
import sqlite3

# Leer tu CSV generado
df = pd.read_csv("../../MLP-Generator/dataset/license_plates_metadata.csv")

# Crear conexion y guardar como tabla indexada
import sqlite3
import pandas as pd

with sqlite3.connect('../database/MLPR.db') as conexion:
    # Guardar DataFrame
    df.to_sql('Registros', conexion, if_exists='replace', index=False)
    print(f"Tabla 'Registros' creada con {len(df)} registros")
    
    # Verificar primeros registros
    resultado = pd.read_sql_query("SELECT * FROM Registros LIMIT 5", conexion)
    print("Primeros 5 registros:")
    print(resultado)
    
    # CORRECCIÓN 3: Usar parámetros (forma segura)
    matricula = "AF1-564-C"
    consulta = pd.read_sql_query(
        "SELECT * FROM Registros WHERE Matricula = ?", 
        conexion, 
        params=(matricula,)
    )
    
    print(f"\nResultado para matrícula '{matricula}':")
    print(consulta)
    
    # Verificar si encontró resultados
    if consulta.empty:
        print("No se encontraron registros con esa matrícula")
    else:
        print(f"Se encontraron {len(consulta)} registros")