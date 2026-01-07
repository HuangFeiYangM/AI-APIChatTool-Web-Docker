from datetime import datetime
import pytz

# 情况1：默认无时区（naive datetime）
now_naive = datetime.now()  # 使用系统时区
print(now_naive)  # 2024-01-15 10:30:00（时区不明确）

# 情况2：明确指定时区（推荐）
from datetime import timezone

# 使用 UTC 时区
now_utc = datetime.now(timezone.utc)  # 2024-01-15 02:30:00+00:00

# 使用特定时区
tz_shanghai = pytz.timezone('Asia/Shanghai')
now_shanghai = datetime.now(tz_shanghai)  # 2024-01-15 10:30:00+08:00
