import pytest
from datetime import datetime, timezone, timedelta
from domain.reminder_engine import compute_planned_time, generate_today_events
from domain.models import UserProfile, DrugItem

def test_compute_planned_time_after_meal():
    # Setup
    date_str = "2023-10-27"
    base_hhmm = "08:00"
    timing = "after_meal"
    
    # Execute
    result = compute_planned_time(date_str, base_hhmm, timing)
    
    # Verify: 08:00 + 30min = 08:30 (aware)
    expected = datetime(2023, 10, 27, 8, 30, tzinfo=timezone(timedelta(hours=8)))
    assert result == expected

def test_compute_planned_time_anytime():
    # Setup
    date_str = "2023-10-27"
    base_hhmm = "08:00"
    timing = "anytime"
    
    # Execute
    result = compute_planned_time(date_str, base_hhmm, timing)
    
    # Verify: 08:00 + 0min = 08:00 (aware)
    expected = datetime(2023, 10, 27, 8, 0, tzinfo=timezone(timedelta(hours=8)))
    assert result == expected

def test_generate_today_events():
    # Setup
    user = UserProfile(
        id=1, name="Test", phone=None, email=None,
        breakfast_time="08:00", lunch_time="12:00", dinner_time="18:00", sleep_time="22:00",
        haptics_enabled=True, snooze_minutes=10, gentle_mode=True
    )
    drugs = [
        DrugItem(
            id=101, drug_name="Aspirin", usage_method="口服", intake_timing="after_meal", 
            intake_periods=["breakfast", "dinner"], pills_per_intake=1, active=True
        ),
        DrugItem(
            id=102, drug_name="Vitamin", usage_method="口服", intake_timing="anytime", 
            intake_periods=["lunch"], pills_per_intake=1, active=True
        )
    ]
    date_str = "2023-10-27"
    
    # Execute
    events = generate_today_events(date_str, user, drugs)
    
    # Verify
    # Event 1: Drug 101, Breakfast (08:00) + 30m = 08:30
    # Event 2: Drug 101, Dinner (18:00) + 30m = 18:30
    # Event 3: Drug 102, Lunch (12:00) + 0m = 12:00
    assert len(events) == 3
    
    # Sort by time to be deterministic
    sorted_events = sorted(events, key=lambda x: x[1])
    
    tz = timezone(timedelta(hours=8))
    assert sorted_events[0][0] == 101
    assert sorted_events[0][1] == datetime(2023, 10, 27, 8, 30, tzinfo=tz)
    
    assert sorted_events[1][0] == 102
    assert sorted_events[1][1] == datetime(2023, 10, 27, 12, 0, tzinfo=tz)
    
    assert sorted_events[2][0] == 101
    assert sorted_events[2][1] == datetime(2023, 10, 27, 18, 30, tzinfo=tz)

