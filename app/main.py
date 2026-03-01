import asyncio
import os
import flet as ft
from app.container import Container
from domain.watcher import reminder_watcher, pet_watcher
from domain.utils import get_now_taiwan
from domain import reminder_engine
from domain.services.auth_service import AuthService
from data.database import init_async_pool
from ui.pages.home_page import build_home
from ui.pages.records_page import build_records
from ui.pages.member_page import build_member
from ui.pages.add_drug_page import build_add_drug
from ui.pages.shop_page import build_shop
from ui.pages.task_page import build_tasks
from ui.pages.gallery_page import build_gallery
from ui.pages.login_page import build_login
from ui.pages.register_page import build_register
from ui.pages.add_bp_page import build_add_bp
from ui.styles import colors

async def main(page: ft.Page) -> None:
    print(">>> 進入 app/main.py:main() 函式")
    page.title = "GameMed MVP"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.bgcolor = colors.BACKGROUND
    
    # --- 消滅留白關鍵修改 ---
    page.padding = 0
    page.spacing = 0

    page.window.width = 450
    page.window.height = 850
    
    # 立即渲染 Loading 畫面，避免白屏
    print(">>> [Step 1/5] 正在顯示初始化 Loading 畫面...")
    loading_text = ft.Text("正在啟動系統 (1/5)...", color=colors.TEXT_PRIMARY)
    root_container = ft.Container(
        expand=True, 
        bgcolor=colors.BACKGROUND,
        content=ft.Column([
            ft.ProgressRing(color=colors.PRIMARY),
            loading_text
        ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
    )
    page.add(root_container)
    page.update()

    print(">>> [Step 2/5] 正在初始化資料庫連接池...")
    loading_text.value = "正在連線資料庫 (2/5)..."
    page.update()
    
    if os.getenv("FORCE_SQLITE", "").lower() == "true":
        print(">>> DEBUG: 檢測到 FORCE_SQLITE=true，跳過 Asyncpg 初始化。")
    else:
        try:
            # Initialize Async DB Pool with a 15s timeout
            await asyncio.wait_for(init_async_pool(), timeout=15.0)
            print(">>> [Step 2/5] 資料庫連線初始化成功。")
        except asyncio.TimeoutError:
            print(">>> [Step 2/5] 警告: 資料庫初始化超時 (15秒)，將嘗試降級。")
        except Exception as e:
            print(f">>> [Step 2/5] 資料庫初始化發生異常: {e}")
    
    print(">>> [Step 3/5] 正在獲取系統組件 (Container)...")
    loading_text.value = "正在載入系統組件 (3/5)..."
    page.update()
    
    try:
        # Run synchronous Container.get_instance in a thread to avoid blocking Flet
        container = await asyncio.wait_for(asyncio.to_thread(Container.get_instance), timeout=20.0)
        auth_service = container.auth_service
        print(">>> [Step 3/5] 系統組件載入完成。")
    except asyncio.TimeoutError:
        print(">>> [Step 3/5] 錯誤: 系統組件初始化超時 (20秒)。")
        root_container.content = ft.Text("❌ 系統初始化超時，請檢查網路或環境。", color="red")
        page.update()
        return
    except Exception as e:
        print(f">>> [Step 3/5] Container 獲取失敗: {e}")
        import traceback
        traceback.print_exc()
        root_container.content = ft.Text(f"❌ 系統組件失敗: {e}", color="red")
        page.update()
        return


    # Connect notification backend to AlertDialog
    def show_app_notification(title, body):
        def close_dlg(e):
            dlg.open = False
            page.update()

        def go_to_tasks(e):
            dlg.open = False
            # Close first, then navigate
            page.update()
            page.go("/tasks")

        dlg = ft.AlertDialog(
            title=ft.Text(title, weight="bold"),
            content=ft.Text(body),
            actions=[
                ft.TextButton("知道了", on_click=close_dlg),
                ft.TextButton("前往用藥清單", on_click=go_to_tasks),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        page.overlay.append(dlg)
        dlg.open = True
        page.update()

    if hasattr(container.notification_service.backend, "on_notify"):
        container.notification_service.backend.on_notify = show_app_notification


    state = {"route": "/", "is_authenticated": False, "navigating": False}
    
    print(">>> [Step 4/5] 正在還原登入狀態...")
    loading_text.value = "正在檢查登入狀態 (4/5)..."
    page.update()
    
    state = {"route": "/", "is_authenticated": False, "navigating": False}
    
    try:
        # Also run restore_session in a thread to be safe
        session_restored = await asyncio.wait_for(asyncio.to_thread(auth_service.restore_session), timeout=10.0)
        if session_restored:
            state["is_authenticated"] = True
            print(f">>> [Step 4/5] Session 已還原。")
        else:
            print(f">>> [Step 4/5] 無現有 Session。")
    except Exception as e:
        print(f">>> [Step 4/5] Session 還原異常: {e}")

    print(">>> [Step 5/5] 正在進入主畫面...")
    loading_text.value = "即將進入系統 (5/5)..."
    page.update()


    async def navigate(e):
        if state["navigating"]:
            print(f"DEBUG: Navigation already in progress, skipping {e}")
            return
        
        route = e.route if hasattr(e, "route") else (e if isinstance(e, str) else "/")
        state["route"] = route
        state["navigating"] = True
        print(f"DEBUG: Navigating to {route}, auth={state['is_authenticated']}")
        
        try:
            content = None
            path = route.split("?", 1)[0] if "?" in route else route
            
            # Authentication Check
            if not state["is_authenticated"]:
                if path == "/register":
                    content = await build_register(page, handle_register, lambda: page.go("/login"))
                else:
                    content = await build_login(page, handle_login, lambda: page.go("/register"))
            else:
                # Page Factory
                if path == "/": content = await build_home(page)
                elif path == "/records": content = await build_records(page)
                elif path == "/member": content = await build_member(page, handle_logout)
                elif path == "/add_drug": content = await build_add_drug(page)
                elif path == "/shop": content = await build_shop(page)
                elif path == "/tasks": content = await build_tasks(page)
                elif path == "/add_bp": content = await build_add_bp(page)
                elif path == "/gallery": content = await build_gallery(page)
            
            if content:
                print(f">>> DEBUG: 已找到路徑 {path} 的內容，正在更新 root_container...")
                root_container.content = content
                try:
                    root_container.update() 
                    page.update()
                    print(f">>> DEBUG: {path} 頁面更新指令已發送。")
                except Exception as e:
                    print(f">>> DEBUG: 更新 UI 時發生異常: {e}")
            else:
                print(f">>> DEBUG: 警告: 路徑 {path} 未返回任何內容 (content is None)")
        except Exception as ex:
             print(f">>> DEBUG: Navigation Error: {ex}")
             import traceback
             traceback.print_exc()
        finally:
            state["navigating"] = False

    
    async def handle_login(phone: str, password: str) -> tuple[bool, str]:
        """Handle login attempt."""
        success, message = auth_service.login(phone, password)
        if success:
            state["is_authenticated"] = True
            # user = auth_service.get_current_user()
            # if user:
            #     page.run_task(start_user_services, user.id)
            await navigate("/")
        return success, message
    
    async def handle_register(phone: str, password: str) -> tuple[bool, str]:
        """Handle registration attempt."""
        success, message = auth_service.register(phone, password)
        if success:
            state["is_authenticated"] = True
            user = auth_service.get_current_user()
            if user:
                await start_user_services(user.id)
            await navigate("/")
        return success, message
    
    async def handle_logout(_=None):
        """Handle logout."""
        print("DEBUG: handle_logout called in main.py")
        auth_service.logout()
        state["is_authenticated"] = False
        await navigate("/login")

    page.on_route_change = navigate
    
    # 視窗縮放時自動重新渲染 (優化版：減少頻繁觸發)
    resize_timer = None
    # 視窗縮放時僅通知重新繪製，不再重複觸發導航 (避免頻繁 load_dashboard 導致卡頓)
    async def on_resize(e):
        try:
            print(f"DEBUG: Window resized to {page.window.width}x{page.window.height}")
            page.update()
        except Exception:
            pass

    page.on_resized = on_resize

    # Subscribe to watchers - REMOVED GLOBAL SUBSCRIPTION
    # Watchers are now handled locally within HomeView and TaskView
    # to prevent page.go() loops.

    # Trigger missed dose check on startup
    async def start_user_services(user_id: int):
        """啟動與使用者相關的背景服務"""
        print(f"DEBUG: start_user_services initiated for User {user_id}")
        # Ensure default data exists for the user
        try:
            import asyncio
            print("DEBUG: Initializing default profile...")
            await asyncio.to_thread(container.user_repo.init_default_profile_if_empty, user_id)
            print("DEBUG: Initializing default pet...")
            await asyncio.to_thread(container.pet_repo.init_default_pet_if_empty, user_id)
            print("DEBUG: Initializing demo drug data...")
            await asyncio.to_thread(container.drug_repo.init_demo_data, user_id)
            
            # Initial checks
            print("DEBUG: Checking daily missed doses...")
            await asyncio.to_thread(container.caregiver_service.check_daily_missed_dose, user_id)
            print("DEBUG: Checking caregiver notifications...")
            await asyncio.to_thread(container.caregiver_service.check_and_notify_caregivers, user_id)
            
            # Start periodic check
            print("DEBUG: Starting periodic notification check...")
            asyncio.create_task(periodic_notification_check(user_id))
            print("DEBUG: start_user_services completed successfully")
        except Exception as e:
            print(f"ERROR in start_user_services: {e}")
            import traceback
            traceback.print_exc()

    async def periodic_notification_check(user_id: int):
        """每分鐘檢查是否有需要通知的藥品"""
        import asyncio
        try:
            while True:
                try:
                    # 只有在已登入且與當前 user_id 符合時才檢查
                    if not state["is_authenticated"]:
                         break
                         
                    current_user = auth_service.get_current_user()
                    if not current_user or current_user.id != user_id:
                         break

                    now = get_now_taiwan()
                    today_str = now.strftime("%Y-%m-%d")
                    
                    # 獲取使用者設定
                    profile = await asyncio.to_thread(container.user_repo.get_profile, user_id)
                    if profile and profile.notifications_enabled:
                        events = await asyncio.to_thread(container.reminder_repo.list_today_events, user_id, today_str)
                        for ev in events:
                            # 檢查 scheduled (且時間已到)
                            if ev.status == "scheduled":
                                if ev.planned_time <= now:
                                    drug = await asyncio.to_thread(container.drug_repo.get_by_id, user_id, ev.drug_id)
                                    drug_name = drug.drug_name if drug else "藥物"
                                    
                                    # 發送通知
                                    container.notification_service.schedule(
                                        ev.id, 
                                        ev.planned_time,
                                        "用藥提醒通知 💊",
                                        f"親愛的，該吃藥囉！\n藥名：{drug_name}\n預計時間：{ev.planned_time.strftime('%H:%M')}"
                                    )
                                    
                                    # 更新狀態為 notified
                                    await asyncio.to_thread(container.reminder_repo.update_status, user_id, ev.id, "notified")
                                    # NOTIFY WATCHER to update UI (HomeView/TaskView will pick this up)
                                    reminder_watcher.notify()
                    
                except asyncio.CancelledError:
                    print(f"DEBUG: periodic_check cancelled safely.")
                    return
                except Exception as e:
                    print(f"ERROR in periodic_notification_check logic for User {user_id}: {e}")
                
                await asyncio.sleep(60) # 每分鐘檢查一次
        except asyncio.CancelledError:
            print(f"DEBUG: periodic_notification_check for User {user_id} cancelled.")

    # Initial render
    print(f"DEBUG: Starting initial render. is_authenticated={state['is_authenticated']}")
    if state["is_authenticated"]:
        # user = auth_service.get_current_user()
        # if user:
        #     print(f"DEBUG: Authenticated user found: {user.id}. Starting user services in background.")
        #     page.run_task(start_user_services, user.id)
        print("DEBUG: Triggering initial navigation to /")
        await navigate("/")
    else:
        print("DEBUG: Not authenticated, navigating to /login")
        await navigate("/login")

if __name__ == "__main__":
    import os
    # Ensure assets directory is correctly located relative to this file
    # main.py is in app/, so we need to go up one level to find assets/
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    assets_path = os.path.join(base_dir, "assets")
    
    print(f"DEBUG: Setting assets_dir to {assets_path}")
    ft.app(target=main, assets_dir=assets_path)

