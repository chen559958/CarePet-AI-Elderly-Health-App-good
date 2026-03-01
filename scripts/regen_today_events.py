from __future__ import annotations

from datetime import datetime

from app.container import Container
from domain import reminder_engine


def main() -> None:
    container = Container.build()
    profile = container.user_repo.init_default_profile_if_empty()
    today = datetime.now().strftime("%Y-%m-%d")
    events = reminder_engine.generate_today_events(
        today,
        profile,
        container.drug_repo.list_active_drugs(),
    )
    container.reminder_repo.create_events_for_today(today, events)
    print(f"Generated {len(events)} events for {today}")


if __name__ == "__main__":
    main()
