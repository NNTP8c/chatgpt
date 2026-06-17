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
                # storage_state=f"auths/auth_{iteration}.json"
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

            # Mở trang mailtemp.vn để lấy email tạm thời
            page_mail = context.new_page()
            page_mail.goto("https://mailtemp.vn/")

            ramdom_mail_btn = page_mail.locator("#random-domain-mailbox")
            copy_btn = page_mail.locator("#copy-mailbox")

            ramdom_mail_btn.wait_for(state="visible")
            ramdom_mail_btn.click()
            page_mail.wait_for_timeout(2000)

            copy_btn.wait_for(state="visible")
            copy_btn.click()
            name_mail = pyperclip.paste()

            password_locator = page_mail.locator(".sidebar-mailbox__secret code")
            if password_locator.count() > 0:
                pass_mail = password_locator.text_content().strip()
            else:
                pass_mail = None

            print(f"Name mail: {name_mail}")
            print(f"Pass mail: {pass_mail}")


            # Mở trang chatgpt.com để đăng ký tài khoản
            page_gpt = context.new_page()
            page_gpt.goto("https://www.chatgpt.com/")

            login_btn = page_gpt.locator(
                "button div.flex.items-center.justify-center"
            ).first

            login_btn.wait_for(state="visible")
            login_btn.click()
            page_gpt.wait_for_timeout(2000)

            page_gpt.locator("input#email").fill(name_mail)
            page_gpt.wait_for_timeout(2000)

            page_gpt.locator('button[type="submit"]').click()
            page_gpt.wait_for_timeout(5000)


            # Lấy mã xác nhận từ mailtemp.vn
            page_mail.bring_to_front()
            page_mail.wait_for_selector("button.copy-code-button")
            _pass = page_mail.locator("button.copy-code-button").get_attribute("data-code")
            print(f"Mã xác nhận: {_pass}")
            page_mail.wait_for_timeout(2000)


            # Nhập mã xác nhận vào trang chatgpt.com
            page_gpt.bring_to_front()
            code_input = page_gpt.locator('input[name="code"]')
            code_input.wait_for(state="visible")
            code_input.fill(_pass)
            page_gpt.wait_for_timeout(2000)
            page_gpt.locator('button[name="intent"][value="validate"]').click()
            page_gpt.wait_for_timeout(5000)

            # Chọn ngẫu nhiên tên từ danh sách
            full_name = random.choice(names)

            page_gpt.wait_for_selector('input[name="name"]')
            page_gpt.locator('input[name="name"]').fill(full_name)
            page_gpt.wait_for_timeout(2000)
            print(f"Đã nhập: {full_name}")

            age = str(random.randint(18, 60))
            page_gpt.wait_for_selector('input[name="age"]')
            page_gpt.locator('input[name="age"]').fill(age)
            page_gpt.wait_for_timeout(2000)
            print(f"Tuổi: {age}")

            page_gpt.locator('button._root_2sicu_62._primary_2sicu_111').click()
            page_gpt.wait_for_timeout(5000)

            continue_btn = page_gpt.locator('button.btn.btn-primary.btn-large')
            continue_btn.wait_for(state="visible")
            continue_btn.click()

            # Ghi dữ liệu: Nối thêm (Append) vào file acc_gpt.csv
            with open(csv_file, "a", newline="", encoding="utf-8-sig") as f:
                writer = csv.writer(f)
                writer.writerow([name_mail, pass_mail, full_name, age])
            print("Đã lưu vào acc_gpt.csv")

            # Lưu trạng thái: Xuất file auth.json riêng biệt cho từng vòng lặp
            os.makedirs("auths", exist_ok=True)
            auth_file = f"auths/auth_{iteration}.json"
            context.storage_state(path=auth_file)
            print(f"Đã lưu trạng thái auth vào {auth_file}")

        except Exception as e:
            print(f"Có lỗi xảy ra ở vòng lặp thứ {iteration}: {e}")

        finally:
            # Đóng trình duyệt và bắt đầu vòng lặp mới
            if context:
                context.close()
            if browser:
                browser.close()
            print(f"Đã đóng trình duyệt vòng lặp {iteration}. Chuẩn bị bắt đầu vòng lặp mới...\n")