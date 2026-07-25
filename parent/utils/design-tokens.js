// 设计令牌 — 供 JS / WXS 引用
// 所有 px 值已转换为 rpx (×2)

module.exports = {
  // 主色板
  colors: {
    pl: '#c1d6f1',
    pd: '#778ccd',
    pg: '#dff6e6',
    pp: '#fed4d8',
    pa1: '#B6C2CF',
    pa2: '#97979C',
    pa3: '#DBDDDA',
    warmOlive: '#A89F80',
    warmGold: '#E3DB9E',
    warmPeach: '#FDEDDD',
    warmLime: '#F8FFC7',
    warmSky: '#A4CBF2',
    bg: '#f8f6f2',
    white: '#ffffff',
    warm: '#F7E6D4',
    amber: '#F0A855',
    textPrimary: '#3D3D50',
    textSecondary: '#8B7A73',
    textMuted: '#B8AEA8'
  },

  // 间距 (rpx)
  spacing: {
    r: 56,    // 卡片大圆角
    m: 44,    // 页面左右边距
    g: 28     // 模块间距
  },

  // 字号 (rpx)
  fontSize: {
    t1: 44,   // 22px → 页面主标题
    t2: 34,   // 17px → 卡片标题
    t3: 30,   // 15px → 正文
    t4: 26,   // 13px → 辅助正文
    t5: 24,   // 12px → 标签/日期
    t6: 20    // 10px → 小标签
  },

  // 蛋仔状态配置
  dankeStates: {
    online:  { label: '在线 · 正在解答数学题', dotClass: 'online',  bg: '#ffffff' },
    focused: { label: '专注 · 答题中',          dotClass: 'focused', bg: '#ffffff' },
    tired:   { label: '今日已用 86 分钟，休息一下吧', dotClass: 'tired', bg: '#FFF8F0' },
    offline: { label: '设备已离线',             dotClass: 'offline', bg: '#F0EFEC' }
  },

  // 学习模块颜色
  moduleColors: {
    math:   { bg: 'rgba(119,140,205,0.1)',  fg: '#778ccd', name: '数学' },
    sci:    { bg: 'rgba(109,175,125,0.1)',   fg: '#4F9A5F', name: '科学' },
    eng:    { bg: 'rgba(216,122,130,0.1)',   fg: '#D97A84', name: '英语' },
    poem:   { bg: 'rgba(151,151,156,0.1)',   fg: '#97979C', name: '诗歌' },
    music:  { bg: 'rgba(240,168,85,0.1)',    fg: '#D4892E', name: '音乐' },
    puzzle: { bg: 'rgba(109,175,125,0.1)',   fg: '#4F9A5F', name: '思维' }
  }
}
