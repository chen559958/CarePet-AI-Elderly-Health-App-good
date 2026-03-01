# GameMed Flet App – Engineering Blueprint (4 Tabs)

**Document goal:** actionable build plan derived from the MVP spec you supplied, with fixed directory skeleton, file-level responsibilities, Flet control trees (focus on HomePage), and the TaskWall watcher/data strategy. All timings use the rules from the spec (meal +45 min, snooze +10, missed after 60, 5 s undo window).

---
## 1. High-Level Architecture
- **Pattern:** MVVM + clean-ish layering.
- **Entry point:** `app/main.py` bootstraps Flet, dependency container, DB init/migrations, and notification permission checks.
- **Layers:**
  - `ui/*`: Flet Pages + reusable controls, viewmodels mediate between UI and domain.
  - `domain/*`: pure logic (engines, aggregates, state machines) with unit tests in `tests/domain`.
  - `data/*`: SQLite repositories + migration helpers.
  - `services/*`: device integrations (notifications, haptics, image picker, undo manager).
- **Concurrency:** Single asyncio loop provided by Flet; background jobs (e.g., reminder regeneration, missed detection) run via `asyncio.create_task` triggered by lifecycle hooks.
- **Tabs:** Bottom nav includes `Home`, `Records`, `Shop`, `Member` (4 tabs, Home as default).

---
## 2. Directory & File Map
```
GameMed/
├─ app/
│  ├─ main.py
│  ├─ routes.py
│  └─ container.py
├─ data/
│  ├─ database.py
│  ├─ schema.sql
│  ├─ migrations/
│  │  └─ 0001_initial.sql
│  └─ repositories/
│     ├─ user_repo.py
│     ├─ drug_repo.py
│     ├─ reminder_repo.py
│     ├─ log_repo.py
│     ├─ points_repo.py
│     ├─ pet_repo.py
│     ├─ inventory_repo.py
│     └─ undo_repo.py
├─ domain/
│  ├─ models.py
│  ├─ reminder_engine.py
│  ├─ point_engine.py
│  ├─ pet_engine.py
│  ├─ reminder_state_machine.py
│  └─ validators.py
├─ services/
│  ├─ notification_service.py
│  ├─ image_service.py
│  ├─ haptics_service.py
│  └─ undo_manager.py
├─ ui/
│  ├─ pages/
│  │  ├─ login_page.py
│  │  ├─ register_page.py
│  │  ├─ home_page.py
│  │  ├─ blood_pressure_page.py
│  │  ├─ add_drug_page.py
│  │  ├─ records_page.py
│  │  ├─ shop_page.py
│  │  ├─ member_page.py
│  │  └─ pet_collection_page.py
│  ├─ viewmodels/
│  │  ├─ auth_viewmodel.py
│  │  ├─ home_viewmodel.py
│  │  ├─ reminder_viewmodel.py
│  │  ├─ bp_viewmodel.py
│  │  ├─ drug_viewmodel.py
│  │  ├─ records_viewmodel.py
│  │  ├─ shop_viewmodel.py
│  │  ├─ member_viewmodel.py
│  │  └─ pet_viewmodel.py
│  ├─ components/
│  │  ├─ app_scaffold.py
│  │  ├─ pet_panel.py
│  │  ├─ stat_chip.py
│  │  ├─ quick_action_card.py
│  │  ├─ task_card.py
│  │  ├─ task_wall.py
│  │  ├─ undo_snackbar.py
│  │  ├─ big_button.py
│  │  └─ responsive_layout.py
│  └─ styles/
│     ├─ colors.py
│     ├─ typography.py
│     └─ spacing.py
├─ tests/
│  ├─ domain/
│  │  ├─ test_reminder_engine.py
│  │  ├─ test_point_engine.py
│  │  └─ test_pet_engine.py
│  └─ ui/
│     └─ test_task_wall.py
├─ scripts/
│  └─ regen_today_events.py
├─ assets/
│  ├─ images/
│  └─ fonts/
└─ README.md
```

### 2.1 File Responsibilities & Key Classes
| File | Classes/Functions | Notes |
| --- | --- | --- |
| `app/main.py` | `launch()` | Entry point; sets up DB, DI container, registers page routes, seeds default records, triggers `ReminderOrchestrator` at startup. |
| `app/routes.py` | `register_routes(app)` | Central place to bind Flet routes → page builders; ensures deep links (notification payload) land on Home/Task view. |
| `app/container.py` | `Container.build()` | Very small dependency injector returning singletons for repos/services/viewmodels. |
| `data/database.py` | `get_conn()`, `init_db()`, `run_migrations()` | Wraps sqlite3 connection, auto applies `schema.sql` when DB nonexistent, tracks `PRAGMA user_version`. |
| `data/schema.sql` | (DDL) | Exact schema from spec, stored once for init and tests. |
| `data/repositories/*` | e.g., `UserRepository`, `ReminderRepository` | Each repo isolates SQL; returns dataclasses defined in `domain/models.py`. `ReminderRepository.create_events_for_today(date)` enforces idempotence via unique constraint (`drug_id`, `planned_time`). |
| `domain/models.py` | `UserProfile`, `DrugItem`, `ReminderEvent`, etc. | Dataclasses mirroring DB to keep domain pure. |
| `domain/reminder_engine.py` | `compute_planned_time`, `generate_today_events`, `apply_snooze`, `judge_missed` | Pure functions; covered by tests. |
| `domain/reminder_state_machine.py` | `ReminderStateMachine.apply(event, command)` | Encodes allowed transitions from section 4 of spec; emits domain events for logging/undo. |
| `domain/point_engine.py` | `PointEngine` | Awards/penalties based on triggers, writes only through repo abstraction. |
| `domain/pet_engine.py` | `PetEngine` | Updates pet mood/stamina/level; honors gentle-mode clamp rules. |
| `services/notification_service.py` | `LocalNotificationService` | Wraps Flet/Flutter notification plugin; ensures `schedule`, `cancel`, `reschedule`, `handle_click` exist. |
| `services/image_service.py` | `ImageService.pick_from_camera/gallery`, `save_to_storage` | Handles permissions. |
| `services/haptics_service.py` | `HapticsService.tap/success/warning` | No-ops if disabled. |
| `services/undo_manager.py` | `UndoManager.create_action`, `UndoManager.rollback` | Persists action payloads via `UndoRepository`; TTL enforcement in repo. |
| `ui/components/*` | `AppScaffold`, `PetPanel`, etc. | Each returns a Flet `Control`. `TaskWall` handles responsive columns. |
| `ui/pages/*` | `ViewClass(flet.Page)` | Build page layout; rely on viewmodels for logic. |
| `ui/viewmodels/*` | e.g., `HomeViewModel`, `ShopViewModel` | Observable objects exposing state to controls; talk to domain/ repos via container. |
| `scripts/regen_today_events.py` | CLI helper | Reruns event generation (dev utility). |

---
## 3. Dependency & Flow Overview
1. **App start:**
   - `main.launch()` → `init_db()` → `run_migrations()` (noop if user_version matches).
   - DI container instantiates repos/services, injecting sqlite connection factory.
   - `ReminderOrchestrator` (inside `home_viewmodel`) runs: `ReminderRepository.create_events_for_today(today)` + `NotificationService.schedule(...)` + `ReminderRepository.mark_missed_overdue(now)`.
2. **UI interaction:**
   - Controls bind to ViewModel actions returning async coroutines (Flet `page.run_async`).
3. **Undo pipeline:**
   - After DB mutation (e.g., `mark_taken(event)`), viewmodel registers action via `UndoManager.create_action(payload)`; UI displays `UndoSnackbar` with countdown.
   - Snackbar button triggers `UndoManager.rollback(action_id, rollback_fn)`.

---
## 4. Flet HomePage Control Tree (Responsive)
### 4.1 Base layout
```
HomePage (Page)
└─ AppScaffold(bottom_nav=Home/Records/Shop/Member)
   └─ ResponsiveLayout(
         phone=Column,
         tablet=Row,
         desktop=Row)
      Phone Column (spacing=16, padding=24)
      ├─ PetPanelCard (Container, rounded 24)
      │  ├─ Row
      │  │  ├─ PetAvatar (Image/Animated)
      │  │  └─ Column
      │  │     ├─ Text(pet name + level)
      │  │     ├─ Row [StatChip mood, StatChip stamina]
      │  │     └─ BigButton \"餵食\" (opens FeedDialog)
      ├─ QuickActionsRow (GridView adapt columns=2)
      │  ├─ QuickActionCard \"量血壓\"
      │  ├─ QuickActionCard \"新增藥品\"
      │  └─ QuickActionCard \"下一個提醒\" (shows soonest event)
      └─ TaskWall (see below)
```
### 4.2 Tablet breakpoint (≥480dp)
```
ResponsiveLayout.tablet → Row
├─ Expanded(0.45) → Column
│  ├─ PetPanelCard
│  └─ QuickActionsGrid
└─ Expanded(0.55) → TaskWall
```
### 4.3 Desktop breakpoint (≥900dp)
```
Row(padding=32)
├─ Container(width=360) → same as tablet left column but with extra StatChips (point balance, next reminder)
└─ Expanded → TaskWall with wider cards (Card elevation 6, corner 20)
```
### 4.4 TaskWall Control Tree
```
TaskWall(Container)
└─ Column
   ├─ Header Row
   │  ├─ Text(\"今日任務\")
   │  └─ TextButton(\"刷新\") – manual trigger
   ├─ RecycleView(ListView) bound to HomeViewModel.events
   │  ├─ For each ReminderEvent → TaskCard
   │      ├─ Column
   │      │  ├─ Text(drug_name)
   │      │  ├─ Text(\"早餐後 · 2 錠\")
   │      │  └─ StatusChip
   │      └─ Row(spacing=12)
   │          ├─ BigButton(\"已用藥\")
   │          └─ OutlinedBigButton(\"延後\")
   └─ EmptyState (if no events)
```
- `TaskCard` uses large tap targets (≥56 height) and haptics on interactions.
- `UndoSnackbar` is injected at `AppScaffold` level so any page action can surface it.

---
## 5. ViewModel Contracts (Key ones)
### 5.1 `HomeViewModel`
- **State:** `events: List[ReminderEventVM]`, `pet_summary`, `point_balance`, `next_event`.
- **Methods:**
  - `async prepare()` – called on page mount → ensures today’s events exist, subscribes to watchers.
  - `async mark_taken(event_id)` – orchestrates state machine, logs, points, pet engine, notifications, undo action.
  - `async snooze(event_id)` – updates planned time (+`profile.snooze_minutes`), reschedules notification, undo action.
  - `async refresh()` – reload events from repo and re-run `mark_missed_overdue`.

### 5.2 `ReminderViewModel`
- Wraps `ReminderStateMachine` to guarantee legal transitions.
- Publishes `ReminderChanged` events (asyncio.Queue) consumed by TaskWall watcher.

### 5.3 `ShopViewModel`
- Keeps `inventory`, `shop_items`, `point_balance`.
- `buy_item(item_id)` writes ledger (-cost), inventory ++, undo action for refund.

### 5.4 `MemberViewModel`
- Loads/saves `UserProfile`, toggles haptics, gentle mode, snooze length.
- On profile change, emits `ProfileChanged` event to `HomeViewModel` (regenerate reminders for today).

---
## 6. TaskWall Data & Watcher Strategy
Goal: keep TaskWall synced with DB changes (taken, snoozed, missed, new events) without manual refresh spam.

1. **Watcher sources:**
   - `ReminderRepository.watch_today_events()` – yields async stream of `(event_id, mutation_type)` using SQLite triggers writing to `undo_actions` or via a lightweight polling loop (every 5s) that compares `updated_at`.
   - `ReminderViewModel.command_queue` – emits immediate updates for local actions (taken/snoozed) before DB watcher fires (optimistic UI).
   - `ProfileChanged` queue – when meal schedule changes, triggers `RegenerateTodayEventsJob`.
2. **Implementation detail:**
   - `HomeViewModel.prepare()` spawns `asyncio.create_task(self._taskwall_watcher())`.
   - `_taskwall_watcher` merges multiple async generators using `asyncio.Queue` (`asyncio.create_task` for each source, pushing messages).
   - On message, call `ReminderRepository.list_today_events()`; transform rows to view models and push through `events_signal.on_next(list)` for UI binding.
3. **Missed detection:**
   - Polling job `mark_missed_overdue(now)` runs every 10 minutes (or when `page.on_resume`) to move events to `missed` and fire watcher message.
4. **Undo integration:**
   - When `UndoManager.rollback` completes, it writes `reminder_events.updated_at = now`, ensuring watcher sees the change and UI rebinds automatically.
5. **Offline safety:**
   - All watchers degrade to manual refresh (the “刷新” button) if the async task fails; button displays toast when watchers restart.

Pseudo-flow:
```python
async def _taskwall_watcher(self):
    queue = asyncio.Queue()
    tasks = [
        asyncio.create_task(self._consume_repo_events(queue)),
        asyncio.create_task(self._consume_local_commands(queue)),
    ]
    while True:
        await queue.get()
        events = self.reminder_repo.list_today_events()
        self.events_signal.emit(map_to_vm(events))
```

---
## 7. Undo Action Payload Templates
| Scenario | Payload | Rollback Steps |
| --- | --- | --- |
| `mark_taken` | `{event_id, prev_status, prev_action_time, log_id, ledger_id, pet_delta}` | Set event back to `prev_status`, delete log row, delete ledger row, apply inverse pet delta, reschedule notification if needed. |
| `snooze` | `{event_id, prev_planned_time, prev_status, prev_notification_id}` | Update planned time, decrement snooze_count, reschedule original notification. |
| `add_drug` | `{drug_id, created_event_ids}` | Delete drug, cascade delete generated events/logs, cancel notifications. |
| `buy_item` | `{order_id, ledger_id, inventory_delta}` | Delete order, delete ledger row, decrement inventory. |
| `bp_entry` | `{log_id, ledger_id}` | Delete log, delete ledger row. |

UndoManager enforces 5-second expiry; UI countdown uses `asyncio.sleep` with `page.snack_bar` updated each second.

---
## 8. Page-Level Notes (4 Tabs)
- **HomePage:** described above; hosts pet panel, quick actions, TaskWall, UndoSnackbar.
- **RecordsPage:** Calendar (`flet.CalendarDatePicker` in read-only) + two `ListView`s (blood pressure, medication logs). Provides optional filter chip for statuses. Uses `RecordsViewModel` bridging `LogRepo`.
- **ShopPage:** `Tabs` for categories; each tab shows `ResponsiveGridView` of `ShopItemCard`s with `BigButton("購買")`. Shows `PointBalance` chip pinned to top-right.
- **MemberPage:** Form controls for profile inputs, toggles (haptics, gentle mode, snooze length). Includes caretaker placeholders (disabled until Phase 2). On save, triggers `MemberViewModel.save_profile()` which emits `ProfileChanged` event.
- **Non-tab pages (Login/Register/BP/AddDrug/PetCollection)** push onto navigation stack but keep bottom nav hidden to avoid duplicate bars.

---
## 9. Reminder Generation Orchestration
1. `HomeViewModel.prepare()` obtains `UserProfile` (blocking call) → ensures `init_default_profile_if_empty()`.
2. Calls `ReminderRepository.create_events_for_today(today)`:
   - Query `drugs WHERE active=1`.
   - For each, compute planned times using `ReminderEngine.compute_planned_time(date, profile[period], intake_timing)`.
   - Insert `reminder_events` rows (skip duplicates via unique constraint or manual existence check).
   - Immediately call `NotificationService.schedule` per new event and store `notification_id`.
3. After creation, call `ReminderRepository.mark_missed_overdue(now)` to transition stale events.
4. Watcher refresh displays events sorted by `planned_time`.

---
## 10. Testing Hooks
- `tests/domain/test_reminder_engine.py` includes parametrized cases for each meal period + user schedule to ensure +45 min logic.
- `tests/domain/test_point_engine.py` verifies ledger delta sums.
- `tests/ui/test_task_wall.py` uses Flet’s test harness to simulate button taps and confirm snackbar/undo flows.
- Add `FakeNotificationService` + `FakeUndoRepo` fixtures for deterministic tests.

---
## 11. Developer Workflow Checklist
1. `poetry install` (or pip) for dependencies.
2. `python -m app.main` to run in debug; Flet hot-reload handles UI.
3. First launch seeds DB via `init_db` and inserts default pet + sample shop items.
4. Use `scripts/regen_today_events.py` to regenerate events after editing schema or data for QA.
5. Before release, run `pytest` to cover domain logic, then `flet pack` for Android/iOS.

---
This blueprint locks the 4-tab navigation, explicit folder/file layout, HomePage control tree, and TaskWall watcher strategy so the engineering team can start implementation without further structural decisions.

