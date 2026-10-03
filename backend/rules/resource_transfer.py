from collections.abc import Mapping
from typing import Any, Optional

from backend.rules.rules import ErrorCode, GameState

RESOURCE_TYPES = ("coal", "oil", "trash", "uranium")


def storage_capacity(plant_definition: Mapping[str, Any]) -> int:
    amounts = [plant_definition.get(resource, 0) for resource in RESOURCE_TYPES]
    required = [amount for amount in amounts if amount > 0]
    if not required:
        return 0
    fuel_amount = max(required) if plant_definition.get("hybrid") else sum(required)
    return fuel_amount * 2


def _stored_resource_slots(plant: dict[str, Any]) -> list[str]:
    return [
        resource
        for resource, amount in plant.get("resources", {}).items()
        for _ in range(amount)
    ]


def _find_player_plant(state: GameState, player: str, plant_id: int) -> Optional[dict[str, Any]]:
    plants = state.get("player_power_plants", {}).get(player, [])
    return next((plant for plant in plants if plant.get("plant_id") == plant_id), None)


def transfer_plant_resource(
    state: GameState,
    player: str,
    source_plant_id: int,
    source_slot: int,
    target_plant_id: int,
    target_slot: int,
    plant_definitions: Mapping[int, Mapping[str, Any]],
) -> ErrorCode:
    if source_plant_id == target_plant_id or source_slot < 0 or target_slot < 0:
        return ErrorCode.E_NOT_OKAY

    source = _find_player_plant(state, player, source_plant_id)
    target = _find_player_plant(state, player, target_plant_id)
    source_definition = plant_definitions.get(source_plant_id)
    target_definition = plant_definitions.get(target_plant_id)
    if not source or not target or not source_definition or not target_definition:
        return ErrorCode.E_NOT_OKAY

    source_slots = _stored_resource_slots(source)
    target_slots = _stored_resource_slots(target)
    if source_slot >= len(source_slots):
        return ErrorCode.E_NOT_OKAY
    if len(source_slots) > storage_capacity(source_definition):
        return ErrorCode.E_NOT_OKAY
    if len(target_slots) > storage_capacity(target_definition):
        return ErrorCode.E_NOT_OKAY
    if target_slot >= storage_capacity(target_definition) or target_slot < len(target_slots):
        return ErrorCode.E_NOT_OKAY

    resource = source_slots[source_slot]
    if resource not in RESOURCE_TYPES:
        return ErrorCode.E_NOT_OKAY

    source_resources = source.setdefault("resources", {})
    target_resources = target.setdefault("resources", {})
    source_resources[resource] -= 1
    target_resources[resource] = target_resources.get(resource, 0) + 1
    return ErrorCode.E_OK
