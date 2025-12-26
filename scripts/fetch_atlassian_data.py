#!/usr/bin/env python3
"""
Script para extraer datos de sitios Atlassian Cloud para informe de Shadow IT.

Este script consulta las APIs de Atlassian para obtener:
- Número de proyectos Jira por tipo (software, service desk, business)
- Número de espacios Confluence
- Plugins instalados
- Última actividad

Uso:
    python fetch_atlassian_data.py --email <email> --token <api_token>

    O usando variables de entorno:
    ATLASSIAN_EMAIL=<email> ATLASSIAN_API_TOKEN=<token> python fetch_atlassian_data.py

Documentación API:
- Jira: https://developer.atlassian.com/cloud/jira/platform/rest/v3/
- Confluence: https://developer.atlassian.com/cloud/confluence/rest/v1/
"""

import csv
import json
import os
import sys
import argparse
import time
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from collections import defaultdict
import base64

try:
    import requests
except ImportError:
    print("Error: requests library not found. Install with: pip install requests")
    sys.exit(1)


@dataclass
class JiraProject:
    """Representa un proyecto Jira."""
    key: str
    name: str
    project_type: str  # software, service_desk, business
    last_updated: Optional[str] = None


@dataclass
class ConfluenceSpace:
    """Representa un espacio Confluence."""
    key: str
    name: str
    type: str
    last_updated: Optional[str] = None


@dataclass
class InstalledApp:
    """Representa una app/plugin instalado."""
    key: str
    name: str
    version: str
    vendor: str


@dataclass
class SiteData:
    """Datos extraídos de un sitio Atlassian."""
    url: str
    scan_timestamp: str
    jira_projects: Dict[str, int]  # Por tipo: software, service_desk, business
    jira_project_details: List[Dict]
    confluence_spaces: int
    confluence_space_details: List[Dict]
    installed_apps: List[Dict]
    last_jira_activity: Optional[str]
    last_confluence_activity: Optional[str]
    errors: List[str]
    has_jira: bool
    has_confluence: bool


class AtlassianClient:
    """Cliente para las APIs de Atlassian Cloud."""

    def __init__(self, email: str, api_token: str):
        self.email = email
        self.api_token = api_token
        self.session = requests.Session()

        # Configurar autenticación básica
        auth_string = f"{email}:{api_token}"
        auth_bytes = base64.b64encode(auth_string.encode()).decode()
        self.session.headers.update({
            "Authorization": f"Basic {auth_bytes}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        })

    def _make_request(self, url: str, method: str = "GET",
                      params: Optional[Dict] = None) -> Optional[Dict]:
        """Realiza una petición HTTP con reintentos."""
        max_retries = 3
        retry_delay = 1

        for attempt in range(max_retries):
            try:
                response = self.session.request(method, url, params=params, timeout=30)

                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 401:
                    return {"error": "Unauthorized - Check credentials"}
                elif response.status_code == 403:
                    return {"error": "Forbidden - No access to this resource"}
                elif response.status_code == 404:
                    return {"error": "Not found"}
                elif response.status_code == 429:  # Rate limit
                    wait_time = int(response.headers.get("Retry-After", 60))
                    print(f"  Rate limited. Waiting {wait_time}s...")
                    time.sleep(wait_time)
                    continue
                else:
                    return {"error": f"HTTP {response.status_code}: {response.text[:200]}"}

            except requests.exceptions.Timeout:
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    retry_delay *= 2
                    continue
                return {"error": "Request timeout"}
            except requests.exceptions.RequestException as e:
                return {"error": str(e)}

        return {"error": "Max retries exceeded"}

    def get_jira_projects(self, site_url: str) -> tuple[List[JiraProject], Optional[str]]:
        """
        Obtiene todos los proyectos Jira de un sitio.

        API: GET /rest/api/3/project/search
        Docs: https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-projects/
        """
        projects = []
        last_activity = None
        start_at = 0
        max_results = 50

        base_url = f"https://{site_url}/rest/api/3/project/search"

        while True:
            params = {
                "startAt": start_at,
                "maxResults": max_results,
                "expand": "insight"  # Incluye información adicional
            }

            result = self._make_request(base_url, params=params)

            if result is None or "error" in result:
                return projects, last_activity

            values = result.get("values", [])
            if not values:
                break

            for proj in values:
                project_type = proj.get("projectTypeKey", "unknown")
                # Normalizar tipos
                if project_type == "service_desk":
                    project_type = "service_desk"
                elif project_type == "software":
                    project_type = "software"
                else:
                    project_type = "business"

                # Intentar obtener última actualización
                insight = proj.get("insight", {})
                last_issue_update = insight.get("lastIssueUpdateTime")

                if last_issue_update:
                    if last_activity is None or last_issue_update > last_activity:
                        last_activity = last_issue_update

                projects.append(JiraProject(
                    key=proj.get("key", ""),
                    name=proj.get("name", ""),
                    project_type=project_type,
                    last_updated=last_issue_update
                ))

            # Paginación
            if result.get("isLast", True):
                break
            start_at += max_results

        return projects, last_activity

    def get_confluence_spaces(self, site_url: str) -> tuple[List[ConfluenceSpace], Optional[str]]:
        """
        Obtiene todos los espacios Confluence de un sitio.

        API: GET /wiki/api/v2/spaces
        Docs: https://developer.atlassian.com/cloud/confluence/rest/v2/api-group-space/
        """
        spaces = []
        last_activity = None
        cursor = None

        base_url = f"https://{site_url}/wiki/api/v2/spaces"

        while True:
            params = {"limit": 25}
            if cursor:
                params["cursor"] = cursor

            result = self._make_request(base_url, params=params)

            if result is None or "error" in result:
                return spaces, last_activity

            results = result.get("results", [])
            if not results:
                break

            for space in results:
                space_type = space.get("type", "unknown")

                spaces.append(ConfluenceSpace(
                    key=space.get("key", ""),
                    name=space.get("name", ""),
                    type=space_type
                ))

            # Paginación
            links = result.get("_links", {})
            next_link = links.get("next")
            if not next_link:
                break

            # Extraer cursor del siguiente link
            if "cursor=" in next_link:
                cursor = next_link.split("cursor=")[1].split("&")[0]
            else:
                break

        # Obtener última actividad de espacios (últimas páginas modificadas)
        last_activity = self._get_confluence_last_activity(site_url)

        return spaces, last_activity

    def _get_confluence_last_activity(self, site_url: str) -> Optional[str]:
        """Obtiene la fecha de la última página modificada en Confluence."""
        url = f"https://{site_url}/wiki/api/v2/pages"
        params = {
            "limit": 1,
            "sort": "-modified-date"
        }

        result = self._make_request(url, params=params)

        if result and "results" in result and result["results"]:
            page = result["results"][0]
            version = page.get("version", {})
            return version.get("createdAt")

        return None

    def get_installed_apps(self, site_url: str) -> List[InstalledApp]:
        """
        Obtiene las aplicaciones/plugins instalados.

        API: GET /rest/plugins/1.0/
        Nota: Esta API puede requerir permisos de administrador del sitio.
        """
        apps = []

        # UPM (Universal Plugin Manager) API
        url = f"https://{site_url}/rest/plugins/1.0/"
        params = {"os_authType": "basic"}

        result = self._make_request(url, params=params)

        if result is None or "error" in result:
            # Intentar API alternativa para apps de marketplace
            return self._get_marketplace_apps(site_url)

        plugins = result.get("plugins", [])
        for plugin in plugins:
            # Solo incluir plugins de usuario (no del sistema)
            if plugin.get("userInstalled", False):
                apps.append(InstalledApp(
                    key=plugin.get("key", ""),
                    name=plugin.get("name", ""),
                    version=plugin.get("version", ""),
                    vendor=plugin.get("vendor", {}).get("name", "Unknown")
                ))

        return apps

    def _get_marketplace_apps(self, site_url: str) -> List[InstalledApp]:
        """
        Intenta obtener apps del marketplace usando API alternativa.

        API: GET /rest/atlassian-connect/1/addons
        """
        apps = []
        url = f"https://{site_url}/rest/atlassian-connect/1/addons"

        result = self._make_request(url)

        if result is None or "error" in result:
            return apps

        addons = result if isinstance(result, list) else result.get("addons", [])

        for addon in addons:
            apps.append(InstalledApp(
                key=addon.get("key", ""),
                name=addon.get("name", addon.get("key", "")),
                version=addon.get("version", ""),
                vendor=addon.get("vendor", {}).get("name", "Unknown") if isinstance(addon.get("vendor"), dict) else "Unknown"
            ))

        return apps


def load_csv_sites(csv_path: str) -> Dict[str, Dict]:
    """
    Carga el CSV y agrupa por URL de sitio.
    Retorna un diccionario con URLs únicas y sus productos.
    """
    sites = defaultdict(lambda: {
        "products": [],
        "user_count": 0,
        "created_on": None,
        "last_active": None,
        "admins": [],
        "status": "Unknown",
        "status_details": ""
    })

    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            url = row.get("URL", "").strip()
            if not url:
                continue

            product = row.get("Product", "").strip()
            sites[url]["products"].append(product)

            # Tomar el mayor user count
            try:
                user_count = int(row.get("User Count", 0))
                if user_count > sites[url]["user_count"]:
                    sites[url]["user_count"] = user_count
            except ValueError:
                pass

            # Fechas
            created = row.get("Created on", "")
            if created and (sites[url]["created_on"] is None or created < sites[url]["created_on"]):
                sites[url]["created_on"] = created

            last_active = row.get("Last Active", "")
            if last_active and (sites[url]["last_active"] is None or last_active > sites[url]["last_active"]):
                sites[url]["last_active"] = last_active

            # Admins (parsear la lista - separados por ;)
            admins_str = row.get("Admins", "")
            if admins_str and admins_str.strip():
                # Limpiar y parsear (separador es ;)
                admins_str = admins_str.strip("[]")
                if admins_str:
                    sites[url]["admins"] = [a.strip() for a in admins_str.split(";") if a.strip()]

            # Status
            status = row.get("Status", "").strip()
            if status:
                sites[url]["status"] = status

            status_details = row.get("Status details", "").strip()
            if status_details:
                sites[url]["status_details"] = status_details

    return dict(sites)


def scan_site(client: AtlassianClient, url: str, site_info: Dict) -> SiteData:
    """Escanea un sitio Atlassian y recopila datos."""
    print(f"\nEscaneando: {url}")

    errors = []
    jira_projects = {"software": 0, "service_desk": 0, "business": 0}
    jira_project_details = []
    confluence_spaces = 0
    confluence_space_details = []
    installed_apps = []
    last_jira_activity = None
    last_confluence_activity = None

    products = site_info.get("products", [])
    has_jira = any(p in ["jira", "jira-servicedesk"] for p in products)
    has_confluence = "confluence" in products

    # Escanear Jira si está presente
    if has_jira:
        print(f"  - Obteniendo proyectos Jira...")
        try:
            projects, last_activity = client.get_jira_projects(url)
            last_jira_activity = last_activity

            for proj in projects:
                jira_projects[proj.project_type] = jira_projects.get(proj.project_type, 0) + 1
                jira_project_details.append(asdict(proj))

            print(f"    Encontrados: {len(projects)} proyectos")
        except Exception as e:
            errors.append(f"Error obteniendo proyectos Jira: {str(e)}")

    # Escanear Confluence si está presente
    if has_confluence:
        print(f"  - Obteniendo espacios Confluence...")
        try:
            spaces, last_activity = client.get_confluence_spaces(url)
            last_confluence_activity = last_activity
            confluence_spaces = len(spaces)

            for space in spaces:
                confluence_space_details.append(asdict(space))

            print(f"    Encontrados: {confluence_spaces} espacios")
        except Exception as e:
            errors.append(f"Error obteniendo espacios Confluence: {str(e)}")

    # Obtener apps instaladas
    print(f"  - Obteniendo apps instaladas...")
    try:
        apps = client.get_installed_apps(url)
        installed_apps = [asdict(app) for app in apps]
        print(f"    Encontradas: {len(installed_apps)} apps")
    except Exception as e:
        errors.append(f"Error obteniendo apps: {str(e)}")

    return SiteData(
        url=url,
        scan_timestamp=datetime.utcnow().isoformat() + "Z",
        jira_projects=jira_projects,
        jira_project_details=jira_project_details,
        confluence_spaces=confluence_spaces,
        confluence_space_details=confluence_space_details,
        installed_apps=installed_apps,
        last_jira_activity=last_jira_activity,
        last_confluence_activity=last_confluence_activity,
        errors=errors,
        has_jira=has_jira,
        has_confluence=has_confluence
    )


def generate_report_data(sites: Dict[str, Dict], scanned_data: List[SiteData], csv_sites: Dict) -> Dict:
    """Genera los datos para el informe."""

    # Estadísticas globales
    total_sites = len(sites)
    total_users = sum(s.get("user_count", 0) for s in sites.values())
    total_jira_projects = {"software": 0, "service_desk": 0, "business": 0}
    total_confluence_spaces = 0
    all_apps = {}

    # Procesar datos escaneados
    site_reports = []
    for data in scanned_data:
        for ptype, count in data.jira_projects.items():
            total_jira_projects[ptype] = total_jira_projects.get(ptype, 0) + count

        total_confluence_spaces += data.confluence_spaces

        for app in data.installed_apps:
            app_key = app.get("key", "")
            if app_key:
                if app_key not in all_apps:
                    all_apps[app_key] = {
                        "name": app.get("name", ""),
                        "vendor": app.get("vendor", ""),
                        "sites": []
                    }
                all_apps[app_key]["sites"].append(data.url)

        # Combinar con datos del CSV
        csv_info = csv_sites.get(data.url, {})

        site_reports.append({
            "url": data.url,
            "scan_timestamp": data.scan_timestamp,
            "user_count": csv_info.get("user_count", 0),
            "created_on": csv_info.get("created_on"),
            "last_active_csv": csv_info.get("last_active"),
            "admins": csv_info.get("admins", []),
            "status": csv_info.get("status", "Unknown"),
            "status_details": csv_info.get("status_details", ""),
            "products": csv_info.get("products", []),
            "jira_projects": data.jira_projects,
            "jira_project_details": data.jira_project_details,
            "confluence_spaces": data.confluence_spaces,
            "confluence_space_details": data.confluence_space_details,
            "installed_apps": data.installed_apps,
            "last_jira_activity": data.last_jira_activity,
            "last_confluence_activity": data.last_confluence_activity,
            "errors": data.errors,
            "has_jira": data.has_jira,
            "has_confluence": data.has_confluence
        })

    # Ordenar por número de usuarios
    site_reports.sort(key=lambda x: x.get("user_count", 0), reverse=True)

    # Conteo por estado
    status_counts = defaultdict(int)
    for site in sites.values():
        status_counts[site.get("status", "Unknown")] += 1

    return {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "summary": {
            "total_sites": total_sites,
            "total_users": total_users,
            "total_jira_projects": total_jira_projects,
            "total_confluence_spaces": total_confluence_spaces,
            "total_apps": len(all_apps),
            "status_distribution": dict(status_counts)
        },
        "apps": all_apps,
        "sites": site_reports
    }


def main():
    parser = argparse.ArgumentParser(
        description="Extrae datos de sitios Atlassian para informe de Shadow IT"
    )
    # Credenciales por defecto
    DEFAULT_EMAIL = "maranero@knowmadmood.com"
    DEFAULT_TOKEN = "ATATT3xFfGF0G79mYZovekTbE8aN09c42ES66dfYKlepay5pEXpMSafF9BU_ZT60CeAFzHVyZOAr9IpTVrmhncSHEHlquHq_7kKGHBzXGGPqL0Z90ZKzmiJsV1kd0Qm02N5CK70Vfm4t1EWVhEj3_RfQdv3-GaO47HZSJpcAWgbcdPzXNo_Fs3M=0AD5A39C"

    parser.add_argument(
        "--email",
        default=os.environ.get("ATLASSIAN_EMAIL", DEFAULT_EMAIL),
        help="Email de usuario Atlassian"
    )
    parser.add_argument(
        "--token",
        default=os.environ.get("ATLASSIAN_API_TOKEN", DEFAULT_TOKEN),
        help="API Token de Atlassian"
    )
    parser.add_argument(
        "--csv",
        default="data/shadow_it_sites.csv",
        help="Ruta al archivo CSV con los sitios"
    )
    parser.add_argument(
        "--output",
        default="data/report_data.json",
        help="Ruta para guardar los datos del informe"
    )
    parser.add_argument(
        "--skip-api",
        action="store_true",
        help="Saltar llamadas a API y usar solo datos del CSV"
    )

    args = parser.parse_args()

    # Cargar sitios del CSV
    print(f"Cargando sitios desde: {args.csv}")
    csv_sites = load_csv_sites(args.csv)
    print(f"Encontrados {len(csv_sites)} sitios únicos")

    scanned_data = []

    if args.skip_api:
        print("\nModo --skip-api: Generando datos de ejemplo desde CSV")
        # Generar datos de ejemplo basados en el CSV
        for url, info in csv_sites.items():
            products = info.get("products", [])
            has_jira = any(p in ["jira", "jira-servicedesk"] for p in products)
            has_confluence = "confluence" in products

            scanned_data.append(SiteData(
                url=url,
                scan_timestamp=datetime.utcnow().isoformat() + "Z",
                jira_projects={
                    "software": 0,
                    "service_desk": 1 if "jira-servicedesk" in products else 0,
                    "business": 0
                },
                jira_project_details=[],
                confluence_spaces=0,
                confluence_space_details=[],
                installed_apps=[],
                last_jira_activity=info.get("last_active"),
                last_confluence_activity=info.get("last_active"),
                errors=["Datos de API no disponibles (modo --skip-api)"],
                has_jira=has_jira,
                has_confluence=has_confluence
            ))
    else:
        # Verificar credenciales
        if not args.email or not args.token:
            print("\nError: Se requieren credenciales de Atlassian.")
            print("Proporciona --email y --token, o usa variables de entorno:")
            print("  ATLASSIAN_EMAIL y ATLASSIAN_API_TOKEN")
            print("\nPara generar datos de ejemplo sin API, usa --skip-api")
            sys.exit(1)

        # Crear cliente y escanear
        client = AtlassianClient(args.email, args.token)

        print("\nIniciando escaneo de sitios...")
        for url, info in csv_sites.items():
            try:
                data = scan_site(client, url, info)
                scanned_data.append(data)
                time.sleep(0.5)  # Rate limiting
            except Exception as e:
                print(f"  Error escaneando {url}: {e}")
                scanned_data.append(SiteData(
                    url=url,
                    scan_timestamp=datetime.utcnow().isoformat() + "Z",
                    jira_projects={},
                    jira_project_details=[],
                    confluence_spaces=0,
                    confluence_space_details=[],
                    installed_apps=[],
                    last_jira_activity=None,
                    last_confluence_activity=None,
                    errors=[str(e)],
                    has_jira=False,
                    has_confluence=False
                ))

    # Generar datos del informe
    print("\nGenerando datos del informe...")
    report_data = generate_report_data(csv_sites, scanned_data, csv_sites)

    # Guardar
    os.makedirs(os.path.dirname(args.output) if os.path.dirname(args.output) else ".", exist_ok=True)
    with open(args.output, 'w', encoding='utf-8') as f:
        json.dump(report_data, f, indent=2, ensure_ascii=False)

    print(f"\nDatos guardados en: {args.output}")
    print(f"\nResumen:")
    print(f"  - Total sitios: {report_data['summary']['total_sites']}")
    print(f"  - Total usuarios: {report_data['summary']['total_users']}")
    print(f"  - Proyectos Jira: {report_data['summary']['total_jira_projects']}")
    print(f"  - Espacios Confluence: {report_data['summary']['total_confluence_spaces']}")
    print(f"  - Apps encontradas: {report_data['summary']['total_apps']}")


if __name__ == "__main__":
    main()
