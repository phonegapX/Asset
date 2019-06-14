# -*- coding:utf-8 -*-

"""
OKEx 账户资产

Author: HuangTao
Date:   2019/01/20
"""

from quant.const import OKEX
from quant.utils import tools
from quant.utils import logger
from quant.event import EventAsset
from quant.tasks import LoopRunTask
from quant.platform.okex import OKExRestAPI


class OKExAsset:
    """ 账户资金
    self._assets
    {
        "BTC": {
            "free": 11.11,
            "locked": 22.22,
            "total": 33.33
        },
        ...
    }
    """

    def __init__(self, account, access_key, secret_key, passphrase, host=None):
        """ 初始化
        @param host 请求的host
        @param account 资产账户
        @param access_key 请求的access_key
        @param secret_key 请求的secret_key
        @param passphrase API KEY的密码
        """
        self._platform = OKEX
        self._host = host or "https://www.okex.com"
        self._account = account
        self._access_key = access_key
        self._secret_key = secret_key
        self._passphrase = passphrase
        self._update_interval = 10  # 更新时间间隔(秒)

        self._assets = {}  # 所有资金详情

        # 创建rest api请求对象
        self._rest_api = OKExRestAPI(self._host, self._access_key, self._secret_key, self._passphrase)

        # 注册心跳定时任务
        LoopRunTask.register(self.check_asset_update, self._update_interval)

    async def check_asset_update(self, *args, **kwargs):
        """ 检查账户资金是否更新
        """
        result, error = await self._rest_api.get_user_account()
        if error:
            logger.warn("platform:", self._platform, "account:", self._account, "get asset info failed!", caller=self)
            return

        assets = {}
        for item in result:
            symbol = item["currency"]
            total = float(item["balance"])
            free = float(item["available"])
            locked = float(item["frozen"])
            if total > 0:
                assets[symbol] = {
                    "total": "%.8f" % total,
                    "free": "%.8f" % free,
                    "locked": "%.8f" % locked
                }

        if assets == self._assets:
            update = False
        else:
            update = True
        self._assets = assets

        # 推送当前资产
        timestamp = tools.get_cur_timestamp_ms()
        EventAsset(self._platform, self._account, self._assets, timestamp, update).publish()
        logger.info("platform:", self._platform, "account:", self._account, "asset:", self._assets, caller=self)
