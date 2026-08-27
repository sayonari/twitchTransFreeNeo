#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""チャット1件分の見た目を組み立てる共通部品

メイン画面と、設定画面のプレビューの両方から使う。
片方だけ直して見た目がずれることがないよう、ここに集約している。
"""

from typing import Any, Callable, Dict, Optional

import flet as ft


# 表示項目の既定値（設定に無い場合はすべて表示する）
DEFAULT_VIEW_OPTIONS: Dict[str, bool] = {
    "view_show_time": True,        # 受信時刻
    "view_show_username": True,    # ユーザー名
    "view_show_lang": True,        # 言語コード [en] など
    "view_show_original": True,    # 原文
    "view_show_translation": True, # 翻訳文
}


def get_view_options(config: Dict[str, Any]) -> Dict[str, bool]:
    """設定から表示項目だけを取り出す"""
    return {
        key: bool(config.get(key, default))
        for key, default in DEFAULT_VIEW_OPTIONS.items()
    }


def build_message_content(
    message,
    options: Dict[str, bool],
    font_size: int = 13,
    actions: Optional[ft.Control] = None,
) -> ft.Column:
    """メッセージ本体（ヘッダー・原文・翻訳文）を組み立てる

    actions を渡すとヘッダー右側に操作アイコンを並べる。
    プレビューでは操作できる必要がないので省略できる。
    """
    header_items = []

    if options.get("view_show_time", True):
        header_items.append(
            ft.Text(message.timestamp.strftime("%H:%M:%S"), size=10, color=ft.Colors.GREY)
        )

    if options.get("view_show_username", True):
        header_items.append(
            ft.Text(f"{message.user}:", size=font_size, weight=ft.FontWeight.BOLD)
        )

    if options.get("view_show_lang", True) and message.lang:
        header_items.append(ft.Text(f"[{message.lang}]", size=10, color=ft.Colors.GREY))

    rows = []
    # ヘッダーに出すものが何も無い場合は行ごと省く
    if header_items or actions is not None:
        header_items.append(ft.Container(expand=True))
        if actions is not None:
            header_items.append(actions)
        rows.append(ft.Row(header_items, spacing=5, height=22))

    if options.get("view_show_original", True):
        rows.append(ft.Text(message.text, size=font_size, selectable=True))

    if options.get("view_show_translation", True) and message.translation:
        rows.append(
            ft.Row([
                ft.Container(width=3, height=16, bgcolor=ft.Colors.BLUE_200,
                             border_radius=2, margin=ft.margin.only(top=2)),
                ft.Text(message.translation, size=font_size,
                        color=ft.Colors.BLUE_700, selectable=True, expand=True),
            ], spacing=6, vertical_alignment=ft.CrossAxisAlignment.START)
        )

    # すべて非表示にされた場合でも空欄が続かないように案内を出す
    if not rows:
        rows.append(
            ft.Text("（表示する項目が選ばれていません）", size=font_size - 1,
                    color=ft.Colors.GREY, italic=True)
        )

    return ft.Column(rows, spacing=1, tight=True)


def build_message_container(
    content: ft.Column,
    bgcolor=None,
    on_hover: Optional[Callable] = None,
) -> ft.Container:
    """メッセージ1件分の枠（下線区切り）"""
    return ft.Container(
        content=content,
        padding=ft.padding.symmetric(vertical=5, horizontal=10),
        bgcolor=bgcolor,
        border=ft.border.only(
            bottom=ft.BorderSide(1, ft.Colors.with_opacity(0.4, ft.Colors.GREY))
        ),
        on_hover=on_hover,
    )
