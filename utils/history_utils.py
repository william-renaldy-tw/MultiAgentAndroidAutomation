def get_recent_updates(history: list[dict], last_marker_type: str = "agent_selection") -> str:
    """
    Extracts messages from history after the last occurrence of a specified type (default: 'agent_selection').
    Filters out 'screen_image' messages unless they are part of the recent changes.
    
    Args:
        history (list[dict]): Full chat history.
        last_marker_type (str): Message type to mark the cutoff point (default is agent selection event).
    
    Returns:
        str: Formatted string of recent history entries.
    """
    last_index = 0
    for i in reversed(range(len(history))):
        if history[i]["type"] == last_marker_type:
            last_index = i + 1
            break

    recent = history[last_index:]

    return recent