import time

class Timer:
    def __init__(self):
        self.start_time = None
        self.end_time = None
        self.note = None

    def start(self, note: str = ""):
        """开始计时，可以添加备注说明"""
        self.start_time = time.time()
        self.end_time = None
        self.note = note
        if note:
            print(f"计时开始...（备注：{note}）")
        else:
            print("计时开始...")

    def end(self):
        """结束计时并返回耗时（秒）"""
        if self.start_time is None:
            raise ValueError("请先调用 start() 再调用 end()")
        self.end_time = time.time()
        duration = self.end_time - self.start_time
        if self.note:
            print(f"计时结束（备注：{self.note}），用时 {duration:.4f} 秒")
        else:
            print(f"计时结束，用时 {duration:.4f} 秒")
        return duration