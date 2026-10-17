"""Plans and coupons, loaded once from fixtures/catalog.json."""
import json
import os

from billing.models import Coupon, Plan

CATALOG_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "fixtures", "catalog.json")


def _load(path):
    with open(path) as f:
        raw = json.load(f)
    plans = {p["id"]: Plan(**p) for p in raw["plans"]}
    coupons = {c["id"]: Coupon(**c) for c in raw["coupons"]}
    return plans, coupons


PLANS, COUPONS = _load(CATALOG_PATH)
