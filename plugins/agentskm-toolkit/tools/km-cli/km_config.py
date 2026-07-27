#!/usr/bin/env python3
"""AgentsKM user configuration and runtime profile resolution."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any


ROLES = {"contributor", "reviewer", "compiler"}
DEFAULT_CONFIG = Path.home() / ".agentskm" / "config.json"


@dataclass(frozen=True)
class RuntimeContext:
    config_path: Path
    profile_name: str
    actor_id: str
    host: str
    role: str
    vault_name: str
    vault_path: Path

    def as_dict(self) -> dict[str, object]:
        return {
            "config_path": str(self.config_path),
            "profile": self.profile_name,
            "actor_id": self.actor_id,
            "host": self.host,
            "role": self.role,
            "vault_name": self.vault_name,
            "vault_path": str(self.vault_path),
        }


def get_config_path() -> Path:
    configured = os.environ.get("AGENTSKM_CONFIG")
    return Path(configured or DEFAULT_CONFIG).expanduser().resolve()


def requested_profile(explicit: str | None = None) -> str:
    return (explicit or os.environ.get("AGENTSKM_PROFILE") or "").strip()


def read_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise RuntimeError(f"Cannot read AgentsKM config: {path}: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Invalid AgentsKM config JSON: {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise RuntimeError(f"AgentsKM config must contain a JSON object: {path}")
    return payload


def validate_config(config: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if config.get("schema_version") != 1:
        errors.append("schema_version must be 1")

    vaults = config.get("vaults")
    if not isinstance(vaults, dict) or not vaults:
        errors.append("vaults must be a non-empty object")
        vaults = {}
    for name, item in vaults.items():
        if not isinstance(name, str) or not name.strip():
            errors.append("vault names must be non-empty strings")
            continue
        if not isinstance(item, dict):
            errors.append(f"vaults.{name} must be an object")
            continue
        raw_path = item.get("path")
        if not isinstance(raw_path, str) or not raw_path.strip():
            errors.append(f"vaults.{name}.path must be a non-empty string")
        elif not Path(raw_path).expanduser().is_absolute():
            errors.append(f"vaults.{name}.path must be an absolute path")
        create_if_missing = item.get("create_if_missing", False)
        if not isinstance(create_if_missing, bool):
            errors.append(f"vaults.{name}.create_if_missing must be a boolean")

    profiles = config.get("profiles")
    if not isinstance(profiles, dict) or not profiles:
        errors.append("profiles must be a non-empty object")
        profiles = {}
    actor_ids: dict[str, str] = {}
    for name, item in profiles.items():
        if not isinstance(name, str) or not name.strip():
            errors.append("profile names must be non-empty strings")
            continue
        if not isinstance(item, dict):
            errors.append(f"profiles.{name} must be an object")
            continue
        role = item.get("role")
        if role not in ROLES:
            errors.append(f"profiles.{name}.role must be one of: {', '.join(sorted(ROLES))}")
        vault_name = item.get("vault")
        if not isinstance(vault_name, str) or vault_name not in vaults:
            errors.append(f"profiles.{name}.vault must reference a configured vault")
        actor_id = item.get("actor_id")
        if not isinstance(actor_id, str) or not actor_id.strip():
            errors.append(f"profiles.{name}.actor_id must be a non-empty string")
        elif actor_id in actor_ids:
            errors.append(
                f"profiles.{name}.actor_id duplicates profiles.{actor_ids[actor_id]}.actor_id"
            )
        else:
            actor_ids[actor_id] = name
        host = item.get("host")
        if not isinstance(host, str) or not host.strip():
            errors.append(f"profiles.{name}.host must be a non-empty string")
        enabled = item.get("enabled", True)
        if not isinstance(enabled, bool):
            errors.append(f"profiles.{name}.enabled must be a boolean")

    default_profile = config.get("default_profile")
    if not isinstance(default_profile, str) or default_profile not in profiles:
        errors.append("default_profile must reference a configured profile")
    elif not bool(profiles[default_profile].get("enabled", True)):
        errors.append("default_profile must reference an enabled profile")
    return errors


def is_legacy_config(config: dict[str, Any]) -> bool:
    vault = config.get("vault")
    return isinstance(vault, str) and bool(vault.strip()) and "schema_version" not in config


def vault_is_valid(path: Path) -> bool:
    return (path / "000_Inbox").is_dir() and (path / "wiki").is_dir()


def inspect_setup(config_path: Path, profile: str | None = None) -> dict[str, object]:
    selected = requested_profile(profile)
    base: dict[str, object] = {
        "ok": True,
        "configured": False,
        "config_path": str(config_path),
        "requested_profile": selected or "default",
    }
    if not config_path.exists():
        return {
            **base,
            "state": "config_missing",
            "message": "AgentsKM user configuration does not exist.",
        }
    try:
        config = read_json(config_path)
    except RuntimeError as exc:
        return {**base, "state": "config_invalid", "message": str(exc)}
    if is_legacy_config(config):
        return {
            **base,
            "state": "legacy_config",
            "message": "Legacy single-vault configuration must be migrated by setup.",
            "legacy_vault": config["vault"],
        }
    errors = validate_config(config)
    if errors:
        return {
            **base,
            "state": "config_invalid",
            "message": "AgentsKM configuration failed validation.",
            "errors": errors,
        }

    selected = selected or str(config["default_profile"])
    profiles = config["profiles"]
    vaults = config["vaults"]
    base["requested_profile"] = selected
    base["available_profiles"] = sorted(profiles)
    base["available_vaults"] = sorted(vaults)
    if selected not in profiles:
        return {
            **base,
            "state": "profile_missing",
            "message": f"AgentsKM profile is not configured: {selected}",
        }
    profile_data = profiles[selected]
    if not profile_data.get("enabled", True):
        return {
            **base,
            "state": "profile_disabled",
            "message": f"AgentsKM profile is disabled: {selected}",
        }
    vault_name = profile_data["vault"]
    vault_path = Path(vaults[vault_name]["path"]).expanduser().resolve()
    context = RuntimeContext(
        config_path=config_path,
        profile_name=selected,
        actor_id=profile_data["actor_id"],
        host=profile_data["host"],
        role=profile_data["role"],
        vault_name=vault_name,
        vault_path=vault_path,
    )
    if not vault_is_valid(vault_path):
        return {
            **base,
            **context.as_dict(),
            "state": "vault_invalid",
            "message": f"Not an AgentsKM vault: {vault_path}",
        }
    return {
        **base,
        **context.as_dict(),
        "configured": True,
        "state": "ready",
        "message": "AgentsKM profile is ready.",
    }


def resolve_runtime(config_path: Path, profile: str | None = None) -> RuntimeContext:
    status = inspect_setup(config_path, profile)
    if not status.get("configured"):
        state = status.get("state", "not_configured")
        message = status.get("message", "AgentsKM is not configured.")
        raise RuntimeError(f"AGENTSKM_{str(state).upper()}: {message}")
    return RuntimeContext(
        config_path=config_path,
        profile_name=str(status["profile"]),
        actor_id=str(status["actor_id"]),
        host=str(status["host"]),
        role=str(status["role"]),
        vault_name=str(status["vault_name"]),
        vault_path=Path(str(status["vault_path"])),
    )


def default_config(vault_name: str, vault_path: Path) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "default_profile": "default",
        "vaults": {
            vault_name: {
                "path": str(vault_path),
                "create_if_missing": False,
            }
        },
        "profiles": {
            "default": {
                "display_name": "Unknown local agent",
                "host": "unknown",
                "actor_id": "local-default",
                "role": "contributor",
                "vault": vault_name,
                "enabled": True,
            }
        },
        "policies": {
            "review": {"separation_of_duties": False},
            "reminders": {"enabled": True, "default_snooze_days": 7},
        },
    }
