# Nexus — Sistema de Monitoreo de Disponibilidad de Red
**Grupo Carval** · Django 6 · SQL Server · Bootstrap 5

---

## Descripción

Nexus es una plataforma web interna para registrar, gestionar y analizar la **disponibilidad de los canales de comunicación** (Primario, Secundario y MPLS) de las sedes del Grupo Carval. Calcula KPIs de SLA, genera dashboards con gráficas dinámicas y exporta reportes a Excel compatibles con Power BI.

---

## Stack tecnológico

| Capa | Tecnología |
|------|-----------|
| Backend | Django 6.x (Python 3.12) |
| Base de datos | SQL Server (vía `mssql-django` + `pyodbc`) |
| Frontend admin | Django Admin personalizado (CSS/JS propio) |
| Frontend dashboard | Bootstrap 5.3 + Chart.js 3.9 + SheetJS + Flatpickr |
| Caché | LocMemCache (desarrollo) / Redis (producción) |
| Configuración | Variables de entorno con `python-dotenv` |
| Auditoría | Signals de Django + modelo `LogAccion` |

---

## Estructura del proyecto

```
nexus/
├── app/
│   ├── migrations/          # Migraciones de base de datos
│   ├── templates/
│   │   ├── admin/           # Templates del panel admin personalizados
│   │   │   ├── base_site.html
│   │   │   ├── change_list.html
│   │   │   └── login.html   # Login con caja blanca + ver contraseña
│   │   └── dashboard.html   # Dashboard KPI principal
│   ├── admin.py             # Configuración del panel admin + roles + auditoría
│   ├── apps.py              # Conecta signals al arrancar
│   ├── models.py            # Modelos de datos (Evento, Sede, LogAccion...)
│   ├── signals.py           # Auditoría de login/logout
│   ├── utils.py             # Utilidades auxiliares
│   └── views.py             # Lógica del dashboard KPI (optimizado N+1)
├── static/
│   ├── css/                 # CSS modular del admin
│   │   ├── base_admin.css
│   │   ├── layout_admin.css
│   │   ├── navigation_admin.css
│   │   ├── components_admin.css
│   │   ├── overrides_admin.css
│   │   └── diseno_admin.css  # Estilos del login
│   ├── js/
│   │   └── modulos/
│   │       ├── reloj.js              # Selectores de fecha/hora (Flatpickr)
│   │       ├── boton_eliminar.js
│   │       ├── filtros_toggle.js     # Mostrar/ocultar filtros + expandir tabla
│   │       └── evento_proveedores.js # Filtra proveedores según la sede
│   └── images/
├── .env                     # Variables sensibles (NO se sube a Git)
├── .env.example             # Plantilla de variables de entorno
├── .gitignore
├── manage.py
├── requirements.txt
├── settings.py
├── urls.py
└── README.md
```

---

## Instalación local

### 1. Clonar el repositorio
```bash
git clone https://github.com/DanielFe1212/nexus.git
cd nexus
```

### 2. Crear entorno virtual
```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# Linux/Mac
source .venv/bin/activate
```

### 3. Instalar dependencias
```bash
pip install -r requirements.txt
```

### 4. Configurar variables de entorno
Copia la plantilla y completa tus credenciales reales:
```bash
# Windows
copy .env.example .env
# Linux/Mac
cp .env.example .env
```

Edita `.env` con los valores de tu entorno:

| Variable | Descripción | Ejemplo |
|----------|-------------|---------|
| `SECRET_KEY` | Clave secreta de Django | (generar, ver abajo) |
| `DEBUG` | Modo depuración | `True` (dev) / `False` (prod) |
| `ALLOWED_HOSTS` | Hosts permitidos (separados por coma) | `127.0.0.1,localhost` |
| `DB_NAME` | Nombre de la base de datos | `nexus_db` |
| `DB_USER` | Usuario de SQL Server | `daniel` |
| `DB_PASSWORD` | Contraseña de SQL Server | `********` |
| `DB_HOST` | Servidor de base de datos | `DANIEL` |
| `DB_PORT` | Puerto (vacío = por defecto) | |
| `DB_DRIVER` | Driver ODBC | `ODBC Driver 18 for SQL Server` |
| `DB_EXTRA_PARAMS` | Parámetros extra de conexión | `TrustServerCertificate=yes;Encrypt=yes;` |

Para generar una nueva `SECRET_KEY`:
```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

> **Importante:** el archivo `.env` contiene datos sensibles y está incluido en `.gitignore`. Nunca debe subirse al repositorio. Comparte únicamente `.env.example`.

### 5. Aplicar migraciones
```bash
python manage.py migrate
```

### 6. Crear superusuario
```bash
python manage.py createsuperuser
```

### 7. Colectar estáticos
```bash
python manage.py collectstatic
```

### 8. Correr servidor de desarrollo
```bash
python manage.py runserver
```

Acceder en: `http://127.0.0.1:8000/admin/`

---

## Modelos principales

| Modelo | Descripción |
|--------|-------------|
| `Empresa` | Empresa cliente del grupo |
| `Proveedor` | Proveedor de internet/MPLS |
| `Sede` | Sede de una empresa con sus canales asignados |
| `TipoFalla` | Catálogo de causas de caída |
| `Evento` | Registro de incidente (caída de canal) |
| `ConfiguracionGlobal` | Meta de SLA y minutos por día |
| `LogAccion` | Auditoría de acciones de usuarios |

---

## Roles y permisos

El sistema gestiona el acceso mediante **dos grupos de Django**:

- **Administrador**: acceso total. Crea, edita y elimina en todos los módulos; gestiona usuarios y roles; configura parámetros globales; consulta la auditoría (Logs de Acciones).
- **Operador**: registra eventos y ve todos los del sistema, pero solo edita/elimina los que él mismo creó. Consulta (sin modificar) los catálogos. No accede a usuarios ni a la auditoría.

> Para asignar un rol: en `/admin/auth/user/`, marca **Es staff**, agrega el usuario al grupo correspondiente (**Administrador** u **Operador**) y **no** marques *Es superusuario* salvo para acceso técnico total.

---

## Exportación a Power BI

Desde cada tabla del dashboard, el botón **"Exportar Excel"** genera un `.xlsx` directamente en el navegador (SheetJS, sin servidor). Luego en Power BI Desktop:

1. `Inicio → Obtener datos → Excel`
2. Seleccionar el archivo exportado
3. Seleccionar la hoja y cargar

Para automatización directa desde Power BI a la BD, usar el conector nativo de **SQL Server** apuntando al mismo servidor.

---

## Buenas prácticas implementadas

- Variables sensibles separadas del código en `.env` (cargado con `python-dotenv`)
- Patrón DRY en `BaseNexusAdmin` (CSS/JS centralizado)
- Sistema de roles por grupos con permisos a nivel de objeto (cada operador gestiona solo sus eventos)
- Queries optimizadas con `select_related` y filtrado en memoria (eliminado N+1)
- Caché del dashboard con invalidación automática y botón de actualización manual
- Auditoría completa: login, logout, CRUD de todos los modelos
- Modo oscuro del navegador bloqueado con `color-scheme: light only`
- Migraciones versionadas y nombradas descriptivamente

---

## Licencia

Uso interno — Grupo Carval. Todos los derechos reservados.
