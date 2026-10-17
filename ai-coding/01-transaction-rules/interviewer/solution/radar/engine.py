"""Decide accept, block or review for one transaction."""
import dataclasses
import logging

from radar.errors import RuleSyntaxError
from radar.models import ACCEPT, Decision
from radar.parser import parse

log = logging.getLogger(__name__)

DEFAULT_ACTION = ACCEPT


def _compile(rules):
    """Parse every rule first, so one bad rule stops the whole decision."""
    compiled = []
    for rule in rules:
        try:
            compiled.append((rule, parse(rule.when, rule.version)))
        except RuleSyntaxError as e:
            raise RuleSyntaxError(f"rule {rule.id}: {e}") from None
    return compiled


def explain(txn, rules):
    """The first rule in list order whose clause is true decides."""
    for rule, tree in _compile(rules):
        if tree.eval(txn):
            log.debug("rule %s matched", rule.id)
            return Decision(rule.action, rule.id)
    return Decision(DEFAULT_ACTION, None)


def evaluate(txn, rules):
    return explain(txn, rules).action


def migrate(rule):
    """Rewrite a version 1 rule as a version 2 rule with the same decisions."""
    if rule.version == 2:
        return rule
    tree = parse(rule.when, 1)
    return dataclasses.replace(rule, when=tree.render(), version=2)
