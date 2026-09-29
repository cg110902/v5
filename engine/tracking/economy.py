"""Novel Studio 5.0 资金池复式流水账本中枢 (Economy Ledger Manager)。

纯数值计算与账户借贷记账，零体裁货币硬编码。
支持任意题材的货币或资源键（如 credits, gold, energy_points, bullets 等）。
"""
from typing import Dict, Any, List, Optional
from engine.errors import BusinessError


class EconomyManager:
    """通用资金池与复式记账管理器"""

    def __init__(self, ledger_data: Optional[Dict[str, Any]] = None):
        self.ledger_data = ledger_data or {"pools": {}, "transactions": []}
        if "pools" not in self.ledger_data or not isinstance(self.ledger_data["pools"], dict):
            self.ledger_data["pools"] = {}
        if "transactions" not in self.ledger_data or not isinstance(self.ledger_data["transactions"], list):
            self.ledger_data["transactions"] = []

    def get_balance(self, pool_key: str) -> int:
        """获取指定资源池余额"""
        return int(self.ledger_data["pools"].get(pool_key, 0))

    def record_income(self, pool_key: str, amount: int, desc: str = "", chapter: int = 0) -> int:
        """记录收入（加法）"""
        cur = self.get_balance(pool_key)
        new_balance = cur + amount
        self.ledger_data["pools"][pool_key] = new_balance
        self.ledger_data["transactions"].append({
            "chapter": chapter,
            "type": "income",
            "pool": pool_key,
            "amount": amount,
            "balance_after": new_balance,
            "desc": desc
        })
        return new_balance

    def record_expense(self, pool_key: str, amount: int, desc: str = "", chapter: int = 0) -> int:
        """记录支出（减法，透支拦截）"""
        cur = self.get_balance(pool_key)
        if cur < amount:
            raise BusinessError(
                f"资源池透支阻断：账户 [{pool_key}] 当前余额为 {cur}，无法支出 {amount}！",
                remediation=f"请调整消费额度，或在前序情节中补充该账户的入账收益。"
            )
        new_balance = cur - amount
        self.ledger_data["pools"][pool_key] = new_balance
        self.ledger_data["transactions"].append({
            "chapter": chapter,
            "type": "expense",
            "pool": pool_key,
            "amount": amount,
            "balance_after": new_balance,
            "desc": desc
        })
        return new_balance
