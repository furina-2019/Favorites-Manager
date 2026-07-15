/**
 * 收藏项数据模型
 */
export interface FavoriteItem {
  id: string;                    // 唯一标识
  title: string;                 // 标题
  sourceApp: string;             // 来源应用名称
  sourcePackage: string;         // 来源应用包名
  url: string;                   // 原始链接
  coverImage?: string;           // 封面图片URI
  description?: string;          // 描述/摘要
  folderId: string;              // 所属文件夹ID
  category: string;              // 智能分类标签
  createTime: number;            // 创建时间戳
  updateTime: number;            // 更新时间戳
  type: 'article' | 'video' | 'image' | 'website' | 'other';  // 内容类型
}

/**
 * 文件夹数据模型
 */
export interface Folder {
  id: string;                    // 唯一标识
  name: string;                  // 文件夹名称
  icon?: string;                 // 图标
  color?: string;                // 主题色
  isDefault: boolean;            // 是否为默认文件夹
  createTime: number;            // 创建时间戳
  updateTime: number;            // 更新时间戳
}

/**
 * 分享数据模型
 */
export interface ShareData {
  title?: string;                // 分享标题
  text?: string;                 // 分享文本
  url?: string;                  // 分享链接
  imageUri?: string;             // 分享图片URI
  sourceApp?: string;            // 来源应用
  sourcePackage?: string;        // 来源应用包名
}

/**
 * 分类定义
 */
export interface Category {
  id: string;
  name: string;
  keywords: string[];            // 关键词列表
  icon?: string;
  color?: string;
}

/**
 * 预定义分类
 */
export const DEFAULT_CATEGORIES: Category[] = [
  {
    id: 'travel',
    name: '旅行',
    keywords: ['旅游', '旅行', '景点', '攻略', '酒店', '机票', '度假', '自驾', '出境', '签证', '民宿'],
    color: '#4CAF50'
  },
  {
    id: 'food',
    name: '美食',
    keywords: ['美食', '餐厅', '菜谱', '做饭', '烹饪', '食材', '小吃', '甜品', '饮品', '咖啡'],
    color: '#FF9800'
  },
  {
    id: 'game',
    name: '游戏攻略',
    keywords: ['游戏', '攻略', '通关', '副本', '装备', '角色', '技能', '皮肤', '电竞', '手游', '端游', '原神', '王者', '吃鸡'],
    color: '#9C27B0'
  },
  {
    id: 'study',
    name: '学习',
    keywords: ['学习', '教程', '课程', '笔记', '考试', '考研', '英语', '编程', '技术', '知识', '教育'],
    color: '#2196F3'
  },
  {
    id: 'tech',
    name: '科技',
    keywords: ['科技', '数码', '手机', '电脑', 'AI', '人工智能', '互联网', '软件', '硬件', '评测', '新品'],
    color: '#00BCD4'
  },
  {
    id: 'life',
    name: '生活',
    keywords: ['生活', '日常', '家居', '装修', '收纳', '清洁', '穿搭', '护肤', '健身', '运动'],
    color: '#E91E63'
  },
  {
    id: 'entertainment',
    name: '娱乐',
    keywords: ['娱乐', '明星', '电影', '电视剧', '综艺', '音乐', '动漫', '追剧', '八卦'],
    color: '#FF5722'
  },
  {
    id: 'finance',
    name: '财经',
    keywords: ['财经', '理财', '投资', '股票', '基金', '经济', '金融', '保险', '房产'],
    color: '#795548'
  },
  {
    id: 'website',
    name: '网站',
    keywords: ['网站', '网页', '链接', '网址', '官网', '首页', '导航'],
    color: '#3F51B5'
  },
  {
    id: 'other',
    name: '其他',
    keywords: [],
    color: '#9E9E9E'
  }
];

/**
 * 默认文件夹
 */
export const DEFAULT_FOLDERS: Folder[] = [
  {
    id: 'all',
    name: '全部收藏',
    isDefault: true,
    createTime: Date.now(),
    updateTime: Date.now()
  }
];