from __future__ import annotations

import os
from copy import deepcopy
from datetime import datetime, timedelta
from typing import Any

from redis.asyncio import from_url as redis_from_url

from ..app.core.config import settings
from .mock_data import (
    MOCK_AGENT_GROUPS,
    MOCK_AI_RESOLUTIONS,
    MOCK_API_CALL_LOGS,
    MOCK_AUDIT_LOGS,
    MOCK_CONFIDENCE_THRESHOLDS,
    MOCK_DASHBOARD_SUMMARY,
    MOCK_PS_EXECUTIONS,
    MOCK_ROI_METRICS,
    MOCK_SLA_CONFIGS,
    MOCK_SOPS,
    MOCK_TICKET_NOTES,
    MOCK_TICKETS,
    MOCK_USERS,
)


DATA_SOURCE_KEY = "stack:data_source"


def _serialize(value: Any) -> Any:
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, list):
        return [_serialize(item) for item in value]
    if isinstance(value, dict):
        return {key: _serialize(item) for key, item in value.items()}
    return value


def _matches_filters(item: dict, filters: dict | None) -> bool:
    if not filters:
        return True
    for key, value in filters.items():
        if value is None:
            continue
        if item.get(key) != value:
            return False
    return True


def _sorted_desc(items: list[dict], field: str = "created_at") -> list[dict]:
    return sorted(items, key=lambda item: item.get(field) or datetime.min, reverse=True)


class MockStore:
    _instance: "MockStore | None" = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if getattr(self, "_initialized", False):
            return
        self._load_state()
        self._initialized = True

    def _load_state(self):
        self._users = deepcopy(MOCK_USERS)
        self._agent_groups = deepcopy(MOCK_AGENT_GROUPS)
        self._tickets = deepcopy(MOCK_TICKETS)
        self._resolutions = deepcopy(MOCK_AI_RESOLUTIONS)
        self._ps_executions = deepcopy(MOCK_PS_EXECUTIONS)
        self._notes = deepcopy(MOCK_TICKET_NOTES)
        self._audit_logs = deepcopy(MOCK_AUDIT_LOGS)
        self._api_logs = deepcopy(MOCK_API_CALL_LOGS)
        self._sops = deepcopy(MOCK_SOPS)
        self._thresholds = deepcopy(MOCK_CONFIDENCE_THRESHOLDS)
        self._sla_configs = deepcopy(MOCK_SLA_CONFIGS)
        self._roi = deepcopy(MOCK_ROI_METRICS)
        self._dashboard = deepcopy(MOCK_DASHBOARD_SUMMARY)

    @staticmethod
    async def get_mode() -> str:
        client = redis_from_url(settings.REDIS_URL, decode_responses=True)
        try:
            mode = await client.get(DATA_SOURCE_KEY)
            if mode in {"mock", "live"}:
                return mode
        except Exception:
            pass
        finally:
            await client.aclose()
        env_mode = os.getenv("STACK_DATA_SOURCE", "live").lower()
        return env_mode if env_mode in {"mock", "live"} else "live"

    @staticmethod
    async def set_mode(mode: str):
        client = redis_from_url(settings.REDIS_URL, decode_responses=True)
        try:
            await client.set(DATA_SOURCE_KEY, mode)
        finally:
            await client.aclose()
        os.environ["STACK_DATA_SOURCE"] = mode

    @staticmethod
    async def is_mock() -> bool:
        return await MockStore.get_mode() == "mock"

    def _serialize_list(self, items: list[dict]) -> list[dict]:
        return [_serialize(deepcopy(item)) for item in items]

    def get_all_tickets(self, filters: dict | None = None) -> list[dict]:
        tickets = [ticket for ticket in self._tickets if _matches_filters(ticket, filters)]
        return self._serialize_list(_sorted_desc(tickets))

    def get_ticket(self, ticket_id: str) -> dict | None:
        ticket = next((ticket for ticket in self._tickets if ticket["ticket_id"] == ticket_id), None)
        return _serialize(deepcopy(ticket)) if ticket else None

    def create_ticket(self, ticket_data: dict) -> dict:
        record = deepcopy(ticket_data)
        if not record.get("ticket_id"):
            record["ticket_id"] = f"tkt-{len(self._tickets) + 1:03d}"
        now = datetime.now()
        record.setdefault("created_at", now)
        record.setdefault("updated_at", record["created_at"])
        record.setdefault("closed_at", None)
        self._tickets.append(record)
        return _serialize(deepcopy(record))

    def update_ticket(self, ticket_id: str, updates: dict) -> dict | None:
        ticket = next((ticket for ticket in self._tickets if ticket["ticket_id"] == ticket_id), None)
        if not ticket:
            return None
        for key, value in updates.items():
            ticket[key] = value
        ticket["updated_at"] = updates.get("updated_at", datetime.now())
        if ticket.get("status") in {"closed", "auto_resolved"} and ticket.get("closed_at") is None:
            ticket["closed_at"] = ticket["updated_at"]
        return _serialize(deepcopy(ticket))

    def get_tickets_for_user(self, user_id: str) -> list[dict]:
        return self.get_all_tickets({"user_id": user_id})

    def get_at_risk_tickets(self) -> list[dict]:
        tickets = [
            ticket
            for ticket in self._tickets
            if ticket.get("sla_status") in {"at_risk", "breached"}
            and ticket.get("status") not in {"closed", "auto_resolved"}
        ]
        return self._serialize_list(_sorted_desc(tickets))

    def get_user_by_email(self, email: str) -> dict | None:
        user = next((user for user in self._users if user["email"].lower() == email.lower()), None)
        return _serialize(deepcopy(user)) if user else None

    def get_user_by_id(self, user_id: str) -> dict | None:
        user = next((user for user in self._users if user["user_id"] == user_id), None)
        return _serialize(deepcopy(user)) if user else None

    def get_all_users(self) -> list[dict]:
        users = sorted(self._users, key=lambda user: user.get("created_at") or datetime.min, reverse=True)
        return self._serialize_list(users)

    def get_resolution_for_ticket(self, ticket_id: str) -> dict | None:
        resolution = next((item for item in self._resolutions if item["ticket_id"] == ticket_id), None)
        return _serialize(deepcopy(resolution)) if resolution else None

    def get_all_resolutions(self) -> list[dict]:
        return self._serialize_list(_sorted_desc(self._resolutions))

    def get_notes_for_ticket(self, ticket_id: str, include_internal: bool = False) -> list[dict]:
        notes = [
            note
            for note in self._notes
            if note["ticket_id"] == ticket_id and (include_internal or not note.get("is_internal"))
        ]
        return self._serialize_list(_sorted_desc(notes))

    def add_note(self, note_data: dict) -> dict:
        record = deepcopy(note_data)
        if not record.get("note_id"):
            record["note_id"] = f"note-{len(self._notes) + 1:03d}"
        record.setdefault("created_at", datetime.now())
        self._notes.append(record)
        return _serialize(deepcopy(record))

    def get_audit_logs(self, filters: dict | None = None, limit: int = 50) -> list[dict]:
        logs = [log for log in self._audit_logs if _matches_filters(log, filters)]
        return self._serialize_list(_sorted_desc(logs))[:limit]

    def get_api_logs(self, limit: int = 50) -> list[dict]:
        return self._serialize_list(_sorted_desc(self._api_logs))[:limit]

    def get_ps_executions(self, limit: int = 50) -> list[dict]:
        return self._serialize_list(_sorted_desc(self._ps_executions))[:limit]

    def add_audit_log(self, log_data: dict) -> dict:
        record = deepcopy(log_data)
        if not record.get("log_id"):
            record["log_id"] = f"log-{len(self._audit_logs) + 1:03d}"
        record.setdefault("created_at", datetime.now())
        self._audit_logs.append(record)
        return _serialize(deepcopy(record))

    def get_dashboard_summary(self) -> dict:
        summary = deepcopy(self._dashboard)
        active_tickets = [ticket for ticket in self._tickets if ticket.get("status") not in {"closed", "auto_resolved"}]
        summary["total_open"] = len(active_tickets)
        summary["resolved_today"] = sum(
            1
            for ticket in self._tickets
            if ticket.get("status") in {"closed", "auto_resolved"}
            and isinstance(ticket.get("updated_at"), datetime)
            and ticket["updated_at"] >= datetime.now() - timedelta(days=1)
        )
        summary["sla_at_risk_count"] = sum(
            1
            for ticket in active_tickets
            if ticket.get("sla_status") in {"at_risk", "breached"}
        )
        return _serialize(summary)

    def get_recent_activity(self, limit: int = 20) -> list[dict]:
        return self.get_audit_logs(limit=limit)

    def get_all_sops(self) -> list[dict]:
        active_sops = [sop for sop in self._sops if sop.get("is_active")]
        return self._serialize_list(_sorted_desc(active_sops))

    def get_sop(self, sop_id: str) -> dict | None:
        sop = next((item for item in self._sops if item["sop_id"] == sop_id), None)
        return _serialize(deepcopy(sop)) if sop else None

    def get_thresholds(self) -> list[dict]:
        return self._serialize_list(_sorted_desc(self._thresholds))

    def update_threshold(self, use_case: str, updates: dict) -> dict | None:
        threshold = next((item for item in self._thresholds if item["use_case"] == use_case), None)
        if not threshold:
            return None
        for key, value in updates.items():
            if key in {"auto_resolve_min", "review_after_min", "updated_by", "updated_at"}:
                threshold[key] = value
        threshold["updated_at"] = updates.get("updated_at", datetime.now())
        return _serialize(deepcopy(threshold))

    def get_sla_configs(self) -> list[dict]:
        return self._serialize_list(_sorted_desc(self._sla_configs))

    def get_agent_groups(self) -> list[dict]:
        return self._serialize_list(_sorted_desc(self._agent_groups))

    def update_group(self, group_id: str, updates: dict) -> dict | None:
        group = next((item for item in self._agent_groups if item["group_id"] == group_id), None)
        if not group:
            return None
        for key, value in updates.items():
            if key in {"group_name", "use_case", "assignment_mode", "freshservice_group_id", "members"}:
                group[key] = value
        return _serialize(deepcopy(group))

    def get_roi_current(self) -> dict:
        return _serialize(deepcopy(self._roi["current_period"]))

    def get_roi_trend(self) -> list[dict]:
        return self._serialize_list(deepcopy(self._roi["monthly_trend"]))

    def get_resolution_rate(self) -> dict:
        use_cases = [
            "sharepoint_access",
            "sharepoint_admin",
            "license_bluebeam",
            "license_adobe",
            "license_o365",
            "dl_update",
            "windows_troubleshooting",
        ]
        by_use_case = []
        total_auto = 0
        total_manual = 0

        for use_case in use_cases:
            tickets = [ticket for ticket in self._tickets if ticket.get("use_case") == use_case]
            auto_resolved = sum(1 for ticket in tickets if ticket.get("resolution_type") == "auto")
            manual_resolved = sum(1 for ticket in tickets if ticket.get("resolution_type") == "manual")
            total_auto += auto_resolved
            total_manual += manual_resolved
            total = len(tickets)
            by_use_case.append(
                {
                    "use_case": use_case,
                    "total": total,
                    "auto_resolved": auto_resolved,
                    "manual_resolved": manual_resolved,
                    "auto_pct": round((auto_resolved / total * 100) if total else 0, 1),
                }
            )

        grand_total = total_auto + total_manual
        return {
            "by_use_case": by_use_case,
            "overall_auto_pct": round((total_auto / grand_total * 100) if grand_total else 0, 1),
            "overall_manual_pct": round((total_manual / grand_total * 100) if grand_total else 0, 1),
        }

    def get_sla_compliance(self) -> dict:
        met = sum(1 for ticket in self._tickets if ticket.get("sla_status") == "safe")
        breached = sum(1 for ticket in self._tickets if ticket.get("sla_status") == "breached")
        at_risk = sum(1 for ticket in self._tickets if ticket.get("sla_status") == "at_risk")
        total = met + breached + at_risk
        trend = [
            {
                "date": (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d"),
                "met_pct": round(met / total * 100 if total else 100, 1),
            }
            for i in range(6, -1, -1)
        ]
        return {
            "met": met,
            "breached": breached,
            "at_risk": at_risk,
            "met_pct": round(met / total * 100 if total else 100, 1),
            "trend": trend,
        }

    def get_agent_performance(self) -> list[dict]:
        agents = [user for user in self._users if user.get("role") in {"agent", "admin"}]
        result = []
        for agent in agents:
            tickets_resolved = sum(
                1
                for ticket in self._tickets
                if ticket.get("assigned_agent_id") == agent["user_id"]
                and ticket.get("status") in {"auto_resolved", "closed"}
            )
            result.append(
                {
                    "agent_id": agent["user_id"],
                    "agent_name": agent.get("full_name"),
                    "tickets_resolved": tickets_resolved,
                    "avg_resolution_mins": 30.0,
                    "sla_met_pct": 85.0,
                }
            )
        return result

    def get_ticket_trends(self) -> dict:
        end_day = datetime.now().date()
        start_day = end_day - timedelta(days=29)
        trend = []
        current_day = start_day
        while current_day <= end_day:
            day_total = sum(
                1
                for ticket in self._tickets
                if isinstance(ticket.get("created_at"), datetime)
                and ticket["created_at"].date() == current_day
            )
            trend.append({"date": current_day.strftime("%Y-%m-%d"), "total": day_total, "by_use_case": {}})
            current_day += timedelta(days=1)
        return {"trend": trend}

    def get_ai_accuracy(self) -> dict:
        if not self._resolutions:
            return {
                "avg_confidence": 0,
                "distribution": [
                    {"range": "90-100", "count": 0},
                    {"range": "80-89", "count": 0},
                    {"range": "70-79", "count": 0},
                    {"range": "60-69", "count": 0},
                    {"range": "<60", "count": 0},
                ],
                "auto_resolve_accuracy": 0,
            }

        avg_confidence = sum(item.get("confidence_score", 0) for item in self._resolutions) / len(self._resolutions)
        auto_count = sum(1 for item in self._resolutions if item.get("decision") == "auto_resolve")
        total = len(self._resolutions)
        distribution = [
            {"range": "90-100", "count": 0},
            {"range": "80-89", "count": 0},
            {"range": "70-79", "count": 0},
            {"range": "60-69", "count": 0},
            {"range": "<60", "count": 0},
        ]
        for item in self._resolutions:
            score = item.get("confidence_score", 0)
            if score >= 90:
                distribution[0]["count"] += 1
            elif score >= 80:
                distribution[1]["count"] += 1
            elif score >= 70:
                distribution[2]["count"] += 1
            elif score >= 60:
                distribution[3]["count"] += 1
            else:
                distribution[4]["count"] += 1

        return {
            "avg_confidence": round(avg_confidence, 1),
            "distribution": distribution,
            "auto_resolve_accuracy": round(auto_count / total * 100 if total else 0, 1),
        }

    def get_payback(self) -> dict:
        return {
            "estimated_months": self._roi["payback_months_estimated"],
            "percent_complete": self._roi["payback_percent_complete"],
        }

    def reset(self):
        self._initialized = False
        self.__init__()


mock_store = MockStore()
