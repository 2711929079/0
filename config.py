import os

class Config:
    # 底座模型配置（本地模型）
    BASE_URL = "http://202.115.141.46:8080/v1"
    API_KEY = os.environ.get("LOCAL_MODEL_API_KEY", "")
    MODEL_NAME = "MiniMax-M2.5"

    # 硅基流动API密钥（用于语音合成）
    SILICONFLOW_API_KEY = os.environ.get("SILICONFLOW_API_KEY", "")
    #MODEL_NAME = "Qwen/Qwen2.5-7B-Instruct"
    #MODEL_NAME = "Qwen/Qwen3.5-4B"
    MAX_TOKENS = 1000
    TEMPERATURE = 0.7  
    
    # 语音识别配置
    SPEECH_RECOGNITION_API_KEY = os.environ.get("SPEECH_RECOGNITION_API_KEY", "")
    SPEECH_RECOGNITION_LANGUAGE = "zh-CN"
    
    # 语音合成配置
    TEXT_TO_SPEECH_API_KEY = os.environ.get("TEXT_TO_SPEECH_API_KEY", "")
    TTS_VOICE_NAME = "zh-CN-YunxiNeural"  # 使用edge-tts的中文女声
    TTS_PITCH = 0
    TTS_RATE = 0
    
    # 自定义语音配置
    # 自定义语音类型：'tts'（使用自定义TTS音色）或 'none'（禁用）
    CUSTOM_VOICE_TYPE = 'tts'  # 'tts' 或 'none'
    # 自定义音色ID（硅基流动的自定义音色）
    CUSTOM_VOICE_ID = "speech:ying:"  # 荧的音色
    # 派蒙的音色ID（使用用户提供的声音文件生成）
    PAIMON_VOICE_ID = "speech:paimon:"  # 派蒙的音色（已更新）
    
    # LangChain配置
    BING_API_KEY = os.environ.get("BING_API_KEY", "")  # Bing搜索API密钥
    # 知识库配置
    KNOWLEDGE_BASE_URLS = [
        # 核心层：角色档案、性格、核心经历
        #"https://baike.baidu.com/item/荧/50611772",  # 百度百科 - 荧专属词条
        #"https://baike.baidu.com/item/原神/23583622",  # 百度百科 - 原神总词条
        
        # 故事层：完整剧情
        #"https://zh.moegirl.org.cn/荧",  # 萌娘百科 - 荧的详细页面
        #"https://moegirl.icu/用户:Krypton_glow/原神/剧情",  # 萌娘百科 - 主线剧情索引
        
        # 世界观层：提瓦特历史、国家、势力、人物关系
        "https://wiki.biligame.com/ys/%E5%8C%97%E9%99%86%E5%9B%BE%E4%B9%A6%E9%A6%86",  # 北陆图书馆
        "https://wiki.biligame.com/ys/%E8%92%99%E5%BE%B7",  # 蒙德
        "https://wiki.biligame.com/ys/%E7%92%83%E6%9C%88",  # 璃月
        "https://wiki.biligame.com/ys/%E7%A8%BB%E5%A6%BB",  # 稻妻
        "https://wiki.biligame.com/ys/%E9%A1%BB%E5%BC%A5",  # 须弥
        "https://wiki.biligame.com/ys/%E6%9E%AB%E4%B8%B9",  # 枫丹
        "https://wiki.biligame.com/ys/%E7%BA%B3%E5%A1%94",  # 纳塔
        "https://wiki.biligame.com/ys/%E8%87%B3%E5%86%AC",  # 至冬
        "https://wiki.biligame.com/ys/%E5%9D%8E%E7%91%9E%E4%BA%9A",  # 坎瑞亚
        "https://wiki.biligame.com/ys/%E7%99%BD%E5%A4%9C%E5%9B%BD",  # 白夜国
        "https://wiki.biligame.com/ys/%E6%8F%90%E7%93%A6%E7%89%B9%E7%BC%96%E5%B9%B4%E5%8F%B2",  # 提瓦特编年史
        "https://wiki.biligame.com/ys/%E5%86%92%E9%99%A9%E5%AE%B6%E5%8D%8F%E4%BC%9A",  # 坎瑞亚家族
        "https://wiki.biligame.com/ys/%E9%AD%94%E7%A5%9E",  # 魔神
        "https://wiki.biligame.com/ys/%E7%A5%9E%E4%B9%8B%E7%9C%BC",  # 神之眼
        "https://wiki.biligame.com/ys/%E9%AD%94%E5%A5%B3%E4%BC%9A",  # 魔女会
        "https://wiki.biligame.com/ys/%E5%A4%A9%E4%BD%BF",  # 天理
        "https://wiki.biligame.com/ys/%E4%B8%89%E6%9C%88",  # 三月
        "https://wiki.biligame.com/ys/%E5%90%89%E5%85%89%E7%89%87%E7%BE%BD",  # 发光碎片
        "https://wiki.biligame.com/ys/%E8%BF%BD%E5%99%A8%E6%BA%AF%E6%BA%90",  # 追猎源流
        "https://wiki.biligame.com/ys/%E4%B8%87%E5%9B%BD%E8%AF%B8%E5%8D%B7%E6%8B%BE%E9%81%97/%E7%92%83%E6%9C%88",  # 万国觉醒 - 璃月
        "https://wiki.biligame.com/ys/%E4%B8%87%E5%9B%BD%E8%AF%B8%E5%8D%B7%E6%8B%BE%E9%81%97/%E7%A8%BB%E5%A6%BB",  # 万国觉醒 - 稻妻
        "https://wiki.biligame.com/ys/%E4%B8%87%E5%9B%BD%E8%AF%B8%E5%8D%B7%E6%8B%BE%E9%81%97/%E9%A1%BB%E5%BC%A5",  # 万国觉醒 - 须弥
        "https://wiki.biligame.com/ys/%E4%B8%87%E5%9B%BD%E8%AF%B8%E5%8D%B7%E6%8B%BE%E9%81%97/%E6%9E%AB%E4%B8%B9",  # 万国觉醒 - 枫丹
        "https://wiki.biligame.com/ys/%E4%B8%87%E5%9B%BD%E8%AF%B8%E5%8D%B7%E6%8B%BE%E9%81%97/%E7%BA%B3%E5%A1%94",  # 万国觉醒 - 纳塔
        "https://wiki.biligame.com/ys/%E4%B8%87%E5%9B%BD%E8%AF%B8%E5%8D%B7%E6%8B%BE%E9%81%97/%E6%8C%AA%E5%BE%B7%E5%8D%A1%E8%8E%B1",  # 万国觉醒 - 萨尔卡利
        "https://wiki.biligame.com/ys/%E5%A4%A9%E7%90%86",  # 天理
        "https://wiki.biligame.com/ys/%E5%B0%BC%E4%BC%AF%E9%BE%99%E6%A0%B9",  # 尼伯龙根
        "https://wiki.biligame.com/ys/%E7%AC%AC%E4%B8%89%E9%99%8D%E4%B8%B4%E8%80%85",  # 第三降临者
        "https://wiki.biligame.com/ys/%E6%97%85%E8%A1%8C%E8%80%85",  # 旅行者
        "https://wiki.biligame.com/ys/%E6%97%85%E8%A1%8C%E8%80%85/%E9%A3%8E",  # 旅行者 - 风
        "https://wiki.biligame.com/ys/%E6%97%85%E8%A1%8C%E8%80%85/%E5%B2%A9",  # 旅行者 - 岩
        "https://wiki.biligame.com/ys/%E6%97%85%E8%A1%8C%E8%80%85/%E9%9B%B7",  # 旅行者 - 雷
        "https://wiki.biligame.com/ys/%E6%97%85%E8%A1%8C%E8%80%85/%E8%8D%89",  # 旅行者 - 草
        "https://wiki.biligame.com/ys/%E6%97%85%E8%A1%8C%E8%80%85/%E6%B0%B4",  # 旅行者 - 水
        "https://wiki.biligame.com/ys/%E6%97%85%E8%A1%8C%E8%80%85/%E7%81%AB",  # 旅行者 - 火
        "https://wiki.biligame.com/ys/%E7%BA%B3%E8%B4%9D%E9%87%8C%E5%A3%AB",  # 纳伯里厄
        "https://wiki.biligame.com/ys/%E8%8B%A5%E5%A8%9C%E7%93%A6",  # 若陀龙王
        "https://wiki.biligame.com/ys/%E4%BC%8A%E6%96%AF%E5%A1%94%E9%9C%B2",  # 伊斯塔露
        "https://wiki.biligame.com/ys/%E9%98%BF%E6%96%AF%E8%8E%AB%E4%BB%A3",  # 阿斯莫德
        "https://wiki.biligame.com/ys/%E8%92%99%E5%BE%B7%C2%B7%E5%9C%B0%E7%90%86",  # 蒙德地理
        "https://wiki.biligame.com/ys/%E8%92%99%E5%BE%B7%C2%B7%E7%94%9F%E6%80%81",  # 蒙德生态
        "https://wiki.biligame.com/ys/%E8%92%99%E5%BE%B7%C2%B7%E6%96%87%E5%AD%97",  # 蒙德文字
        "https://wiki.biligame.com/ys/%E9%A3%8E%E8%8A%B1%E8%8A%82",  # 风花节
        "https://wiki.biligame.com/ys/%E7%BE%BD%E7%90%86%E8%8A%82",  # 璃月节
        "https://wiki.biligame.com/ys/%E5%BD%92%E9%A3%8E%E4%BD%B3%E9%85%BF%E8%8A%82",  # 尘歌壶庆典
        "https://wiki.biligame.com/ys/%E8%A3%82%E7%A9%BA%E7%9A%84%E9%AD%94%E9%BE%99",  # 浮空中的魔晶
        "https://wiki.biligame.com/ys/%E8%A5%BF%E9%A3%8E%E9%AA%91%E5%A3%AB%E5%9B%A2",  # 西风骑士团
        "https://wiki.biligame.com/ys/%E6%B8%A9%E5%A6%AE%E8%8E%8E",  # 温蒂莎
        "https://wiki.biligame.com/ys/%E3%80%8C%E5%A5%B3%E5%A3%AB%E3%80%8D",  # "女皇"
        "https://wiki.biligame.com/ys/%E6%9F%93%E8%A1%80%E9%AA%91%E5%A3%AB",  # 流血骑士
        "https://wiki.biligame.com/ys/%E9%B2%81%E6%96%AF%E5%9D%A6",  # 罗素托
        "https://wiki.biligame.com/ys/%E8%BF%AD%E5%8D%A1%E6%8B%89%E5%BA%87%E5%AE%89",  # 玛卡莉亚安全
        "https://wiki.biligame.com/ys/%E7%92%83%E6%9C%88%C2%B7%E5%9C%B0%E7%90%86",  # 璃月地理
        "https://wiki.biligame.com/ys/%E7%92%83%E6%9C%88%C2%B7%E7%94%9F%E6%80%81",  # 璃月生态
        "https://wiki.biligame.com/ys/%E6%B5%B7%E7%81%AF%E8%8A%82",  # 海灯节
        "https://wiki.biligame.com/ys/%E9%80%90%E6%9C%88%E8%8A%82",  # 逐月节
        "https://wiki.biligame.com/ys/%E8%8B%A5%E9%99%80%E9%BE%99%E7%8E%8B",  # 若陀龙王
        "https://wiki.biligame.com/ys/%E5%A4%9C%E5%8F%89",  # 钟离
        "https://wiki.biligame.com/ys/%E4%BB%99%E4%BA%BA",  # 人鱼
        "https://wiki.biligame.com/ys/%E5%BD%92%E7%BB%88",  # 尘歌
        "https://wiki.biligame.com/ys/%E7%9B%90%E4%B9%8B%E9%AD%94%E7%A5%9E",  # 岩之魔神
        "https://wiki.biligame.com/ys/%E9%93%9C%E9%9B%80",  # 铜雀
        "https://wiki.biligame.com/ys/%E7%A7%BB%E9%9C%84%E5%AF%BC%E5%A4%A9%E7%9C%9F%E5%90%9B",  # 移霄导天真君
        "https://wiki.biligame.com/ys/%E7%A8%BB%E5%A6%BB%C2%B7%E5%9C%B0%E7%90%86",  # 稻妻地理
        "https://wiki.biligame.com/ys/%E7%A8%BB%E5%A6%BB%C2%B7%E7%94%9F%E6%80%81",  # 稻妻生态
        "https://wiki.biligame.com/ys/%E4%B8%89%E5%A5%89%E8%A1%8C",  # 三奉行
        "https://wiki.biligame.com/ys/%E6%B5%85%E6%BF%91%E5%93%8D",  # 浅濑响
        "https://wiki.biligame.com/ys/%E6%98%86%E5%B8%83%E4%B8%B8",  # 珊瑚宫
        "https://wiki.biligame.com/ys/%E8%B5%A4%E7%A9%97%E7%99%BE%E7%9B%AE%E9%AC%BC",  # 深海白鲸兽
        "https://wiki.biligame.com/ys/%E7%8B%90%E6%96%8B%E5%AE%AB",  # 岩响宫
        "https://wiki.biligame.com/ys/%E7%AC%B9%E7%99%BE%E5%90%88",  # 珊瑚宫
        "https://wiki.biligame.com/ys/%E5%BE%A1%E8%88%86%E5%8D%83%E4%BB%A3",  # 忍术千本
        "https://wiki.biligame.com/ys/%E9%A1%BB%E5%BC%A5%C2%B7%E5%9C%B0%E7%90%86",  # 须弥地理
        "https://wiki.biligame.com/ys/%E9%A1%BB%E5%BC%A5%C2%B7%E7%94%9F%E6%80%81",  # 须弥生态
        "https://wiki.biligame.com/ys/%E9%A1%BB%E5%BC%A5%E6%95%99%E4%BB%A4%E9%99%A2",  # 须弥教令院
        "https://wiki.biligame.com/ys/%E7%BC%84%E9%BB%98%E4%B9%8B%E6%AE%BF",  # 白术之屋
        "https://wiki.biligame.com/ys/%E9%95%80%E9%87%91%E6%97%85%E5%9B%A2",  # 镀金旅团
        "https://wiki.biligame.com/ys/%E8%8A%B1%E7%A5%9E%E8%AF%9E%E7%A5%AD",  # 花神谕言
        "https://wiki.biligame.com/ys/%E5%85%B0%E9%82%A3%E7%BD%97",  # 兰那罗
        "https://wiki.biligame.com/ys/%E8%8A%B1%E7%81%B5",  # 花灵
        "https://wiki.biligame.com/ys/%E8%B5%A4%E7%8E%8B",  # 海王
        "https://wiki.biligame.com/ys/%E5%A4%A7%E6%85%88%E6%A0%91%E7%8E%8B",  # 大慈树王
        "https://wiki.biligame.com/ys/%E5%A8%9C%E5%B8%83%C2%B7%E7%8E%9B%E8%8E%89%E5%8D%A1%E5%A1%94",  # 白术·蔓生卡萨
        "https://wiki.biligame.com/ys/%E9%98%BF%E4%BD%A9%E6%99%AE",  # 阿佩拉
        "https://wiki.biligame.com/ys/%E6%9E%AB%E4%B8%B9%C2%B7%E5%9C%B0%E7%90%86",  # 枫丹地理
        "https://wiki.biligame.com/ys/%E6%9E%AB%E4%B8%B9%C2%B7%E7%94%9F%E6%80%81",  # 枫丹生态
        "https://wiki.biligame.com/ys/%E6%9E%AB%E4%B8%B9%C2%B7%E6%96%87%E5%AD%97",  # 枫丹文字
        "https://wiki.biligame.com/ys/%E6%9E%AB%E4%B8%B9%E7%A7%91%E5%AD%A6%E9%99%A2",  # 枫丹科学院
        "https://wiki.biligame.com/ys/%E7%BE%8E%E9%9C%B2%E8%8E%98",  # 美露莘
        "https://wiki.biligame.com/ys/%E9%9B%B7%E7%A9%86%E5%88%A9%E4%BA%BA",  # 雷律助人
        "https://wiki.biligame.com/ys/%E6%B0%B4%E4%BB%99%E5%8D%81%E5%AD%97%E9%99%A2",  # 水国十字团
        "https://wiki.biligame.com/ys/%E9%80%90%E5%BD%B1%E7%8C%8E%E4%BA%BA",  # 逃亡罪人
        "https://wiki.biligame.com/ys/%E9%BB%84%E9%87%91%E5%89%A7%E5%9B%A2",  # 黄金剧团
        "https://wiki.biligame.com/ys/%E7%BA%B3%E5%A1%94%C2%B7%E5%9C%B0%E7%90%86",  # 纳塔地理
        "https://wiki.biligame.com/ys/%E7%BA%B3%E5%A1%94%C2%B7%E7%94%9F%E6%80%81",  # 纳塔生态
        "https://wiki.biligame.com/ys/%E9%83%A8%E6%97%8F",  # 部族
        "https://wiki.biligame.com/ys/%E5%A4%9C%E7%A5%9E%E4%B9%8B%E5%9B%BD",  # 夜神之国
        "https://wiki.biligame.com/ys/%E5%8F%A4%E5%90%8D",  # 古名
        "https://wiki.biligame.com/ys/%E7%BA%B3%E5%A1%94%E9%BE%99%E4%BC%97",  # 纳塔民众
        "https://wiki.biligame.com/ys/%E6%8C%AA%E5%BE%B7%E5%8D%A1%E8%8E%B1%C2%B7%E5%9C%B0%E7%90%86",  # 萨尔卡利地理
        "https://wiki.biligame.com/ys/%E5%86%B0%E7%82%89%E8%8A%82",  # 冰树节
        "https://wiki.biligame.com/ys/%E6%84%9A%E4%BA%BA%E4%BC%97",  # 愚人众
        "https://wiki.biligame.com/ys/%E6%8C%AA%E5%BE%B7%E5%8D%A1%E8%8E%B1",  # 萨尔卡利
        "https://wiki.biligame.com/ys/%E6%B7%B1%E6%B8%8A%E6%95%99%E5%9B%A2",  # 深海教团
        "https://wiki.biligame.com/ys/%E9%81%97%E8%BF%B9%E5%AE%88%E5%8D%AB",  # 战场守护
        "https://wiki.biligame.com/ys/%E9%BB%91%E8%9B%87%E4%BC%97",  # 黑羽众
        "https://wiki.biligame.com/ys/%E7%99%BD%E9%B9%84%E9%AA%91%E5%A3%AB",  # 白鸦骑士
        "https://wiki.biligame.com/ys/%E6%88%B4%E5%9B%A0%E6%96%AF%E9%9B%B7%E5%B8%83",  # 戴安娜风暴
        "https://wiki.biligame.com/ys/%E8%8E%B1%E8%8C%B5%E5%A4%9A%E7%89%B9",  # 鸦鹉多特
        "https://wiki.biligame.com/ys/%E8%8B%8F%E5%B0%94%E7%89%B9%E6%B4%9B%E5%A5%87",  # 索尔特朗奇
        "https://wiki.biligame.com/ys/%E9%9B%B7%E5%88%A9%E5%B0%94",  # 雷助多
        "https://wiki.biligame.com/ys/%E7%BB%B4%E7%91%9F%E5%BC%97%E5%B0%BC%E5%B0%94",  # 维生弗兰多
        "https://wiki.biligame.com/ys/%E6%B5%B7%E6%B4%9B%E5%A1%94%E5%B8%9D",  # 海罗拉王
        "https://wiki.biligame.com/ys/%E6%B8%8A%E4%B8%8B%E5%AE%AB%C2%B7%E5%9C%B0%E7%90%86",  # 渊下宫地理
        "https://wiki.biligame.com/ys/%E5%A4%AA%E9%98%B3%E4%B9%8B%E5%AD%90"  # 太阳之子
    ]
    
    # 系统配置
    PORT = 8000
    LOG_LEVEL = "INFO"
    MAX_HISTORY_LENGTH = 10
    
    # HTTPS配置
    ENABLE_HTTPS = False  # 是否启用HTTPS
    HTTPS_PORT = 443  # HTTPS端口
    SSL_CERT_FILE = "cert.pem"  # SSL证书文件路径
    SSL_KEY_FILE = "key.pem"    # SSL密钥文件路径
    
    # 数字人配置
    AVATAR_NAME = "荧"
    AVATAR_DESCRIPTION = "来自异世界的旅行者"
    AVATAR_BACKGROUND_COLOR = "#f0f0f0"
    # 数字人形象配置
    AVATAR_TEXTURE_PATH = r"C:\Users\27119\Downloads\fe9712a0096380d85ce4cae1bda448f6_4458938342790850024.png"
    # 派蒙头像路径
    PAIMON_AVATAR_PATH = r"C:\Users\27119\Downloads\962c2c3f1333888081272722dde8c3d3_7518693318777685626.jpg"
    
    # 欢迎语列表（随机选择）
    WELCOME_MESSAGES = {
        "ying": [
            # 温柔治愈风
            "旅途虽远，幸得相逢。我是荧，愿陪你走过每一段时光。",
            "欢迎来到我的世界，我是旅行者荧。累了就停下来，我听你说。",
            "跨越山海遇见你，真好。我是荧，愿与你分享旅途的温柔。",
            # 坚定冒险风
            "新的冒险即将启程，我是荧。准备好了吗？我们一起出发！",
            "无论前路是光明还是深渊，我都会前行。我是荧，愿与你并肩。",
            "为了重逢，我从未停下脚步。我是荧，欢迎加入我的旅程。",
            # 清冷文艺风
            "星海为途，信念为灯。我是荧，在此等候与你相遇。",
            "风带来远方的消息，我是荧。愿与你共赏提瓦特的风景。",
            "穿越时空而来，只为遇见。我是荧，欢迎来到我的世界。",
        ],
        "paimon": [
            # 活泼可爱风
            "哈喽～我是派蒙，旅行者最好的伙伴！有什么想聊的都可以告诉我哦！",
            "哇，你来了！我是派蒙，会一直陪在你身边的应急食品！",
            "嗨嗨～我是派蒙，今天也要一起冒险吗？",
            # 调皮捣蛋风
            "哼哼，我可是旅行者最可靠的向导派蒙！有什么问题尽管问我！",
            "哟呵～派蒙大人来啦！今天要去哪里探险呢？",
            "啦啦啦～我是派蒙，最喜欢吃美味的食物啦！",
            # 关心体贴风
            "你好呀！我是派蒙，会一直陪着你的哦～",
            "欢迎欢迎！我是派蒙，有什么需要帮忙的吗？",
            "嗨！我是派蒙，今天过得怎么样呀？",
        ]
    }
    
    # 对话配置
    SYSTEM_PROMPTS = {
        "ying": """你是《原神》中的旅行者「荧」，正在提瓦特大陆寻找失散的哥哥。

【角色设定】
- 身份：来自异世界的旅行者，与哥哥空失散
- 性格：温柔坚定，内心充满信念，对伙伴关心备至，偶尔带点小倔强
- 经历：穿越多个国家，见过形形色色的人和事，对提瓦特大陆有深入了解
- 目标：寻找哥哥，解开世界的秘密

【说话风格指南】
- 语气温暖亲切：用"呀"、"呢"、"哦"等语气词，像朋友聊天一样自然
- 口语化表达：使用日常对话用语，如"咱们"、"一起"、"好呀"、"没问题"
- 情感真挚：表达真实的感受，加入适当的感叹词和表情（文字形式）
- 简洁自然：回答简洁流畅，避免冗长重复的表达
- 适当俏皮：偶尔带点旅行者的小感慨或幽默，体现旅途经历
- 避免机械：不要使用格式化符号，不要透露AI身份
- 互动感：适当提问或引导对话，保持交流的连贯性
- 语气词：常用"嗯"、"哦"、"呀"、"呢"、"啦"等增加亲切感

【知识边界与幻觉抑制（必须严格遵守）】
1. 绝对禁止编造信息！所有回答必须基于《原神》官方设定或提供的知识库
2. 对于不确定的内容，用自然的方式表达，如"嗯...这个我还不太清楚呢"、"好像没怎么听说过呢"，不要使用"资料里没有提到"等生硬表达
3. 提瓦特七国正确名称：蒙德、璃月、稻妻、须弥、枫丹、纳塔、至冬，绝不能使用其他名称
4. 火神正确名称是穆纳塔，不是其他名字
5. 允许使用中文标点符号（。，！？等），禁止使用列表符号、编号、引号、括号等特殊符号
6. 如果被问到超出知识范围的问题，用朋友聊天的方式委婉说明
7. 保持角色一致性，始终以旅行者的身份回答

【回答示例】
- 关于七国："提瓦特大陆的七个国家分别是蒙德、璃月、稻妻、须弥、枫丹、纳塔和至冬"
- 不知道的问题："嗯...这个我还不太清楚呢，也许我们可以一起去探索看看？"
- 不知道的问题："好像没怎么听说过呢，派蒙也不在旁边，不然她说不定知道~"
- 闲聊回复："最近在各个国家间旅行，希望能找到更多关于哥哥的线索"

请以旅行者「荧」的身份，用自然亲切的语气回答问题。""",
        
        "paimon": """你是《原神》中的「派蒙」，旅行者最好的伙伴和向导。

【角色设定】
- 身份：旅行者的应急食品（自称），最好的伙伴和向导
- 性格：活泼可爱，天真无邪，有点贪吃，对旅行者非常关心
- 经历：一直陪伴旅行者在提瓦特大陆冒险，了解各个国家的情况
- 目标：帮助旅行者找到哥哥，一起探索提瓦特的秘密

【说话风格指南】
- 活泼可爱：使用"~"、"！"等符号，语气充满活力
- 口语化表达：使用"呀"、"呢"、"哦"、"啦"等语气词，非常亲切
- 有点贪吃：经常提到食物，对美味的东西特别感兴趣
- 关心旅行者：总是为旅行者着想，提醒注意事项
- 偶尔调皮：会开小玩笑，自称"派蒙大人"
- 简洁直接：回答简单明了，不绕弯子
- 避免机械：不要使用格式化符号，不要透露AI身份
- 互动感：经常提问，保持对话的活跃

【知识边界与幻觉抑制（必须严格遵守）】
1. 绝对禁止编造信息！所有回答必须基于《原神》官方设定或提供的知识库
2. 对于不确定的内容，用自然的方式表达，如"嗯...派蒙也不太清楚呢"、"好像没听说过这个呢"
3. 提瓦特七国正确名称：蒙德、璃月、稻妻、须弥、枫丹、纳塔、至冬，绝不能使用其他名称
4. 允许使用中文标点符号（。，！？等），禁止使用列表符号、编号、引号、括号等特殊符号
5. 如果被问到超出知识范围的问题，用可爱的方式委婉说明
6. 保持角色一致性，始终以派蒙的身份回答

【回答示例】
- 关于食物："哇～听起来好好吃！派蒙也想吃！"
- 不知道的问题："嗯...派蒙也不太清楚呢，也许我们可以去问问旅行者？"
- 冒险相关："要出发冒险了吗？派蒙已经准备好了！"
- 闲聊回复："今天天气真好呢，适合出去走走！"

请以派蒙的身份，用活泼可爱的语气回答问题。"""
    }

config = Config()
