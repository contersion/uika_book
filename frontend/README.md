# Frontend

TXT Reader 前端基于 Vue 3 + Vite + TypeScript，负责登录、书架、书籍详情、阅读页和目录规则管理。

## 技术栈

- Vue 3
- Vite
- TypeScript
- Vue Router
- Pinia
- Naive UI

## 启动前准备

1. 先启动 backend，默认接口地址是 `http://localhost:8000`
2. 确认 Node.js 版本建议为 18+
3. 进入 `frontend/` 目录安装依赖

```bash
npm install
```

## 本地开发

```bash
npm run dev
```

默认会启动 Vite 开发服务器。若 backend 不在默认地址，可通过环境变量覆盖：

```bash
VITE_API_BASE_URL=http://127.0.0.1:8000
```

Windows PowerShell 示例：

```powershell
$env:VITE_API_BASE_URL = 'http://127.0.0.1:8000'
npm run dev
```

## 常用命令

```bash
npm run dev
npm run build
npm run preview
npm run typecheck
```

## 目录说明

- `src/api/`: 接口请求封装
- `src/components/`: 通用前端组件
- `src/layouts/`: 页面布局
- `src/pages/`: 业务页面
- `src/router/`: 路由与鉴权
- `src/stores/`: Pinia 状态管理
- `src/utils/`: 通用工具函数
- `src/types/`: API 类型定义

## 当前能力

- 登录态恢复与路由鉴权
- 书架搜索、上传、删除与继续阅读
- 书籍详情、目录重解析
- 规则管理、规则测试、规则应用到书籍
- 阅读设置本地保存与阅读进度自动同步

## 联调说明

- 若登录时报“无法连接到后端服务”，通常是 backend 未启动或接口地址不一致
- 阅读页会优先读取服务端进度，并按 `chapter_index + char_offset` 恢复位置
- 阅读设置保存在浏览器 `localStorage`