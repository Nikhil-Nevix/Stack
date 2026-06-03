from __future__ import annotations

from typing import Any

from .mock_store import MockStore, mock_store


class DataRouter:
    async def get_tickets(self, filters: dict | None = None, user_id: str | None = None):
        if await MockStore.is_mock():
            if user_id:
                return mock_store.get_tickets_for_user(user_id)
            return mock_store.get_all_tickets(filters)
        # TODO: replace with real DB query
        return []

    async def get_ticket(self, ticket_id: str, current_user: Any = None):
        if await MockStore.is_mock():
            ticket = mock_store.get_ticket(ticket_id)
            if not ticket:
                return None
            if current_user and getattr(current_user, "role", None) == "user":
                if ticket.get("user_id") != getattr(current_user, "user_id", None):
                    return None
            if current_user and getattr(current_user, "role", None) == "agent":
                if ticket.get("assigned_agent_id") not in {None, getattr(current_user, "user_id", None)}:
                    group_allowed = any(
                        group.get("use_case") == ticket.get("use_case")
                        and any(member.get("user_id") == getattr(current_user, "user_id", None) for member in group.get("members", []))
                        for group in mock_store.get_agent_groups()
                    )
                    if not group_allowed:
                        return None
            return ticket
        # TODO: replace with real DB query
        return None

    async def get_dashboard_summary(self):
        if await MockStore.is_mock():
            return mock_store.get_dashboard_summary()
        # TODO: replace with real DB query
        return {}

    async def get_at_risk_tickets(self):
        if await MockStore.is_mock():
            return mock_store.get_at_risk_tickets()
        # TODO: replace with real DB query
        return []

    async def get_recent_activity(self, limit: int = 20):
        if await MockStore.is_mock():
            return mock_store.get_recent_activity(limit=limit)
        # TODO: replace with real DB query
        return []

    async def get_audit_logs(self, filters: dict | None = None, limit: int = 50):
        if await MockStore.is_mock():
            return mock_store.get_audit_logs(filters=filters, limit=limit)
        # TODO: replace with real DB query
        return []

    async def get_api_logs(self, limit: int = 50):
        if await MockStore.is_mock():
            return mock_store.get_api_logs(limit=limit)
        # TODO: replace with real DB query
        return []

    async def get_ps_executions(self, limit: int = 50):
        if await MockStore.is_mock():
            return mock_store.get_ps_executions(limit=limit)
        # TODO: replace with real DB query
        return []

    async def get_roi_current(self):
        if await MockStore.is_mock():
            return mock_store.get_roi_current()
        # TODO: replace with real DB query
        return {}

    async def get_roi_trend(self):
        if await MockStore.is_mock():
            return mock_store.get_roi_trend()
        # TODO: replace with real DB query
        return []

    async def get_all_sops(self):
        if await MockStore.is_mock():
            return mock_store.get_all_sops()
        # TODO: replace with real DB query
        return []

    async def get_thresholds(self):
        if await MockStore.is_mock():
            return mock_store.get_thresholds()
        # TODO: replace with real DB query
        return []

    async def get_sla_configs(self):
        if await MockStore.is_mock():
            return mock_store.get_sla_configs()
        # TODO: replace with real DB query
        return []

    async def get_agent_groups(self):
        if await MockStore.is_mock():
            return mock_store.get_agent_groups()
        # TODO: replace with real DB query
        return []

    async def get_all_users(self):
        if await MockStore.is_mock():
            return mock_store.get_all_users()
        # TODO: replace with real DB query
        return []

    async def get_resolution_for_ticket(self, ticket_id: str):
        if await MockStore.is_mock():
            return mock_store.get_resolution_for_ticket(ticket_id)
        # TODO: replace with real DB query
        return None

    async def get_notes_for_ticket(self, ticket_id: str, include_internal: bool = False):
        if await MockStore.is_mock():
            return mock_store.get_notes_for_ticket(ticket_id, include_internal=include_internal)
        # TODO: replace with real DB query
        return []

    async def update_ticket(self, ticket_id: str, updates: dict):
        if await MockStore.is_mock():
            return mock_store.update_ticket(ticket_id, updates)
        # TODO: replace with real DB query
        return None

    async def add_note(self, note_data: dict):
        if await MockStore.is_mock():
            return mock_store.add_note(note_data)
        # TODO: replace with real DB query
        return None

    async def add_audit_log(self, log_data: dict):
        if await MockStore.is_mock():
            return mock_store.add_audit_log(log_data)
        # TODO: replace with real DB query
        return None

    async def update_threshold(self, use_case: str, updates: dict):
        if await MockStore.is_mock():
            return mock_store.update_threshold(use_case, updates)
        # TODO: replace with real DB query
        return None

    async def update_group(self, group_id: str, updates: dict):
        if await MockStore.is_mock():
            return mock_store.update_group(group_id, updates)
        # TODO: replace with real DB query
        return None

    async def set_data_source(self, mode: str):
        await MockStore.set_mode(mode)

    async def get_data_source(self):
        return await MockStore.get_mode()


data_router = DataRouter()
