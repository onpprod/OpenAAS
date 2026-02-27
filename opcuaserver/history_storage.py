"""Additional history storage backends for opcuaserver."""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import Any

from asyncua import ua
from asyncua.common.utils import Buffer
from asyncua.server.history import HistoryDict, HistoryStorageInterface
from asyncua.server.history_sql import HistorySQLite
from asyncua.ua.ua_binary import variant_from_binary, variant_to_binary

try:
    from bson import Binary
    from pymongo import ASCENDING, DESCENDING, MongoClient
except ImportError:  # pragma: no cover - optional dependency
    Binary = None
    MongoClient = None
    ASCENDING = 1
    DESCENDING = -1


class MongoHistoryStorage(HistoryStorageInterface):
    """History backend storing data changes in MongoDB."""

    def __init__(
        self,
        *,
        uri: str,
        database: str,
        collection: str,
        username: str | None = None,
        password: str | None = None,
        auth_source: str | None = None,
        max_history_data_response_size: int = 10000,
    ) -> None:
        super().__init__(max_history_data_response_size=max_history_data_response_size)
        self._uri = uri
        self._database_name = database
        self._collection_name = collection
        self._username = username
        self._password = password
        self._auth_source = auth_source
        self._client: Any | None = None
        self._collection: Any | None = None
        self._node_config: dict[str, tuple[Any, int]] = {}

    async def init(self):
        if MongoClient is None or Binary is None:
            raise RuntimeError(
                "MongoDB historization requires 'pymongo'. Install it and retry."
            )

        self._client = await asyncio.to_thread(self._create_client)
        self._collection = self._client[self._database_name][self._collection_name]
        await asyncio.to_thread(
            self._collection.create_index,
            [("node_id", ASCENDING), ("source_ts", ASCENDING)],
        )

    async def stop(self):
        if self._client is None:
            return
        await asyncio.to_thread(self._client.close)

    async def new_historized_node(self, node_id, period, count=0):
        self._node_config[self._node_key(node_id)] = (period, count)

    async def save_node_value(self, node_id, datavalue):
        if self._collection is None:
            return

        datavalue = _normalize_data_value_timestamps(datavalue)
        node_key = self._node_key(node_id)
        source_ts = datavalue.SourceTimestamp
        server_ts = datavalue.ServerTimestamp

        await asyncio.to_thread(
            self._collection.insert_one,
            {
                "node_id": node_key,
                "server_ts": server_ts,
                "source_ts": source_ts,
                "status_code": datavalue.StatusCode.value,
                "value_text": str(datavalue.Value.Value),
                "variant_type": datavalue.Value.VariantType.name,
                "variant_binary": Binary(variant_to_binary(datavalue.Value)),
            },
        )

        period, count = self._node_config.get(node_key, (None, 0))
        if period:
            limit_ts = datetime.now(timezone.utc) - period
            await asyncio.to_thread(
                self._collection.delete_many,
                {"node_id": node_key, "source_ts": {"$lt": limit_ts}},
            )

        if count and count > 0:
            total = await asyncio.to_thread(
                self._collection.count_documents,
                {"node_id": node_key},
            )
            overflow = total - count
            if overflow > 0:
                old_ids = await asyncio.to_thread(
                    self._select_oldest_ids,
                    node_key,
                    overflow,
                )
                if old_ids:
                    await asyncio.to_thread(
                        self._collection.delete_many,
                        {"_id": {"$in": old_ids}},
                    )

    async def read_node_history(self, node_id, start, end, nb_values):
        if self._collection is None:
            return [], None

        node_key = self._node_key(node_id)
        start, end, sort_dir = self._normalize_bounds(start, end)
        query_filter: dict[str, Any] = {"node_id": node_key}

        if end is None:
            query_filter["source_ts"] = {"$gte": start}
        else:
            query_filter["source_ts"] = {"$gte": start, "$lte": end}

        max_items = self.max_history_data_response_size + 1
        if nb_values and nb_values > 0:
            max_items = min(max_items, nb_values)

        docs = await asyncio.to_thread(
            self._query_docs,
            query_filter,
            sort_dir,
            max_items,
        )

        results = [self._doc_to_datavalue(doc) for doc in docs]
        cont = None
        if len(results) > self.max_history_data_response_size:
            cont = results[self.max_history_data_response_size].SourceTimestamp
        results = results[: self.max_history_data_response_size]
        return results, cont

    async def new_historized_event(self, source_id, evtypes, period, count=0):
        del source_id
        del evtypes
        del period
        del count

    async def save_event(self, event):
        del event

    async def read_event_history(self, source_id, start, end, nb_values, evfilter):
        del source_id
        del start
        del end
        del nb_values
        del evfilter
        return [], None

    def _create_client(self):
        kwargs: dict[str, Any] = {}
        if self._username is not None:
            kwargs["username"] = self._username
        if self._password is not None:
            kwargs["password"] = self._password
        if self._auth_source is not None:
            kwargs["authSource"] = self._auth_source
        return MongoClient(self._uri, **kwargs)

    def _select_oldest_ids(self, node_key: str, limit_count: int) -> list[Any]:
        if self._collection is None:
            return []
        cursor = (
            self._collection.find({"node_id": node_key}, {"_id": 1})
            .sort("source_ts", ASCENDING)
            .limit(limit_count)
        )
        return [row["_id"] for row in cursor]

    def _query_docs(
        self,
        query_filter: dict[str, Any],
        sort_dir: int,
        limit_count: int,
    ) -> list[dict[str, Any]]:
        if self._collection is None:
            return []
        cursor = (
            self._collection.find(query_filter)
            .sort("source_ts", sort_dir)
            .limit(limit_count)
        )
        return list(cursor)

    @staticmethod
    def _node_key(node_id: ua.NodeId) -> str:
        return f"{node_id.NamespaceIndex}:{node_id.IdentifierType.name}:{node_id.Identifier}"

    @staticmethod
    def _normalize_bounds(start, end):
        if start is None:
            start = ua.get_win_epoch()
        if end is None:
            end = ua.get_win_epoch()

        if start == ua.get_win_epoch():
            return start, None, DESCENDING
        if end == ua.get_win_epoch():
            return start, None, ASCENDING
        if start > end:
            return end, start, DESCENDING
        return start, end, ASCENDING

    @staticmethod
    def _doc_to_datavalue(doc: dict[str, Any]) -> ua.DataValue:
        status_code = int(doc.get("status_code", ua.StatusCodes.Good))
        variant_blob = doc.get("variant_binary", b"")
        variant_bytes = bytes(variant_blob)
        return ua.DataValue(
            variant_from_binary(Buffer(variant_bytes)),
            ServerTimestamp=doc.get("server_ts"),
            SourceTimestamp=doc.get("source_ts"),
            StatusCode_=ua.StatusCode(status_code),
        )


class SafeHistoryDict(HistoryDict):
    """HistoryDict variant that guarantees non-null timestamps."""

    async def save_node_value(self, node_id, datavalue):
        await super().save_node_value(node_id, _normalize_data_value_timestamps(datavalue))


class SafeHistorySQLite(HistorySQLite):
    """HistorySQLite variant that guarantees non-null timestamps."""

    async def save_node_value(self, node_id, datavalue):
        await super().save_node_value(node_id, _normalize_data_value_timestamps(datavalue))


def _normalize_data_value_timestamps(datavalue: ua.DataValue) -> ua.DataValue:
    source_ts = datavalue.SourceTimestamp
    server_ts = datavalue.ServerTimestamp

    if source_ts is None and server_ts is None:
        now = datetime.now(timezone.utc)
        source_ts = now
        server_ts = now

    if source_ts is None:
        source_ts = server_ts
    if server_ts is None:
        server_ts = source_ts

    return ua.DataValue(
        datavalue.Value,
        StatusCode_=datavalue.StatusCode,
        SourceTimestamp=source_ts,
        ServerTimestamp=server_ts,
        SourcePicoseconds=datavalue.SourcePicoseconds,
        ServerPicoseconds=datavalue.ServerPicoseconds,
    )
