# Aliens_eye 下一步迭代规划

## 目标
在 Python 核心扫描路径上加固鲁棒性，关闭多签网关分支，确保现有测试无回归。

## 范围
- `src/aliens_eye/core/scanner.py`
- `src/aliens_eye/core/http.py`
- `src/aliens_eye/core/rate_limit.py`
- `src/aliens_eye/core/detector.py`

## 迭代 1：清理多签网关分支
- 不提交 `claude_filter.js` 相关修改
- 不在主扫描路径内做双签透传

## 迭代 2：核心扫描路径鲁棒性加固
- 固定 HTTP 会话和重试策略
- 增强异常分类和熔断
- 统一埋点与错误回传

## 验收
- ruff 全绿
- pytest 全绿
