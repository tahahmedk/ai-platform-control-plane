import pytest

from ai_platform.evals import evaluate
from ai_platform.models import Provider, RequestContext
from ai_platform.routing import RoutingWeights, choose_provider


def test_lexical_signal_is_not_empty_success():
    assert not evaluate("", "", "").passed
    assert evaluate("synthetic answer", "synthetic answer", "synthetic answer").passed
    with pytest.raises(ValueError):
        evaluate("a", "a", "a", threshold=0)


def test_tie_break_independent_of_config_order():
    a = Provider("a", frozenset({"us"}), frozenset({"chat"}), 1, 100, 0.9, 0.99)
    b = Provider("b", a.regions, a.capabilities, 1, 100, 0.9, 0.99)
    context = RequestContext("demo", "us", frozenset({"chat"}), 10)
    assert choose_provider([a, b], context) == choose_provider([b, a], context)
    assert choose_provider([b, a], context).provider == "a"


def test_invalid_weights_rejected():
    with pytest.raises(ValueError):
        RoutingWeights(quality=-1)
