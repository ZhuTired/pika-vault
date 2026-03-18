from sqlalchemy.orm import Session
from backend.models import Credential, Bookmark, CredentialType
from backend.crypto import encrypt_value

def populate_example_data(db: Session):
    # Check if data already exists
    if db.query(Credential).first():
        return

    # --- Credentials ---
    credentials_data = [
        {
            "name": "Google 账号",
            "type": CredentialType.ACCOUNT,
            "tags": ["个人", "邮箱"],
            "fields": [
                {"name": "邮箱", "value": "ziggs@gmail.com", "is_sensitive": False},
                {"name": "密码", "value": "placeholder-pwd-xxxx", "is_sensitive": True}
            ],
            "notes": "Main Google Account"
        },
        {
            "name": "测试机 MySQL (1.1.1.1)",
            "type": CredentialType.DATABASE,
            "tags": ["工作", "测试机"],
            "fields": [
                {"name": "Host", "value": "1.1.1.1", "is_sensitive": False},
                {"name": "Port", "value": "3306", "is_sensitive": False},
                {"name": "用户名", "value": "root", "is_sensitive": False},
                {"name": "密码", "value": "placeholder-db-xxxx", "is_sensitive": True}
            ],
            "notes": None
        },
        {
            "name": "本地 MySQL",
            "type": CredentialType.DATABASE,
            "tags": ["开发", "本地"],
            "fields": [
                {"name": "Host", "value": "127.0.0.1", "is_sensitive": False},
                {"name": "Port", "value": "3306", "is_sensitive": False},
                {"name": "用户名", "value": "root", "is_sensitive": False},
                {"name": "密码", "value": "placeholder-local-xxxx", "is_sensitive": True}
            ],
            "notes": None
        },
        {
            "name": "公司 LLM",
            "type": CredentialType.AI_LLM,
            "tags": ["工作", "AI"],
            "fields": [
                {"name": "模型名称", "value": "Moonshot-v1", "is_sensitive": False},
                {"name": "APIKey", "value": "placeholder-llm-key-xxxx", "is_sensitive": True},
                {"name": "BaseURL", "value": "https://api.moontontech.com", "is_sensitive": False}
            ],
            "notes": None
        },
        {
            "name": "火山引擎数仓（国内）",
            "type": CredentialType.DATA_WAREHOUSE,
            "tags": ["工作", "数仓"],
            "fields": [
                {"name": "APIKey", "value": "placeholder-vke-cn-xxxx", "is_sensitive": True},
                {"name": "请求URL", "value": "https://console.volcengine.com/dataleap/api/cn", "is_sensitive": False}
            ],
            "notes": None
        },
        {
            "name": "Moonton 海外数仓",
            "type": CredentialType.DATA_WAREHOUSE,
            "tags": ["工作", "海外"],
            "fields": [
                {"name": "APIKey", "value": "placeholder-dw-global-xxxx", "is_sensitive": True},
                {"name": "请求URL", "value": "https://dataleap.bi.moonton.net/api", "is_sensitive": False}
            ],
            "notes": None
        },
        {
            "name": "阿里云 POC",
            "type": CredentialType.CLOUD,
            "tags": ["POC", "阿里云"],
            "fields": [
                {"name": "AccessKeyId", "value": "LTAI-placeholder-xxxx", "is_sensitive": False},
                {"name": "AccessKeySecret", "value": "placeholder-aliyun-sk-xxxx", "is_sensitive": True}
            ],
            "notes": "POC 测试账号，2024-12 申请"
        }
    ]

    for cred in credentials_data:
        encrypted_fields = []
        for field in cred["fields"]:
            f_data = field.copy()
            if f_data["is_sensitive"]:
                f_data["value"] = encrypt_value(f_data["value"])
            encrypted_fields.append(f_data)
        
        db_cred = Credential(
            name=cred["name"],
            type=cred["type"],
            tags=cred["tags"],
            fields=encrypted_fields,
            notes=cred["notes"]
        )
        db.add(db_cred)

    # --- Bookmarks ---
    bookmarks_data = [
        {
            "category": "Moonton 风控",
            "title": "国内数仓（火山引擎）",
            "url": "https://console.volcengine.com/dataleap/console/region:dataleap-console+cn-shanghai/overview?projectName=default",
            "favicon_url": "https://www.google.com/s2/favicons?domain=console.volcengine.com&sz=64"
        },
        {
            "category": "Moonton 风控",
            "title": "海外数仓（Dorado）",
            "url": "https://dataleap.bi.moonton.net/dorado/development/query/100044388?project=cn_82&version=-1",
            "favicon_url": "https://www.google.com/s2/favicons?domain=dataleap.bi.moonton.net&sz=64"
        },
        {
            "category": "个人工作",
            "title": "iconfont 图标库",
            "url": "https://www.iconfont.cn/",
            "favicon_url": "https://www.google.com/s2/favicons?domain=www.iconfont.cn&sz=64"
        },
        {
            "category": "个人工作",
            "title": "博客参考文章",
            "url": "https://www.cnblogs.com/dmcs95/p/11667817.html",
            "favicon_url": "https://www.google.com/s2/favicons?domain=www.cnblogs.com&sz=64"
        }
    ]

    for bm in bookmarks_data:
        db_bm = Bookmark(
            category=bm["category"],
            title=bm["title"],
            url=bm["url"],
            favicon_url=bm["favicon_url"]
        )
        db.add(db_bm)

    db.commit()
