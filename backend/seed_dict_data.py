"""
Seed data script for dictionary items:
1. 地区: 山东省 + 16个地级市（二级省-市结构）
2. 行业: 固定分类（政府单位、事业单位、其他）+ 常见企业行业
3. 商机来源: 常见商机来源
"""

import asyncio
import sys
from sqlalchemy import text
from app.database import async_session_maker

DICT_DATA = {
    "地区": [
        # 山东省（parent_id=None）
        {"id": 1, "code": "37", "name": "山东省", "parent_id": None, "sort_order": 1},
        # 山东省下辖16个地级市
        {"id": 101, "code": "3701", "name": "济南市", "parent_id": 1, "sort_order": 1},
        {"id": 102, "code": "3702", "name": "青岛市", "parent_id": 1, "sort_order": 2},
        {"id": 103, "code": "3703", "name": "淄博市", "parent_id": 1, "sort_order": 3},
        {"id": 104, "code": "3704", "name": "枣庄市", "parent_id": 1, "sort_order": 4},
        {"id": 105, "code": "3705", "name": "东营市", "parent_id": 1, "sort_order": 5},
        {"id": 106, "code": "3706", "name": "烟台市", "parent_id": 1, "sort_order": 6},
        {"id": 107, "code": "3707", "name": "潍坊市", "parent_id": 1, "sort_order": 7},
        {"id": 108, "code": "3708", "name": "济宁市", "parent_id": 1, "sort_order": 8},
        {"id": 109, "code": "3709", "name": "泰安市", "parent_id": 1, "sort_order": 9},
        {"id": 110, "code": "3710", "name": "威海市", "parent_id": 1, "sort_order": 10},
        {"id": 111, "code": "3711", "name": "日照市", "parent_id": 1, "sort_order": 11},
        {"id": 112, "code": "3713", "name": "临沂市", "parent_id": 1, "sort_order": 12},
        {"id": 113, "code": "3714", "name": "德州市", "parent_id": 1, "sort_order": 13},
        {"id": 114, "code": "3715", "name": "聊城市", "parent_id": 1, "sort_order": 14},
        {"id": 115, "code": "3716", "name": "滨州市", "parent_id": 1, "sort_order": 15},
        {"id": 116, "code": "3717", "name": "菏泽市", "parent_id": 1, "sort_order": 16},
    ],
    "行业": [
        # 固定分类
        {
            "id": 2,
            "code": "GOV",
            "name": "政府单位",
            "parent_id": None,
            "sort_order": 1,
        },
        {
            "id": 3,
            "code": "PSU",
            "name": "事业单位",
            "parent_id": None,
            "sort_order": 2,
        },
        {"id": 4, "code": "OTHER", "name": "其他", "parent_id": None, "sort_order": 3},
        # 常见企业行业
        {"id": 5, "code": "MFG", "name": "制造", "parent_id": None, "sort_order": 4},
        {"id": 6, "code": "CHEM", "name": "化工", "parent_id": None, "sort_order": 5},
        {"id": 7, "code": "PHA", "name": "医药", "parent_id": None, "sort_order": 6},
        {"id": 8, "code": "ENER", "name": "能源", "parent_id": None, "sort_order": 7},
        {"id": 9, "code": "AUTO", "name": "汽车", "parent_id": None, "sort_order": 8},
        {"id": 10, "code": "CHIP", "name": "芯片", "parent_id": None, "sort_order": 9},
        {
            "id": 11,
            "code": "IT",
            "name": "信息技术",
            "parent_id": None,
            "sort_order": 10,
        },
        {"id": 12, "code": "FIN", "name": "金融", "parent_id": None, "sort_order": 11},
        {"id": 13, "code": "EDU", "name": "教育", "parent_id": None, "sort_order": 12},
        {
            "id": 14,
            "code": "HEALTH",
            "name": "医疗",
            "parent_id": None,
            "sort_order": 13,
        },
        {
            "id": 15,
            "code": "RETAIL",
            "name": "零售",
            "parent_id": None,
            "sort_order": 14,
        },
        {
            "id": 16,
            "code": "LOGST",
            "name": "物流",
            "parent_id": None,
            "sort_order": 15,
        },
        {
            "id": 17,
            "code": "CONST",
            "name": "建筑",
            "parent_id": None,
            "sort_order": 16,
        },
        {"id": 18, "code": "AGRI", "name": "农业", "parent_id": None, "sort_order": 17},
        {
            "id": 19,
            "code": "TELECOM",
            "name": "通信",
            "parent_id": None,
            "sort_order": 18,
        },
        {
            "id": 20,
            "code": "MEDIA",
            "name": "传媒",
            "parent_id": None,
            "sort_order": 19,
        },
    ],
    "商机来源": [
        {
            "id": 21,
            "code": "REF",
            "name": "客户推荐",
            "parent_id": None,
            "sort_order": 1,
        },
        {
            "id": 22,
            "code": "WEB",
            "name": "网络推广",
            "parent_id": None,
            "sort_order": 2,
        },
        {"id": 23, "code": "EXPO", "name": "展会", "parent_id": None, "sort_order": 3},
        {
            "id": 24,
            "code": "CALL",
            "name": "电话营销",
            "parent_id": None,
            "sort_order": 4,
        },
        {
            "id": 25,
            "code": "EXIST",
            "name": "老客户二次开发",
            "parent_id": None,
            "sort_order": 5,
        },
        {
            "id": 26,
            "code": "PART",
            "name": "合作伙伴推荐",
            "parent_id": None,
            "sort_order": 6,
        },
    ],
    "客户状态": [
        {
            "id": 27,
            "code": "POTENTIAL",
            "name": "潜在",
            "parent_id": None,
            "sort_order": 1,
        },
        {
            "id": 28,
            "code": "ACTIVE",
            "name": "活跃",
            "parent_id": None,
            "sort_order": 2,
        },
        {
            "id": 29,
            "code": "CONTRACTED",
            "name": "已签约",
            "parent_id": None,
            "sort_order": 3,
        },
        {
            "id": 30,
            "code": "DORMANT",
            "name": "休眠",
            "parent_id": None,
            "sort_order": 4,
        },
        {
            "id": 31,
            "code": "CHURNED",
            "name": "流失",
            "parent_id": None,
            "sort_order": 5,
        },
    ],
}


async def seed_dict_items():
    async with async_session_maker() as session:
        # Check existing dict_types to avoid duplicates
        for dict_type in DICT_DATA.keys():
            result = await session.execute(
                text("SELECT COUNT(*) FROM dict_items WHERE dict_type = :dt"),
                {"dt": dict_type},
            )
            count = result.scalar()

            if count > 0:
                print(f"  跳过 '{dict_type}' — 已存在 {count} 条记录")
                continue

            for item in DICT_DATA[dict_type]:
                await session.execute(
                    text(
                        """
                        INSERT INTO dict_items (id, dict_type, code, name, parent_id, sort_order, is_active)
                        VALUES (:id, :dict_type, :code, :name, :parent_id, :sort_order, true)
                        ON CONFLICT DO NOTHING
                        """
                    ),
                    {
                        "id": item["id"],
                        "dict_type": dict_type,
                        "code": item["code"],
                        "name": item["name"],
                        "parent_id": item["parent_id"],
                        "sort_order": item["sort_order"],
                    },
                )
            # Reset sequence after explicit ID inserts
            await session.execute(
                text(
                    "SELECT setval('dict_items_id_seq', (SELECT MAX(id) FROM dict_items))"
                )
            )
            await session.commit()
            print(f"  已插入 '{dict_type}' — {len(DICT_DATA[dict_type])} 条记录")


async def main():
    print("开始导入数据字典...")
    for dict_type, items in DICT_DATA.items():
        print(f"\n  【{dict_type}】")

    await seed_dict_items()

    print("\n数据字典导入完成！")

    # Show loaded data
    from app.database import engine

    async with engine.connect() as conn:
        result = await conn.execute(
            text(
                "SELECT dict_type, COUNT(*) as cnt FROM dict_items GROUP BY dict_type ORDER BY dict_type"
            )
        )
        print("\n当前数据字典统计：")
        for row in result:
            print(f"  {row[0]}: {row[1]} 条")


if __name__ == "__main__":
    asyncio.run(main())
