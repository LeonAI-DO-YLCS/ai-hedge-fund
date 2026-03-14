from __future__ import annotations

from src.agents.prompts import get_default_prompt


def test_agent_config_upsert_and_reset(client):
    update_response = client.put(
        "/agent-config/warren_buffett",
        json={
            "effective": {
                "system_prompt_text": "Custom Buffett prompt",
                "prompt_mode": "override",
                "model_name": "gpt-4.1",
                "model_provider": "OpenAI",
                "temperature": 0.1,
                "max_tokens": None,
                "top_p": None,
                "fallback_model_name": None,
                "fallback_model_provider": None,
            }
        },
    )
    assert update_response.status_code == 200
    assert update_response.json()["agent_key"] == "warren_buffett"
    assert (
        update_response.json()["effective"]["system_prompt_text"]
        == "Custom Buffett prompt"
    )
    assert (
        update_response.json()["persisted"]["system_prompt_override"]
        == "Custom Buffett prompt"
    )

    list_response = client.get("/agent-config/")
    assert list_response.status_code == 200
    assert any(
        agent["agent_key"] == "warren_buffett"
        for agent in list_response.json()["agents"]
    )

    reset_response = client.delete("/agent-config/warren_buffett")
    assert reset_response.status_code == 204


def test_agent_default_prompt_endpoint_exists(client):
    response = client.get("/agent-config/warren_buffett/default-prompt")
    assert response.status_code == 200
    assert response.json()["agent_key"] == "warren_buffett"


def test_agent_config_detail_returns_effective_defaults(client):
    response = client.get("/agent-config/warren_buffett")

    assert response.status_code == 200
    payload = response.json()
    assert payload["agent_key"] == "warren_buffett"
    assert payload["effective"]["prompt_mode"] == "default"
    assert payload["effective"]["system_prompt_text"] == get_default_prompt(
        "warren_buffett"
    )
    assert payload["sources"]["temperature"] == "provider_default"


def test_agent_config_update_can_save_append_mode(client):
    default_prompt = get_default_prompt("warren_buffett")
    response = client.put(
        "/agent-config/warren_buffett",
        json={
            "effective": {
                "system_prompt_text": f"{default_prompt}\n\nFocus on capital allocation.",
                "prompt_mode": "append",
                "model_name": None,
                "model_provider": None,
                "temperature": None,
                "max_tokens": None,
                "top_p": None,
                "fallback_model_name": None,
                "fallback_model_provider": None,
            }
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["persisted"]["system_prompt_override"] is None
    assert (
        payload["persisted"]["system_prompt_append"] == "Focus on capital allocation."
    )
    assert payload["effective"]["prompt_mode"] == "append"


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
