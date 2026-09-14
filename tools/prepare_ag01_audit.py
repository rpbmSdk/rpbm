"""Acquiert le snapshot de métadonnées nécessaire à l'audit AG-01.

Le profil Odoo est résolu par ``.paradigme.yaml`` puis par les fichiers globaux
Paradigme. Le script n'appelle que des opérations MCP de lecture et n'exporte
aucun enregistrement métier.
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
STOCK_TOOLS = ROOT / "Jobs" / "rpbm_agent_stock"
import sys

sys.path.insert(0, str(STOCK_TOOLS))
from common import PROFILES_PATH, _parse_simple_yaml, load_env, load_profile  # noqa: E402


PROFILE = load_profile()
assert PROFILE["profile"] == "rpbm-preprod", (
    "AG-01 doit rester rattaché au profil explicitement sélectionné par le projet"
)
ENV = load_env()
GLOBAL_CONFIG = _parse_simple_yaml(PROFILES_PATH.read_text(encoding="utf-8"))
ENDPOINT = GLOBAL_CONFIG.get("mcp_server_url", "https://mcp.odoo.paradigme.io/mcp")
RUN_ID = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H-%M-%SZ")
SNAPSHOT = ROOT / ".paradigme" / "audits" / PROFILE["profile"] / "data" / f"ag01-{RUN_ID[:10]}"

TARGET_MODELS = [
    "crm.lead",
    "sale.order",
    "sale.order.line",
    "fleet.vehicle",
    "delivery.carrier",
    "stock.picking",
    "stock.picking.type",
    "stock.move",
    "stock.rule",
    "stock.route",
    "stock.warehouse",
    "product.template",
    "product.product",
    "res.partner",
]

FAMILY_SPECS: dict[str, tuple[str, list[list[Any]], list[str]]] = {
    "models/ir.model.json": (
        "ir.model",
        [["model", "in", TARGET_MODELS]],
        ["id", "name", "model", "info", "state", "transient", "modules", "create_date", "write_date"],
    ),
    "fields/ir.model.fields.json": (
        "ir.model.fields",
        [["model", "in", TARGET_MODELS]],
        [
            "id", "name", "field_description", "model", "model_id", "state", "ttype",
            "relation", "relation_field", "related", "store", "readonly", "required",
            "compute", "depends", "groups", "domain", "selection", "on_delete", "copied",
            "index", "modules", "create_date", "write_date", "create_uid", "write_uid",
        ],
    ),
    "views/ir.ui.view.json": (
        "ir.ui.view",
        ["|", ["model", "in", TARGET_MODELS], ["type", "=", "qweb"]],
        [
            "id", "name", "model", "type", "inherit_id", "priority", "active", "mode", "key",
            "arch_db", "create_date", "write_date", "create_uid", "write_uid",
        ],
    ),
    "navigation/ir.actions.report.json": (
        "ir.actions.report",
        [["model", "in", ["crm.lead", "sale.order", "fleet.vehicle"]]],
        [
            "id", "name", "model", "report_name", "report_file", "binding_model_id", "binding_type",
            "paperformat_id", "active", "create_date", "write_date", "create_uid", "write_uid",
        ],
    ),
    "navigation/ir.actions.act_window.json": (
        "ir.actions.act_window",
        [["res_model", "in", TARGET_MODELS]],
        [
            "id", "name", "res_model", "view_mode", "view_id", "view_ids", "domain", "context",
            "target", "limit", "groups_id", "active", "create_date", "write_date", "create_uid", "write_uid",
        ],
    ),
    "navigation/ir.ui.menu.json": (
        "ir.ui.menu",
        [],
        ["id", "name", "parent_id", "action", "sequence", "active", "groups_id", "create_date", "write_date"],
    ),
    "automations/base.automation.json": (
        "base.automation",
        [],
        [
            "id", "name", "active", "model_id", "trigger", "trigger_field_ids", "filter_domain",
            "state", "code", "action_server_ids", "create_date", "write_date", "create_uid", "write_uid",
        ],
    ),
    "automations/ir.actions.server.json": (
        "ir.actions.server",
        [],
        [
            "id", "name", "model_id", "state", "code", "crud_model_id", "link_field_id",
            "fields_lines", "activity_type_id", "activity_summary", "template_id", "create_date",
            "write_date", "create_uid", "write_uid",
        ],
    ),
    "security/ir.model.access.json": (
        "ir.model.access",
        [["model_id.model", "in", TARGET_MODELS]],
        ["id", "name", "model_id", "group_id", "perm_read", "perm_write", "perm_create", "perm_unlink", "active", "create_date", "write_date"],
    ),
    "security/ir.rule.json": (
        "ir.rule",
        [["model_id.model", "in", TARGET_MODELS]],
        ["id", "name", "model_id", "domain_force", "groups", "perm_read", "perm_write", "perm_create", "perm_unlink", "active", "create_date", "write_date"],
    ),
    "models/ir.model.data.json": (
        "ir.model.data",
        [["module", "=", "studio_customization"], ["model", "in", ["ir.model.fields", "ir.ui.view", "ir.actions.report", "ir.actions.act_window"]]],
        ["id", "module", "name", "model", "res_id", "noupdate", "studio", "complete_name", "create_date", "write_date"],
    ),
}


def mcp_call(tool_name: str, arguments: dict[str, Any]) -> Any:
    connection = {key: value for key, value in PROFILE.items() if key != "profile"}
    connection.update(arguments)
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {"name": tool_name, "arguments": connection},
    }
    headers = {"Content-Type": "application/json", "Accept": "application/json, text/event-stream"}
    api_key = ENV.get("PARADIGME_MCP_API_KEY")
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    request = urllib.request.Request(
        ENDPOINT,
        data=json.dumps(payload).encode("utf-8"),
        headers=headers,
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            raw = response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f"MCP HTTP {exc.code}: réponse non conservée") from exc
    if raw.startswith("event:") or raw.startswith("data:"):
        data_lines = [line[5:].strip() for line in raw.splitlines() if line.startswith("data:")]
        raw = data_lines[-1] if data_lines else raw
    envelope = json.loads(raw)
    if envelope.get("error"):
        raise RuntimeError(f"MCP {tool_name}: {envelope['error']}")
    result = envelope.get("result", envelope)
    if result.get("isError"):
        raise RuntimeError(f"MCP {tool_name}: réponse en erreur")
    for content in result.get("content", []):
        if content.get("type") == "text":
            try:
                return json.loads(content["text"])
            except (KeyError, TypeError, ValueError):
                return content["text"]
    return result.get("structuredContent", result)


def field_capabilities(model: str) -> dict[str, Any]:
    result = mcp_call(
        "get_model_fields",
        {
            "model": model,
            "attributes": [
                "string", "type", "relation", "readonly", "required", "store", "related",
                "depends", "compute", "selection", "domain",
            ],
        },
    )
    if isinstance(result, dict) and isinstance(result.get("fields"), list):
        return {
            item["name"]: {
                **{key: value for key, value in item.items() if key != "name"},
                **(item.get("attributes") or {}),
            }
            for item in result["fields"]
            if isinstance(item, dict) and item.get("name")
        }
    if isinstance(result, dict) and isinstance(result.get("fields"), dict):
        return result["fields"]
    if isinstance(result, dict) and all(isinstance(value, dict) for value in result.values()):
        return result
    raise RuntimeError(f"fields_get inexploitable pour {model}")


def normalize_records(result: Any) -> list[dict[str, Any]]:
    if isinstance(result, dict):
        for key in ("records", "result", "data"):
            if key in result:
                return normalize_records(result[key])
        return []
    if not isinstance(result, list):
        return []
    records: list[dict[str, Any]] = []
    for item in result:
        if not isinstance(item, dict):
            continue
        values = item.get("values", item)
        if not isinstance(values, dict):
            continue
        record_id = item.get("id", values.get("id"))
        records.append({"id": record_id, "values": values})
    return records


def read_all(model: str, domain: list[list[Any]] | list[Any], requested_fields: list[str]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    capabilities = field_capabilities(model)
    available = set(capabilities)
    fields = [name for name in requested_fields if name in available]
    if "id" in available and "id" not in fields:
        fields.insert(0, "id")
    page_size = 200
    offset = 0
    pages = 0
    records: dict[Any, dict[str, Any]] = {}
    while True:
        result = mcp_call(
            "model_search_read",
            {
                "model": model,
                "domain": domain,
                "fields": fields,
                "limit": page_size,
                "offset": offset,
                "order": "id asc",
            },
        )
        page = normalize_records(result)
        pages += 1
        for record in page:
            records[record["id"]] = record
        if len(page) < page_size:
            break
        offset += page_size
    return list(records.values()), {
        "odoo_model": model,
        "domain": domain,
        "fields": fields,
        "field_capabilities": capabilities,
        "page_size": page_size,
        "pages": pages,
        "record_count": len(records),
        "extracted_at": datetime.now(timezone.utc).isoformat(),
    }


def write_json(relative_path: str, obj: Any) -> None:
    path = SNAPSHOT / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> None:
    started = datetime.now(timezone.utc)
    write_json(
        "acquisition.json",
        {
            "schema_version": 1,
            "audit": "AG-01",
            "profile": PROFILE["profile"],
            "transport": PROFILE["transport"],
            "started_at": started.isoformat(),
            "status": "running",
            "scope": {"models": TARGET_MODELS, "business_records": False},
        },
    )
    manifest: dict[str, Any] = {"schema_version": 1, "audit": "AG-01", "profile": PROFILE["profile"], "files": {}}
    for relative_path, (model, domain, fields) in FAMILY_SPECS.items():
        records, source = read_all(model, domain, fields)
        write_json(relative_path, {"schema_version": 1, "family": relative_path.split("/", 1)[0], "source": source, "records": records})
        manifest["files"][relative_path] = {"model": model, "record_count": len(records), "extracted_at": source["extracted_at"]}
        print(f"{relative_path}: {len(records)}")

    field_records = json.loads((SNAPSHOT / "fields" / "ir.model.fields.json").read_text(encoding="utf-8"))["records"]
    field_ids = [record["id"] for record in field_records if record.get("id")]
    selections, selection_source = read_all(
        "ir.model.fields.selection",
        [["field_id", "in", field_ids]],
        ["id", "field_id", "value", "name", "sequence", "create_date", "write_date"],
    )
    write_json("fields/ir.model.fields.selection.json", {"schema_version": 1, "family": "fields", "source": selection_source, "records": selections})
    manifest["files"]["fields/ir.model.fields.selection.json"] = {"model": "ir.model.fields.selection", "record_count": len(selections), "extracted_at": selection_source["extracted_at"]}

    completed = datetime.now(timezone.utc)
    manifest.update({"started_at": started.isoformat(), "completed_at": completed.isoformat(), "status": "complete"})
    write_json("manifest.json", manifest)
    write_json(
        "acquisition.json",
        {
            "schema_version": 1,
            "audit": "AG-01",
            "profile": PROFILE["profile"],
            "transport": PROFILE["transport"],
            "started_at": started.isoformat(),
            "completed_at": completed.isoformat(),
            "status": "complete",
            "scope": {"models": TARGET_MODELS, "business_records": False},
            "manifest": "manifest.json",
        },
    )
    print(f"Snapshot AG-01 terminé: {SNAPSHOT}")


if __name__ == "__main__":
    main()
