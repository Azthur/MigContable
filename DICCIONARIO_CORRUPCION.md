# Diccionario de Patrones de Corrupción de Caracteres

## Resumen de Análisis

### Base de Datos: Staging Local (migconta_db)

#### Tablas y Campos Afectados

| Tabla | Campo | Registros Corruptos | Tipo de Datos |
|-------|-------|---------------------|---------------|
| cbdmauxi | nomaux | 0 | Nombre de auxiliar |
| cbdmauxi | diraux | 0 | Dirección |
| cbdmauxi | tlfaux | 0 | Teléfono |
| cbdmauxi | email | 0 | Email |
| cbdmauxi | contacto | 0 | Contacto |

**Total registros corruptos en staging local: 0 ✓**

### Base de Datos: Contasis Final (contasis_002, contasis_003, contasis_004, contasis_005, contasis_006)

**Estado actual:** Todos los caracteres corruptos fueron corregidos.
- contasis_002: 5 registros corregidos
- contasis_003: 23 registros corregidos
- contasis_005: 3 registros corregidos
- contasis_004: 0 registros corruptos
- contasis_006: 0 registros corruptos

**Total registros corregidos en Contasis final: 31 ✓**

---

## Patrones de Corrupción Identificados y Confirmados

### Patrones Principales Confirmados (Funcionan Correctamente)

| Patrón Corrupto | Corrección Confirmada | Descripción |
|-----------------|---------------------|-------------|
| ├æ | Ñ | Enye mayúscula corrupta |
| ├ü | ú | Vocal u mayúscula corrupta |
| ├ë | é | Vocal e mayúscula corrupta |
| ├ô | ó | Vocal o mayúscula corrupta |
| ├á | á | Vocal a mayúscula corrupta |
| ├â┬▒ | ñ | Enye en combinación corrupta |
| ├â┬í | á | Vocal a en combinación corrupta |
| ├âí | á | Vocal a en combinación corrupta |
| ├▒ | ñ | Enye corrupta |
| ├¡ | í | Vocal i corrupta |
| ├Ü | ú | Vocal u mayúscula corrupta |
| ├í | í | Vocal i corrupta |
| ├ì | í | Vocal i corrupta |
| Dé | D' | D con apóstrofe corrupto |
| ├® | é | Vocal e minúscula corrupta (UTF-8 a WIN1252) |

### Patrones Adicionales Identificados (Requieren Validación)

| Patrón Corrupto | Ejemplo | Corrección Sugerida | Estado |
|-----------------|---------|---------------------|--------|
| â┼í | PER â┼í S.A. | Ú | Pendiente validación |
| â?A | FERRETER â?A LA UNION | ÍA | Pendiente validación |
| âÔÇ░TIC | COSM âÔÇ░TIC | ÉTIC | Pendiente validación |
| âÔÇôNIMA | AN âÔÇôNIMA | ÓNIMA | Pendiente validación |
| âÔÇ░TICA | EST âÔÇ░TICA | ÉTICA | Pendiente validación |
| â?MAC | R â?MAC | ÍMAC | Pendiente validación |
| âÔÇôN | RAM âÔÇôN | ÓN | Pendiente validación |
| âÔÇ░N | AYEL âÔÇ░N | ÓN | Pendiente validación |

### Patrones Problemáticos (Causan Efectos Secundarios)

| Patrón Corrupto | Problema | Recomendación |
|-----------------|----------|---------------|
| ┬á | Puede afectar datos válidos | Usar solo en contexto específico |
| ┬é | Puede afectar datos válidos | Usar solo en contexto específico |
| ┬í | Puede afectar datos válidos | Usar solo en contexto específico |
| ┬ó | Puede afectar datos válidos | Usar solo en contexto específico |
| ┬ú | Puede afectar datos válidos | Usar solo en contexto específico |
| ┬ñ | Puede afectar datos válidos | Usar solo en contexto específico |
| ┬ | Puede afectar datos válidos | Usar solo en contexto específico |
| á | Reemplazo muy genérico | NO USAR - causa efectos secundarios |
| íÁ | Puede afectar datos válidos | Usar solo en contexto específico |
| Á | Reemplazo muy genérico | NO USAR - causa efectos secundarios |

---

## Estrategia de Corrección

### Para cg_entitrib (Entidades) - COMPLETADO ✓

**Método:** API DNI/RUC externa
- Script: `fix_corrupted_entities.py`
- Proceso: Consultar API para datos correctos y actualizar registros
- Resultado: 0 registros corruptos en Contasis final

### Para cbdmauxi (Auxiliares) - COMPLETADO ✓

**Método:** Reemplazo de patrones específicos confirmados
- Script: `fix_cbdmauxi_encoding.py`
- Proceso: Aplicar solo patrones confirmados que no causan efectos secundarios
- Campos afectados: nomaux, diraux, tlfaux, email, contacto, contacto2
- Resultado: 0 registros corruptos ✓ (reducido de 704 iniciales)

**Lección aprendida:** Los patrones genéricos como `á` → espacio causan efectos secundarios. La solución fue usar solo patrones específicos confirmados.

---

## Recomendaciones

1. **Usar solo patrones específicos confirmados** para evitar efectos secundarios
2. **Validar cada patrón** antes de aplicarlo masivamente
3. **Backup** antes de correcciones masivas
4. **Monitoreo** de encoding en futuras migraciones
5. **Evitar patrones genéricos** como reemplazos de caracteres individuales que pueden afectar datos válidos

---

## Scripts Disponibles

- `analyze_staging_corruption.py` - Análisis de corrupción en staging local
- `analyze_cbdmauxi_patterns.py` - Análisis detallado de patrones en cbdmauxi
- `show_cbdmauxi_corruption.py` - Muestra registros corruptos actuales
- `show_remaining_corruption.py` - Muestra registros corruptos restantes
- `fix_corrupted_entities.py` - Corrección de entidades usando API
- `fix_cbdmauxi_encoding.py` - Corrección de encoding en cbdmauxi (solo patrones confirmados)
- `run_etl_entidades_no_extract.py` - ETL sin re-extracción
- `verify_entidades_migration.py` - Verificación de correcciones
