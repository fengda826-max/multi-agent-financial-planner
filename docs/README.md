# Financial Planner 文档

## 快速开始

### 安装依赖

```bash
uv pip install mkdocs mkdocs-material
```

### 本地预览

```bash
# 启动开发服务器
mkdocs serve

# 访问 http://localhost:8000
```

### 构建静态站点

```bash
# 构建文档
mkdocs build

# 输出目录：site/
```

### 部署到 GitHub Pages

```bash
# 部署到 gh-pages 分支
mkdocs gh-deploy
```

## 文档结构

```
docs/
├── index.md                    # 首页
├── getting-started/            # 快速开始
│   ├── installation.md        # 安装指南
│   ├── configuration.md       # 配置说明
│   └── quickstart.md          # 快速上手
├── api/                        # API 文档
│   ├── authentication.md      # 认证
│   ├── users.md               # 用户
│   └── risk-assessment.md     # 风险测评
├── architecture/               # 架构设计
│   ├── overview.md            # 系统架构
│   ├── agents.md              # Agent 设计
│   └── data-models.md         # 数据模型
└── development/                # 开发指南
    ├── setup.md               # 开发环境
    ├── testing.md             # 测试指南
    └── deployment.md          # 部署指南
```

## 自定义配置

### 修改主题

编辑 `mkdocs.yml`：

```yaml
theme:
  name: material
  palette:
    - scheme: default
      primary: indigo
      accent: indigo
```

### 添加新页面

1. 在 `docs/` 目录创建新的 `.md` 文件
2. 在 `mkdocs.yml` 的 `nav` 部分添加页面链接

### 自定义样式

编辑 `docs/stylesheets/extra.css` 添加自定义 CSS。

## 部署选项

### GitHub Pages

```bash
mkdocs gh-deploy --force
```

### Netlify

1. 连接 GitHub 仓库
2. 构建命令：`mkdocs build`
3. 发布目录：`site`

### Vercel

1. 导入 GitHub 仓库
2. 构建命令：`mkdocs build`
3. 输出目录：`site`

### 自托管

```bash
# 构建
mkdocs build

# 使用 Nginx 部署
cp -r site/* /var/www/html/
```

## 常见问题

### Q: 如何添加搜索功能？

A: MkDocs Material 主题默认包含搜索功能，无需额外配置。

### Q: 如何支持多语言？

A: 在 `mkdocs.yml` 中配置 `language` 选项：

```yaml
theme:
  name: material
  language: zh
```

### Q: 如何添加代码高亮？

A: 在 `mkdocs.yml` 中配置 `markdown_extensions`：

```yaml
markdown_extensions:
  - pymdownx.highlight:
      anchor_linenums: true
  - pymdownx.superfences
```

### Q: 如何自定义导航？

A: 在 `mkdocs.yml` 的 `nav` 部分定义导航结构：

```yaml
nav:
  - 首页: index.md
  - 指南:
    - 安装: getting-started/installation.md
    - 配置: getting-started/configuration.md
```

## 相关资源

- [MkDocs 官方文档](https://www.mkdocs.org/)
- [Material for MkDocs](https://squidfunk.github.io/mkdocs-material/)
- [Markdown 语法指南](https://www.markdownguide.org/)

## 贡献指南

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建 Pull Request

## 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](../LICENSE) 文件
