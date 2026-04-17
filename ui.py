from __future__ import annotations

import sys
from io import BytesIO

import qrcode
from PySide6.QtCore import QEvent, QTimer, Qt
from PySide6.QtGui import QAction, QFont, QGuiApplication, QImage, QPixmap
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QFormLayout,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMenu,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QStyle,
    QSystemTrayIcon,
    QVBoxLayout,
    QWidget,
)

from config import ConfigManager, generate_access_token
from service import RemoteShutdownService
from startup import is_startup_enabled, set_startup_enabled


class MainWindow(QMainWindow):
    def __init__(self, start_minimized: bool = False) -> None:
        super().__init__()
        self.setWindowTitle("局域网关机主机端")
        self.resize(1020, 820)
        self.setMinimumSize(900, 720)

        self.config_manager = ConfigManager()
        self.service: RemoteShutdownService | None = None
        self._allow_close = False
        self._tray_hint_shown = False
        self._start_minimized = start_minimized

        config = self.config_manager.config
        try:
            startup_enabled = is_startup_enabled()
        except Exception:
            startup_enabled = bool(config.start_with_windows)
        if startup_enabled != bool(config.start_with_windows):
            self.config_manager.update(start_with_windows=startup_enabled)
            config = self.config_manager.config

        self._build_ui(config, startup_enabled)
        self._setup_tray_icon()

        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self.refresh_status)
        self.refresh_timer.start(1000)

        if self.auto_start_checkbox.isChecked():
            self.start_service(show_message=False)
        self.refresh_status()

    def _build_ui(self, config, startup_enabled: bool) -> None:
        self._apply_styles()

        central = QWidget()
        central_layout = QVBoxLayout(central)
        central_layout.setContentsMargins(0, 0, 0, 0)
        self.setCentralWidget(central)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        central_layout.addWidget(scroll)

        content = QWidget()
        scroll.setWidget(content)

        root = QVBoxLayout(content)
        root.setContentsMargins(22, 22, 22, 22)
        root.setSpacing(18)

        title = QLabel("局域网电脑关机")
        title_font = QFont()
        title_font.setPointSize(21)
        title_font.setBold(True)
        title.setFont(title_font)
        root.addWidget(title)

        intro = QLabel(
            "电脑端会提供一个局域网控制页面。手机第一次扫码后，把页面加入书签或添加到主屏幕；"
            "以后只要手机和电脑还在同一个网络下，就可以直接打开链接，安排关机、重启、取消倒计时或休眠。"
        )
        intro.setWordWrap(True)
        root.addWidget(intro)

        settings_group = QGroupBox("服务设置")
        settings_layout = QVBoxLayout(settings_group)
        settings_layout.setSpacing(12)

        form = QFormLayout()
        form.setContentsMargins(0, 0, 0, 0)
        form.setHorizontalSpacing(12)
        form.setVerticalSpacing(12)
        form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)

        self.port_edit = QLineEdit(str(config.port))
        self.port_edit.setClearButtonEnabled(True)
        form.addRow("监听端口", self.port_edit)

        self.delay_edit = QLineEdit(str(config.shutdown_delay_seconds))
        self.delay_edit.setClearButtonEnabled(True)
        form.addRow("默认倒计时（秒）", self.delay_edit)

        token_row_widget = QWidget()
        token_row = QHBoxLayout(token_row_widget)
        token_row.setContentsMargins(0, 0, 0, 0)
        token_row.setSpacing(10)
        self.token_edit = QLineEdit(config.access_token)
        self.token_edit.setClearButtonEnabled(True)
        self.regenerate_token_button = QPushButton("重新生成访问口令")
        self.regenerate_token_button.clicked.connect(self.rotate_token)
        token_row.addWidget(self.token_edit, 1)
        token_row.addWidget(self.regenerate_token_button)
        form.addRow("访问口令", token_row_widget)

        settings_layout.addLayout(form)

        checkbox_row = QHBoxLayout()
        checkbox_row.setSpacing(18)
        self.auto_start_checkbox = QCheckBox("启动软件时自动开启服务")
        self.auto_start_checkbox.setChecked(bool(config.auto_start))
        self.auto_start_checkbox.checkStateChanged.connect(self._save_form_config)
        checkbox_row.addWidget(self.auto_start_checkbox)

        self.start_with_windows_checkbox = QCheckBox("Windows 开机自启")
        self.start_with_windows_checkbox.setChecked(startup_enabled)
        self.start_with_windows_checkbox.checkStateChanged.connect(self._on_toggle_start_with_windows)
        checkbox_row.addWidget(self.start_with_windows_checkbox)
        checkbox_row.addStretch()
        settings_layout.addLayout(checkbox_row)

        settings_hint = QLabel(
            "手机页面中的倒计时会覆盖这里的默认值。这个默认值同时用于“安排关机”和“安排重启”；“立即休眠”不使用倒计时。"
        )
        settings_hint.setWordWrap(True)
        settings_layout.addWidget(settings_hint)

        root.addWidget(settings_group)

        service_controls_group = QGroupBox("服务控制")
        service_controls_layout = QHBoxLayout(service_controls_group)
        service_controls_layout.setSpacing(10)
        self.toggle_service_button = self._create_action_button("启动服务", role="primary")
        self.toggle_service_button.clicked.connect(self.toggle_service)
        service_controls_layout.addWidget(self.toggle_service_button)

        self.copy_url_button = self._create_action_button("复制手机访问链接")
        self.copy_url_button.clicked.connect(self.copy_primary_url)
        service_controls_layout.addWidget(self.copy_url_button)
        service_controls_layout.addStretch()
        root.addWidget(service_controls_group)

        quick_actions_group = QGroupBox("快捷操作")
        quick_actions_layout = QHBoxLayout(quick_actions_group)
        quick_actions_layout.setSpacing(10)

        self.shutdown_button = self._create_action_button("按倒计时关机", role="primary")
        self.shutdown_button.clicked.connect(self.shutdown_from_desktop)
        quick_actions_layout.addWidget(self.shutdown_button)

        self.cancel_shutdown_button = self._create_action_button("立即取消倒计时", role="warning")
        self.cancel_shutdown_button.clicked.connect(self.cancel_shutdown_from_desktop)
        quick_actions_layout.addWidget(self.cancel_shutdown_button)

        self.restart_button = self._create_action_button("按倒计时重启", role="secondary")
        self.restart_button.clicked.connect(self.restart_from_desktop)
        quick_actions_layout.addWidget(self.restart_button)

        self.sleep_button = self._create_action_button("立即休眠", role="success")
        self.sleep_button.clicked.connect(self.sleep_from_desktop)
        quick_actions_layout.addWidget(self.sleep_button)

        quick_actions_layout.addStretch()
        root.addWidget(quick_actions_group)

        status_group = QGroupBox("运行状态")
        status_layout = QVBoxLayout(status_group)
        status_layout.setSpacing(8)
        self.status_label = QLabel("服务未启动")
        self.status_label.setStyleSheet("font-weight: 700; font-size: 14px;")
        status_layout.addWidget(self.status_label)
        self.last_request_label = QLabel("暂无操作记录")
        self.last_request_label.setWordWrap(True)
        status_layout.addWidget(self.last_request_label)
        root.addWidget(status_group)

        bottom_row = QHBoxLayout()
        bottom_row.setSpacing(18)

        qr_group = QGroupBox("首次扫码二维码")
        qr_group.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Preferred)
        qr_group.setMinimumWidth(360)
        qr_layout = QVBoxLayout(qr_group)
        qr_layout.setSpacing(10)

        qr_card = QFrame()
        qr_card.setObjectName("qrCard")
        qr_card_layout = QVBoxLayout(qr_card)
        qr_card_layout.setContentsMargins(12, 12, 12, 12)
        qr_card_layout.setSpacing(0)

        self.qr_label = QLabel("启动服务后显示二维码")
        self.qr_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.qr_label.setMinimumSize(300, 300)
        self.qr_label.setMaximumSize(320, 320)
        self.qr_label.setStyleSheet("border: none; background: transparent;")
        qr_card_layout.addWidget(self.qr_label, 0, Qt.AlignmentFlag.AlignCenter)
        qr_layout.addWidget(qr_card, 0, Qt.AlignmentFlag.AlignCenter)

        self.qr_tip_label = QLabel(
            "请使用手机相机或微信扫描这个二维码。第一次打开后，把该页面收藏起来，后续就不需要再重新扫码。"
        )
        self.qr_tip_label.setWordWrap(True)
        qr_layout.addWidget(self.qr_tip_label)

        qr_hint = QLabel("建议在 iPhone 的 Safari 中打开后，选择“添加到主屏幕”或“加入书签”。")
        qr_hint.setWordWrap(True)
        qr_layout.addWidget(qr_hint)
        qr_layout.addStretch()

        bottom_row.addWidget(qr_group)

        access_group = QGroupBox("访问链接")
        access_layout = QVBoxLayout(access_group)
        access_layout.setSpacing(10)

        primary_url_title = QLabel("完整访问链接")
        primary_url_title.setStyleSheet("font-weight: 700;")
        access_layout.addWidget(primary_url_title)

        url_hint = QLabel("如果扫码不方便，也可以直接复制下面的完整链接到手机浏览器。")
        url_hint.setWordWrap(True)
        access_layout.addWidget(url_hint)

        self.url_text = QPlainTextEdit()
        self.url_text.setReadOnly(True)
        self.url_text.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        self.url_text.setPlaceholderText("启动服务后，这里会显示可访问的完整链接。")
        self.url_text.setMinimumHeight(280)
        access_layout.addWidget(self.url_text, 1)

        bottom_row.addWidget(access_group, 1)
        root.addLayout(bottom_row, 1)

    def _apply_styles(self) -> None:
        self.setStyleSheet(
            """
            QMainWindow {
                background: #f4f7fb;
            }
            QLabel {
                color: #1e293b;
            }
            QGroupBox {
                font-weight: 700;
                border: 1px solid #d7deea;
                border-radius: 12px;
                margin-top: 10px;
                background: #ffffff;
                padding-top: 8px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 4px;
            }
            QLineEdit, QPlainTextEdit {
                border: 1px solid #cfd7e4;
                border-radius: 8px;
                background: #ffffff;
                padding: 8px 10px;
                selection-background-color: #2f6edb;
            }
            QLineEdit {
                min-height: 18px;
            }
            QPushButton {
                min-height: 36px;
                padding: 0 14px;
                border: 1px solid #ced6e4;
                border-radius: 8px;
                background: #f8fafc;
            }
            QPushButton:hover {
                background: #edf2f7;
            }
            QPushButton:disabled {
                color: #8a94a6;
                background: #eef2f6;
            }
            QPushButton#primaryButton {
                color: #ffffff;
                border: none;
                background: #1f62d1;
            }
            QPushButton#primaryButton:hover {
                background: #194faa;
            }
            QPushButton#warningButton {
                color: #ffffff;
                border: none;
                background: #cc3d3d;
            }
            QPushButton#warningButton:hover {
                background: #a92f2f;
            }
            QPushButton#secondaryButton {
                color: #ffffff;
                border: none;
                background: #475569;
            }
            QPushButton#secondaryButton:hover {
                background: #344255;
            }
            QPushButton#successButton {
                color: #ffffff;
                border: none;
                background: #2f7d55;
            }
            QPushButton#successButton:hover {
                background: #245f40;
            }
            QFrame#qrCard {
                border: 1px solid #d7deea;
                border-radius: 14px;
                background: #ffffff;
            }
            """
        )

    def _create_action_button(self, text: str, role: str | None = None) -> QPushButton:
        button = QPushButton(text)
        role_to_object_name = {
            "primary": "primaryButton",
            "warning": "warningButton",
            "secondary": "secondaryButton",
            "success": "successButton",
        }
        if role in role_to_object_name:
            button.setObjectName(role_to_object_name[role])
        return button

    def _setup_tray_icon(self) -> None:
        self.tray_icon: QSystemTrayIcon | None = None
        self.show_action: QAction | None = None

        if not QSystemTrayIcon.isSystemTrayAvailable():
            return

        tray_icon = QApplication.style().standardIcon(QStyle.StandardPixmap.SP_ComputerIcon)
        self.setWindowIcon(tray_icon)

        tray_menu = QMenu(self)
        self.show_action = tray_menu.addAction("显示窗口")
        self.show_action.triggered.connect(self.restore_from_tray)

        tray_menu.addSeparator()
        exit_action = tray_menu.addAction("退出")
        exit_action.triggered.connect(self.quit_from_tray)

        self.tray_icon = QSystemTrayIcon(tray_icon, self)
        self.tray_icon.setToolTip("局域网关机主机端")
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.activated.connect(self._on_tray_activated)
        self.tray_icon.show()

    def can_run_in_tray(self) -> bool:
        return self.tray_icon is not None and self.tray_icon.isVisible()

    def start_hidden(self) -> None:
        if self.can_run_in_tray():
            self.hide_to_tray(show_message=False)
        else:
            self.showMinimized()

    def toggle_service(self) -> None:
        if self.service and self.service.is_running:
            self.stop_service()
        else:
            self.start_service()

    def start_service(self, show_message: bool = True) -> None:
        values = self._read_form_values()
        if values is None:
            return

        port, delay, token = values
        self._save_form_config()

        try:
            self.service = RemoteShutdownService(
                port=port,
                token=token,
                shutdown_delay_seconds=delay,
            )
            self.service.start(host=self.config_manager.config.bind_host)
        except OSError as exc:
            QMessageBox.critical(self, "启动失败", f"服务启动失败：{exc}")
            self.service = None
            return

        self.port_edit.setText(str(self.service.port))
        self._save_form_config()
        self.refresh_status()
        if show_message:
            QMessageBox.information(self, "服务已启动", "二维码和手机访问链接已经生成。")

    def stop_service(self) -> None:
        if self.service:
            self.service.stop()
        self.service = None
        self.refresh_status()

    def rotate_token(self) -> None:
        self.token_edit.setText(generate_access_token())
        self._save_form_config()
        if self.service and self.service.is_running:
            self.stop_service()
            self.start_service(show_message=False)
        QMessageBox.information(self, "口令已更新", "访问口令已重置，二维码和访问链接已同步刷新。")

    def copy_primary_url(self) -> None:
        if not self.service or not self.service.is_running:
            QMessageBox.warning(self, "服务未启动", "请先启动服务，再复制手机访问链接。")
            return

        QGuiApplication.clipboard().setText(self.service.get_primary_url())
        QMessageBox.information(self, "已复制", "手机访问链接已经复制到剪贴板。")

    def shutdown_from_desktop(self) -> None:
        if not self._ensure_service_running("请先启动服务，再发送关机指令。"):
            return

        values = self._read_form_values()
        if values is None:
            return

        _, delay, _ = values
        answer = QMessageBox.question(
            self,
            "确认关机",
            f"确定要在 {delay} 秒后关机吗？",
        )
        if answer != QMessageBox.StandardButton.Yes:
            return

        try:
            self.service.request_shutdown("desktop-ui", delay)
        except Exception as exc:
            QMessageBox.critical(self, "关机失败", f"发送关机指令失败：{exc}")
            return

        self.refresh_status()
        QMessageBox.information(self, "已发送", f"电脑将在 {delay} 秒后关机。")

    def cancel_shutdown_from_desktop(self) -> None:
        if not self._ensure_service_running("请先启动服务，再发送取消指令。"):
            return

        try:
            self.service.request_cancel_shutdown("desktop-ui")
        except Exception as exc:
            QMessageBox.critical(self, "取消失败", f"取消关机 / 重启失败：{exc}")
            return

        self.refresh_status()
        QMessageBox.information(self, "已取消", "已经发送取消关机 / 重启指令。")

    def restart_from_desktop(self) -> None:
        if not self._ensure_service_running("请先启动服务，再发送重启指令。"):
            return

        values = self._read_form_values()
        if values is None:
            return

        _, delay, _ = values
        answer = QMessageBox.question(
            self,
            "确认重启",
            f"确定要在 {delay} 秒后重启吗？",
        )
        if answer != QMessageBox.StandardButton.Yes:
            return

        try:
            self.service.request_restart("desktop-ui", delay)
        except Exception as exc:
            QMessageBox.critical(self, "重启失败", f"发送重启指令失败：{exc}")
            return

        self.refresh_status()
        QMessageBox.information(self, "已发送", f"电脑将在 {delay} 秒后重启。")

    def sleep_from_desktop(self) -> None:
        if not self._ensure_service_running("请先启动服务，再发送休眠指令。"):
            return

        answer = QMessageBox.question(
            self,
            "确认休眠",
            "确定要让电脑立即休眠吗？",
        )
        if answer != QMessageBox.StandardButton.Yes:
            return

        try:
            self.service.request_sleep("desktop-ui")
        except Exception as exc:
            QMessageBox.critical(self, "休眠失败", f"发送休眠指令失败：{exc}")
            return

        self.refresh_status()
        QMessageBox.information(self, "已发送", "已经发送休眠指令。")

    def refresh_status(self) -> None:
        running = self.service is not None and self.service.is_running
        self.toggle_service_button.setText("停止服务" if running else "启动服务")
        self.copy_url_button.setEnabled(running)
        self.shutdown_button.setEnabled(running)
        self.cancel_shutdown_button.setEnabled(running)
        self.restart_button.setEnabled(running)
        self.sleep_button.setEnabled(running)

        if not running:
            self.status_label.setText("服务未启动")
            self.last_request_label.setText("暂无操作记录")
            self.qr_tip_label.setText(
                "启动服务后，这里会显示二维码。第一次扫码打开后，把该页面加入书签或主屏幕，后续就可以直接打开。"
            )
            self.url_text.setPlainText("启动服务后，这里会显示完整访问链接。")
            self._clear_qr_code()
            return

        status = self.service.get_status()
        startup_text = "已启用" if self.start_with_windows_checkbox.isChecked() else "未启用"
        self.status_label.setText(
            f"服务运行中，端口 {status['port']}，默认倒计时 {status['shutdown_delay_seconds']} 秒，开机自启 {startup_text}"
        )
        self.last_request_label.setText(self._format_last_action(status))
        self.qr_tip_label.setText(
            "请用手机相机或微信扫描二维码。第一次打开后，将该页面收藏起来；以后只要手机和电脑在同一个网络下，"
            "就可以直接打开该链接执行关机、重启、取消倒计时或休眠。"
        )
        self.url_text.setPlainText("\n".join(status["available_urls"]))
        self._update_qr_code(self.service.get_primary_url())

    def _on_toggle_start_with_windows(self) -> None:
        enabled = self.start_with_windows_checkbox.isChecked()
        try:
            set_startup_enabled(enabled)
        except Exception as exc:
            self.start_with_windows_checkbox.blockSignals(True)
            self.start_with_windows_checkbox.setChecked(not enabled)
            self.start_with_windows_checkbox.blockSignals(False)
            QMessageBox.critical(self, "设置失败", f"更新开机自启失败：{exc}")
            return

        self._save_form_config()
        self.refresh_status()

    def _read_form_values(self) -> tuple[int, int, str] | None:
        try:
            port = int(self.port_edit.text().strip())
            delay = int(self.delay_edit.text().strip())
            if port <= 0 or delay < 0:
                raise ValueError
        except ValueError:
            QMessageBox.warning(self, "参数错误", "端口必须是正整数，默认倒计时必须是 0 或更大的整数秒数。")
            return None

        token = self.token_edit.text().strip() or generate_access_token()
        self.token_edit.setText(token)
        return port, delay, token

    def _save_form_config(self) -> None:
        values = self._read_form_values()
        if values is None:
            return
        port, delay, token = values
        self.config_manager.update(
            port=port,
            access_token=token,
            auto_start=self.auto_start_checkbox.isChecked(),
            start_with_windows=self.start_with_windows_checkbox.isChecked(),
            shutdown_delay_seconds=delay,
        )

    def _ensure_service_running(self, warning_text: str) -> bool:
        if self.service and self.service.is_running:
            return True
        QMessageBox.warning(self, "服务未启动", warning_text)
        return False

    def _format_last_action(self, status: dict[str, object]) -> str:
        action = status.get("last_action")
        if not isinstance(action, dict):
            return "暂无操作记录"

        action_type = str(action.get("type") or "")
        action_name = {
            "shutdown": "安排关机",
            "restart": "安排重启",
            "cancel_shutdown": "取消关机 / 重启",
            "sleep": "立即休眠",
        }.get(action_type, "未知操作")

        requested_by = action.get("requested_by", "unknown")
        requested_at = action.get("requested_at", "--")
        detail = f"最近一次操作：{action_name}。来源 {requested_by}，时间 {requested_at}"

        if action_type in {"shutdown", "restart"}:
            detail += f"，倒计时 {action.get('delay_seconds', '--')} 秒。"
        else:
            detail += "。"
        return detail

    def _update_qr_code(self, url: str) -> None:
        if not url:
            self._clear_qr_code()
            return

        qr = qrcode.QRCode(
            version=None,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=10,
            border=4,
        )
        qr.add_data(url)
        qr.make(fit=True)

        image = qr.make_image(fill_color="black", back_color="white").convert("RGB")
        buffer = BytesIO()
        image.save(buffer, format="PNG")
        qimage = QImage.fromData(buffer.getvalue(), "PNG")
        pixmap = QPixmap.fromImage(qimage).scaled(
            300,
            300,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        self.qr_label.setPixmap(pixmap)
        self.qr_label.setText("")

    def _clear_qr_code(self) -> None:
        self.qr_label.setPixmap(QPixmap())
        self.qr_label.setText("启动服务后显示二维码")

    def hide_to_tray(self, show_message: bool = True) -> None:
        if not self.can_run_in_tray():
            self.showMinimized()
            return

        self.hide()
        if show_message and not self._tray_hint_shown:
            self.tray_icon.showMessage(
                "局域网关机主机端",
                "程序已最小化到系统托盘，右键托盘图标可以显示窗口或退出。",
                QSystemTrayIcon.MessageIcon.Information,
                3000,
            )
            self._tray_hint_shown = True

    def restore_from_tray(self) -> None:
        self.showNormal()
        self.raise_()
        self.activateWindow()

    def quit_from_tray(self) -> None:
        self._allow_close = True
        self.close()

    def _on_tray_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        if reason in (
            QSystemTrayIcon.ActivationReason.Trigger,
            QSystemTrayIcon.ActivationReason.DoubleClick,
        ):
            if self.isVisible():
                self.hide_to_tray(show_message=False)
            else:
                self.restore_from_tray()

    def changeEvent(self, event) -> None:  # type: ignore[override]
        if event.type() == QEvent.Type.WindowStateChange and self.isMinimized():
            QTimer.singleShot(0, self.hide_to_tray)
        super().changeEvent(event)

    def closeEvent(self, event) -> None:  # type: ignore[override]
        if self._allow_close:
            self.refresh_timer.stop()
            self._save_form_config()
            if self.service:
                self.service.stop()
            if self.tray_icon:
                self.tray_icon.hide()
            super().closeEvent(event)
            return

        if self.can_run_in_tray():
            event.ignore()
            self.hide_to_tray()
            return

        self.refresh_timer.stop()
        self._save_form_config()
        if self.service:
            self.service.stop()
        super().closeEvent(event)


def run(start_minimized: bool = False) -> None:
    app = QApplication.instance() or QApplication(sys.argv)
    window = MainWindow(start_minimized=start_minimized)
    app.setQuitOnLastWindowClosed(not window.can_run_in_tray())

    if start_minimized and window.can_run_in_tray():
        window.start_hidden()
    elif start_minimized:
        window.showMinimized()
    else:
        window.show()

    app.exec()
