import csv
import random
import json
import os
from playwright.sync_api import sync_playwright
import pyperclip

# --- KHỞI TẠO ---
# 1. Khai báo danh sách User-Agents
profiles_file = "user_agents.json"
if os.path.exists(profiles_file):
    with open(profiles_file, "r", encoding="utf-8") as f:
        profiles = json.load(f)
else:
    profiles = [{
        "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "platform": "Win32",
        "hardware_concurrency": 8,
        "device_memory": 8,
        "languages": ["vi-VN", "vi", "en-US", "en"],
        "locale": "vi-VN",
        "timezone_id": "Asia/Ho_Chi_Minh",
        "viewport": {"width": 1366, "height": 768},
        "screen": {"width": 1366, "height": 768}
    }]

# 2. Mở/tạo file acc_gpt.csv và ghi tiêu đề nếu chưa tồn tại
csv_file = "acc_gpt.csv"
if not os.path.exists(csv_file):
    with open(csv_file, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(["tên mail", "pass mail", "tên user", "tuổi"])

# Đọc danh sách tên từ file names.txt
names_file = "names.txt"
if os.path.exists(names_file):
    with open(names_file, "r", encoding="utf-8") as f:
        names = [line.strip() for line in f if line.strip()]
else:
    names = []
if not names:
    names = ["Nguyễn Văn A"]

# --- VÒNG LẶP VÔ HẠN (while (true)) ---
iteration = 0

with sync_playwright() as p:
    while True:
        user_input = input("\nNhấn Enter để bắt đầu đăng ký tài khoản tiếp theo (hoặc gõ 'exit' rồi Enter để thoát): ")
        if user_input.strip().lower() in ['exit', 'quit', 'q']:
            print("Đã thoát chương trình.")
            break

        iteration += 1
        print(f"\n==========================================")
        print(f"BẮT ĐẦU VÒNG LẶP THỨ: {iteration}")
        print(f"==========================================")

        # Lấy tuần tự một User-Agent từ danh sách
        profile = profiles[(iteration - 1) % len(profiles)]
        print(f"Selected Profile User Agent: {profile['user_agent']}")
        print(f"Platform: {profile['platform']}, Locale: {profile['locale']}, Timezone: {profile['timezone_id']}")

        browser = None
        context = None
        try:
            # Khởi tạo trình duyệt với User-Agent đã chọn
            browser = p.chromium.launch(
                headless=False,
                slow_mo=200,
                args=[
                    "--disable-blink-features=AutomationControlled",
                ]
            )

            context = browser.new_context(
                user_agent=profile["user_agent"],
                locale=profile["locale"],
                timezone_id=profile["timezone_id"],
                viewport=profile["viewport"],
                screen=profile["screen"],
                color_scheme="light",
                device_scale_factor=1,
                has_touch=False,
                is_mobile=False,
                storage_state=f"auths/auth_{4}.json"
            )

            # Spoof navigator properties at the context level
            context.add_init_script(f"""
                Object.defineProperty(navigator, 'webdriver', {{
                    get: () => undefined
                }});

                Object.defineProperty(navigator, 'languages', {{
                    get: () => {profile['languages']}
                }});

                Object.defineProperty(navigator, 'platform', {{
                    get: () => '{profile['platform']}'
                }});

                Object.defineProperty(navigator, 'hardwareConcurrency', {{
                    get: () => {profile['hardware_concurrency']}
                }});

                Object.defineProperty(navigator, 'deviceMemory', {{
                    get: () => {profile['device_memory']}
                }});
            """)

            # Truy cập trang cài đặt bảo mật của ChatGPT
            page_gpt = context.new_page()
            page_gpt.goto("http://chatgpt.com/#settings/Security")
            page_gpt.wait_for_timeout(10000)
            btn_add = page_gpt.get_by_test_id("password-setting")
            btn_add.wait_for(state="visible", timeout=10000)
            btn_add.click()
            page_gpt.wait_for_timeout(5000)

            # Đăng nhập vào mailtemp.vn
            page_mail = context.new_page()
            page_mail.goto("https://mailtemp.vn/")
            btn_login = page_mail.locator("span.account-popover__avatar")
            btn_login.wait_for(state="visible", timeout=10000)
            btn_login.click()
            page_mail.wait_for_timeout(2000)

            input_pass_mail = page_mail.locator("#public-login-password")
            input_pass_mail.wait_for(state="visible", timeout=10000)
            input_pass_mail.fill("LnCJg86n4t")
            page_mail.wait_for_timeout(2000)

            btn_submit_mail = page_mail.locator("#login-mailbox")
            btn_submit_mail.wait_for(state="visible", timeout=10000)
            btn_submit_mail.click()
            page_mail.wait_for_timeout(5000)

            vua_xong = page_mail.locator('article.message-item:has-text("vừa xong")')
            vua_xong.wait_for(state="visible", timeout=10000)
            vua_xong.click()
            _pass = page_mail.locator("button.copy-code-button").get_attribute("data-code")
            print(f"Mã xác nhận: {_pass}")

            page_gpt.bring_to_front()
            page_gpt.locator('input[name="code"]').wait_for()
            page_gpt.locator('input[name="code"]').fill(_pass)
            page_gpt.get_by_role("button", name="Tiếp tục").click()

            password = "MyPassword123@"
            page_gpt.wait_for_selector('input[name="new-password"]')
            page_gpt.locator('input[name="new-password"]').fill(password)
            page_gpt.locator('input[name="confirm-password"]').fill(password)
            page_gpt.locator('button[type="submit"]').click()   

        except Exception as e:
            print(f"Có lỗi xảy ra ở vòng lặp thứ {iteration}: {e}")