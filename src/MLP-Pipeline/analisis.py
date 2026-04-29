import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from collections import Counter
import warnings
warnings.filterwarnings('ignore')

# Configurar estilo para mejor visualización
plt.style.use('seaborn-v0_8-darkgrid')
sns.set_palette("husl")

# Cargar tu CSV
df = pd.read_csv('resultados.csv')

print("="*80)
print("ANÁLISIS DE MATRIZ DE CONFUSIÓN Y RENDIMIENTO DEL LPR")
print("="*80)

# ============================================================================
# CASO 1: ANÁLISIS CON TODAS LAS IMÁGENES (incluyendo no detectadas)
# ============================================================================
print("\n" + "="*80)
print("CASO 1: ANÁLISIS COMPLETO (incluyendo imágenes sin detección)")
print("="*80)

# Métricas básicas caso 1
total_c1 = len(df)
aciertos_c1 = df['acierto'].sum()
fallos_c1 = df['fn'].sum()
sin_deteccion_c1 = len(df[df['matricula_detectada'] == '[NO_DETECTADA]'])
ocr_incorrecto_c1 = fallos_c1 - sin_deteccion_c1

print(f"\nEstadísticas básicas:")
print(f"  Total imágenes: {total_c1}")
print(f"  Aciertos: {aciertos_c1} ({aciertos_c1/total_c1:.2%})")
print(f"  Fallos totales: {fallos_c1} ({fallos_c1/total_c1:.2%})")
print(f"    - Sin detección: {sin_deteccion_c1}")
print(f"    - OCR incorrecto: {ocr_incorrecto_c1}")

# ============================================================================
# CASO 2: ANÁLISIS EXCLUYENDO NO DETECTADAS
# ============================================================================
print("\n" + "="*80)
print("CASO 2: ANÁLISIS SOLO CON DETECCIONES (excluyendo no detectadas)")
print("="*80)

# Filtrar solo imágenes con detección exitosa (excluir [NO_DETECTADA])
df_con_deteccion = df[df['matricula_detectada'] != '[NO_DETECTADA]'].copy()
total_c2 = len(df_con_deteccion)
aciertos_c2 = df_con_deteccion['acierto'].sum()
fallos_c2 = total_c2 - aciertos_c2

print(f"\nEstadísticas básicas:")
print(f"  Total detecciones: {total_c2}")
print(f"  Aciertos: {aciertos_c2} ({aciertos_c2/total_c2:.2%})")
print(f"  Fallos OCR: {fallos_c2} ({fallos_c2/total_c2:.2%})")

# Comparativa entre casos
print(f"\nComparativa de Accuracy:")
print(f"  Caso 1 (incluye no detectadas): {aciertos_c1/total_c1:.2%}")
print(f"  Caso 2 (solo detecciones): {aciertos_c2/total_c2:.2%}")
print(f"  Mejora: {(aciertos_c2/total_c2 - aciertos_c1/total_c1):.2%}")

# Por tipo de imagen en caso 2
diurnas_c2 = df_con_deteccion[df_con_deteccion['tipo'] == 'diurna']
nocturnas_c2 = df_con_deteccion[df_con_deteccion['tipo'] == 'nocturna']
print(f"\nRendimiento por tipo (solo detecciones):")
print(f"  Diurnas: {diurnas_c2['acierto'].sum()}/{len(diurnas_c2)} ({diurnas_c2['acierto'].mean():.2%})")
print(f"  Nocturnas: {nocturnas_c2['acierto'].sum()}/{len(nocturnas_c2)} ({nocturnas_c2['acierto'].mean():.2%})")

# ============================================================================
# MÉTRICAS DE TIEMPO (CORREGIDO)
# ============================================================================
# Definir tiempos_validos ANTES de usarlo
tiempos_validos = df[df['tiempo_ms'] > 0]['tiempo_ms']
if len(tiempos_validos) > 0:
    tiempo_promedio = tiempos_validos.mean()
    tiempo_std = tiempos_validos.std()
    tiempo_min = tiempos_validos.min()
    tiempo_max = tiempos_validos.max()
else:
    tiempo_promedio = tiempo_std = tiempo_min = tiempo_max = 0

print(f"\nMétricas de tiempo de respuesta:")
print(f"  Promedio: {tiempo_promedio:.2f} ms")
print(f"  Desviación std: {tiempo_std:.2f} ms")
print(f"  Mínimo: {tiempo_min:.2f} ms")
print(f"  Máximo: {tiempo_max:.2f} ms")

# ============================================================================
# MATRIZ DE CONFUSIÓN GENERAL
# ============================================================================
print("\n" + "="*80)
print("MATRIZ DE CONFUSIÓN GENERAL")
print("="*80)

# Crear matriz de confusión a nivel de imagen
from sklearn.metrics import confusion_matrix, classification_report

# Para caso 1 (todas las imágenes)
y_true_c1 = ['positivo'] * total_c1
y_pred_c1 = ['positivo' if x else 'negativo' for x in df['acierto']]

# Para caso 2 (solo detecciones)
y_true_c2 = ['positivo'] * total_c2
y_pred_c2 = ['positivo' if x else 'negativo' for x in df_con_deteccion['acierto']]

print("\nMatriz de Confusión - Caso 1 (todas las imágenes):")
cm_c1 = confusion_matrix(y_true_c1, y_pred_c1, labels=['positivo', 'negativo'])
print(f"  Verdaderos Positivos (TP): {cm_c1[0,0]}")
print(f"  Falsos Negativos (FN): {cm_c1[0,1]}")
print(f"  Falsos Positivos (FP): {cm_c1[1,0]}")
print(f"  Verdaderos Negativos (TN): {cm_c1[1,1]}")

print("\nMatriz de Confusión - Caso 2 (solo detecciones):")
cm_c2 = confusion_matrix(y_true_c2, y_pred_c2, labels=['positivo', 'negativo'])
print(f"  Verdaderos Positivos (TP): {cm_c2[0,0]}")
print(f"  Falsos Negativos (FN): {cm_c2[0,1]}")
print(f"  Falsos Positivos (FP): {cm_c2[1,0]}")
print(f"  Verdaderos Negativos (TN): {cm_c2[1,1]}")

# ============================================================================
# MATRIZ DE CONFUSIÓN DE CARACTERES (OCR a nivel de caracter)
# ============================================================================
print("\n" + "="*80)
print("MATRIZ DE CONFUSIÓN DE CARACTERES (OCR)")
print("="*80)

def build_character_confusion_matrix(df_analysis):
    """Construye matriz de confusión a nivel de caracteres"""
    confusion_counts = {}
    character_errors = []
    
    for _, row in df_analysis.iterrows():
        if row['matricula_detectada'] == '[NO_DETECTADA]' or row['acierto']:
            continue
        
        real = row['matricula_real']
        pred = row['matricula_detectada']
        
        if not real or not pred:
            continue
            
        # Alinear longitudes
        max_len = max(len(real), len(pred))
        real = real.ljust(max_len, '?')
        pred = pred.ljust(max_len, '?')
        
        for i, (r_char, p_char) in enumerate(zip(real, pred)):
            if r_char != p_char:
                key = (r_char, p_char)
                confusion_counts[key] = confusion_counts.get(key, 0) + 1
                character_errors.append({
                    'position': i,
                    'real': r_char,
                    'predicted': p_char,
                    'plate': real,
                    'prediction': pred
                })
    
    return confusion_counts, character_errors

# Matriz para caso 2 (solo detecciones)
confusion_counts, char_errors = build_character_confusion_matrix(df_con_deteccion)

print(f"\nTotal de errores a nivel de caracter: {sum(confusion_counts.values())}")
print(f"\nTop 10 confusiones más frecuentes:")
sorted_confusions = sorted(confusion_counts.items(), key=lambda x: x[1], reverse=True)[:10]

for (real, pred), count in sorted_confusions:
    print(f"  '{real}' → '{pred}': {count} veces")

# ============================================================================
# ANÁLISIS POR POSICIÓN DEL CARÁCTER
# ============================================================================
print("\n" + "="*80)
print("ANÁLISIS DE ERRORES POR POSICIÓN EN LA PLACA")
print("="*80)

# Estructura típica de placa mexicana: CCC-NNN-C (9 caracteres)
positions = ['P1', 'P2', 'P3', 'G1', 'G2', 'G3', 'U1']
position_errors = {pos: [] for pos in positions}

for error in char_errors:
    pos_idx = error['position']
    if pos_idx < 3:
        if pos_idx == 0:
            position_errors['P1'].append(error)
        elif pos_idx == 1:
            position_errors['P2'].append(error)
        else:
            position_errors['P3'].append(error)
    elif pos_idx < 6:
        if pos_idx == 3:
            position_errors['G1'].append(error)
        elif pos_idx == 4:
            position_errors['G2'].append(error)
        else:
            position_errors['G3'].append(error)
    elif pos_idx == 6:
        position_errors['U1'].append(error)

print("\nErrores por sección de la placa:")
print(f"  Primeras 3 letras (Estado/Municipio): {len(position_errors['P1'])+len(position_errors['P2'])+len(position_errors['P3'])} errores")
print(f"  Números (Folio): {len(position_errors['G1'])+len(position_errors['G2'])+len(position_errors['G3'])} errores")
print(f"  Última letra (Serie): {len(position_errors['U1'])} errores")

# Detalle por posición específica
print("\nErrores por posición específica:")
for pos in positions:
    print(f"  {pos}: {len(position_errors[pos])} errores")

# ============================================================================
# VISUALIZACIÓN DE MATRICES DE CONFUSIÓN
# ============================================================================
print("\n" + "="*80)
print("GENERANDO VISUALIZACIONES")
print("="*80)

# Figura 1: Comparativa de rendimiento
fig, axes = plt.subplots(2, 2, figsize=(14, 10))

# Gráfico 1: Comparativa de accuracy
cases = ['Caso 1\n(Todas)\n46%', 'Caso 2\n(Solo detecciones)\n63%']
accuracies = [aciertos_c1/total_c1*100, aciertos_c2/total_c2*100]
colors = ['#FF6B6B', '#4ECDC4']
bars = axes[0, 0].bar(cases, accuracies, color=colors, edgecolor='black', linewidth=1.5)
axes[0, 0].set_ylabel('Accuracy (%)', fontsize=12)
axes[0, 0].set_title('Comparativa de Accuracy entre Casos', fontsize=14, fontweight='bold')
axes[0, 0].set_ylim(0, 100)
for bar, acc in zip(bars, accuracies):
    axes[0, 0].text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1, 
                    f'{acc:.1f}%', ha='center', va='bottom', fontsize=11, fontweight='bold')

# Gráfico 2: Distribución de fallos (Caso 1)
fallos_labels = [f'Sin Detección\n({sin_deteccion_c1})', f'OCR Incorrecto\n({ocr_incorrecto_c1})']
fallos_counts = [sin_deteccion_c1, ocr_incorrecto_c1]
colors_fallos = ['#FF6B6B', '#FFE66D']
axes[0, 1].pie(fallos_counts, labels=fallos_labels, autopct='%1.0f%%', colors=colors_fallos, 
                startangle=90, explode=(0.05, 0), shadow=True)
axes[0, 1].set_title('Distribución de Fallos (Caso 1)', fontsize=14, fontweight='bold')

# Gráfico 3: Rendimiento por tipo (Caso 2)
if len(diurnas_c2) > 0 and len(nocturnas_c2) > 0:
    tipos = ['Diurnas', 'Nocturnas']
    rendimiento = [diurnas_c2['acierto'].mean()*100, nocturnas_c2['acierto'].mean()*100]
    colors_tipo = ['#95E1D3', '#F38181']
    bars = axes[1, 0].bar(tipos, rendimiento, color=colors_tipo, edgecolor='black', linewidth=1.5)
    axes[1, 0].set_ylabel('Precisión (%)', fontsize=12)
    axes[1, 0].set_title('Rendimiento por Tipo (Solo Detecciones)', fontsize=14, fontweight='bold')
    axes[1, 0].set_ylim(0, 100)
    for bar, acc in zip(bars, rendimiento):
        axes[1, 0].text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1, 
                        f'{acc:.1f}%', ha='center', va='bottom', fontsize=11, fontweight='bold')

# Gráfico 4: Evolución de confianza (aciertos vs fallos)
conf_aciertos = df[df['acierto']==True]['confianza_ocr'].mean() * 1000 if len(df[df['acierto']==True]) > 0 else 0
conf_fallos = df[df['acierto']==False]['confianza_ocr'].mean() * 1000 if len(df[df['acierto']==False]) > 0 else 0
conf_data = [conf_aciertos, conf_fallos]
bars = axes[1, 1].bar(['Aciertos', 'Fallos'], conf_data, color=['#4ECDC4', '#FF6B6B'], 
                      edgecolor='black', linewidth=1.5)
axes[1, 1].set_ylabel('Confianza OCR (x1000)', fontsize=12)
axes[1, 1].set_title('Confianza Promedio: Aciertos vs Fallos', fontsize=14, fontweight='bold')
for bar, conf in zip(bars, conf_data):
    axes[1, 1].text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5, 
                    f'{conf:.1f}', ha='center', va='bottom', fontsize=11, fontweight='bold')

plt.tight_layout()
plt.savefig('comparativa_rendimiento.png', dpi=150, bbox_inches='tight')
print("✓ Gráfico guardado: comparativa_rendimiento.png")

# Figura 2: Matriz de confusión de caracteres (top confusiones)
fig2, ax2 = plt.subplots(figsize=(12, 8))

if sorted_confusions:
    top_chars = [f"'{real}' → '{pred}'" for (real, pred), _ in sorted_confusions[:15]]
    top_counts = [count for _, count in sorted_confusions[:15]]
    
    colors = plt.cm.YlOrRd(np.linspace(0.3, 0.9, len(top_chars)))
    bars = ax2.barh(top_chars, top_counts, color=colors, edgecolor='black', linewidth=1)
    ax2.set_xlabel('Número de ocurrencias', fontsize=12)
    ax2.set_title('Top 15 Confusiones de Caracteres (OCR)', fontsize=14, fontweight='bold')
    ax2.invert_yaxis()
    
    for bar, count in zip(bars, top_counts):
        ax2.text(bar.get_width() + 0.5, bar.get_y() + bar.get_height()/2, 
                f'{count}', va='center', fontsize=10)
    
    plt.tight_layout()
    plt.savefig('confusion_caracteres.png', dpi=150, bbox_inches='tight')
    print("✓ Gráfico guardado: confusion_caracteres.png")

# Figura 3: Mapa de calor de matriz de confusión por posición
fig3, ax3 = plt.subplots(figsize=(10, 8))

# Crear matriz de confusión para caracteres específicos
characters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
conf_matrix = np.zeros((len(characters), len(characters)))

for (real, pred), count in confusion_counts.items():
    if real in characters and pred in characters:
        i = characters.index(real)
        j = characters.index(pred)
        conf_matrix[i, j] = count

# Mostrar solo las confusiones significativas (>0)
mask = conf_matrix == 0
sns.heatmap(conf_matrix, mask=mask, cmap='YlOrRd', annot=False, 
            xticklabels=10, yticklabels=10, ax=ax3, cbar_kws={'label': 'Frecuencia'})
ax3.set_title('Mapa de Calor de Confusiones de Caracteres', fontsize=14, fontweight='bold')
ax3.set_xlabel('Carácter Predicho', fontsize=12)
ax3.set_ylabel('Carácter Real', fontsize=12)

plt.tight_layout()
plt.savefig('heatmap_confusion.png', dpi=150, bbox_inches='tight')
print("✓ Gráfico guardado: heatmap_confusion.png")

# ============================================================================
# REPORTE FINAL DETALLADO
# ============================================================================
print("\n" + "="*80)
print("REPORTE FINAL DE EVALUACIÓN")
print("="*80)

# Tabla de métricas completas
metrics_data = {
    'Métrica': [
        'Total imágenes evaluadas',
        'Detecciones exitosas',
        'Tasa de detección',
        '',
        'Accuracy (Caso 1 - todas)',
        'Accuracy (Caso 2 - solo detecciones)',
        'Mejora al excluir no detectadas',
        '',
        'Precisión (sin FP)',
        'Recall (Caso 1)',
        'Recall (Caso 2)',
        'F1-Score (Caso 1)',
        'F1-Score (Caso 2)',
        '',
        'Errores totales',
        '- Sin detección',
        '- OCR incorrecto',
        '',
        'Rendimiento diurno (Caso 2)',
        'Rendimiento nocturno (Caso 2)',
        'Brecha diurna/nocturna',
        '',
        'Tiempo promedio respuesta',
        'Tiempo mínimo',
        'Tiempo máximo',
        '',
        'Confianza OCR (aciertos)',
        'Confianza OCR (fallos)',
        'Diferencia de confianza'
    ],
    'Valor': [
        f"{total_c1}",
        f"{total_c2}",
        f"{total_c2/total_c1:.2%}",
        '---',
        f"{aciertos_c1/total_c1:.2%}",
        f"{aciertos_c2/total_c2:.2%}",
        f"{(aciertos_c2/total_c2 - aciertos_c1/total_c1):.2%}",
        '---',
        "100%",
        f"{aciertos_c1/total_c1:.2%}",
        f"{aciertos_c2/total_c2:.2%}",
        f"{2*(aciertos_c1/total_c1)/(1+aciertos_c1/total_c1):.2%}",
        f"{2*(aciertos_c2/total_c2)/(1+aciertos_c2/total_c2):.2%}",
        '---',
        f"{fallos_c1}",
        f"{sin_deteccion_c1}",
        f"{ocr_incorrecto_c1}",
        '---',
        f"{diurnas_c2['acierto'].mean():.2%}" if len(diurnas_c2) > 0 else "N/A",
        f"{nocturnas_c2['acierto'].mean():.2%}" if len(nocturnas_c2) > 0 else "N/A",
        f"{(diurnas_c2['acierto'].mean() - nocturnas_c2['acierto'].mean()):.2%}" if len(diurnas_c2) > 0 and len(nocturnas_c2) > 0 else "N/A",
        '---',
        f"{tiempo_promedio:.2f} ms",
        f"{tiempo_min:.2f} ms",
        f"{tiempo_max:.2f} ms",
        '---',
        f"{df[df['acierto']==True]['confianza_ocr'].mean():.4f}" if len(df[df['acierto']==True]) > 0 else "N/A",
        f"{df[df['acierto']==False]['confianza_ocr'].mean():.4f}" if len(df[df['acierto']==False]) > 0 else "N/A",
        f"{(df[df['acierto']==True]['confianza_ocr'].mean() - df[df['acierto']==False]['confianza_ocr'].mean()):.4f}" if len(df[df['acierto']==True]) > 0 and len(df[df['acierto']==False]) > 0 else "N/A"
    ]
}

metrics_df = pd.DataFrame(metrics_data)
print("\n" + metrics_df.to_string(index=False))

# Exportar resultados a CSV
metrics_df.to_csv('reporte_metricas_completo.csv', index=False)
df_con_deteccion.to_csv('resultados_solo_detecciones.csv', index=False)

print("\n✓ Reportes exportados:")
print("  - reporte_metricas_completo.csv")
print("  - resultados_solo_detecciones.csv")
print("  - comparativa_rendimiento.png")
print("  - confusion_caracteres.png")
print("  - heatmap_confusion.png")

print("\n" + "="*80)
print("ANÁLISIS COMPLETADO")
print("="*80)