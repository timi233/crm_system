# 报表页面UI/UX统一修复规范

## 一、页面布局统一标准

**强制顺序：**
```
页面标题 (page-title)
  ↓
筛选条件 (filter-section)
  ↓
数据统计卡片 (Row + Col + stat-card)
  ↓
图表/表格区域
```

**修改文件：**
- PerformanceReport.tsx - 调整标题和筛选条件顺序

---

## 二、数据统计卡片统一规范

### 2.1 图标规范
- **数量类卡片**：使用Outlined图标
- **金额类卡片**：使用¥符号 + 字体大小16px
- **百分比类卡片**：使用%符号
- **所有图标颜色**：使用CSS变量（--primary-color, --success-color等）

### 2.2 颜色规范
- **主数据（总数）**：success类（绿色渐变顶部条）
- **金额数据**：info类（蓝色渐变顶部条）
- **警告数据（逾期等）**：warning类（橙色渐变顶部条）
- **危险数据**：danger类（红色渐变顶部条，需新增）

### 2.3 字号规范
- **标题**：fontSize: 14, color: 'var(--text-secondary)'
- **数字**：fontSize: 24, fontWeight: 700
- **金额**：precision: 0（添加千分位）

### 2.4 数字格式
```tsx
// 使用Ant Design Statistic组件的formatter
<Statistic 
  value={data.amount}
  formatter={(value) => `¥${Number(value).toLocaleString()}`}
/>
```

---

## 三、图表优化规范

### 3.1 销售漏斗图
```javascript
{
  series: [{
    type: 'funnel',
    sort: 'none',
    orient: 'horizontal', // 横向排列
    label: {
      show: true,
      position: 'inside',
      color: '#fff',
      fontSize: 13,
      formatter: '{b}: {c}'
    },
    data: [
      { value: 100, name: '线索', itemStyle: { color: '#0052cc' } },
      { value: 80, name: '商机', itemStyle: { color: '#1890ff' } },
      { value: 60, name: '项目', itemStyle: { color: '#52c41a' } },
      { value: 40, name: '合同', itemStyle: { color: '#faad14' } }
    ]
  }]
}
```

### 3.2 回款状态环形图
```javascript
{
  series: [{
    type: 'pie',
    radius: ['45%', '75%'],
    avoidLabelOverlap: true,
    itemStyle: {
      borderRadius: 8,
      borderColor: '#fff',
      borderWidth: 2
    },
    label: {
      show: true,
      formatter: '{b}\n¥{c}',
      fontSize: 12
    },
    data: [
      { 
        value: paidAmount, 
        name: '已回款', 
        itemStyle: { color: '#52c41a' },
        label: { formatter: `已回款\n¥${paidAmount.toLocaleString()}` }
      },
      { 
        value: pendingAmount, 
        name: '待回款', 
        itemStyle: { color: '#d9d9d9' }, // 灰色而非黄色
        label: { formatter: `待回款\n¥${pendingAmount.toLocaleString()}` }
      }
    ]
  }]
}
```

### 3.3 仪表盘优化
```javascript
{
  series: [{
    type: 'gauge',
    detail: { 
      formatter: '{value}%',
      fontSize: 28,
      fontWeight: 'bold',
      color: '#0052cc'
    },
    axisLine: {
      lineStyle: {
        width: 20,
        color: [
          [0.3, '#ff4d4f'],  // 0-30% 红色
          [0.6, '#faad14'],  // 30-60% 橙色
          [0.8, '#52c41a'],  // 60-80% 绿色
          [1, '#1890ff']     // 80-100% 蓝色
        ]
      }
    },
    // 0%时显示灰色背景
    splitLine: { show: true, length: 15 },
    axisTick: { show: true }
  }]
}
```

---

## 四、转化率表格优化

```tsx
<Table 
  columns={columns}
  dataSource={data}
  pagination={false}
  size="small" // 减少行高
  rowClassName="compact-row"
/>

// CSS
.compact-row td {
  padding: 8px 16px !important;
}
```

---

## 五、千分位格式化工具函数

```typescript
// utils/format.ts
export const formatCurrency = (value: number): string => {
  return `¥${value.toLocaleString('zh-CN')}`;
};

export const formatNumber = (value: number): string => {
  return value.toLocaleString('zh-CN');
};
```

---

## 六、执行计划

### P0修复（立即）
1. PerformanceReport布局调整
2. 漏斗图横向优化
3. 回款状态环形图颜色修正
4. 数字千分位格式化

### P1修复（统一）
1. 数据卡片样式统一
2. 图标和颜色规范
3. 转化率表格优化
4. 仪表盘颜色说明

### P2修复（优化）
1. 0%进度视觉提示
2. 留白比例调整
3. 弹窗位置优化