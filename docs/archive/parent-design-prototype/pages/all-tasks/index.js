Page({
  data: {
    tasks: [
      { id: 1, name: '完成今日数学练习', desc: '加减法练习 · 15道题', status: 'done' },
      { id: 2, name: '阅读一篇绘本故事', desc: '语文阅读 · 10分钟', status: 'progress' },
      { id: 3, name: '英语单词跟读', desc: '单词练习 · 10个单词', status: 'done' },
      { id: 4, name: '跟蛋仔对话10分钟', desc: '自由对话练习', status: 'pending' },
      { id: 5, name: '完成科学小实验', desc: '动手探索 · 1个实验', status: 'pending' },
      { id: 6, name: '整理床铺', desc: '好习惯养成', status: 'done' },
      { id: 7, name: '帮忙摆放碗筷', desc: '家务小帮手', status: 'pending' },
      { id: 8, name: '和爸妈一起阅读', desc: '亲子时光 · 20分钟', status: 'progress' }
    ],
    statusMap: {
      done: '已完成',
      progress: '进行中',
      pending: '待开始'
    }
  }
})
