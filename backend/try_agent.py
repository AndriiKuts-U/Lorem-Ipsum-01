import sys
from typing import Any
from backend.agent_ai import agent, ChatDeps


def run(lat: float, lng: float, radius_m: int = 2000):
    prompt = (
        "Please find nearby supermarkets using your tool and list the top 5 with distances.\n"
        f"Coordinates: lat={lat}, lng={lng}, radius={radius_m} m."
    )

    deps = ChatDeps(lat=lat, lng=lng, radius_m=radius_m, types=["supermarket"])
    deps_any: Any = deps
    result = agent.run_sync(prompt, deps=deps_any)

    print("Model output:\n", result.output)
    try:
        # Print a short summary of messages to confirm tool usage
        msgs = result.all_messages()
        tool_calls = [m for m in msgs if "ToolCallPart" in str(m) or "ToolReturnPart" in str(m)]
        print(f"\nTool calls in run: {len(tool_calls)}")
        for m in tool_calls:
            print(m)
    except Exception:
        pass


if __name__ == "__main__":
    # Default coords around Košice
    lat = 48.7318664
    lng = 21.2431019
    radius = 2000
    if len(sys.argv) >= 3:
        lat = float(sys.argv[1])
        lng = float(sys.argv[2])
    if len(sys.argv) >= 4:
        radius = int(sys.argv[3])
    run(lat, lng, radius)
