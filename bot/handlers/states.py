from __future__ import annotations

"""Finite-state machine states for the car-selection conversation."""

from aiogram.fsm.state import State, StatesGroup


class CarSetup(StatesGroup):
    waiting_make = State()
    waiting_model = State()
    waiting_year = State()
    waiting_category = State()
    waiting_season = State()
    waiting_style = State()
    waiting_budget = State()
