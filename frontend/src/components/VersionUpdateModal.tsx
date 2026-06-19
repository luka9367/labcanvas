import { useState } from 'react'
import { X, Zap, Sparkles, Images, ListChecks, Globe, User, Layers, Smartphone, Shield } from 'lucide-react'

interface VersionUpdateModalProps {
  isOpen: boolean
  onClose: () => void
}

const VERSION_DATA = {
  version: 'v1.2.2',
  date: '2026年6月29日',
  author: '范嘉许',
  updates: [
    {
      icon: Sparkles,
      title: '优化日常生活类场景生图效果',
      desc: '重构 PromptEngine 需求分析逻辑，自动识别输入属于学术图表还是日常生活场景。针对小猫小狗、节日庆祝、人物肖像、校园风景、自然风光等日常主题，采用 realistic、cute、festive、casual 等自然生活化风格，并移除学术图表的强制规范（LaTeX 排版、矢量图边缘、模块框等），避免日常画面被过度学术化，观感更自然亲切。',
      highlight: '日常场景不再强行学术风',
    },
    {
      icon: Smartphone,
      title: '移动端全面适配优化',
      desc: '针对手机端重新设计全局布局：侧边栏改为抽屉式抽屉导航并添加遮罩层；创作页改为整页上下滚动布局，输入面板自然展开、画布置于下方，彻底解决可视区域被严重压缩的问题；首页、素材库、设置页全面适配小屏间距与字体。',
      highlight: '手机端可用性大幅提升',
    },
    {
      icon: Globe,
      title: '一键分享与部署优化',
      desc: '后端直接托管前端静态文件，配合 cpolar 内网穿透实现"一个链接即可访问"。优化本地启动脚本与网关配置，朋友无需安装任何软件，浏览器打开链接就能使用完整功能。',
      highlight: '一个链接，开箱即用',
    },
    {
      icon: Shield,
      title: '设置页 API Key 显示修复',
      desc: '修复手机上 API 密钥因密码输入框显示异常导致的"空白"问题。隐藏状态下通过占位符清晰展示已保存的 masked key，点击显示后可见完整密钥，支持一键复制与清除。',
      highlight: '密钥状态一目了然',
    },
    {
      icon: Images,
      title: '素材库图片加载修复',
      desc: '修复后端静态文件挂载路径变化导致素材库 256 张参考图片无法加载的问题。同时支持 /static 与 / 双重挂载，确保图片、前端页面与 API 接口全部正常访问。',
      highlight: '256张素材正常加载',
    },
    {
      icon: Layers,
      title: '系统性图像生成效果架构优化',
      desc: '在继续免费模型的前提下，构建5层质量跃升架构：①多层Prompt工程（需求结构化→核心提示词→质量增强→风格融合）；②多候选生成+负面提示词（一次生成2张并择优）；③算法级图像后处理增强（锐化、边缘增强、对比度、降噪）；④光影质量校验引擎7维度评估；⑤最多2轮迭代优化闭环。',
      highlight: '免费模型质量跨越式提升',
    },
    {
      icon: Zap,
      title: '新增光影自我校正引擎',
      desc: '引入7维度量化质量校验体系（画质精度、模块组件、图标插图、材质质感、数学符号与公式、信息密度、构图逻辑），生成后自动对标样张质量特征库，未达标即触发智能优化。',
      highlight: '支持最多2次精准迭代修正',
    },
    {
      icon: Images,
      title: '新增参考素材库图片',
      desc: '完整引入256张真实学术参考素材库图像，覆盖多种学术领域与图表风格。创作时可一键选取参考图，显著提升生成结果的风格一致性与内容相关性。',
      highlight: '256张真实素材，风格对齐',
    },
    {
      icon: ListChecks,
      title: '任务编排与任务流显示',
      desc: '创作模式新增可视化任务列表，实时展示AI处理流程及进度。从需求分析到最终输出，每一步状态清晰可见，实现思维链的透明化展示。',
      highlight: '思维链可视化，进度透明',
    },
    {
      icon: Sparkles,
      title: '修复与优化',
      desc: '修复处理进度弹窗逻辑错乱、提示词排版异常等关键问题；全面优化全站语言体系与页面视觉交互体验，操作反馈更及时、界面更直观。',
      highlight: '全站体验升级',
    },
  ],
  advantages: [
    {
      title: '免费模型，付费级输出',
      desc: '通过PromptEngine多层结构化优化、多候选择优、负面提示词过滤、ImageEnhancer算法增强的四重叠加，让免费的CogView-3-Flash输出无限趋近付费模型的视觉效果，实现零成本质量跃升。',
    },
    {
      title: '质量自进化',
      desc: '光影引擎不是简单的"生成即结束"，而是"生成-评估-再进化"的闭环。每一张输出图都经过严格的学术级质量把关，确保视觉精度无限趋近甚至超越样张标准。',
    },
    {
      title: '智能迭代不费心',
      desc: '用户无需手动调试提示词，引擎自动识别画质缺陷并生成针对性优化方向，最多2轮迭代即可将 mediocre 输出提升为 publication-ready 级别的学术插图。',
    },
    {
      title: '移动端友好',
      desc: '专为手机重新设计的交互布局，创作页支持整页自然滚动，侧边栏改为抽屉式，设置页与素材库全面适配小屏。随时随地都能用手机创作学术插图。',
    },
    {
      title: '一键分享',
      desc: '本地部署 + cpolar 内网穿透，只需一个浏览器链接就能邀请朋友使用。无需服务器、无需域名、无需复杂配置，打开即用的轻量级共享方案。',
    },
    {
      title: '全流程可感知',
      desc: '任务流可视化让黑盒AI变白盒。用户能清楚看到当前处于"分析需求"、"优化提示词"、"图像增强"还是"质量校验"阶段，对时间敏感型用户极其友好。',
    },
    {
      title: '素材生态完善',
      desc: '256张经过筛选的真实学术参考图构成强大的风格锚点。无论是系统架构图、算法流程图还是数学公式插图，都能找到高匹配度的参考基准。',
    },
  ],
}

export default function VersionUpdateModal({ isOpen, onClose }: VersionUpdateModalProps) {
  const [activeTab, setActiveTab] = useState<'updates' | 'advantages'>('updates')

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/80 backdrop-blur-sm p-4">
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-2xl max-h-[90vh] flex flex-col overflow-hidden animate-in fade-in zoom-in duration-200">
        {/* Header */}
        <div className="relative bg-gradient-to-r from-primary-600 to-primary-500 px-6 py-5 text-white shrink-0">
          <button
            onClick={onClose}
            className="absolute top-4 right-4 p-1 rounded-full hover:bg-white/20 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 rounded-xl bg-white/20 flex items-center justify-center backdrop-blur-sm">
              <Globe className="w-6 h-6" />
            </div>
            <div>
              <h2 className="text-xl font-bold">LabCanvas 版本更新</h2>
              <div className="flex items-center gap-3 mt-1 text-sm text-white/90">
                <span className="px-2 py-0.5 rounded-md bg-white/20 font-mono font-semibold">
                  {VERSION_DATA.version}
                </span>
                <span>{VERSION_DATA.date}</span>
                <span className="flex items-center gap-1">
                  <User className="w-3.5 h-3.5" />
                  {VERSION_DATA.author}
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* Tabs */}
        <div className="flex border-b border-gray-200 shrink-0">
          <button
            onClick={() => setActiveTab('updates')}
            className={`flex-1 py-3 text-sm font-medium transition-colors ${
              activeTab === 'updates'
                ? 'text-primary-600 border-b-2 border-primary-600'
                : 'text-gray-500 hover:text-gray-700'
            }`}
          >
            更新内容
          </button>
          <button
            onClick={() => setActiveTab('advantages')}
            className={`flex-1 py-3 text-sm font-medium transition-colors ${
              activeTab === 'advantages'
                ? 'text-primary-600 border-b-2 border-primary-600'
                : 'text-gray-500 hover:text-gray-700'
            }`}
          >
            核心亮点
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6">
          {activeTab === 'updates' && (
            <div className="space-y-5">
              {VERSION_DATA.updates.map((item, idx) => {
                const Icon = item.icon
                return (
                  <div
                    key={idx}
                    className="flex gap-4 p-4 rounded-xl bg-gray-50 border border-gray-100 hover:border-primary-200 transition-colors"
                  >
                    <div className="w-10 h-10 rounded-lg bg-primary-100 text-primary-600 flex items-center justify-center shrink-0">
                      <Icon className="w-5 h-5" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 flex-wrap">
                        <h3 className="font-semibold text-gray-900">{item.title}</h3>
                        <span className="px-1.5 py-0.5 rounded text-[11px] font-medium bg-primary-50 text-primary-600">
                          {item.highlight}
                        </span>
                      </div>
                      <p className="text-sm text-gray-600 mt-1 leading-relaxed">{item.desc}</p>
                    </div>
                  </div>
                )
              })}
            </div>
          )}

          {activeTab === 'advantages' && (
            <div className="space-y-5">
              {VERSION_DATA.advantages.map((item, idx) => (
                <div
                  key={idx}
                  className="p-4 rounded-xl bg-gradient-to-br from-primary-50/50 to-white border border-primary-100"
                >
                  <h3 className="font-semibold text-primary-700 mb-2 flex items-center gap-2">
                    <span className="w-6 h-6 rounded-full bg-primary-100 text-primary-600 flex items-center justify-center text-xs font-bold">
                      {idx + 1}
                    </span>
                    {item.title}
                  </h3>
                  <p className="text-sm text-gray-600 leading-relaxed">{item.desc}</p>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="px-6 py-4 border-t border-gray-200 bg-gray-50 shrink-0 flex items-center justify-between">
          <p className="text-xs text-gray-500">
            当前版本 {VERSION_DATA.version} · {VERSION_DATA.date}
          </p>
          <button
            onClick={onClose}
            className="px-5 py-2 bg-primary-600 text-white text-sm font-medium rounded-lg hover:bg-primary-700 transition-colors"
          >
            知道了
          </button>
        </div>
      </div>
    </div>
  )
}
