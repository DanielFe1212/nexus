# Nexus — Sistema de Monitoreo de Disponibilidad de Red
**Grupo Carval** · Django 6 · SQL Server · Bootstrap 5

---

## Descripción

Nexus es una plataforma web interna para registrar, gestionar y analizar la **disponibilidad de los canales de internet** (Primario, Secundario y MPLS) de las sedes del Grupo Carval. Calcula KPIs de SLA en tiempo real, genera dashboards con gráficas dinámicas y exporta reportes a Excel compatibles con Power BI.

---

## Stack tecnológico

| Capa | Tecnología |
|------|-----------|
| Backend | Django 6.x (Python 3.12) |
| Base de datos | SQL Server (via `mssql-django` + `pyodbc`) |
| Frontend admin | Django Admin personalizado (CSS/JS propio) |
| Frontend dashboard | Bootstrap 5.3 + Chart.js 4.4 + SheetJS |
| Caché | LocMemCache (desarrollo) / Redis (producción) |
| Auditoría | Signals de Django + modelo `LogAccion` |

---

## Estructura del proyecto

```
nexus/
├── app/
│   ├── migrations/          # Migraciones de base de datos
│   ├── templates/
│   │   ├── admin/           # Templates del panel admin personalizados
│   │   └── dashboard.html   # Dashboard KPI principal
│   ├── admin.py             # Configuración del panel admin + auditoría
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
│   │   └── diseno_admin.css
│   ├── js/
│   │   ├── custom_admin.js
│   │   └── modulos/
│   │       ├── reloj.js
│   │       ├── boton_eliminar.js
│   │       └── filtros_toggle.js
│   └── images/
├── .env.example             # Plantilla de variables de entorno
├── .gitignore
├── manage.py
├── settings.py
├── urls.py
└── README.md
```

---

## Instalación local

### 1. Clonar el repositorio
```bash
git clone https://github.com/tu-usuario/nexus.git
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
```bash
cp .env.example .env
# Editar .env con tus credenciales reales
```

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

## Exportación a Power BI

Desde cada tabla del dashboard, el botón **"⬇ Exportar Excel"** genera un `.xlsx` directamente en el navegador (SheetJS, sin servidor). Luego en Power BI Desktop:

1. `Inicio → Obtener datos → Excel`
2. Seleccionar el archivo exportado
3. Seleccionar la hoja y cargar

Para automatización directa desde Power BI a la BD, usar el conector nativo de **SQL Server** apuntando al mismo servidor.

---

## Roles y permisos

- **Superusuario**: acceso total, ve todos los eventos y logs de auditoría
- **Usuario normal**: solo ve y gestiona los eventos que él mismo registró

---

## Buenas prácticas implementadas

- Patrón DRY en `BaseNexusAdmin` (CSS/JS centralizado)
- Queries optimizadas con `select_related` y filtrado en memoria (eliminado N+1)
- Auditoría completa: login, logout, CRUD de todos los modelos
- Modo oscuro del navegador bloqueado con `color-scheme: light only`
- Variables de entorno separadas del código (`.env`)
- Migraciones versionadas y nombradas descriptivamente

---

## Licencia

Uso interno — Grupo Carval. Todos los derechos reservados.
