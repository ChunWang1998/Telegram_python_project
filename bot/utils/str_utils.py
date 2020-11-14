start_message = """
/start
歡迎使用 Telegram@ Like bot (alpha 測試版) !
這是一款測試中的軟體 由 老張軟體 (@changsclub_bot) 提供
使用它表示同意 https://www.changsclub.com 上的用戶協議

使用教學：
將 @{bot_username} 加入您的頻道並成為管理員身分，並轉發頻道內的任何訊息到這裡以啟用服務 。

1️⃣ 開啟頻道的管理員清單並點擊 "新增管理員"
2️⃣ 搜尋 @{bot_username} 並選擇它
3️⃣ 確認開啟 "編輯他人訊息" 權限後，點擊 "儲存"
4️⃣ 轉發頻道內的任何訊息到這裡

設定完成後，頻道裡的每一篇貼文將自動新增按讚按鈕!
"""

channel_added_message = """
<b>頻道名稱： "{channel_title}" 設定成功, 幹得好! </b>

👍 現在起您可以開啟後台儀表板(Dashboard)查看所有數據，甚至更換按鈕圖示!
"""

reaction_added_message = """
您按了這篇文章的 {emoji} 
"""

reaction_removed_message = """
您移除了這篇文章的 {emoji} 
"""

something_went_wrong = """
Oops! 軟體出錯囉 若一直發生的話請聯絡我們 @changsclub_bot 將盡快為您處理喔! 
"""

successful_subscription = """
成功訂閱此篇貼文的留言通知
"""

successful_unsubscription = """
成功關閉此篇貼文的留言通知
"""

comment_not_found = """
沒有找到此篇留言
"""

comment_replied_message = """
{full_name} 已回覆您在 <a href='{post_url}'>這篇貼文</a> 中的留言

<pre>{text}</pre>
"""

comment_left_message = """
{full_name} 已在 <a href='{post_url}'>這篇貼文</a> 中留言

<pre>{text}</pre>
"""

open_dashboard = """
開啟後台儀表板(Dashboard)
"""

unsubscribe = """
取消留言通知
"""

subscribe = """
開啟留言通知
"""

open_comment = """
查看留言
"""

show_all_comments = """
查看所有留言
"""
show_remaining_comments = """
查看上 50 則留言 (共 {remaining_count} 則留言未讀)
"""

one = "1"
two = "2"
three = "3"
button = "按鈕"
