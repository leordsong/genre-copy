"""账单查询模块 - 使用火山引擎官方 SDK"""

import volcenginesdkbilling
import volcenginesdkcore
from volcenginesdkcore.rest import ApiException

from .config import config


class BillingClient:
    def __init__(self) -> None:
        self.configuration = volcenginesdkcore.Configuration()
        self.configuration.ak = config.VOLC_ACCESS_KEY
        self.configuration.sk = config.VOLC_SECRET_KEY
        self.configuration.region = "cn-beijing"
        volcenginesdkcore.Configuration.set_default(self.configuration)
        self.api_instance = volcenginesdkbilling.BILLINGApi()

    def query_balance(self) -> dict:
        request = volcenginesdkbilling.QueryBalanceAcctRequest()

        print("\n" + "=" * 60)
        print("【账单查询请求】")
        print(f"AK: {config.VOLC_ACCESS_KEY[:8]}...")
        print(f"Region: cn-beijing")
        print("=" * 60 + "\n")

        try:
            response = self.api_instance.query_balance_acct(request)
            data = response.to_dict()

            print("\n" + "=" * 60)
            print("【账单查询响应】")
            print(f"Response: {data}")
            print("=" * 60 + "\n")

            return {"Result": data}
        except ApiException as e:
            print(f"\n【错误】API Exception: {e}")
            return {"error": str(e)}
        except Exception as e:
            print(f"\n【错误】{str(e)}")
            return {"error": str(e)}

    def format_balance(self, data: dict) -> str:
        if "error" in data:
            return f"❌ 查询失败: {data['error']}"

        if "Result" not in data:
            return f"❌ 响应格式异常: {data}"

        result = data["Result"]
        lines = [
            "📊 账户余额信息",
            "-" * 30,
            f"账户ID: {result.get('account_id', 'N/A')}",
            f"可用余额: ¥{result.get('available_balance', '0')}",
            f"现金余额: ¥{result.get('cash_balance', '0')}",
            f"欠费金额: ¥{result.get('arrears_balance', '0')}",
            f"冻结金额: ¥{result.get('freeze_amount', '0')}",
            f"信用额度: ¥{result.get('credit_limit', '0')}",
        ]
        return "\n".join(lines)


billing_client: BillingClient | None = None


def get_billing_client() -> BillingClient:
    global billing_client
    if billing_client is None:
        billing_client = BillingClient()
    return billing_client
