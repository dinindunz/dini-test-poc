from datetime import datetime
from pathlib import Path
import json

def save_metrics_log(user_prompt, metrics_summary, system_prompt_template=None, include_traces_content=True):
    """Save metrics summary to a JSON file in logs directory"""
    # Create logs directory if it doesn't exist
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)

    # Create timestamp in dd/mm/yy-hh:mm format
    timestamp = datetime.now().strftime("%d-%m-%y-%H-%M")

    # Sanitise user prompt for filename (remove special characters)
    sanitised_prompt = "".join(c for c in user_prompt if c.isalnum() or c in (' ', '-', '_')).rstrip()
    sanitised_prompt = sanitised_prompt.replace(' ', '_')[:50]  # Limit length and replace spaces

    # Create filename
    filename = f"{timestamp}-{sanitised_prompt}.json"
    file_path = logs_dir / filename

    # Filter metrics_summary to exclude message content if needed
    filtered_metrics = metrics_summary.copy() if isinstance(metrics_summary, dict) else metrics_summary

    if not include_traces_content and isinstance(filtered_metrics, dict):
        # Remove message content from traces to reduce log size
        if 'traces' in filtered_metrics:
            for trace in filtered_metrics['traces']:
                if 'message' in trace:
                    trace['message'] = "[CONTENT_EXCLUDED]"
                if 'children' in trace:
                    for child in trace['children']:
                        if 'message' in child:
                            child['message'] = "[CONTENT_EXCLUDED]"

    # Prepare log data
    log_data = {
        "timestamp": datetime.now().isoformat(),
        "user_prompt": user_prompt,
        "system_prompt_template": system_prompt_template,
        "metrics_summary": filtered_metrics,
        "formatted_timestamp": timestamp,
        "traces_content_included": include_traces_content
    }

    try:
        # Save to JSON file
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(log_data, f, indent=2, ensure_ascii=False)

        content_status = "with traces content" if include_traces_content else "without traces content"
        print(f"📊 Metrics logged to: {file_path} ({content_status})")
        return str(file_path)
    except Exception as e:
        print(f"⚠️  Failed to save metrics log: {e}")
        return None