from upfront.portal import estimate_cost, is_chat, normalize

CHAT = {"output_modalities": ["text"]}
EMBED = {"output_modalities": ["embeddings"]}

PAYLOAD = {"data": [
    {"id": "meta/muse-ember", "name": "Meta: Muse Ember", "context_length": 1048576,
     "pricing": {"prompt": "0.0000001000", "completion": "0.0000005000"},
     "reasoning": False, "architecture": CHAT},
    {"id": "stepfun/step-3.7-flash:free", "name": "Step: Flash (free)", "context_length": 32768,
     "pricing": {"prompt": "0", "completion": "0"}, "reasoning": False, "architecture": CHAT},
    {"id": "big/reasoner", "name": "Big Reasoner", "context_length": 200000,
     "pricing": {"prompt": "0.000003", "completion": "0.000015"}, "reasoning": True,
     "architecture": CHAT},
    {"id": "baai/bge-base-en-v1.5", "name": "BAAI: bge", "context_length": 512,
     "pricing": {"prompt": "0.000000005", "completion": "0"}, "reasoning": False,
     "architecture": EMBED},
]}


def test_prices_are_per_million():
    models = {m["id"]: m for m in normalize(PAYLOAD)}
    assert models["meta/muse-ember"]["prompt_per_m"] == 0.1
    assert models["meta/muse-ember"]["completion_per_m"] == 0.5
    assert models["big/reasoner"]["prompt_per_m"] == 3.0


def test_free_models_are_detected_and_sorted_first():
    models = normalize(PAYLOAD)
    assert models[0]["free"] is True
    assert sum(1 for m in models if m["free"]) == 1


def test_embedding_models_are_not_offered():
    ids = [m["id"] for m in normalize(PAYLOAD)]
    assert "baai/bge-base-en-v1.5" not in ids
    assert is_chat({"architecture": CHAT}) is True
    assert is_chat({"architecture": EMBED}) is False


def test_cost_estimate_scales_with_calls():
    models = {m["id"]: m for m in normalize(PAYLOAD)}
    assert estimate_cost(models["stepfun/step-3.7-flash:free"], 176) == 0.0
    # 176 x (700/1M x 0.1 + 120/1M x 0.5) = 176 x 0.00013 = 0.0229
    assert estimate_cost(models["meta/muse-ember"], 176) == 0.0229
