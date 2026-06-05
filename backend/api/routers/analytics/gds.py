from __future__ import annotations

from fastapi import APIRouter

from backend.api.dependencies import read_json

router = APIRouter(prefix="/gds")


@router.get("")
def get_gds_analytics():
    return {
        "bottlenecks": read_json("bottlenecks.json", default=[]),
        "communities": read_json("communities.json", default=[]),
        "pagerank":    read_json("pagerank.json",    default=[]),
        "wcc":         read_json("wcc.json",         default={}),
    }