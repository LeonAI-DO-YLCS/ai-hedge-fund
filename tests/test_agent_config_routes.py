from __future__ import annotations


def test_agent_config_upsert_and_reset(client):
    update_response = client.put(
        "/agent-config/warren_buffett",
        json={"model_name": "gpt-4.1", "model_provider": "OpenAI", "temperature": 0.1},
    )
    assert update_response.status_code == 200
    assert update_response.json()["agent_key"] == "warren_buffett"

    list_response = client.get("/agent-config/")
    assert list_response.status_code == 200
    assert any(
        agent["agent_key"] == "warren_buffett"
        for agent in list_response.json()["agents"]
    )

    reset_response = client.delete("/agent-config/warren_buffett")
    assert reset_response.status_code == 200


def test_agent_default_prompt_endpoint_exists(client):
    response = client.get("/agent-config/warren_buffett/default-prompt")
    assert response.status_code == 200
    assert response.json()["agent_key"] == "warren_buffett"


def test_agent_apply_to_all_updates_multiple_agents(client):
    response = client.post(
        "/agent-config/apply-to-all",
        json={
            "fields": {
                "model_name": "gpt-4.1",
                "model_provider": "OpenAI",
                "temperature": 0.2,
            },
            "exclude_agents": ["portfolio_manager"],
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert "warren_buffett" in payload["updated_agents"]
    assert "portfolio_manager" not in payload["updated_agents"]
