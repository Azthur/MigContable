# Diagrama Entidad-Relación - SistemaMigConta

Este documento presenta los diagramas de entidad-relación (ER) para la base de datos `migconta_db` del proyecto. Dado que la base de datos cuenta con más de 50 tablas, el diagrama se ha dividido en módulos lógicos para facilitar su visualización y comprensión.

Puedes ver la renderización gráfica de estos diagramas abriendo la vista previa de Markdown en tu IDE (VS Code u otro compatible con Mermaid).

---

## 1. Módulo Central (Empresas, Usuarios y Conexiones)
Este módulo gestiona los usuarios del sistema, las empresas registradas y las credenciales/conexiones a las bases de datos de origen (SQL Server), intermedia (PostgreSQL) y destino final (Contasis).

```mermaid
erDiagram
    users {
        int id PK
        string email
        string hashed_password
        string full_name
        string role
        boolean is_active
        timestamp created_at
        timestamp updated_at
    }

    companies {
        int id PK
        string name
        string ruc
        string description
        boolean is_active
        timestamp created_at
        timestamp updated_at
    }

    source_connections {
        int id PK
        int company_id FK
        string db_type
        string host
        int port
        string database_name
        string username
        string password
        string driver
        string extra_params
        boolean is_active
        timestamp created_at
    }

    destination_connections {
        int id PK
        int company_id FK
        string host
        int port
        string database_name
        string username
        string password
        boolean is_active
        timestamp created_at
    }

    final_dest_connections {
        int id PK
        int company_id FK
        string db_type
        string host
        int port
        string database_name
        string username
        string password
        string target_table
        string target_schema
        boolean is_active
        timestamp created_at
    }

    final_table_selections {
        int id PK
        int company_id FK
        int final_dest_connection_id FK
        string table_schema
        string table_name
        boolean is_selected
        string description
        timestamp created_at
    }

    companies ||--o{ source_connections : "tiene"
    companies ||--o{ destination_connections : "tiene"
    companies ||--o{ final_dest_connections : "tiene"
    companies ||--o{ final_table_selections : "tiene"
    final_dest_connections ||--o{ final_table_selections : "se_asocia_a"
```

---

## 2. Módulo de Configuración de Extracción y Mapeos
Controla las tablas de origen que se extraerán de SQL Server, los filtros de columnas aplicados, las columnas calculadas tipo Excel y las reglas de mapeo contable para generar asientos.

```mermaid
erDiagram
    companies {
        int id PK
    }

    source_connections {
        int id PK
    }

    table_selections {
        int id PK
        int company_id FK
        int source_connection_id FK
        string table_schema
        string table_name
        boolean is_selected
        int extraction_order
        string custom_query
        string date_column
        string control_column
        string control_column_type
        string description
    }

    column_filters {
        int id PK
        int table_selection_id FK
        string column_name
        string operator
        string filter_value
        string filter_value2
        boolean is_active
    }

    computed_column_rules {
        int id PK
        int table_selection_id FK
        string new_column_name
        string source_column
        string condition_value
        string result_value
        string default_value
        int priority
        boolean is_active
    }

    mapeo_categorias {
        int id PK
        int company_id FK
        string nombre
        string descripcion
        boolean is_active
    }

    mapeo_subcategorias {
        int id PK
        int categoria_id FK
        string nombre
        string descripcion
        string tabla_origen
        string codigo_origen
        string clave_asiento
        json mapeo_cabecera
        string tabla_destino_detalle
        string tabla_destino_cabecera
        string col_destino_nasiento
        string col_destino_nidlin
        string schema_destino
        json pares_redondeo
        boolean generate_headers
        boolean generate_details
        int asiento_inicial
        string control_column_origen
        string last_generated_control_value
    }

    mapeo_lineas_asiento {
        int id PK
        int subcategoria_id FK
        int orden
        string nombre_linea
        json mapeo_detalle
        string condicion_aplicacion
        boolean aplica_ajuste_redondeo
        string nivel
        boolean is_active
    }

    companies ||--o{ table_selections : "registra"
    source_connections ||--o{ table_selections : "provee"
    table_selections ||--o{ column_filters : "filtra_por"
    table_selections ||--o{ computed_column_rules : "calcula_con"
    companies ||--o{ mapeo_categorias : "define"
    mapeo_categorias ||--o{ mapeo_subcategorias : "contiene"
    mapeo_subcategorias ||--o{ mapeo_lineas_asiento : "define_lineas"
```

---

## 3. Módulo de Asientos Contables y Staging (Destino Contasis)
Representa el proceso en el cual los datos procesados son convertidos a asientos contables en la estructura exacta requerida por la base de datos de Contasis.

```mermaid
erDiagram
    companies {
        int id PK
    }

    mapeo_subcategorias {
        int id PK
    }

    asientos_contables_generados {
        int id PK
        int company_id FK
        int subcategoria_id FK
        string cper
        string cmes
        string ccodori
        int nasiento
        int nidlin
        decimal ntc
        string ccodcue
        decimal ndebe
        decimal nhaber
        string cglosa
        decimal ndebes
        decimal nhabers
        string ccoddoc
        string cserie
        string cnumero
        string ffechadoc
        string ccodruc
        decimal ntot
        string estado
        string lote_id
        timestamp created_at
    }

    cf_diario {
        int id PK
        int company_id FK
        string lote_id
        string estado
        string cper
        string cmes
        string ccodori
        int nasiento
        decimal ntc
        string cglosa
        string ccoddoc
        string cserie
        string cnumero
        string ffechadoc
        string ccodruc
        decimal ntot
    }

    cf_diariol {
        int id PK
        int company_id FK
        int subcategoria_id FK
        string lote_id
        string estado
        string idcontrol
        string cper
        string cmes
        string ccodori
        int nasiento
        int nidlin
        string ccodcue
        decimal ndebe
        decimal nhaber
        string cglosa
        decimal ndebes
        decimal nhabers
        string ccoddoc
        string cserie
        string cnumero
        string ffechadoc
        string ccodruc
        decimal ntot
    }

    asiento_correlativos {
        int id PK
        int company_id FK
        int subcategoria_id FK
        string periodo
        string mes
        int asiento_inicial
        int asiento_actual
        timestamp updated_at
    }

    companies ||--o{ asientos_contables_generados : "contiene"
    mapeo_subcategorias ||--o{ asientos_contables_generados : "genera"
    companies ||--o{ cf_diario : "almacena_cabecera"
    companies ||--o{ cf_diariol : "almacena_linea"
    mapeo_subcategorias ||--o{ cf_diariol : "asocia_linea"
    companies ||--o{ asiento_correlativos : "controla"
    mapeo_subcategorias ||--o{ asiento_correlativos : "controla"
```

---

## 4. Módulo de Pipelines ETL, Automatizaciones y Logs
Gestiona la ejecución automática de los pipelines ETL utilizando Celery/Redis, el control incremental y el registro histórico/tiempo real de logs.

```mermaid
erDiagram
    companies {
        int id PK
    }

    mapeo_subcategorias {
        int id PK
    }

    etl_pipeline_config {
        int id PK
        int empresa_id FK
        int subcategoria_id FK
        string nombre
        boolean is_active
        string schedule_type
        string schedule_value
        boolean run_extraction
        boolean run_generation
        boolean run_migration
        json params
        int priority
        int max_retries
        timestamp last_run_at
        string last_status
    }

    etl_ejecuciones {
        int id PK
        int pipeline_id FK
        int empresa_id FK
        int subcategoria_id
        string celery_task_id
        string status
        int records_extracted
        int records_generated
        int records_migrated
        timestamp queued_at
        timestamp started_at
        timestamp finished_at
        decimal duration_s
        string error_message
    }

    migration_controls {
        int id PK
        int company_id FK
        string source_table
        string control_column
        string last_migrated_value
        bigint total_migrated
        timestamp last_run_at
        string last_run_status
        string last_run_message
    }

    etl_realtime_logs {
        int id PK
        int company_id FK
        timestamp run_date
        string status
        string message
        int records_extracted
        int records_generated
        int records_migrated
        string subcategorias
    }

    integ_logs {
        int id PK
        int company_id FK
        string process_name
        string status
        string message
        string details
        int records_processed
        timestamp created_at
    }

    companies ||--o{ etl_pipeline_config : "configura"
    mapeo_subcategorias ||--o{ etl_pipeline_config : "mapea_a"
    etl_pipeline_config ||--o{ etl_ejecuciones : "registra_ejecucion"
    companies ||--o{ etl_ejecuciones : "pertenece_a"
    companies ||--o{ migration_controls : "controla_migracion"
    companies ||--o{ etl_realtime_logs : "monitorea"
    companies ||--o{ integ_logs : "registra_integ"
```

---

## 5. Módulo de Catálogos Contables
Agrupa los catálogos del plan de cuentas, centros de costo, productos, tipos de cambio y catálogos personalizados definidos por el usuario.

```mermaid
erDiagram
    companies {
        int id PK
    }

    cat_cuentas_contables {
        int id PK
        int company_id FK
        string codigo
        string descripcion
        string tipo
        int nivel
        string moneda
        boolean is_active
    }

    cat_cuentas_presupuesto {
        int id PK
        int company_id FK
        string codigo
        string descripcion
        boolean is_active
    }

    cat_centros_costo {
        int id PK
        int company_id FK
        string codigo
        string descripcion
        boolean is_active
    }

    cat_tipo_analitica {
        int id PK
        int company_id FK
        string codigo
        string descripcion
        boolean is_active
    }

    cat_productos {
        int id PK
        int company_id FK
        string codigo
        string descripcion
        string unidad
        boolean is_active
    }

    cat_tipo_movimiento {
        int id PK
        int company_id FK
        string codigo
        string descripcion
        boolean is_active
    }

    user_catalogs {
        int id PK
        int company_id FK
        string name
        string description
        json columns
        timestamp created_at
    }

    user_catalog_items {
        int id PK
        int catalog_id FK
        json data
        timestamp created_at
    }

    companies ||--o{ cat_cuentas_contables : "tiene"
    companies ||--o{ cat_cuentas_presupuesto : "tiene"
    companies ||--o{ cat_centros_costo : "tiene"
    companies ||--o{ cat_tipo_analitica : "tiene"
    companies ||--o{ cat_productos : "tiene"
    companies ||--o{ cat_tipo_movimiento : "tiene"
    companies ||--o{ user_catalogs : "define"
    user_catalogs ||--o{ user_catalog_items : "contiene"
```
