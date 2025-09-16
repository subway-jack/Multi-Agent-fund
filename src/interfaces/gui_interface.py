import pygame
import sys
import threading
import time
from typing import Dict, List, Optional
from src.models.models import Stock, MarketData
from src.core.trading_system import TradingEngine
from src.core.banker_interface import BankerInterface
from src.interfaces.visualization import RealTimeVisualizer
from src.core.price_engine import PriceEngine
from src.core.ai_traders import TraderManager
from src.utils.font_loader import font_manager
from src.core.app import app

class Button:
    def __init__(self, x, y, width, height, text, color=(100, 100, 100), text_color=(255, 255, 255)):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.color = color
        self.text_color = text_color
        self.font = font_manager.get_font('normal')
        self.clicked = False
    
    def draw(self, screen):
        pygame.draw.rect(screen, self.color, self.rect)
        pygame.draw.rect(screen, (0, 0, 0), self.rect, 2)
        text_surface = self.font.render(self.text, True, self.text_color)
        text_rect = text_surface.get_rect(center=self.rect.center)
        screen.blit(text_surface, text_rect)
    
    def is_clicked(self, pos):
        return self.rect.collidepoint(pos)

class InputBox:
    def __init__(self, x, y, width, height, placeholder=""):
        self.rect = pygame.Rect(x, y, width, height)
        self.color_inactive = pygame.Color('lightskyblue3')
        self.color_active = pygame.Color('dodgerblue2')
        self.color = self.color_inactive
        self.active = False
        self.text = ''
        self.placeholder = placeholder
        self.font = font_manager.get_font('normal')
    
    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos):
                self.active = not self.active
            else:
                self.active = False
            self.color = self.color_active if self.active else self.color_inactive
        
        if event.type == pygame.KEYDOWN:
            if self.active:
                if event.key == pygame.K_RETURN:
                    self.active = False
                    self.color = self.color_inactive
                elif event.key == pygame.K_BACKSPACE:
                    self.text = self.text[:-1]
                else:
                    self.text += event.unicode
    
    def draw(self, screen):
        pygame.draw.rect(screen, self.color, self.rect)
        pygame.draw.rect(screen, (0, 0, 0), self.rect, 2)
        
        display_text = self.text if self.text else self.placeholder
        text_color = (0, 0, 0) if self.text else (128, 128, 128)
        text_surface = self.font.render(display_text, True, text_color)
        screen.blit(text_surface, (self.rect.x + 5, self.rect.y + 5))

class StockSimulatorGUI:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((1400, 900))
        pygame.display.set_caption("股票模拟器 - 交易平台")
        
        # 使用应用程序实例
        app.initialize()
        self.stocks = app.get_stocks()
        self.market_data = app.get_component('market_data')
        self.trader_manager = app.get_component('trader_manager')
        self.price_engine = app.get_component('price_engine')
        self.trading_engine = app.get_component('trading_engine')
        self.banker = app.get_component('banker')
        self.visualizer = app.get_component('visualizer')
        self.user_trader = app.get_component('user_trader')
        
        # GUI组件 - 使用统一的字体管理器
        font_manager.initialize()
        self.font = font_manager.get_font('normal')
        self.title_font = font_manager.get_font('title')
        self.small_font = font_manager.get_font('small')
        
        # 页面管理
        self.current_page = 'home'  # 'home', 'player', 'banker'
        self.pages = ['home', 'player', 'banker']
        
        # 导航按钮
        self.nav_buttons = {
            'home': Button(50, 50, 100, 40, "首页", (0, 120, 200)),
            'player': Button(160, 50, 100, 40, "玩家操作", (0, 150, 0)),
            'banker': Button(270, 50, 100, 40, "庄家操作", (200, 120, 0)),
            'back': Button(50, 50, 80, 30, "返回", (100, 100, 100))
        }
        
        # 首页按钮
        self.home_buttons = {
            'start_sim': Button(50, 120, 150, 50, "开始模拟", (0, 150, 0)),
            'stop_sim': Button(220, 120, 150, 50, "停止模拟", (200, 100, 0)),
            'reset_account': Button(50, 180, 150, 40, "重置账户", (100, 100, 0))
        }
        
        # 用户交易按钮
        self.trading_buttons = {
            'buy_stock': Button(50, 300, 120, 40, "买入", (0, 150, 0)),
            'sell_stock': Button(180, 300, 120, 40, "卖出", (150, 0, 0)),
            'refresh_account': Button(310, 300, 120, 40, "刷新账户", (0, 100, 150))
        }
        
        # 庄家操控按钮
        self.banker_buttons = {
            'trend_up': Button(50, 150, 150, 40, "上涨趋势", (0, 150, 0)),
            'trend_down': Button(220, 150, 150, 40, "下跌趋势", (150, 0, 0)),
            'crash': Button(50, 200, 150, 40, "市场崩盘", (200, 0, 0)),
            'boom': Button(220, 200, 150, 40, "市场暴涨", (0, 200, 0)),
            'reset_market': Button(50, 250, 150, 40, "重置市场", (100, 0, 100)),
            'volatility_high': Button(220, 250, 150, 40, "高波动", (150, 100, 0))
        }
        
        # 输入框
        self.input_boxes = {
            'stock_symbol': InputBox(50, 250, 120, 35, "股票代码"),
            'trade_quantity': InputBox(180, 250, 120, 35, "交易数量"),
            'trend_value': InputBox(50, 300, 120, 35, "趋势强度"),
            'volatility_value': InputBox(220, 300, 120, 35, "波动率"),
            'initial_balance': InputBox(380, 180, 120, 35, "初始资金")
        }
        
        # 状态变量
        self.selected_stock = 'AAPL'  # 默认选择的股票
        self.account_info = {}
        
        # 状态
        self.clock = pygame.time.Clock()
        
        # 添加缺失的按钮字典
        self.buttons = self.home_buttons
        
        # 市场数据显示区域
        self.market_data_rect = pygame.Rect(500, 50, 850, 800)
        
    def start_simulation_thread(self):
        """启动模拟线程"""
        if not self.simulation_running:
            self.simulation_running = True
            self.simulation_thread = threading.Thread(target=self.simulation_loop, daemon=True)
            self.simulation_thread.start()
    
    def simulation_loop(self):
        """模拟循环"""
        while self.simulation_running:
            try:
                current_time = time.time()
                
                # AI交易者决策
                decisions = self.trader_manager.get_all_decisions(current_time)
                for decision in decisions:
                    if decision:
                        self.trading_engine.place_order(decision)
                
                # 价格更新
                self.price_engine.update_all_prices()
                
                # 清理过期订单
                self.trading_engine.cleanup_expired_orders()
                
                time.sleep(0.1)  # 100ms间隔
            except Exception as e:
                print(f"模拟循环错误: {e}")
                break
    
    def handle_navigation(self, event):
        """处理页面导航"""
        if event.type == pygame.MOUSEBUTTONDOWN:
            pos = pygame.mouse.get_pos()
            
            # 检查导航按钮
            if self.current_page == 'home':
                if self.nav_buttons['player'].is_clicked(pos):
                    self.current_page = 'player'
                elif self.nav_buttons['banker'].is_clicked(pos):
                    self.current_page = 'banker'
            elif self.current_page in ['player', 'banker']:
                if self.nav_buttons['back'].is_clicked(pos):
                    self.current_page = 'home'
    
    def handle_home_events(self, event):
        """处理首页事件"""
        # 处理输入框事件
        self.input_boxes['initial_balance'].handle_event(event)
        
        if event.type == pygame.MOUSEBUTTONDOWN:
            pos = pygame.mouse.get_pos()
            
            # 检查首页按钮
            for button_name, button in self.home_buttons.items():
                if button.is_clicked(pos):
                    self.handle_button_click(button_name)
    
    def handle_player_events(self, event):
         """处理玩家页面事件"""
         # 处理输入框
         for input_box in self.input_boxes.values():
             input_box.handle_event(event)
         
         if event.type == pygame.MOUSEBUTTONDOWN:
             pos = pygame.mouse.get_pos()
             
             # 检查交易按钮
             for button_name, button in self.trading_buttons.items():
                 if button.is_clicked(pos):
                     self.handle_trading_click(button_name)
             
             # 检查股票选择
             self.handle_player_stock_selection(pos)
    
    def handle_player_stock_selection(self, pos):
        """处理玩家页面的股票选择"""
        if not self.market_data:
            return
        
        x, y = pos
        # 检查是否点击在股票列表区域
        if 30 <= x <= 450 and 480 <= y <= 650:
            # 计算点击的股票索引
            stock_index = (y - 480) // 35
            stock_symbols = list(self.market_data.stocks.keys())
            
            if 0 <= stock_index < len(stock_symbols):
                self.selected_stock = stock_symbols[stock_index]
                # 更新输入框中的股票代码
                self.input_boxes['stock_symbol'].text = self.selected_stock
                print(f"选择股票: {self.selected_stock}")
    
    def handle_banker_events(self, event):
        """处理庄家页面事件"""
        # 处理输入框
        for input_box in self.input_boxes.values():
            input_box.handle_event(event)
        
        if event.type == pygame.MOUSEBUTTONDOWN:
            pos = pygame.mouse.get_pos()
            
            # 检查庄家按钮
            for button_name, button in self.banker_buttons.items():
                if button.is_clicked(pos):
                    self.handle_banker_click(button_name)
    
    def handle_button_click(self, button_name):
        """处理按钮点击"""
        if button_name == 'start_sim':
            app.start_simulation()
        elif button_name == 'stop_sim':
            app.stop_simulation()
        elif button_name == 'reset_market':
            app.reset()
        elif button_name == 'reset_account':
            balance_text = self.input_boxes['initial_balance'].text
            try:
                balance = float(balance_text) if balance_text else 100000.0
                self.user_trader.reset_account(balance)
                self.account_info = self.user_trader.get_account_info()
            except ValueError:
                print("❌ 无效的初始资金金额")
    
    def handle_trading_click(self, button_name):
        """处理交易按钮点击"""
        if button_name == 'refresh_account':
            self.account_info = self.user_trader.get_account_info()
            return
        
        symbol = self.input_boxes['stock_symbol'].text or self.selected_stock
        quantity_text = self.input_boxes['trade_quantity'].text or '100'
        
        try:
            quantity = int(quantity_text)
        except ValueError:
            print("❌ 无效的交易数量")
            return
        
        if button_name == 'buy_stock':
            result = self.user_trader.buy_stock(symbol, quantity)
            print(result['message'])
            if result['success']:
                self.account_info = self.user_trader.get_account_info()
        elif button_name == 'sell_stock':
            result = self.user_trader.sell_stock(symbol, quantity)
            print(result['message'])
            if result['success']:
                self.account_info = self.user_trader.get_account_info()
    
    def handle_banker_click(self, button_name):
        """处理庄家操控按钮点击"""
        try:
            if button_name == 'trend_up':
                # 获取趋势强度输入
                trend_value = self.input_boxes['trend_value'].text
                strength = float(trend_value) if trend_value else 0.05
                self.banker.set_market_trend(abs(strength))
                print(f"设置上涨趋势: {strength*100:.1f}%")
            elif button_name == 'trend_down':
                # 获取趋势强度输入
                trend_value = self.input_boxes['trend_value'].text
                strength = float(trend_value) if trend_value else 0.05
                self.banker.set_market_trend(-abs(strength))
                print(f"设置下跌趋势: {strength*100:.1f}%")
            elif button_name == 'crash':
                self.banker.trigger_market_crash()
                print("触发市场崩盘")
            elif button_name == 'boom':
                self.banker.trigger_market_boom()
                print("触发市场暴涨")
            elif button_name == 'reset_market':
                self.banker.reset_market_controls()
                print("重置市场控制")
            elif button_name == 'volatility_high':
                # 获取波动率输入
                vol_value = self.input_boxes['volatility_value'].text
                volatility = float(vol_value) if vol_value else 0.1
                # 设置高波动率（这里需要在价格引擎中实现）
                print(f"设置高波动率: {volatility*100:.1f}%")
        except ValueError:
            print("输入值无效，请输入数字")
        except Exception as e:
            print(f"庄家操作错误: {e}")
    
    def handle_stock_selection(self, pos):
        """处理股票选择"""
        # 股票列表区域
        y_start = 480  # 股票列表开始位置
        y_offset = y_start
        
        stocks = self.user_trader.get_available_stocks()
        
        for i, stock in enumerate(stocks[:8]):
            # 检查点击是否在股票行内
            stock_rect = pygame.Rect(25, y_offset - 2, 400, 18)
            if stock_rect.collidepoint(pos):
                self.selected_stock = stock['symbol']
                # 更新股票输入框
                self.input_boxes['stock_symbol'].text = stock['symbol']
                break
            y_offset += 20
    
    def handle_manipulation_click(self, button_name):
        """处理操控按钮点击"""
        symbol = self.input_boxes['stock_symbol'].text or 'AAPL'
        value_text = self.input_boxes['manipulation_value'].text or '10'
        amount_text = self.input_boxes['order_amount'].text or '100'
        
        try:
            value = float(value_text)
            amount = int(amount_text)
        except ValueError:
            return
        
        if button_name == 'manipulate_up':
            self.banker.manipulate_price(symbol, value)
        elif button_name == 'manipulate_down':
            self.banker.manipulate_price(symbol, -value)
        elif button_name == 'big_buy':
            self.banker.place_large_order(symbol, 'buy', amount, value)
        elif button_name == 'big_sell':
            self.banker.place_large_order(symbol, 'sell', amount, value)
    
    def draw_market_data(self):
        """绘制市场数据"""
        # 背景
        pygame.draw.rect(self.screen, (240, 240, 240), self.market_data_rect)
        pygame.draw.rect(self.screen, (0, 0, 0), self.market_data_rect, 2)
        
        y_offset = self.market_data_rect.y + 10
        
        # 标题
        title = self.title_font.render("市场实时数据", True, (0, 0, 0))
        self.screen.blit(title, (self.market_data_rect.x + 10, y_offset))
        y_offset += 50
        
        # 股票价格
        for symbol, stock in self.market_data.stocks.items():
            # 计算价格变化
            price_change = 0
            if len(stock.price_history) >= 2:
                price_change = stock.current_price - stock.price_history[-2]
            
            price_text = f"{symbol} ({stock.name}): ${stock.current_price:.2f}"
            if price_change != 0:
                change_text = f" ({price_change:+.2f})"
                price_text += change_text
            
            color = (0, 150, 0) if price_change >= 0 else (150, 0, 0)
            text_surface = self.font.render(price_text, True, color)
            self.screen.blit(text_surface, (self.market_data_rect.x + 10, y_offset))
            y_offset += 30
        
        y_offset += 20
        
        # 交易统计
        stats = self.trading_engine.get_market_summary()
        stats_text = [
            f"总交易量: {stats.get('total_volume', 0)}",
            f"总交易额: ${stats.get('total_value', 0):.2f}",
            f"待处理订单: {stats.get('pending_orders', 0)}",
            f"已完成交易: {stats.get('total_trades', 0)}"
        ]
        
        for text in stats_text:
            text_surface = self.font.render(text, True, (0, 0, 0))
            self.screen.blit(text_surface, (self.market_data_rect.x + 10, y_offset))
            y_offset += 25
        
        y_offset += 20
        
        # 交易者表现
        trader_stats = self.trading_engine.get_trader_performance()
        if trader_stats:
            performance_title = self.font.render("交易者表现 (前10名):", True, (0, 0, 0))
            self.screen.blit(performance_title, (self.market_data_rect.x + 10, y_offset))
            y_offset += 30
            
            for i, (trader_id, stats) in enumerate(list(trader_stats.items())[:10]):
                pnl = stats['total_pnl']
                color = (0, 150, 0) if pnl >= 0 else (150, 0, 0)
                trader_text = f"{i+1}. {trader_id[:8]}... PnL: ${pnl:.2f}"
                text_surface = self.small_font.render(trader_text, True, color)
                self.screen.blit(text_surface, (self.market_data_rect.x + 10, y_offset))
                y_offset += 20
        
        # 庄家操控历史
        y_offset += 20
        history_title = self.font.render("最近操控记录:", True, (0, 0, 0))
        self.screen.blit(history_title, (self.market_data_rect.x + 10, y_offset))
        y_offset += 30
        
        history = self.banker.get_manipulation_history()[-5:]  # 最近5条
        for record in history:
            # 将时间戳转换为可读格式
            import datetime
            timestamp = datetime.datetime.fromtimestamp(record['timestamp'])
            history_text = f"{timestamp.strftime('%H:%M:%S')} - {record['action']}"
            text_surface = self.small_font.render(history_text, True, (100, 100, 100))
            self.screen.blit(text_surface, (self.market_data_rect.x + 10, y_offset))
            y_offset += 20
    
    def update_display(self):
        """更新显示"""
        # 清屏
        self.screen.fill((255, 255, 255))
        
        # 根据当前页面绘制内容
        if self.current_page == 'home':
            self.draw_home_page()
        elif self.current_page == 'player':
            self.draw_player_page()
        elif self.current_page == 'banker':
            self.draw_banker_page()
        
        # 绘制市场数据（所有页面都显示）
        self.draw_market_data()
        
        pygame.display.flip()
    
    def draw_home_page(self):
        """绘制首页"""
        # 导航栏
        self.draw_navigation()
        
        # 控制面板背景
        panel_rect = pygame.Rect(20, 100, 460, 780)
        pygame.draw.rect(self.screen, (240, 240, 240), panel_rect)
        pygame.draw.rect(self.screen, (200, 200, 200), panel_rect, 2)
        
        # 标题
        title_text = self.title_font.render("股票交易平台", True, (50, 50, 50))
        self.screen.blit(title_text, (30, 110))
        
        # 绘制首页按钮
        for button in self.home_buttons.values():
            button.draw(self.screen)
        
        # 状态显示
        simulation_running = app.is_simulation_running()
        status_text = "模拟运行中" if simulation_running else "模拟已停止"
        status_color = (0, 150, 0) if simulation_running else (150, 0, 0)
        status_surface = self.font.render(f"状态: {status_text}", True, status_color)
        self.screen.blit(status_surface, (30, 200))
        
        # 初始资金输入框
        balance_label = self.font.render("初始资金:", True, (0, 0, 0))
        self.screen.blit(balance_label, (380, 150))
        self.input_boxes['initial_balance'].draw(self.screen)
        
        # 欢迎信息
        welcome_texts = [
            "欢迎使用股票模拟交易系统！",
            "",
            "功能介绍：",
            "• 玩家操作：进行股票买卖交易",
            "• 庄家操作：控制市场走势",
            "• 实时数据：查看市场动态",
            "",
            "请选择相应页面开始操作。"
        ]
        
        y_offset = 250
        for text in welcome_texts:
            if text:
                text_surface = self.font.render(text, True, (0, 0, 0))
                self.screen.blit(text_surface, (30, y_offset))
            y_offset += 30
    
    def draw_player_page(self):
        """绘制玩家操作页面"""
        # 导航栏
        self.draw_navigation()
        
        # 左侧交易面板
        panel_rect = pygame.Rect(20, 100, 460, 780)
        pygame.draw.rect(self.screen, (240, 240, 240), panel_rect)
        pygame.draw.rect(self.screen, (200, 200, 200), panel_rect, 2)
        
        # 标题
        title_text = self.title_font.render("玩家交易面板", True, (50, 50, 50))
        self.screen.blit(title_text, (30, 110))
        
        # 账户信息区域
        account_title = self.font.render("账户信息", True, (0, 0, 0))
        self.screen.blit(account_title, (30, 150))
        
        if not self.account_info:
            self.account_info = self.user_trader.get_account_info()
        
        if self.account_info:
            y_offset = 180
            info_texts = [
                f"余额: ¥{self.account_info.get('balance', 0):,.2f}",
                f"总资产: ¥{self.account_info.get('total_assets', 0):,.2f}",
                f"盈亏: ¥{self.account_info.get('total_profit_loss', 0):+,.2f}",
                f"收益率: {self.account_info.get('total_profit_loss_pct', 0):+.2f}%"
            ]
            for text in info_texts:
                color = (0, 150, 0) if '+' in text else (150, 0, 0) if '-' in text else (0, 0, 0)
                text_surface = self.font.render(text, True, color)
                self.screen.blit(text_surface, (30, y_offset))
                y_offset += 25
        
        # 用户交易区域
        trade_title = self.font.render("股票交易", True, (0, 0, 0))
        self.screen.blit(trade_title, (30, 300))
        
        # 绘制输入框（只显示交易相关的）
        self.input_boxes['stock_symbol'].draw(self.screen)
        self.input_boxes['trade_quantity'].draw(self.screen)
        
        # 绘制交易按钮
        for button in self.trading_buttons.values():
            button.draw(self.screen)
        
        # 账户信息
        self.draw_account_info()
        
        # 可交易股票列表
        self.draw_stock_list()
    
    def draw_banker_page(self):
        """绘制庄家操作页面"""
        # 导航栏
        self.draw_navigation()
        
        # 控制面板背景
        panel_rect = pygame.Rect(20, 100, 460, 780)
        pygame.draw.rect(self.screen, (240, 240, 240), panel_rect)
        pygame.draw.rect(self.screen, (200, 200, 200), panel_rect, 2)
        
        # 标题
        title_text = self.title_font.render("庄家操作面板", True, (50, 50, 50))
        self.screen.blit(title_text, (30, 110))
        
        # 绘制庄家按钮
        for button in self.banker_buttons.values():
            button.draw(self.screen)
        
        # 绘制庄家输入框
        self.input_boxes['trend_value'].draw(self.screen)
        self.input_boxes['volatility_value'].draw(self.screen)
    
    def draw_navigation(self):
        """绘制导航栏"""
        # 导航栏背景
        nav_rect = pygame.Rect(0, 0, 1400, 90)
        pygame.draw.rect(self.screen, (50, 50, 50), nav_rect)
        
        # 绘制导航按钮
        if self.current_page == 'home':
            self.nav_buttons['player'].draw(self.screen)
            self.nav_buttons['banker'].draw(self.screen)
        elif self.current_page in ['player', 'banker']:
            self.nav_buttons['back'].draw(self.screen)
        
        # 当前页面标题
        page_titles = {'home': '首页', 'player': '玩家操作', 'banker': '庄家操作'}
        page_title = page_titles.get(self.current_page, '首页')
        title_text = self.title_font.render(page_title, True, (255, 255, 255))
        self.screen.blit(title_text, (400, 25))
    
    def draw_account_info(self):
        """绘制账户信息"""
        y_start = 320
        
        # 账户信息标题
        account_title = self.font.render("账户信息:", True, (0, 0, 0))
        self.screen.blit(account_title, (30, y_start))
        
        if not self.account_info:
            self.account_info = self.user_trader.get_account_info()
        
        y_offset = y_start + 30
        
        # 显示账户基本信息
        info_texts = [
            f"可用资金: ¥{self.account_info.get('balance', 0):.2f}",
            f"市值: ¥{self.account_info.get('market_value', 0):.2f}",
            f"总资产: ¥{self.account_info.get('total_assets', 0):.2f}",
            f"盈亏: ¥{self.account_info.get('total_profit_loss', 0):.2f}",
            f"收益率: {self.account_info.get('total_profit_loss_pct', 0):.2f}%"
        ]
        
        for text in info_texts:
            color = (0, 0, 0)
            if "盈亏" in text or "收益率" in text:
                value = float(text.split(': ')[-1].replace('¥', '').replace('%', ''))
                color = (0, 150, 0) if value >= 0 else (150, 0, 0)
            
            text_surface = self.small_font.render(text, True, color)
            self.screen.blit(text_surface, (30, y_offset))
            y_offset += 20
    
    def draw_stock_list(self):
        """绘制股票列表"""
        y_start = 450
        
        # 股票列表标题
        stock_title = self.font.render("可交易股票:", True, (0, 0, 0))
        self.screen.blit(stock_title, (30, y_start))
        
        y_offset = y_start + 30
        
        # 获取股票列表
        stocks = self.user_trader.get_available_stocks()
        
        for stock in stocks[:8]:  # 显示前8只股票
            # 股票信息
            change_color = (0, 150, 0) if stock['change_pct'] >= 0 else (150, 0, 0)
            stock_text = f"{stock['symbol']}: ¥{stock['current_price']:.2f} ({stock['change_pct']:+.2f}%)"
            
            # 高亮选中的股票
            if stock['symbol'] == self.selected_stock:
                highlight_rect = pygame.Rect(25, y_offset - 2, 400, 18)
                pygame.draw.rect(self.screen, (200, 220, 255), highlight_rect)
            
            text_surface = self.small_font.render(stock_text, True, change_color)
            self.screen.blit(text_surface, (30, y_offset))
            y_offset += 20
    
    def draw_stock_selection(self):
        """绘制股票选择区域"""
        if not self.market_data:
            return
        
        # 股票选择标题
        stock_title = self.font.render("选择股票", True, (0, 0, 0))
        self.screen.blit(stock_title, (30, 450))
        
        # 绘制股票列表
        y_offset = 480
        for symbol, stock in self.market_data.stocks.items():
            # 股票背景
            stock_rect = pygame.Rect(30, y_offset, 420, 30)
            color = (200, 255, 200) if symbol == self.selected_stock else (255, 255, 255)
            pygame.draw.rect(self.screen, color, stock_rect)
            pygame.draw.rect(self.screen, (150, 150, 150), stock_rect, 1)
            
            # 股票信息
            stock_text = f"{symbol} - {stock.name}: ¥{stock.current_price:.2f}"
            text_surface = self.font.render(stock_text, True, (0, 0, 0))
            self.screen.blit(text_surface, (35, y_offset + 5))
            
            y_offset += 35

    
    def run(self):
        """主循环"""
        running = True
        
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                    app.stop_simulation()
                
                # 处理导航
                self.handle_navigation(event)
                
                # 处理当前页面的事件
                if self.current_page == 'home':
                    self.handle_home_events(event)
                elif self.current_page == 'player':
                    self.handle_player_events(event)
                elif self.current_page == 'banker':
                    self.handle_banker_events(event)
            
            # 更新显示
            self.update_display()
            self.clock.tick(60)
        
        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    gui = StockSimulatorGUI()
    gui.run()