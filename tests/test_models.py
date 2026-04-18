def test_list_models_status(client):
    r = client.get("/v1/models")
    assert r.status_code == 200


def test_list_models_shape(client):
    data = client.get("/v1/models").json()
    assert data["object"] == "list"
    assert isinstance(data["data"], list)
    assert len(data["data"]) > 0


def test_model_fields(client):
    models = client.get("/v1/models").json()["data"]
    for model in models:
        assert "id" in model
        assert "object" in model
        assert model["object"] == "model"