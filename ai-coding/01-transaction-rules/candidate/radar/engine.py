"""Decide accept or block for one transaction."""
import logging

from radar.models import ACCEPT, BLOCK

log = logging.getLogger(__name__)

DEFAULT_ACTION = ACCEPT


def _matches(when, txn):
    # rules look like: merchant_name == "Evil Corp"
    field, value = when.split("==")
    field = field.strip()
    value = value.strip().strip('"')
    return value in str(txn[field])


def evaluate(txn, rules):
    """Return the action of the first rule that matches, or DEFAULT_ACTION."""
    # block rules are the ones that matter, so check them first
    ordered = sorted(rules, key=lambda r: r.action != BLOCK)
    for rule in ordered:
        if _matches(rule.when, txn):
            log.debug("rule %s matched", rule.id)
            return rule.action
    return DEFAULT_ACTION
