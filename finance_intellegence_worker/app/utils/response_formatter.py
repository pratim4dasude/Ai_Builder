def format_agent_response(agent_name: str, result: dict) -> dict:
    return {
        "agent": agent_name,
        "status": "completed",
        "result": result,
    }


def format_error(agent_name: str, error: str) -> dict:
    return {
        "agent": agent_name,
        "status": "failed",
        "error": error,
    }