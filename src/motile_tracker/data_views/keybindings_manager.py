"""Singleton that manages the mutable keybinding state with disk persistence.

The manager loads user-customised keybindings from a JSON file in the user's
config directory (via ``appdirs``).  Unknown actions in the file are ignored,
and actions missing from the file get their defaults from
:data:`keybindings_config.KEYBINDINGS`.
"""

from __future__ import annotations

import copy
import json
import logging
from pathlib import Path

from appdirs import AppDirs
from psygnal import Signal

from motile_tracker.data_views.keybindings_config import KEYBINDINGS

logger = logging.getLogger(__name__)


class KeybindingsManager:
    """Singleton owner of the current keybinding state.

    Attributes
    ----------
    keybindings_changed : Signal
        Emitted (with no arguments) after any call to :meth:`set_keys`,
        :meth:`reset_action`, or :meth:`reset_to_defaults`.
    """

    keybindings_changed = Signal()

    _instance: KeybindingsManager | None = None

    @classmethod
    def get_instance(cls) -> KeybindingsManager:
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self) -> None:
        self._defaults: dict[str, dict] = copy.deepcopy(KEYBINDINGS)
        self._keybindings: dict[str, dict] = copy.deepcopy(KEYBINDINGS)
        self._settings_path: Path = self._get_settings_path()
        self._load()

    # -- public API -----------------------------------------------------------

    @property
    def keybindings(self) -> dict[str, dict]:
        return self._keybindings

    def get_keys(self, action: str) -> list[str]:
        return list(self._keybindings[action]["keys"])

    def get_default_keys(self, action: str) -> list[str]:
        return list(self._defaults[action]["keys"])

    def get_targets(self, action: str) -> list[str]:
        return self._keybindings[action]["targets"]

    def set_keys(self, action: str, keys: list[str]) -> None:
        self._keybindings[action]["keys"] = keys
        self._save()
        self.keybindings_changed.emit()

    def reset_action(self, action: str) -> None:
        self._keybindings[action]["keys"] = list(self._defaults[action]["keys"])
        self._save()
        self.keybindings_changed.emit()

    def reset_to_defaults(self) -> None:
        self._keybindings = copy.deepcopy(self._defaults)
        self._save()
        self.keybindings_changed.emit()

    def find_conflicts(self, action: str, key: str) -> list[str]:
        """Return action names that already use *key* in an overlapping context."""
        targets = set(self._keybindings[action]["targets"])
        # "tracks_viewer" actions are active in all widgets, so they overlap
        # with everything.  "tree_widget"-only actions only overlap with other
        # tree_widget or tracks_viewer actions.
        conflicts: list[str] = []
        for other, config in self._keybindings.items():
            if other == action:
                continue
            if key in config["keys"]:
                other_targets = set(config["targets"])
                # Two actions conflict if their resolved widget scopes overlap.
                # tracks_viewer actions are present in tree + table + napari,
                # tree_widget actions are present only in tree.  So there's
                # always an overlap unless both are exclusively non-overlapping
                # (which doesn't happen with the current target design).
                if targets & other_targets or "tracks_viewer" in (
                    targets | other_targets
                ):
                    conflicts.append(other)
        return conflicts

    # -- keymap derivation ----------------------------------------------------

    def get_napari_keymap(self) -> dict[str, list[str]]:
        return {
            action: list(cfg["keys"])
            for action, cfg in self._keybindings.items()
            if "tracks_viewer" in cfg["targets"]
        }

    def get_tree_widget_keymap(self) -> dict[str, list[str]]:
        return {
            action: list(cfg["keys"])
            for action, cfg in self._keybindings.items()
            if "tree_widget" in cfg["targets"] or "tracks_viewer" in cfg["targets"]
        }

    def get_table_widget_keymap(self) -> dict[str, list[str]]:
        return {
            action: list(cfg["keys"])
            for action, cfg in self._keybindings.items()
            if "tracks_viewer" in cfg["targets"]
        }

    # -- persistence ----------------------------------------------------------

    @staticmethod
    def _get_settings_path() -> Path:
        appdir = AppDirs("motile-tracker")
        settings_dir = Path(appdir.user_config_dir)
        settings_dir.mkdir(parents=True, exist_ok=True)
        return settings_dir / "keybindings.json"

    def _save(self) -> None:
        data = {action: config["keys"] for action, config in self._keybindings.items()}
        try:
            with open(self._settings_path, "w") as f:
                json.dump(data, f, indent=2, sort_keys=True)
        except OSError:
            logger.warning("Failed to save keybindings to %s", self._settings_path)

    def _load(self) -> None:
        if not self._settings_path.exists():
            return
        try:
            with open(self._settings_path) as f:
                data = json.load(f)
            for action, keys in data.items():
                if action in self._keybindings and isinstance(keys, list):
                    self._keybindings[action]["keys"] = keys
        except (json.JSONDecodeError, OSError, TypeError):
            logger.warning(
                "Failed to load keybindings from %s; using defaults.",
                self._settings_path,
            )
