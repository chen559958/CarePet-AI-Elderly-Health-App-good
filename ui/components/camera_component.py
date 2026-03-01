from __future__ import annotations
import asyncio
import base64
import os
import cv2
import flet as ft
from ui.styles import colors

class CameraComponent(ft.Column):
    def __init__(self, on_capture):
        super().__init__()
        self.on_capture = on_capture
        self.is_running = False
        self.cap = None
        
        # UI Elements
        self.img_preview = ft.Image(
            src_base64="",
            width=400,
            height=300,
            fit=ft.ImageFit.CONTAIN,
            border_radius=10,
        )
        
        self.status_text = ft.Text("正在啟動攝影機...", color=colors.TEXT_PRIMARY)
        
        self.capture_btn = ft.ElevatedButton(
            "拍照",
            icon=ft.icons.CAMERA,
            on_click=self.take_photo,
            color=colors.WHITE,
            bgcolor=colors.SECONDARY,
            disabled=True
        )
        
        self.cancel_btn = ft.TextButton(
            "取消",
            on_click=self.stop_camera,
        )
        
        self.controls = [
            ft.Container(
                content=self.img_preview,
                border=ft.border.all(1, colors.PRIMARY),
                border_radius=10,
                alignment=ft.alignment.center,
                bgcolor=colors.BLACK,
            ),
            ft.Row([self.status_text], alignment=ft.MainAxisAlignment.CENTER),
            ft.Row([self.capture_btn, self.cancel_btn], alignment=ft.MainAxisAlignment.CENTER),
        ]
        self.alignment = ft.MainAxisAlignment.CENTER
        self.horizontal_alignment = ft.CrossAxisAlignment.CENTER
        self.spacing = 20

    def did_mount(self):
        self.page.run_task(self.start_camera)

    async def start_camera(self):
        self.is_running = True
        # 使用 to_thread 避免阻塞事件循環
        self.cap = await asyncio.to_thread(cv2.VideoCapture, 0)
        
        if not self.cap or not self.cap.isOpened():
            self.status_text.value = "錯誤: 無法開啟攝影機"
            self.status_text.color = colors.ERROR
            self.page.update()
            return

        # 優化：降低解析度減少資料量
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

        self.status_text.value = "攝影機已就緒"
        self.capture_btn.disabled = False
        self.page.update()

        while self.is_running:
            try:
                ret, frame = await asyncio.to_thread(self.cap.read)
                if not ret or frame is None:
                    break
                
                # 優化：壓縮畫質並縮小顯示圖片
                # 轉換為 base64 顯示在 Flet，降低品質至 40 以提升流暢度
                encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 40]
                _, buffer = cv2.imencode('.jpg', frame, encode_param)
                img_base64 = base64.b64encode(buffer).decode('utf-8')
                
                self.img_preview.src_base64 = img_base64
                self.img_preview.update()
                await asyncio.sleep(0.06) # 約 16 FPS，兼顧流暢與效能
            except Exception as e:
                print(f"Camera feed error: {e}")
                break

    async def stop_camera(self, _=None):
        self.is_running = False
        if self.cap:
            await asyncio.to_thread(self.cap.release)
        if self.on_capture:
            await self.on_capture(None) # 表示取消

    async def take_photo(self, _):
        self.is_running = False
        if self.cap:
            ret, frame = await asyncio.to_thread(self.cap.read)
            if ret:
                # 儲存到暫存檔
                temp_path = "temp_capture.jpg"
                cv2.imwrite(temp_path, frame)
                await asyncio.to_thread(self.cap.release)
                if self.on_capture:
                    await self.on_capture(temp_path)
            else:
                await asyncio.to_thread(self.cap.release)
                if self.on_capture:
                    await self.on_capture(None)
