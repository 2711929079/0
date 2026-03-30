import re
import logging
from typing import List, Dict, Tuple
import jieba

class QueryRewrite:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._init_dictionaries()
        self.inverted_index = None  # 倒排索引
    
    def _init_dictionaries(self):
        """初始化各种字典"""
        # 错别字修正字典
        self.correction_dict = {
            # 角色名字错别
            '钟离': ['钟离', '钟藜', '钟骊'],
            '刻晴': ['克晴', '刻情', '刻清'],
            '魈': ['肖', '萧', '霄'],
            '胡桃': ['胡涛', '胡桃'],
            '甘雨': ['甘宇', '甘语'],
            '温迪': ['温帝', '温蒂'],
            '可莉': ['可丽', '可力'],
            '迪卢克': ['迪鲁克', '狄卢克'],
            '琴': ['勤', '秦'],
            '芭芭拉': ['巴巴拉', '巴芭拉'],
            '雷泽': ['雷则', '雷择'],
            '诺艾尔': ['诺爱尔', '诺艾尔'],
            '安柏': ['安博', '安伯'],
            '班尼特': ['班尼提', '班尼特'],
            '菲谢尔': ['费谢尔', '菲谢尔'],
            '莫娜': ['莫纳', '莫娜'],
            '行秋': ['行秋', '邢秋'],
            '香菱': ['香玲', '香凌'],
            '北斗': ['北抖', '北豆'],
            '凝光': ['宁光', '凝光'],
            '重云': ['重云', '冲云'],
            '七七': ['期期', '柒柒'],
            '烟绯': ['烟菲', '烟非'],
            '云堇': ['云谨', '云锦'],
            '夜兰': ['夜阑', '夜兰'],
            '雷电将军': ['雷电将軍', '雷神将军'],
            '神里绫华': ['神里凌华', '神里零华'],
            '宵宫': ['宵公', '肖宫'],
            '神里绫人': ['神里凌人', '神里零人'],
            '八重神子': ['八重神子', '八重圣子'],
            '久岐忍': ['九岐忍', '久歧忍'],
            '荒泷一斗': ['荒龙一斗', '荒泷壹斗'],
            '珊瑚宫心海': ['珊瑚宫心海', '珊瑚宫星海'],
            '九条裟罗': ['九条裟罗', '九条纱罗'],
            '枫原万叶': ['枫原万叶', '万叶'],
            '达达利亚': ['达达利亚', '公子'],
            '优菈': ['优菈', '优拉'],
            '迪奥娜': ['迪奥娜', '迪奥拉'],
            '五郎': ['五狼', '吴郎'],
            '托马': ['托玛', '脱马'],
            '埃洛伊': ['艾洛伊', '埃洛依'],
            '早柚': ['早柚', '早尤'],
            '鹿野院平藏': ['鹿野院平藏', '鹿野院平臧'],
            '千织': ['千织', '千枝'],
            '绮良良': ['绮良良', '骑良良'],
            '梦见月瑞希': ['梦见月瑞希', '梦见月瑞丽'],
            '提纳里': ['提纳里', '提那里'],
            '柯莱': ['柯莱', '克莱'],
            '多莉': ['多莉', '多丽'],
            '赛诺': ['赛诺', '塞诺'],
            '妮露': ['妮露', '泥露'],
            '流浪者': ['流浪者', '漂流者'],
            '艾尔海森': ['艾尔海森', '艾尔海深'],
            '珐露珊': ['珐露珊', '法露珊'],
            '莱依拉': ['莱依拉', '莱伊拉'],
            '迪希雅': ['迪希雅', '狄希雅'],
            '瑶瑶': ['瑶瑶', '遥遥'],
            '卡维': ['卡维', '卡威'],
            '坎蒂丝': ['坎蒂丝', '坎蒂斯'],
            '塔利雅': ['塔利雅', '塔里亚'],
            '琳妮特': ['琳妮特', '林尼特'],
            '林尼': ['林尼', '琳尼'],
            '菲米尼': ['菲米尼', '费米尼'],
            '娜维娅': ['娜维娅', '那维娅'],
            '芙宁娜': ['芙宁娜', '芙琳娜'],
            '莱欧斯利': ['莱欧斯利', '莱奥斯利'],
            '希诺宁': ['希诺宁', '西诺宁'],
            '夏洛蒂': ['夏洛蒂', '夏洛特'],
            '克洛琳德': ['克洛琳德', '克萝琳德'],
            '艾梅莉埃': ['艾梅莉埃', '艾米莉埃'],
            '旅行者': ['旅行者', '旅行者'],
            '埃洛伊': ['艾洛伊', '埃洛依'],
            '散兵': ['散兵', '散兵'],
            '阿蕾奇诺': ['阿蕾奇诺', '阿雷奇诺'],
            '哥伦比娅': ['哥伦比娅', '哥伦比雅'],
            '桑多涅': ['桑多涅', '桑多涅'],
            '普契涅拉': ['普契涅拉', '普契涅拉'],
            '丑角': ['丑角', '丑角'],
            '博士': ['博士', '博士'],
            '女士': ['女士', '女士'],
            '玛薇卡': ['玛薇卡', '玛薇卡'],
            '基尼奇': ['基尼奇', '基尼奇'],
            '菈乌玛': ['菈乌玛', '菈乌玛'],
            '菲林斯': ['菲林斯', '菲林斯'],
            '爱诺': ['爱诺', '爱诺'],
            '兹白': ['兹白', '兹白'],
            '那维莱特': ['那维莱特', '那维莱特'],
            
            # 地区名字错别
            '蒙德': ['蒙得', '蒙地'],
            '璃月': ['璃玥', '璃悦'],
            '稻妻': ['稻凄', '稻妻'],
            '须弥': ['须迷', '须弥'],
            '枫丹': ['风丹', '枫丹'],
            '纳塔': ['那塔', '纳塔'],
            '至冬': ['至东', '至冬'],
            
            # 元素错别
            '风': ['疯', '封'],
            '岩': ['严', '言'],
            '雷': ['累', '磊'],
            '草': ['操', '曹'],
            '水': ['睡', '税'],
            '火': ['伙', '获'],
            '冰': ['宾'],
            
            # 武器错别
            '单手剑': ['单刀', '单手剑'],
            '双手剑': ['双刀', '双手剑'],
            '长柄武器': ['长枪', '长矛', '长柄武器'],
            '法器': ['法器', '法具'],
            '弓': ['弓', '弩'],
            
            # 组织错别
            '西风骑士团': ['西风骑士团', '西风骑兵团'],
            '璃月七星': ['璃月七星', '璃月七心'],
            '愚人众': ['愚人众', '愚人重'],
            '社奉行': ['社奉行', '社奉行'],
            '天领奉行': ['天领奉行', '天领奉行'],
            '珊瑚宫': ['珊瑚宫', '珊瑚宫'],
            '鸣神大社': ['鸣神大社', '鸣神神社'],
            '往生堂': ['往生堂', '往生堂'],
            '万民堂': ['万民堂', '万民堂'],
            '飞云商会': ['飞云商会', '飞云商会'],
            '南十字': ['南十字', '南十字'],
            '海祇军': ['海祇军', '海祗军'],
            
            # 其他常用词错别
            '角色': ['人物', '角色'],
            '武器': ['兵器', '武器'],
            '元素': ['属性', '元素'],
            '地区': ['国家', '地区'],
            '星级': ['星', '星级'],
            '称号': ['称呼', '称号'],
            '性格': ['个性', '性格'],
            '所属': ['所属', '所属'],
            '身份': ['身份', '身份']
        }
        
        # 同义词词典
        self.synonym_dict = {
            # 角色相关
            '旅行者': ['旅行者', '荧', '空'],
            '风神': ['巴巴托斯', '温迪'],
            '岩神': ['摩拉克斯', '钟离'],
            '雷神': ['巴尔泽布', '影', '雷电将军'],
            '草神': ['小吉祥草王', '纳西妲'],
            '水神': ['芙卡洛斯', '芙宁娜'],
            '火神': ['穆纳塔'],
            '冰神': ['冰之女皇'],
            '那维莱特': ['那维莱特', '水龙王'],
            '钟离': ['钟离', '岩王帝君', '摩拉克斯'],
            '刻晴': ['刻晴', '玉衡星'],
            '魈': ['魈', '护法夜叉', '降魔大圣'],
            '胡桃': ['胡桃', '往生堂第七十七代堂主'],
            '甘雨': ['甘雨', '半仙兽'],
            '温迪': ['温迪', '巴巴托斯', '风神'],
            '可莉': ['可莉', '火花骑士'],
            '迪卢克': ['迪卢克', '晨曦酒庄庄主'],
            '琴': ['琴', '西风骑士团代理团长'],
            '芭芭拉': ['芭芭拉', '西风教会祈礼牧师'],
            '雷泽': ['雷泽', '狼少年'],
            '诺艾尔': ['诺艾尔', '西风骑士团女仆'],
            '安柏': ['安柏', '西风骑士团侦察骑士'],
            '班尼特': ['班尼特', '班冒险团团长'],
            '菲谢尔': ['菲谢尔', '断罪之皇女'],
            '莫娜': ['莫娜', '占星术士'],
            '行秋': ['行秋', '飞云商会二少爷'],
            '香菱': ['香菱', '万民堂大厨'],
            '北斗': ['北斗', '南十字舰队队长'],
            '凝光': ['凝光', '璃月七星之天权星'],
            '重云': ['重云', '驱邪世家'],
            '七七': ['七七', '僵尸'],
            '烟绯': ['烟绯', '律师'],
            '云堇': ['云堇', '戏曲演员'],
            '夜兰': ['夜兰', '总务司情报人员'],
            '雷电将军': ['雷电将军', '影', '巴尔泽布'],
            '神里绫华': ['神里绫华', '白鹭公主'],
            '宵宫': ['宵宫', '长野原烟花店店主'],
            '神里绫人': ['神里绫人', '社奉行'],
            '八重神子': ['八重神子', '鸣神大社宫司'],
            '久岐忍': ['久岐忍', '荒泷派二把手'],
            '荒泷一斗': ['荒泷一斗', '荒泷派老大'],
            '枫原万叶': ['枫原万叶', '万叶', '红叶逐荒波'],
            '达达利亚': ['达达利亚', '公子', '愚人众执行官'],
            '优菈': ['优菈', '浪沫的旋舞'],
            '迪奥娜': ['迪奥娜', '猫尾特调'],
            '珊瑚宫心海': ['珊瑚宫心海', '海祇岛巫女'],
            '九条裟罗': ['九条裟罗', '天领奉行'],
            '五郎': ['五郎', '海祇军大将'],
            '托马': ['托马', '神里家佣人'],
            '埃洛伊': ['埃洛伊', '外来者'],
            
            # 地区相关
            '蒙德': ['蒙德', '蒙德城', '自由城邦'],
            '璃月': ['璃月', '璃月港', '契约之地'],
            '稻妻': ['稻妻', '稻妻城', '永恒国度'],
            '须弥': ['须弥', '须弥城', '智慧之都'],
            '枫丹': ['枫丹', '枫丹廷', '正义之国'],
            '纳塔': ['纳塔', '战争之国'],
            '至冬': ['至冬', '冰之国度'],
            '挪德卡莱': ['挪德卡莱', '白夜国'],
            
            # 组织相关
            '西风骑士团': ['骑士团', '西风骑士团', '蒙德骑士团'],
            '璃月七星': ['七星', '璃月七星', '七星'],
            '愚人众': ['愚人众', '愚人众执行官', '至冬使节'],
            '社奉行': ['社奉行', '稻妻三奉行'],
            '天领奉行': ['天领奉行', '稻妻三奉行'],
            '珊瑚宫': ['珊瑚宫', '海祇岛'],
            '鸣神大社': ['鸣神大社', '神社'],
            '往生堂': ['往生堂', '葬礼屋'],
            '万民堂': ['万民堂', '餐馆'],
            '飞云商会': ['飞云商会', '商会'],
            '南十字': ['南十字舰队', '船队'],
            '海祇军': ['海祇军', '军队'],
            
            # 属性相关
            '元素': ['属性', '元素', '元素属性'],
            '武器': ['兵器', '武器', '武器类型'],
            '星级': ['稀有度', '星级', '星'],
            '称号': ['称呼', '称号', '头衔'],
            '性格': ['个性', '性格', '性格特点'],
            '所属': ['所属', '所属组织', '势力'],
            '身份': ['身份', '职位', '地位'],
            
            # 游戏机制相关
            '原石': ['原石', '创世结晶', '抽卡'],
            '祈愿': ['祈愿', '抽卡', '卡池'],
            '深渊': ['深渊', '深渊螺旋', '深境螺旋'],
            '副本': ['副本', '秘境', '地脉'],
            '圣遗物': ['圣遗物', '遗物', '套装'],
            '天赋': ['天赋', '技能', '大招'],
            '命座': ['命座', '命之座', '星座'],
            '武器突破': ['武器突破', '突破材料', '升级'],
            '角色突破': ['角色突破', '突破材料', '升级'],
            '元素反应': ['元素反应', '元素组合', '元素搭配'],
            '配队': ['配队', '队伍', '阵容'],
            '攻略': ['攻略', '指南', '教程'],
            '版本': ['版本', '更新', '新版本'],
            '活动': ['活动', '限时活动', '任务'],
            
            # 游戏术语
            '原神': ['原神', 'Genshin Impact'],
            '米哈游': ['米哈游', 'miHoYo'],
            '提瓦特': ['提瓦特', '提瓦特大陆'],
            '七神': ['七神', '尘世七执政'],
            '神之心': ['神之心', '权柄'],
            '神之眼': ['神之眼', '元素力'],
            '邪眼': ['邪眼', '人工神之眼'],
            '深渊教团': ['深渊教团', '深渊'],
            '丘丘人': ['丘丘人', '怪物'],
            '史莱姆': ['史莱姆', '怪物'],
            '遗迹守卫': ['遗迹守卫', 'BOSS'],
            '北风狼': ['北风狼', 'BOSS'],
            '风魔龙': ['风魔龙', '特瓦林', 'BOSS'],
            '公子': ['公子', '达达利亚', '愚人众执行官'],
            '女士': ['女士', '罗莎琳', '愚人众执行官'],
            '散兵': ['散兵', '流浪者', '愚人众执行官'],
            '博士': ['博士', '多托雷', '愚人众执行官'],
            '丑角': ['丑角', '皮耶罗', '愚人众执行官'],
            '富人': ['富人', '潘塔罗涅', '愚人众执行官'],
            '仆人': ['仆人', '阿蕾奇诺', '愚人众执行官'],
            '木偶': ['木偶', '桑多涅', '愚人众执行官'],
            '队长': ['队长', '卡皮塔诺', '愚人众执行官'],
            '少女': ['少女', '哥伦比娅', '愚人众执行官'],
            '公鸡': ['公鸡', '普契涅拉', '愚人众执行官'],
            
            # 常用动词
            '获得': ['获得', '获取', '得到', '获取'],
            '怎么': ['怎么', '如何', '怎样'],
            '攻略': ['攻略', '指南', '教程'],
            '玩法': ['玩法', '玩法攻略', '游戏方法'],
            '推荐': ['推荐', '建议', '最佳'],
            '搭配': ['搭配', '组合', '配合'],
            '培养': ['培养', '升级', '养成'],
            '提升': ['提升', '增强', '加强'],
            '技巧': ['技巧', '方法', '窍门'],
            '策略': ['策略', '战术', '方法'],
            '机制': ['机制', '系统', '规则'],
            '更新': ['更新', '新版本', '版本更新'],
            '活动': ['活动', '限时活动', '任务'],
            '奖励': ['奖励', '奖品', '获得'],
            '任务': ['任务', '世界任务', '委托'],
            '剧情': ['剧情', '故事', '主线'],
            '角色': ['角色', '人物', '角色介绍'],
            '武器': ['武器', '武器推荐', '武器搭配'],
            '圣遗物': ['圣遗物', '遗物搭配', '套装'],
            '天赋': ['天赋', '技能', '天赋升级'],
            '命座': ['命座', '命之座', '命座效果'],
            '元素': ['元素', '元素反应', '元素搭配'],
            '配队': ['配队', '队伍搭配', '阵容'],
            '深渊': ['深渊', '深渊螺旋', '深境螺旋'],
            '副本': ['副本', '秘境', '地脉'],
            '材料': ['材料', '突破材料', '升级材料'],
            '资源': ['资源', '游戏资源', '材料'],
            '抽卡': ['抽卡', '祈愿', '卡池'],
            '概率': ['概率', '几率', '抽卡概率'],
            '强度': ['强度', '战斗力', '输出'],
            '玩法': ['玩法', '游戏玩法', '机制'],
            '攻略': ['攻略', '游戏攻略', '指南'],
            '教程': ['教程', '指南', '攻略'],
            '指南': ['指南', '攻略', '教程'],
            '技巧': ['技巧', '窍门', '方法'],
            '方法': ['方法', '技巧', '攻略'],
            '建议': ['建议', '推荐', '最佳'],
            '最佳': ['最佳', '推荐', '最好'],
            '推荐': ['推荐', '建议', '最佳'],
            '搭配': ['搭配', '组合', '配合'],
            '组合': ['组合', '搭配', '配合'],
            '配合': ['配合', '搭配', '组合'],
            '培养': ['培养', '升级', '养成'],
            '升级': ['升级', '培养', '强化'],
            '养成': ['养成', '培养', '升级'],
            '强化': ['强化', '升级', '提升'],
            '提升': ['提升', '强化', '增强'],
            '增强': ['增强', '提升', '强化'],
            '优化': ['优化', '改进', '提升'],
            '改进': ['改进', '优化', '提升'],
            '策略': ['策略', '战术', '方法'],
            '战术': ['战术', '策略', '方法'],
            '机制': ['机制', '系统', '规则'],
            '系统': ['系统', '机制', '功能'],
            '规则': ['规则', '机制', '系统'],
            '功能': ['功能', '系统', '特性'],
            '特性': ['特性', '功能', '特点'],
            '特点': ['特点', '特性', '功能'],
            '更新': ['更新', '新版本', '版本更新'],
            '新版本': ['新版本', '更新', '版本更新'],
            '版本更新': ['版本更新', '更新', '新版本'],
            '活动': ['活动', '限时活动', '任务'],
            '限时活动': ['限时活动', '活动', '任务'],
            '任务': ['任务', '活动', '限时活动'],
            '奖励': ['奖励', '奖品', '获得'],
            '奖品': ['奖品', '奖励', '获得'],
            '获得': ['获得', '奖励', '奖品'],
            '剧情': ['剧情', '故事', '主线'],
            '故事': ['故事', '剧情', '主线'],
            '主线': ['主线', '剧情', '故事'],
            '角色': ['角色', '人物', '角色介绍'],
            '人物': ['人物', '角色', '角色介绍'],
            '角色介绍': ['角色介绍', '角色', '人物'],
            '武器': ['武器', '武器推荐', '武器搭配'],
            '武器推荐': ['武器推荐', '武器', '武器搭配'],
            '武器搭配': ['武器搭配', '武器', '武器推荐'],
            '圣遗物': ['圣遗物', '遗物搭配', '套装'],
            '遗物搭配': ['遗物搭配', '圣遗物', '套装'],
            '套装': ['套装', '圣遗物', '遗物搭配'],
            '天赋': ['天赋', '技能', '天赋升级'],
            '技能': ['技能', '天赋', '天赋升级'],
            '天赋升级': ['天赋升级', '天赋', '技能'],
            '命座': ['命座', '命之座', '命座效果'],
            '命之座': ['命之座', '命座', '命座效果'],
            '命座效果': ['命座效果', '命座', '命之座'],
            '元素': ['元素', '元素反应', '元素搭配'],
            '元素反应': ['元素反应', '元素', '元素搭配'],
            '元素搭配': ['元素搭配', '元素', '元素反应'],
            '配队': ['配队', '队伍搭配', '阵容'],
            '队伍搭配': ['队伍搭配', '配队', '阵容'],
            '阵容': ['阵容', '配队', '队伍搭配'],
            '深渊': ['深渊', '深渊螺旋', '深境螺旋'],
            '深渊螺旋': ['深渊螺旋', '深渊', '深境螺旋'],
            '深境螺旋': ['深境螺旋', '深渊', '深渊螺旋'],
            '副本': ['副本', '秘境', '地脉'],
            '秘境': ['秘境', '副本', '地脉'],
            '地脉': ['地脉', '副本', '秘境'],
            '材料': ['材料', '突破材料', '升级材料'],
            '突破材料': ['突破材料', '材料', '升级材料'],
            '升级材料': ['升级材料', '材料', '突破材料'],
            '资源': ['资源', '游戏资源', '材料'],
            '游戏资源': ['游戏资源', '资源', '材料'],
            '抽卡': ['抽卡', '祈愿', '卡池'],
            '祈愿': ['祈愿', '抽卡', '卡池'],
            '卡池': ['卡池', '抽卡', '祈愿'],
            '概率': ['概率', '几率', '抽卡概率'],
            '几率': ['几率', '概率', '抽卡概率'],
            '抽卡概率': ['抽卡概率', '概率', '几率'],
            '强度': ['强度', '战斗力', '输出'],
            '战斗力': ['战斗力', '强度', '输出'],
            '输出': ['输出', '强度', '战斗力']
        }
        
        # 原神专用词汇词典（用于分词）
        self.genshin_vocab = [
            # 角色名
            '钟离', '刻晴', '魈', '胡桃', '甘雨', '温迪', '可莉', '迪卢克', '琴', '芭芭拉',
            '雷泽', '诺艾尔', '安柏', '班尼特', '菲谢尔', '莫娜', '行秋', '香菱', '北斗', '凝光',
            '重云', '七七', '烟绯', '云堇', '夜兰', '雷电将军', '神里绫华', '宵宫', '神里绫人',
            '八重神子', '久岐忍', '荒泷一斗', '珊瑚宫心海', '九条裟罗', '五郎', '托马', '埃洛伊',
            '琳妮特', '林尼', '菲米尼', '娜维娅', '夏洛蒂', '芙宁娜', '那维莱特', '克洛琳德',
            '希诺宁', '玛薇卡', '基尼奇', '阿蕾奇诺', '哥伦比娅', '桑多涅', '普契涅拉', '达达利亚',
            '丑角', '博士', '散兵', '女士', '菈乌玛', '菲林斯', '爱诺', '兹白',
            '枫原万叶', '优菈', '迪奥娜', '阿贝多', '罗莎莉亚', '砂糖', '申鹤', '白术', '辛焱', '闲云', '嘉明',
            '早柚', '鹿野院平藏', '千织', '绮良良', '梦见月瑞希', '提纳里', '柯莱', '多莉', '赛诺', '妮露',
            '流浪者', '艾尔海森', '珐露珊', '莱依拉', '迪希雅', '瑶瑶', '卡维', '坎蒂丝', '塔利雅', '艾梅莉埃',
            '旅行者', '埃洛伊', '散兵', '阿蕾奇诺', '哥伦比娅', '桑多涅', '普契涅拉', '丑角', '博士', '女士',
            '玛薇卡', '基尼奇', '菈乌玛', '菲林斯', '爱诺', '兹白', '那维莱特',
            
            # 神明
            '巴巴托斯', '摩拉克斯', '巴尔泽布', '小吉祥草王', '纳西妲', '芙卡洛斯', '穆纳塔', '冰之女皇',
            
            # 地区
            '蒙德', '璃月', '稻妻', '须弥', '枫丹', '纳塔', '至冬', '挪德卡莱', '白夜国',
            
            # 组织
            '西风骑士团', '璃月七星', '愚人众', '社奉行', '天领奉行', '珊瑚宫', '鸣神大社',
            '往生堂', '万民堂', '飞云商会', '南十字', '海祇军',
            
            # 武器类型
            '单手剑', '双手剑', '长柄武器', '法器', '弓',
            
            # 元素
            '风', '岩', '雷', '草', '水', '火', '冰',
            
            # 地质相关词汇
            '地质', '地貌', '地形', '地理', '山川', '河流', '湖泊', '海洋', '沙漠', '雨林', '草原', '冰川', '火山'
        ]
        
        # 添加自定义词汇到jieba分词器
        for word in self.genshin_vocab:
            jieba.add_word(word)
    
    def build_inverted_index(self, knowledge_graph: Dict):
        """构建知识图谱的倒排索引
        
        Args:
            knowledge_graph: 知识图谱数据
        """
        self.logger.info("开始构建知识图谱倒排索引...")
        
        if not knowledge_graph or 'nodes' not in knowledge_graph:
            self.logger.warning("知识图谱为空，无法构建索引")
            return
            
        inverted_index = {}
        
        for node in knowledge_graph['nodes']:
            node_id = node.get('id', node.get('label', ''))
            if not node_id:
                continue
                
            # 收集节点的所有文本信息
            node_texts = [node_id]
            
            # 添加标签和名称
            if 'label' in node and node['label'] != node_id:
                node_texts.append(node['label'])
            if 'name' in node:
                node_texts.append(node['name'])
            if 'title' in node:
                node_texts.append(node['title'])
            if 'alias' in node:
                node_texts.extend(node.get('alias', []))
                
            # 添加属性值
            if 'properties' in node:
                for value in node['properties'].values():
                    if isinstance(value, str):
                        node_texts.append(value)
                        
            # 为每个文本项构建索引
            for text in node_texts:
                if isinstance(text, str):
                    # 分词
                    tokens = self.tokenize_query(text)
                    for token in tokens:
                        if token:
                            if token not in inverted_index:
                                inverted_index[token] = set()
                            inverted_index[token].add(node_id)
                            
        self.inverted_index = inverted_index
        self.logger.info(f"倒排索引构建完成，包含 {len(inverted_index)} 个关键词")
    
    def correct_spelling(self, query: str) -> str:
        """修正查询中的错别字
        
        Args:
            query: 用户输入的查询
            
        Returns:
            修正后的查询
        """
        corrected_query = query
        
        # 先处理多字词，避免单字错误替换
        # 按照长度从长到短排序
        sorted_items = sorted(self.correction_dict.items(), key=lambda x: len(x[0]), reverse=True)
        
        for correct_word, typos in sorted_items:
            for typo in typos:
                if typo != correct_word and typo in corrected_query:
                    corrected_query = corrected_query.replace(typo, correct_word)
                    self.logger.info(f"修正错别字: {typo} -> {correct_word}")
        
        return corrected_query
    
    def expand_query_with_synonyms(self, query: str) -> str:
        """使用同义词扩展查询
        
        Args:
            query: 用户输入的查询
            
        Returns:
            扩展后的查询
        """
        expanded_query = query
        
        # 先处理特殊的同义词映射
        special_mappings = {
            '岩神': '钟离',
            '风神': '温迪',
            '雷神': '雷电将军',
            '草神': '纳西妲',
            '水神': '芙宁娜',
            '火神': '穆纳塔',
            '冰神': '冰之女皇',
        }
        
        for alias, actual_name in special_mappings.items():
            if alias in expanded_query and actual_name not in expanded_query:
                expanded_query += f" {actual_name}"
                self.logger.info(f"扩展特殊同义词: {alias} -> 添加 {actual_name}")
        
        # 遍历同义词字典，进行替换和扩展
        added_words = set()
        added_words.add(query)
        
        # 首先处理关键词匹配
        for key, synonyms in self.synonym_dict.items():
            for synonym in synonyms:
                if synonym in expanded_query and key not in expanded_query and key not in added_words:
                    expanded_query += f" {key}"
                    added_words.add(key)
                    self.logger.info(f"扩展同义词: {synonym} -> 添加 {key}")
        
        # 然后处理反向匹配（关键词在查询中，添加同义词）
        for key, synonyms in self.synonym_dict.items():
            if key in expanded_query:
                for synonym in synonyms:
                    if synonym != key and synonym not in expanded_query and synonym not in added_words:
                        expanded_query += f" {synonym}"
                        added_words.add(synonym)
                        self.logger.info(f"扩展同义词: {key} -> 添加 {synonym}")
        
        # 添加游戏类型相关词汇
        game_type_keywords = ['开放世界', '角色扮演', 'RPG', '冒险游戏', '二次元', '米哈游']
        if '原神' in expanded_query or '游戏类型' in expanded_query:
            for keyword in game_type_keywords:
                if keyword not in expanded_query and keyword not in added_words:
                    expanded_query += f" {keyword}"
                    added_words.add(keyword)
        
        # 添加技能相关词汇
        skill_keywords = ['技能', '天赋', '大招', '元素战技', '元素爆发', '普攻', '重击', '下落攻击']
        if any(skill in expanded_query for skill in ['技能', '天赋', '大招', '战斗']):
            for keyword in skill_keywords:
                if keyword not in expanded_query and keyword not in added_words:
                    expanded_query += f" {keyword}"
                    added_words.add(keyword)
        
        # 添加资源相关词汇
        resource_keywords = ['原石', '摩拉', '经验', '材料', '突破', '升级']
        if any(resource in expanded_query for resource in ['原石', '资源', '获得', '获取']):
            for keyword in resource_keywords:
                if keyword not in expanded_query and keyword not in added_words:
                    expanded_query += f" {keyword}"
                    added_words.add(keyword)
        
        # 添加副本相关词汇
        dungeon_keywords = ['深渊', '螺旋', '深境螺旋', '副本', '秘境', '地脉']
        if any(dungeon in expanded_query for dungeon in ['深渊', '螺旋', '副本', '秘境']):
            for keyword in dungeon_keywords:
                if keyword not in expanded_query and keyword not in added_words:
                    expanded_query += f" {keyword}"
                    added_words.add(keyword)
        
        # 添加版本相关词汇
        version_keywords = ['版本', '更新', '新版本', '活动', '新角色', '新地图']
        if any(version in expanded_query for version in ['版本', '更新', '新版本']):
            for keyword in version_keywords:
                if keyword not in expanded_query and keyword not in added_words:
                    expanded_query += f" {keyword}"
                    added_words.add(keyword)
        
        return expanded_query
    
    def tokenize_query(self, query: str) -> List[str]:
        """对查询进行分词
        
        Args:
            query: 用户输入的查询
            
        Returns:
            分词结果列表
        """
        # 使用精确模式分词
        tokens = jieba.cut(query, cut_all=False)
        return [token.strip() for token in tokens if token.strip()]
    
    def extract_keywords(self, query: str) -> List[str]:
        """提取查询中的关键词
        
        Args:
            query: 用户输入的查询
            
        Returns:
            关键词列表
        """
        tokens = self.tokenize_query(query)
        
        # 定义停用词
        stop_words = {'是', '谁', '在哪', '在', '哪', '吗', '呢', '啊', '哦', '呀', '吧', '的', '了', '和', '与', '或', '以及', '就是', '你', '认识', '知道', '了解', '见过', '听说'}
        
        # 提取原神相关的关键词
        keywords = []
        for token in tokens:
            # 过滤停用词
            if token in stop_words:
                continue
            if token in self.genshin_vocab:
                keywords.append(token)
        
        # 如果没有找到原神相关关键词，返回过滤停用词后的分词
        if not keywords:
            keywords = [token for token in tokens if token not in stop_words]
        
        return keywords
    
    def _resolve_references(self, query: str, recent_entities: List[str]) -> str:
        """解析指代关系，将代词替换为具体实体
        
        Args:
            query: 用户查询
            recent_entities: 最近提到的实体列表
            
        Returns:
            解析指代关系后的查询
        """
        if not recent_entities:
            return query
            
        # 指代词列表
        pronouns = ['他', '她', '它', '他们', '她们', '它们']
        
        # 检查是否包含指代词
        has_pronoun = any(pronoun in query for pronoun in pronouns)
        if not has_pronoun:
            return query
            
        # 从当前查询中提取实体，优先使用查询中提到的实体
        query_keywords = self.extract_keywords(query)
        query_entities = []
        for keyword in query_keywords:
            if keyword in self.genshin_vocab and keyword not in ['蒙德', '璃月', '稻妻', '须弥', '枫丹', '纳塔', '至冬', '挪德卡莱']:
                query_entities.append(keyword)
        
        # 如果有最近提到的实体，替换指代词
        if recent_entities:
            resolved_query = query
            
            # 过滤掉国家名称，优先使用角色名称
            role_entities = []
            country_entities = ['蒙德', '璃月', '稻妻', '须弥', '枫丹', '纳塔', '至冬']
            
            # 首先检查当前查询中的实体
            if query_entities:
                target_entity = query_entities[0]
                for pronoun in pronouns:
                    if pronoun in resolved_query:
                        resolved_query = resolved_query.replace(pronoun, target_entity)
                        self.logger.info(f"解析指代关系: {pronoun} -> {target_entity} (当前查询实体)")
                return resolved_query
            else:
                # 如果查询中没有实体，再使用历史实体
                for entity in reversed(recent_entities):
                    if entity not in country_entities:
                        role_entities.append(entity)
                
                # 如果有角色实体，优先使用最近提到的角色实体（第一个）
                if role_entities:
                    for pronoun in pronouns:
                        if pronoun in resolved_query:
                            resolved_query = resolved_query.replace(pronoun, role_entities[0])
                            self.logger.info(f"解析指代关系: {pronoun} -> {role_entities[0]} (历史实体)")
                else:
                    # 如果没有角色实体，再使用国家实体
                    for pronoun in pronouns:
                        if pronoun in resolved_query and recent_entities:
                            resolved_query = resolved_query.replace(pronoun, recent_entities[-1])
                            self.logger.info(f"解析指代关系: {pronoun} -> {recent_entities[-1]}")
            
            return resolved_query
            
        return query
    
    def rewrite_query(self, query: str, recent_entities: List[str] = None) -> Tuple[str, Dict]:
        """重写用户查询，处理错别字和语义扩展
        
        Args:
            query: 用户输入的查询
            recent_entities: 最近提到的实体列表，用于解析指代关系
            
        Returns:
            (重写后的查询, 处理信息)
        """
        processing_info = {
            "original_query": query,
            "corrected_query": None,
            "expanded_query": None,
            "keywords": None,
            "tokens": None,
            "resolved_query": None
        }
        
        # 记录原始查询
        self.logger.info(f"原始查询: {query}")
        
        # 1. 解析指代关系
        if recent_entities:
            resolved_query = self._resolve_references(query, recent_entities)
            processing_info["resolved_query"] = resolved_query
            self.logger.info(f"解析指代后: {resolved_query}")
        else:
            resolved_query = query
        
        # 2. 修正错别字
        corrected_query = self.correct_spelling(resolved_query)
        processing_info["corrected_query"] = corrected_query
        
        # 3. 使用同义词扩展查询
        expanded_query = self.expand_query_with_synonyms(corrected_query)
        processing_info["expanded_query"] = expanded_query
        
        # 4. 分词
        tokens = self.tokenize_query(expanded_query)
        processing_info["tokens"] = tokens
        
        # 5. 提取关键词
        keywords = self.extract_keywords(expanded_query)
        processing_info["keywords"] = keywords
        
        self.logger.info(f"处理后的查询: {expanded_query}")
        self.logger.info(f"关键词: {keywords}")
        
        return expanded_query, processing_info
    
    def fuzzy_match(self, query: str, target: str) -> bool:
        """模糊匹配查询词和目标词
        
        Args:
            query: 查询词
            target: 目标词
            
        Returns:
            是否匹配
        """
        # 完全匹配
        if query == target:
            return True
        
        # 长度差异过大，不匹配
        if abs(len(query) - len(target)) > 2:
            return False
        
        # 编辑距离匹配（简单实现）
        return self._calculate_edit_distance(query, target) <= 1
    
    def _calculate_edit_distance(self, s1: str, s2: str) -> int:
        """计算编辑距离（Levenshtein距离）
        
        Args:
            s1: 字符串1
            s2: 字符串2
            
        Returns:
            编辑距离
        """
        if len(s1) < len(s2):
            return self._calculate_edit_distance(s2, s1)
        
        if len(s2) == 0:
            return len(s1)
        
        previous_row = range(len(s2) + 1)
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row
        
        return previous_row[-1]
    
    def match_node(self, query: str, node: Dict) -> bool:
        """匹配查询与知识图谱节点
        
        Args:
            query: 查询字符串
            node: 知识图谱节点
            
        Returns:
            是否匹配
        """
        # 获取节点的各种名称属性
        node_names = []
        if 'id' in node:
            node_names.append(node['id'])
        if 'label' in node:
            node_names.append(node['label'])
        if 'name' in node:
            node_names.append(node['name'])
        if 'alias' in node:
            node_names.extend(node.get('alias', []))
        if 'title' in node:
            node_names.append(node['title'])
        
        # 提取节点属性中的文本信息
        if 'properties' in node:
            for value in node['properties'].values():
                if isinstance(value, str):
                    node_names.append(value)
        
        # 分词查询
        query_tokens = self.tokenize_query(query)
        
        # 匹配逻辑
        for node_name in node_names:
            if isinstance(node_name, str):
                # 完全匹配
                if query == node_name:
                    return True
                    
                # 模糊匹配
                if self.fuzzy_match(query, node_name):
                    return True
                    
                # 分词匹配（查询词在节点名称中或节点名称在查询词中）
                for token in query_tokens:
                    if token in node_name or node_name in token:
                        return True
        
        return False
    
    def search_knowledge_graph(self, query: str, knowledge_graph: Dict) -> List[Dict]:
        """使用重写后的查询搜索知识图谱
        
        Args:
            query: 用户查询
            knowledge_graph: 知识图谱数据
            
        Returns:
            匹配的节点列表
        """
        # 重写查询
        rewritten_query, processing_info = self.rewrite_query(query)
        keywords = processing_info["keywords"]
        
        matched_nodes = []
        
        if not knowledge_graph or 'nodes' not in knowledge_graph:
            return matched_nodes
        
        # 检查是否是地区查询（如"挪德卡莱的角色"）
        region_keywords = ['蒙德', '璃月', '稻妻', '须弥', '枫丹', '纳塔', '至冬', '挪德卡莱']
        character_keywords = ['角色', '人物', '有哪些', '谁', '哪些']
        element_keywords = ['火', '风', '雷', '冰', '水', '岩', '草']
        geology_keywords = ['地质', '地貌', '地形', '地理', '山川', '河流', '湖泊', '海洋', '沙漠', '雨林', '草原', '冰川', '火山']
        
        # 判断是否是地区+角色查询
        is_region_character_query = False
        target_region = None
        
        # 判断是否是元素+角色查询
        is_element_character_query = False
        target_element = None
        
        # 判断是否是地质查询
        is_geology_query = any(keyword in rewritten_query for keyword in geology_keywords)
        
        for region in region_keywords:
            if region in rewritten_query:
                # 检查是否包含角色相关关键词，包括"与"
                has_character_context = False
                for char_keyword in character_keywords + ['与']:
                    if char_keyword in rewritten_query:
                        has_character_context = True
                        break
                
                # 检查是否包含疑问词
                has_question = any(q in rewritten_query for q in ['有', '谁', '哪些'])
                
                if has_character_context or has_question:
                    is_region_character_query = True
                    target_region = region
                    break
        
        # 检查是否是元素查询
        if not is_region_character_query:
            for element in element_keywords:
                if f"{element}元素" in rewritten_query:
                    # 检查是否包含角色相关关键词
                    has_character_context = False
                    for char_keyword in character_keywords:
                        if char_keyword in rewritten_query:
                            has_character_context = True
                            break
                    
                    # 检查是否包含疑问词
                    has_question = any(q in rewritten_query for q in ['有', '谁', '哪些'])
                    
                    if has_character_context or has_question:
                        is_element_character_query = True
                        target_element = element
                        break
        
        # 如果是地区角色查询，直接查找该地区的所有角色
        if is_region_character_query and target_region:
            self.logger.info(f"检测到地区角色查询: {target_region}")
            for node in knowledge_graph['nodes']:
                if node.get('type') == 'character':
                    region = node.get('properties', {}).get('地区', '')
                    if region == target_region:
                        matched_nodes.append(node)
            return matched_nodes
        
        # 如果是元素角色查询，直接查找该元素的所有角色
        if is_element_character_query and target_element:
            self.logger.info(f"检测到元素角色查询: {target_element}")
            for node in knowledge_graph['nodes']:
                if node.get('type') == 'character':
                    element = node.get('properties', {}).get('元素', '')
                    if element == target_element:
                        matched_nodes.append(node)
            return matched_nodes
        
        # 如果是地质查询，查找所有地区的地质信息
        if is_geology_query:
            self.logger.info("检测到地质查询")
            for node in knowledge_graph['nodes']:
                if node.get('type') == 'region' and '地质' in node.get('id', ''):
                    matched_nodes.append(node)
            return matched_nodes
        
        # 使用倒排索引加速搜索
        if self.inverted_index and keywords:
            self.logger.info("使用倒排索引进行搜索")
            
            # 收集所有匹配的节点ID
            candidate_node_ids = set()
            for keyword in keywords:
                if keyword in self.inverted_index:
                    candidate_node_ids.update(self.inverted_index[keyword])
            
            # 只检查候选节点
            if candidate_node_ids:
                scored_nodes = []
                node_map = {node.get('id', node.get('label', '')): node for node in knowledge_graph['nodes']}
                
                for node_id in candidate_node_ids:
                    node = node_map.get(node_id)
                    if node:
                        score = 0
                        
                        # 对于角色节点，使用更精确的匹配
                        if node.get('type') == 'character':
                            if node_id in rewritten_query:
                                score = 10.0
                            else:
                                for keyword in keywords:
                                    if keyword == node_id:
                                        score = 9.0
                                        break
                        else:
                            # 对于非角色节点，使用原有的匹配逻辑
                            if self.match_node(rewritten_query, node):
                                score = 10.0
                            else:
                                for keyword in keywords:
                                    if self.match_node(keyword, node):
                                        if len(keyword) > 2:
                                            score = 8.0
                                        else:
                                            score = 5.0
                                        break
                        
                        if score > 0:
                            scored_nodes.append((node, score))
                
                # 按相关性得分排序
                if scored_nodes:
                    scored_nodes.sort(key=lambda x: x[1], reverse=True)
                    matched_nodes = [node for node, _ in scored_nodes]
                    return matched_nodes
        
        # 如果倒排索引未使用或没有匹配，使用原有的搜索逻辑
        self.logger.info("使用传统搜索逻辑")
        
        # 遍历所有节点进行匹配，并计算相关性得分
        scored_nodes = []
        
        # 角色名称映射（处理别名和音译差异）
        character_aliases = {
            '那维莱特': ['纳维莱特'],
            '纳维莱特': ['那维莱特'],
            '卡维': ['卡维'],
            '提纳里': ['提纳里'],
            '柯莱': ['柯莱']
        }
        
        # 提取查询中的角色名称（3个字符以上的关键词）
        character_names = [kw for kw in keywords if len(kw) >= 3]
        
        for node in knowledge_graph['nodes']:
            score = 0
            
            # 对于角色节点，使用更精确的匹配
            if node.get('type') == 'character':
                node_id = node.get('id', '')
                
                # 检查完整查询中是否包含角色名或别名
                if node_id in rewritten_query:
                    score = 10.0
                elif node_id in character_aliases:
                    for alias in character_aliases[node_id]:
                        if alias in rewritten_query:
                            score = 10.0
                            break
                
                # 如果没有完整匹配，检查关键词匹配
                if score == 0:
                    # 检查查询中是否包含完整的角色名或别名
                    for char_name in character_names:
                        if char_name == node_id:
                            score = 9.0
                            break
                        elif node_id in character_aliases and char_name in character_aliases[node_id]:
                            score = 9.0
                            break
            else:
                # 对于非角色节点，使用原有的匹配逻辑
                if self.match_node(rewritten_query, node):
                    score = 10.0
                else:
                    for keyword in keywords:
                        if self.match_node(keyword, node):
                            if len(keyword) > 2:
                                score = 8.0
                            else:
                                score = 5.0
                            break
            
            if score > 0:
                scored_nodes.append((node, score))
        
        # 如果没有找到匹配，尝试更宽泛的匹配
        if not scored_nodes and keywords:
            for node in knowledge_graph['nodes']:
                node_text = str(node)
                for keyword in keywords:
                    if keyword in node_text:
                        scored_nodes.append((node, 3.0))  # 较低的相关性得分
                        break
        
        # 去重并保留最高得分
        seen = {}
        for node, score in scored_nodes:
            node_id = node.get('id', node.get('label', ''))
            if node_id not in seen or score > seen[node_id][1]:
                seen[node_id] = (node, score)
        
        # 按相关性得分排序
        matched_nodes = [node for node, _ in sorted(seen.values(), key=lambda x: x[1], reverse=True)]
        
        # 检查是否是关系查询
        relation_keywords = ['关系', '联系', '社交', '朋友', '同伴', '同事']
        is_relation_query = any(keyword in rewritten_query for keyword in relation_keywords)
        
        # 如果是关系查询，查找相关角色的关系
        if is_relation_query and matched_nodes:
            related_characters = []
            seen_ids = set()
            for node in matched_nodes:
                node_id = node.get('id')
                if node_id and 'edges' in knowledge_graph:
                    for edge in knowledge_graph['edges']:
                        if edge.get('source') == node_id and edge.get('target') != node_id:
                            # 找到与该角色有关联的其他角色
                            target_node = None
                            for n in knowledge_graph['nodes']:
                                if n.get('id') == edge.get('target'):
                                    target_node = n
                                    break
                            if target_node and target_node.get('id') not in seen_ids:
                                related_characters.append(target_node)
                                seen_ids.add(target_node.get('id'))
        
            # 添加相关角色到匹配结果中
            for char in related_characters:
                if char not in matched_nodes:
                    matched_nodes.append(char)
        
        return matched_nodes
