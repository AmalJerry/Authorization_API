import os
import json
from pathlib import Path

ENV_PATH = Path(__file__).resolve().parent / "command_env.json"

def load_command_env():
    if ENV_PATH.exists():
        with open(ENV_PATH, "r") as f:
            return json.load(f)
    return []

def save_command_env(commands):
    with open(ENV_PATH, "w") as f:
        json.dump(commands, f)

def add_command_to_env(command_string, device_id, vehicle_id):
    current_env = load_command_env()
    current_env.append({
        "device_id": device_id,
        "vehicle_id": vehicle_id,
        "command_string": command_string,
        "is_sent": False
    })
    save_command_env(current_env)

def mark_command_as_sent(command_string):
    commands = load_command_env()
    updated = []
    for cmd in commands:
        if cmd["command_string"] == command_string:
            cmd["is_sent"] = True
        updated.append(cmd)
    save_command_env(updated)

def get_unsent_commands_for_device(device_id):
    return [
        cmd for cmd in load_command_env()
        if cmd["device_id"] == device_id and not cmd["is_sent"]
    ]
