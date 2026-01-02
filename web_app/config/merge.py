import logging
from typing import List
import time

from django.db import transaction

from util.time_utils import get_pre_date_time
from web_app.model.wa_accounts import WaAccountId, WaUserIdRecord, WaAccountQr, WaUserQrRecord
from web_app.model.wa_accounts2 import WaAccountId2, WaUserIdRecord2, WaAccountQr2, WaUserQrRecord2

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def merge_account_id():
    """
    将WaAccountId数据迁移到WaAccountId2中，同时处理WaUserQrRecord的管理迁移
    时间设置为'2000-1-1 00:00:00'，处理auto_now_add导致的时间插入问题
    """
    start_time = time.time()
    logger.info("开始迁移WaAccountId和相关数据到新表中...")
    t = '2000-1-1 00:00:00'
    
    # 清除之前使用特定时间戳创建的数据
    logger.info("开始清理之前使用特定时间戳创建的数据...")
    delete_start = time.time()
    WaAccountId2.objects.filter(create_time=t).delete()
    WaUserIdRecord2.objects.filter(create_time=t).delete()
    WaAccountQr2.objects.filter(create_time=t).delete()
    WaUserQrRecord2.objects.filter(create_time=t).delete()
    delete_end = time.time()
    logger.info(f"数据清理完成，耗时: {delete_end - delete_start:.2f}秒")
    
    # 迁移WaAccountId到WaAccountId2
    logger.info("开始迁移WaAccountId到WaAccountId2...")
    count = WaAccountId.objects.count()
    logger.info(f"WaAccountId总记录数: {count}")
    div = count / 10000
    
    for i in range(int(div + 1)):
        start = i * 10000
        end = min((i + 1) * 10000, count)
        logger.info(f"处理WaAccountId批次: {i+1}/{int(div + 1)}, 范围: [{start}, {end})")
        
        query_start = time.time()
        # 查询WaAccountId数据
        query_list = WaAccountId.objects.values(
            "id", "account_id", "country", "age", "work", "money", "mark", "link_mark",
            "op_user_id", "is_bind", "is_modify", "used", "images"
        )[start:end]
        query_end = time.time()
        logger.info(f"WaAccountId查询耗时: {query_end - query_start:.2f}秒, 查询记录数: {len(query_list)}")
        
        # 获取ids用于查询相关记录
        ids = [q['id'] for q in query_list]
        
        record_query_start = time.time()
        # 查询相关的WaUserIdRecord数据
        records = WaUserIdRecord.objects.filter(account_id__in=ids).values(
            "user_id", "account__account_id", "used"
        )
        record_query_end = time.time()
        logger.info(f"WaUserIdRecord关联查询耗时: {record_query_end - record_query_start:.2f}秒, 查询记录数: {len(records)}")
        
        # 准备WaAccountId2实例
        items: List[WaAccountId2] = []
        account_ids = []
        aid_map = {}
        
        prep_start = time.time()
        for q in query_list:
            aid_map[q['id']] = q["account_id"]
            account_ids.append(q["account_id"])
            q.pop("id")
            # 创建实例但不设置时间字段，因为auto_now_add和auto_now会覆盖它们
            m = WaAccountId2(**q)
            items.append(m)
        prep_end = time.time()
        logger.info(f"WaAccountId2实例准备耗时: {prep_end - prep_start:.2f}秒, 准备实例数: {len(items)}")

        logger.info(f"WaAccountId2 批量处理 = {len(items)}")
        
        # 使用bulk_create创建记录
        bulk_create_start = time.time()
        WaAccountId2.objects.bulk_create(items, batch_size=1000)
        bulk_create_end = time.time()
        logger.info(f"WaAccountId2批量创建耗时: {bulk_create_end - bulk_create_start:.2f}秒")

        # 由于auto_now_add和auto_now会覆盖时间字段，需要单独更新时间字段
        time_update_start = time.time()
        # 获取所有account_id用于批量更新
        account_ids_to_update = [item.account_id for item in items]
        # 使用in查询进行批量更新，而不是逐个更新
        if account_ids_to_update:
            WaAccountId2.objects.filter(account_id__in=account_ids_to_update, create_time__gt=get_pre_date_time()).update(
                create_time=t,
                update_time=t
            )
        time_update_end = time.time()
        logger.info(f"WaAccountId2时间字段更新耗时: {time_update_end - time_update_start:.2f}秒")

        # 准备WaUserIdRecord2实例
        record_map = {}
        for r in records:
            record_map[r['account__account_id']] = r
            r["create_time"] = t

        # 获取新创建的WaAccountId2数据
        fetch_start = time.time()
        news = WaAccountId2.objects.filter(account_id__in=account_ids, create_time=t).values(
            "id", "account_id"
        )
        fetch_end = time.time()
        logger.info(f"获取新创建的WaAccountId2数据耗时: {fetch_end - fetch_start:.2f}秒")
        
        record_items: List[WaUserIdRecord2] = []
        prep_record_start = time.time()
        for n in news:
            aid = n["account_id"]
            record = record_map.get(aid)
            try:
                if record is not None:
                    record.pop("account__account_id")
                    # 获取对应的account_id (WaAccountId2的id)
                    account_id_2 = n["id"]
                    record['account_id'] = account_id_2
                    record['create_time'] = t
                    record['update_time'] = t
                    m = WaUserIdRecord2(**record)
                    record_items.append(m)
            except Exception as e:
                logger.error(f"处理WaUserIdRecord2数据时出错: {e}")
        prep_record_end = time.time()
        logger.info(f"WaUserIdRecord2实例准备耗时: {prep_record_end - prep_record_start:.2f}秒, 准备实例数: {len(record_items)}")
        
        logger.info(f"WaUserIdRecord2 批量处理 = {len(record_items)}")

        # 批量创建记录
        bulk_create_record_start = time.time()
        WaUserIdRecord2.objects.bulk_create(record_items, batch_size=1000)
        bulk_create_record_end = time.time()
        logger.info(f"WaUserIdRecord2批量创建耗时: {bulk_create_record_end - bulk_create_record_start:.2f}秒")
        
        # 更新时间字段以确保它们是正确的
        time_update_record_start = time.time()
        for record in record_items:
            WaUserIdRecord2.objects.filter(
                account_id=record.account_id,
                user_id=record.user_id, create_time__gt=get_pre_date_time()
            ).update(
                create_time=t,
                update_time=t
            )
        time_update_record_end = time.time()
        logger.info(f"WaUserIdRecord2时间字段更新耗时: {time_update_record_end - time_update_record_start:.2f}秒")
    
    # 迁移WaAccountQr到WaAccountQr2
    logger.info("开始迁移WaAccountQr到WaAccountQr2...")
    qr_count = WaAccountQr.objects.count()
    logger.info(f"WaAccountQr总记录数: {qr_count}")
    qr_div = qr_count / 10000
    
    for i in range(int(qr_div + 1)):
        start = i * 10000
        end = min((i + 1) * 10000, qr_count)
        logger.info(f"处理WaAccountQr批次: {i+1}/{int(qr_div + 1)}, 范围: [{start}, {end})")
        
        qr_query_start = time.time()
        # 查询WaAccountQr数据
        qr_query_list = WaAccountQr.objects.values(
            "id", "qr_content", "qr_path", "country", "age", "work", "money", "mark", "link_mark",
            "op_user_id", "is_bind", "is_modify", "used"
        )[start:end]
        qr_query_end = time.time()
        logger.info(f"WaAccountQr查询耗时: {qr_query_end - qr_query_start:.2f}秒, 查询记录数: {len(qr_query_list)}")
        
        # 获取ids用于查询相关记录
        qr_ids = [q['id'] for q in qr_query_list]
        
        qr_record_query_start = time.time()
        # 查询相关的WaUserQrRecord数据
        qr_records = WaUserQrRecord.objects.filter(account_id__in=qr_ids).values(
            "user_id", "account__qr_content", "used"
        )
        qr_record_query_end = time.time()
        logger.info(f"WaUserQrRecord关联查询耗时: {qr_record_query_end - qr_record_query_start:.2f}秒, 查询记录数: {len(qr_records)}")
        
        # 准备WaAccountQr2实例
        qr_items = []
        qr_contents = []
        qr_aid_map = {}
        
        qr_prep_start = time.time()
        for q in qr_query_list:
            qr_aid_map[q['id']] = q["qr_content"]
            qr_contents.append(q["qr_content"])
            q.pop("id")
            # 创建实例但不设置时间字段，因为auto_now_add和auto_now会覆盖它们
            m = WaAccountQr2(**q)
            qr_items.append(m)
        qr_prep_end = time.time()
        logger.info(f"WaAccountQr2实例准备耗时: {qr_prep_end - qr_prep_start:.2f}秒, 准备实例数: {len(qr_items)}")

        logger.info(f"WaAccountQr2 批量处理 = {len(qr_items)}")
        
        # 使用bulk_create创建记录
        qr_bulk_create_start = time.time()
        WaAccountQr2.objects.bulk_create(qr_items, batch_size=1000)
        qr_bulk_create_end = time.time()
        logger.info(f"WaAccountQr2批量创建耗时: {qr_bulk_create_end - qr_bulk_create_start:.2f}秒")

        # 由于auto_now_add和auto_now会覆盖时间字段，需要单独更新时间字段
        qr_time_update_start = time.time()
        # 获取所有qr_content用于批量更新
        qr_contents_to_update = [item.qr_content for item in qr_items]
        # 使用in查询进行批量更新，而不是逐个更新
        if qr_contents_to_update:
            WaAccountQr2.objects.filter(qr_content__in=qr_contents_to_update, create_time__gt=get_pre_date_time()).update(
                create_time=t,
                update_time=t
            )
        qr_time_update_end = time.time()
        logger.info(f"WaAccountQr2时间字段更新耗时: {qr_time_update_end - qr_time_update_start:.2f}秒")

        # 准备WaUserQrRecord2实例
        qr_record_map = {}
        for r in qr_records:
            qr_record_map[r['account__qr_content']] = r
            r["create_time"] = t

        # 获取新创建的WaAccountQr2数据
        qr_fetch_start = time.time()
        qr_news = WaAccountQr2.objects.filter(qr_content__in=qr_contents, create_time=t).values(
            "id", "qr_content"
        )
        qr_fetch_end = time.time()
        logger.info(f"获取新创建的WaAccountQr2数据耗时: {qr_fetch_end - qr_fetch_start:.2f}秒")
        
        qr_record_items = []
        qr_prep_record_start = time.time()
        for n in qr_news:
            qr_content = n["qr_content"]
            record = qr_record_map.get(qr_content)
            if record is not None:
                try:
                    record.pop("account__qr_content")
                    # 获取对应的account_id (WaAccountQr2的id)
                    qr_account_id = n["id"]
                    record['account_id'] = qr_account_id
                    record['create_time'] = t
                    record['update_time'] = t
                    m = WaUserQrRecord2(**record)
                    qr_record_items.append(m)
                except Exception as e:
                    logger.error(f"处理WaUserQrRecord2实例错误: {e}")
        qr_prep_record_end = time.time()
        logger.info(f"WaUserQrRecord2实例准备耗时: {qr_prep_record_end - qr_prep_record_start:.2f}秒, 准备实例数: {len(qr_record_items)}")
        
        logger.info(f"WaUserQrRecord2 批量处理 = {len(qr_record_items)}")

        # 批量创建记录
        qr_bulk_create_record_start = time.time()
        WaUserQrRecord2.objects.bulk_create(qr_record_items, batch_size=1000)
        qr_bulk_create_record_end = time.time()
        logger.info(f"WaUserQrRecord2批量创建耗时: {qr_bulk_create_record_end - qr_bulk_create_record_start:.2f}秒")
        
        # 更新时间字段以确保它们是正确的
        qr_time_update_record_start = time.time()
        # 获取所有需要更新的account_id和user_id用于批量更新
        if qr_record_items:
            account_ids_to_update = [record.account_id for record in qr_record_items]
            user_ids_to_update = [record.user_id for record in qr_record_items]
            # 使用in查询进行批量更新，而不是逐个更新
            WaUserQrRecord2.objects.filter(
                account_id__in=account_ids_to_update,
                user_id__in=user_ids_to_update, create_time__gt=get_pre_date_time()
            ).update(
                create_time=t,
                update_time=t
            )
        qr_time_update_record_end = time.time()
        logger.info(f"WaUserQrRecord2时间字段更新耗时: {qr_time_update_record_end - qr_time_update_record_start:.2f}秒")

    end_time = time.time()
    logger.info(f"WaAccountId、WaUserIdRecord、WaAccountQr和WaUserQrRecord数据迁移完成，总耗时: {end_time - start_time:.2f}秒")