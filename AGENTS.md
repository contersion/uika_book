# Project Guidance

本项目是个人使用的 TXT 在线阅读器，支持书架、目录、阅读进度同步和用户自定义章节正则。

## Stack
- Frontend: Vue 3 + Vite + TypeScript + Vue Router + Pinia + Naive UI
- Backend: FastAPI + SQLAlchemy + SQLite

## Architecture Rules
- 使用轻量前后端分离
- 不要引入微服务、Redis、MQ、K8s
- 阅读正文必须按章节返回，不能整本返回
- 阅读进度以 chapter_index + char_offset 为主，percent 仅用于展示
- 章节解析支持内置规则和用户自定义 regex
- 没匹配到章节时必须降级为“全文”单章节模式

## Workflow
详细开发步骤见 `docs/IMPLEMENTATION_STEPS.md`。
进行较大功能开发、重构、验收前，先阅读该文件。

## Commands
- backend: `uvicorn app.main:app --reload`
- frontend: `npm run dev`
- docker: see README

## Reading Page Refactor Rules
- 阅读页允许进行 UI 重构与前端交互重构，但不得修改后端接口、数据库结构、API 字段语义。
- 阅读正文仍必须按章节加载与返回，不能改为整本返回。
- 阅读进度定位仍以 `chapter_index + char_offset` 为主，`percent` 仅用于展示。
- 目录、阅读设置、主题、字体大小、行高、进度同步等现有能力应尽量复用，不要重写业务层。
- 阅读页需同时兼容 PC 与移动端，优先通过响应式布局、抽屉、浮动工具区实现。
- 允许将目录与设置从常驻面板改为抽屉式交互，但必须保持原有功能可用。