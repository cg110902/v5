"""Novel Studio 5.0 异常体系与退出码契约。

退出码物理映射契约：
- 0: 正常执行成功放行
- 1: 业务与守卫阻断（BusinessError / GuardError：如已故角色登场、空正文、事务预检冲突、体检不合格）
- 2: CLI 参数语法错误（CLIArgumentError：如缺少参数、工作区不存在、子命令未知）
- 3: 环境依赖异常（EnvironmentError：如 Python 版本过低）
- 4: 存储与系统故障（StorageError / SystemError：如 JSON 文件损坏隔离、磁盘写入受阻）
"""

class StudioError(Exception):
    """Novel Studio 顶层基类异常"""
    exit_code = 1

    def __init__(self, message: str, remediation: str = ""):
        super().__init__(message)
        self.message = message
        self.remediation = remediation

    def formatted(self) -> str:
        out = f"❌ 【阻断原因】：{self.message}"
        if self.remediation:
            out += f"\n💡 【解决方案】：{self.remediation}"
        return out


class BusinessError(StudioError):
    """业务逻辑阻断（体检有 errors、数据不平、ID 冲突等）"""
    exit_code = 1


class GuardError(BusinessError):
    """物理硬守卫阻断（死者复活闸门、空正文封存拦截、法定事实冲突）"""
    exit_code = 1


class CLIArgumentError(StudioError):
    """命令行参数错误"""
    exit_code = 2


class EnvironmentError(StudioError):
    """运行环境与 Python 版本不满足要求"""
    exit_code = 3


class StorageError(StudioError):
    """存储原子写盘异常或数据文件严重损坏已隔离"""
    exit_code = 4
