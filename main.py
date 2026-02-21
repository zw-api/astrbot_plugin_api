from astrbot.api.event import filter, AstrMessageEvent, MessageEventResult
from astrbot.api.star import Context, Star, register
from astrbot.api import logger
from datetime import datetime
from typing import Dict

@register("helloworld", "YourName", "一个简单的 Hello World 插件", "1.0.0")
class MyPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)

    async def initialize(self):
        """可选择实现异步的插件初始化方法，当实例化该插件类之后会自动调用该方法。"""

    # 注册指令的装饰器。指令名为 helloworld。注册成功后，发送 `/helloworld` 就会触发这个指令，并回复 `你好, {user_name}!`
    @filter.command("helloworld")
    async def helloworld(self, event: AstrMessageEvent):
        """这是一个 hello world 指令""" # 这是 handler 的描述，将会被解析方便用户了解插件内容。建议填写。
        user_name = event.get_sender_name()
        message_str = event.message_str # 用户发的纯文本消息字符串
        message_chain = event.get_messages() # 用户所发的消息的消息链 # from astrbot.api.message_components import *
        logger.info(message_chain)
        yield event.plain_result(f"Hello, {user_name}, 你发了 {message_str}!") # 发送一条纯文本消息

    # 菜单数据定义 - 方便后续扩展
    MENU_ITEMS: Dict[str, Dict] = {
        "1": {
            "name": "demo",
            "description": "演示功能",
            "handler": "demo"
        },
        "2": {
            "name": "测试",
            "description": "测试功能",
            "handler": "test"
        }
    }

    def format_menu(self) -> str:
        """格式化菜单输出"""
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        menu_lines = [current_time, "---作文菜单---"]
        
        for key, item in self.MENU_ITEMS.items():
            menu_lines.append(f"{key}.{item['name']}")
        
        menu_lines.append("---作文菜单---")
        return "\n".join(menu_lines)

    # 作文菜单指令 - 唯一的入口命令
    @filter.command("作文菜单")
    async def composition_menu(self, event: AstrMessageEvent):
        """作文功能菜单"""
        user_id = event.get_sender_id()
        
        # 设置用户状态为等待菜单选择
        await self.put_kv_data(f"menu_waiting_{user_id}", True)
        
        # 初始化错误计数
        await self.put_kv_data(f"menu_error_count_{user_id}", 0)
        
        # 显示菜单
        yield event.plain_result(self.format_menu())

    # 监听所有消息，处理菜单选择
    @filter.event_message_type(filter.EventMessageType.ALL)
    async def handle_menu_selection(self, event: AstrMessageEvent):
        """处理菜单选择"""
        user_id = event.get_sender_id()
        message_str = event.message_str.strip()
        
        logger.info(f"监听器触发 - 用户ID: {user_id}, 消息: {message_str}")
        
        # 检查用户是否在等待菜单选择
        is_waiting = await self.get_kv_data(f"menu_waiting_{user_id}", False)
        logger.info(f"等待状态: {is_waiting}")
        
        if not is_waiting:
            return
        
        # 跳过空消息
        if not message_str:
            return
        
        # 过滤掉命令本身（作文菜单）
        if message_str == "作文菜单":
            logger.info(f"跳过命令消息: {message_str}")
            return
        
        # 检查是否匹配菜单项（数字或名称）
        selected_item = None
        
        # 处理可能的命令格式（如 /1 或 /demo）
        normalized_message = message_str
        if normalized_message.startswith('/'):
            normalized_message = normalized_message[1:]  # 去掉开头的 /
        
        for key, item in self.MENU_ITEMS.items():
            logger.info(f"检查匹配 - key: '{key}', name: '{item['name']}', message: '{message_str}', normalized: '{normalized_message}'")
            logger.info(f"  条件1: message_str == key: {message_str == key}")
            logger.info(f"  条件2: message_str == item['name']: {message_str == item['name']}")
            logger.info(f"  条件3: normalized_message == key: {normalized_message == key}")
            logger.info(f"  条件4: normalized_message == item['name']: {normalized_message == item['name']}")
            
            if (message_str == key or message_str == item['name'] or 
                normalized_message == key or normalized_message == item['name']):
                selected_item = item
                logger.info(f"匹配成功: {selected_item}")
                break
        
        if selected_item:
            # 清除等待状态和错误计数
            await self.delete_kv_data(f"menu_waiting_{user_id}")
            await self.delete_kv_data(f"menu_error_count_{user_id}")
            
            # 执行对应功能
            handler_name = selected_item['handler']
            if handler_name == "demo":
                for result in self.handle_demo(event):
                    yield result
            elif handler_name == "test":
                for result in self.handle_test(event):
                    yield result
        else:
            # 不匹配任何菜单项，静默增加错误计数
            error_count = await self.get_kv_data(f"menu_error_count_{user_id}", 0)
            error_count += 1
            await self.put_kv_data(f"menu_error_count_{user_id}", error_count)
            logger.info(f"错误计数: {error_count}")
            
            # 检查是否超过3次错误
            if error_count >= 3:
                # 清除所有状态
                await self.delete_kv_data(f"menu_waiting_{user_id}")
                await self.delete_kv_data(f"menu_error_count_{user_id}")
                yield event.plain_result("错误次数过多，已取消菜单选择。请重新输入 /作文菜单 来查看菜单。")

    def handle_demo(self, event: AstrMessageEvent):
        """处理demo功能"""
        user_name = event.get_sender_name()
        demo_content = f"""
【作文演示功能】

你好，{user_name}！

这是一个演示功能的示例。

功能说明：
- 支持作文模板生成
- 支持作文评分
- 支持作文批改

使用方法：
输入 /作文菜单 查看完整菜单
"""
        yield event.plain_result(demo_content.strip())

    def handle_test(self, event: AstrMessageEvent):
        """处理测试功能"""
        user_name = event.get_sender_name()
        test_result = f"""
【测试功能】

用户：{user_name}
时间：{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

测试项目：
✓ 消息接收测试 - 通过
✓ 响应生成测试 - 通过
✓ 时间格式化测试 - 通过
✓ 用户信息获取测试 - 通过

所有测试项目均已完成！
"""
        yield event.plain_result(test_result.strip())

    async def terminate(self):
        """可选择实现异步的插件销毁方法，当插件被卸载/停用时会调用。"""
