import os
from pathlib import Path
from typing import Any

import pytest
from dotenv import load_dotenv

from backend.agent_ai import agent, ChatDeps


pytestmark = pytest.mark.integration
load_dotenv()


def _env_ok() -> bool:
    return bool(os.getenv("OPENAI_API_KEY"))


@pytest.mark.skipif(not _env_ok(), reason="Requires OPENAI_API_KEY (and optional Qdrant)")
def test_agent_calls_extract_tool(tmp_path: Path, caplog: pytest.LogCaptureFixture) -> None:
    deps = ChatDeps(
        lat=48.7318664,
        lng=21.2431019,
        radius_m=1500,
        types=["supermarket"],
        thread_id="test-thread-extract",
    )
    deps_any: Any = deps

    prompt = "Shopping list: 2kg tomatoes, milk, bread, chicken breasts"
    caplog.set_level("INFO")
    result = agent.run_sync(prompt, deps=deps_any)

    msgs = "\n".join(str(m) for m in result.all_messages())
    assert (
        "tool_name='extract_shopping_list'" in msgs or 'tool_name="extract_shopping_list"' in msgs
    ), "Agent did not call extract_shopping_list tool"

    # Output should include some extracted grocery-related words
    out = str(result.output).lower()
    assert any(x in out for x in ["tomato", "milk", "bread", "chicken"])

    # Logs should include invocation and item count; also print them for visibility
    log_text = "\n".join(caplog.messages)
    print("\n--- agent.tools logs ---\n" + log_text + "\n--- end logs ---\n")
    assert "extract_shopping_list called" in log_text
    assert "parsed items_count" in log_text or "extracted" in log_text
