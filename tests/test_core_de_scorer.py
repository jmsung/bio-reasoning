"""Goal 3: CORE DE scorers over contrastive references.

- voting_pde: P(DE) = fraction of references that are DE (no LLM; = CORE-Voting).
- reasoning_pde: LLM reasons over the pos/neg set → P(DE) via an injectable client
  (mocked here; the real run needs a logprob endpoint).
"""

import math

from bio_reasoning.models.core_de_scorer import reasoning_pde, voting_pde


def _refs(n_pos, n_neg):
    return {
        "positive": [("P", "G", "up")] * n_pos,
        "negative": [("P", "G", "none")] * n_neg,
    }


def test_voting_pde_is_de_fraction():
    assert voting_pde(_refs(2, 3)) == 0.4
    assert voting_pde(_refs(0, 4)) == 0.0
    assert math.isnan(voting_pde(_refs(0, 0)))  # no evidence → nan (uncovered)


class _MockClient:
    """Records the prompt and returns a fixed P(yes)."""

    def __init__(self, p_yes):
        self.p_yes = p_yes
        self.last_prompt = None
        self.last_model = "unset"

    def score_yes(self, prompt, model=None):
        self.last_prompt = prompt
        self.last_model = model
        return self.p_yes


def test_reasoning_pde_uses_client_and_embeds_context():
    client = _MockClient(0.73)
    refs = _refs(1, 2)
    p = reasoning_pde("Pfoo", "Gbar", refs, client, model="qwen")
    assert p == 0.73
    assert client.last_model == "qwen"  # model kwarg forwarded to the client
    # the contrastive set + query are in the prompt the client saw
    assert "Pfoo" in client.last_prompt and "Gbar" in client.last_prompt
    assert "up" in client.last_prompt and "none" in client.last_prompt
